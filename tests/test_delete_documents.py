"""Tests for complete document deletion."""

from datetime import UTC, datetime
from pathlib import Path

from app.application.documents import DeleteDocumentService
from app.domain.entities import Document, DocumentChunk
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.persistence.json_document_repository import (
    JsonDocumentRepository,
)
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore


def test_delete_document_removes_metadata_file_and_vectors(tmp_path: Path) -> None:
    """Deletion should leave no searchable or stored document resources."""

    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"pdf")
    repository = JsonDocumentRepository(tmp_path / "metadata")
    document = Document(
        document_id="doc-1",
        filename="document.pdf",
        stored_path=str(pdf_path),
        uploaded_at=datetime.now(UTC),
        page_count=1,
        text_length=3,
        document_hash="hash",
    )
    repository.save(document)
    chunk = DocumentChunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="contenuto",
        page_number=1,
        chunk_index=0,
        document_hash="hash",
        filename="document.pdf",
    )
    store = InMemoryVectorStore()
    provider = HashingEmbeddingProvider(dimensions=64)
    store.add([chunk], provider.embed_documents([chunk.content]))

    service = DeleteDocumentService(repository, store)

    assert service.delete("doc-1") is True
    assert not pdf_path.exists()
    assert repository.list() == []
    assert store.search(provider.embed_query("contenuto")) == []
    assert service.delete("doc-1") is False
