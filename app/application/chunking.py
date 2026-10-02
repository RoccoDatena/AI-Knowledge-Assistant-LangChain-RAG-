"""Document chunking and source metadata generation."""

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.domain.entities import Document, DocumentChunk
from app.infrastructure.pdf.pypdf_text_extractor import ExtractedPage


class DocumentChunker:
    """Split page text while preserving source traceability."""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150) -> None:
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def create_chunks(
        self,
        document: Document,
        pages: list[ExtractedPage],
    ) -> list[DocumentChunk]:
        """Create chunks with one-based page and zero-based chunk indexes."""

        chunks: list[DocumentChunk] = []
        chunk_index = 0
        for page in pages:
            page_chunks = self._splitter.split_text(page.text)
            for content in page_chunks:
                chunks.append(
                    DocumentChunk(
                        chunk_id=f"{document.document_id}:{chunk_index}",
                        document_id=document.document_id,
                        content=content,
                        page_number=page.page_number,
                        chunk_index=chunk_index,
                        document_hash=document.document_hash,
                        filename=document.filename,
                    )
                )
                chunk_index += 1
        return chunks
