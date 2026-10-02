"""Document indexing use case."""

from pathlib import Path

from app.application.chunking import DocumentChunker
from app.domain.ports import DocumentRepository, EmbeddingProvider, VectorStore
from app.infrastructure.pdf.pypdf_text_extractor import PypdfTextExtractor


class DocumentIndexer:
    """Coordinate extraction, chunking, embedding, and vector storage."""

    def __init__(
        self,
        document_repository: DocumentRepository,
        extractor: PypdfTextExtractor,
        chunker: DocumentChunker,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._document_repository = document_repository
        self._extractor = extractor
        self._chunker = chunker
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def index_all(self) -> int:
        """Index every uploaded document and return the chunk count."""

        total_chunks = 0
        for document in self._document_repository.list():
            content = Path(document.stored_path).read_bytes()
            pages = self._extractor.extract(content)
            chunks = self._chunker.create_chunks(document, pages)
            if not chunks:
                continue
            embeddings = self._embedding_provider.embed_documents(
                [chunk.content for chunk in chunks]
            )
            self._vector_store.add(chunks, embeddings)
            total_chunks += len(chunks)
        return total_chunks
