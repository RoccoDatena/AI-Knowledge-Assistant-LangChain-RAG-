"""Tests for the document indexing use case."""

from datetime import UTC, datetime
from pathlib import Path

from app.application.chunking import DocumentChunker
from app.application.indexing import DocumentIndexer
from app.domain.entities import Document
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.pdf.pypdf_text_extractor import ExtractedPage
from app.infrastructure.persistence.json_document_repository import (
    JsonDocumentRepository,
)
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore


class FakeExtractor:
    """Return deterministic page content for the indexing test."""

    def extract(self, content: bytes) -> list[ExtractedPage]:
        assert content == b"pdf-content"
        return [ExtractedPage(page_number=1, text="Informazioni sul prodotto")]


def test_indexer_connects_extraction_chunking_embeddings_and_store(
    tmp_path: Path,
) -> None:
    """Indexing should create searchable vectors from persisted documents."""

    pdf_path = tmp_path / "document.pdf"
    pdf_path.write_bytes(b"pdf-content")
    repository = JsonDocumentRepository(tmp_path / "metadata")
    repository.save(
        Document(
            document_id="doc-1",
            filename="document.pdf",
            stored_path=str(pdf_path),
            uploaded_at=datetime.now(UTC),
            page_count=1,
            text_length=28,
            document_hash="hash-1",
        )
    )
    store = InMemoryVectorStore()
    indexer = DocumentIndexer(
        repository,
        FakeExtractor(),
        DocumentChunker(chunk_size=100, chunk_overlap=10),
        HashingEmbeddingProvider(dimensions=64),
        store,
    )

    assert indexer.index_all() == 1
    results = store.search(
        HashingEmbeddingProvider(dimensions=64).embed_query("prodotto")
    )
    assert results[0].chunk.document_id == "doc-1"
