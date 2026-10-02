"""Tests for page-aware document chunking."""

from datetime import UTC, datetime

from app.application.chunking import DocumentChunker
from app.domain.entities import Document
from app.infrastructure.pdf.pypdf_text_extractor import ExtractedPage


def test_chunker_preserves_page_and_document_metadata() -> None:
    """Every chunk should remain traceable to its source document and page."""

    document = Document(
        document_id="doc-1",
        filename="manual.pdf",
        stored_path="data/uploads/doc-1.pdf",
        uploaded_at=datetime.now(UTC),
        page_count=2,
        text_length=200,
        document_hash="abc123",
    )
    pages = [
        ExtractedPage(page_number=1, text="Prima pagina. " * 30),
        ExtractedPage(page_number=2, text="Seconda pagina. " * 30),
    ]

    chunks = DocumentChunker(chunk_size=80, chunk_overlap=10).create_chunks(
        document, pages
    )

    assert chunks
    assert all(chunk.document_id == "doc-1" for chunk in chunks)
    assert all(chunk.document_hash == "abc123" for chunk in chunks)
    assert {chunk.page_number for chunk in chunks} == {1, 2}
    assert [chunk.chunk_index for chunk in chunks] == list(range(len(chunks)))
    assert all(0 < len(chunk.content) <= 80 for chunk in chunks)
