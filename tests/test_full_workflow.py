"""Integration test for the complete document-to-answer workflow."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.application.chunking import DocumentChunker
from app.application.documents import DeleteDocumentService
from app.application.indexing import DocumentIndexer
from app.application.retrieval import RetrievalService
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.pdf.pypdf_text_extractor import ExtractedPage
from app.infrastructure.persistence.json_document_repository import (
    JsonDocumentRepository,
)
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore
from app.interfaces.api.document_routes import (
    get_delete_document_service,
    get_document_indexer,
    get_document_repository,
    get_pdf_extractor,
)
from app.interfaces.api.search_routes import get_retrieval_service
from app.main import app


class WorkflowExtractor:
    """Deterministic extractor for the API workflow test."""

    def extract(self, content: bytes) -> list[ExtractedPage]:
        assert content == b"%PDF-fake"
        return [
            ExtractedPage(
                page_number=1,
                text="Il prodotto supporta backup automatici.",
            )
        ]


def test_full_document_workflow(tmp_path: Path, monkeypatch) -> None:
    """The uploaded document should become searchable and then removable."""

    monkeypatch.chdir(tmp_path)
    repository = JsonDocumentRepository(Path("data/documents"))
    extractor = WorkflowExtractor()
    provider = HashingEmbeddingProvider(dimensions=64)
    vector_store = InMemoryVectorStore()
    indexer = DocumentIndexer(
        repository,
        extractor,
        DocumentChunker(chunk_size=100, chunk_overlap=10),
        provider,
        vector_store,
    )
    retrieval = RetrievalService(provider, vector_store)

    app.dependency_overrides[get_document_repository] = lambda: repository
    app.dependency_overrides[get_pdf_extractor] = lambda: extractor
    app.dependency_overrides[get_document_indexer] = lambda: indexer
    app.dependency_overrides[get_retrieval_service] = lambda: retrieval
    app.dependency_overrides[get_delete_document_service] = lambda: (
        DeleteDocumentService(repository, vector_store)
    )

    try:
        with TestClient(app) as client:
            upload = client.post(
                "/documents/upload",
                files={"file": ("manual.pdf", b"%PDF-fake", "application/pdf")},
            )
            document_id = upload.json()["document_id"]
            indexed = client.post("/documents/index")
            search = client.post(
                "/documents/search",
                json={"query": "backup automatici", "min_score": 0.1},
            )
            conversation_id = client.post("/conversations").json()["conversation_id"]
            chat = client.post(
                f"/conversations/{conversation_id}/messages",
                json={"content": "Il prodotto supporta backup?"},
            )
            deleted = client.delete(f"/documents/{document_id}")

        assert upload.status_code == 201
        assert indexed.json()["chunks_indexed"] == 1
        assert search.status_code == 200
        assert search.json()[0]["document_id"] == document_id
        assert chat.status_code == 201
        assert chat.json()["grounded"] is True
        assert chat.json()["sources"][0]["filename"] == "manual.pdf"
        assert deleted.status_code == 204
        assert repository.list() == []
        assert vector_store.search(provider.embed_query("backup")) == []
    finally:
        app.dependency_overrides.clear()
