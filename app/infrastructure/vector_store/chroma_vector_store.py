"""Optional ChromaDB vector store adapter."""

from pathlib import Path
from typing import Any

from app.domain.entities import DocumentChunk, RetrievedChunk


class ChromaConfigurationError(RuntimeError):
    """Raised when the optional ChromaDB dependency is unavailable."""


class ChromaVectorStore:
    """Persist vectors in a local ChromaDB collection."""

    def __init__(self, path: Path, collection_name: str = "knowledge_chunks") -> None:
        try:
            import chromadb
        except ImportError as exc:
            raise ChromaConfigurationError(
                "ChromaDB is not installed; use VECTOR_STORE=json or install chromadb"
            ) from exc

        self._client: Any = chromadb.PersistentClient(path=str(path))
        self._collection: Any = self._client.get_or_create_collection(
            name=collection_name,
            configuration={"hnsw": {"space": "cosine"}},
        )

    def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Add or replace vectors and source metadata."""

        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have the same length")
        if not chunks:
            return
        self._collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            embeddings=embeddings,
            documents=[chunk.content for chunk in chunks],
            metadatas=[self._metadata(chunk) for chunk in chunks],
        )

    def search(
        self,
        query_embedding: list[float],
        limit: int = 4,
        metadata_filter: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return nearest chunks with cosine similarity scores."""

        result = self._collection.query(
            query_embeddings=[query_embedding],
            n_results=max(1, limit),
            where=metadata_filter or None,
            include=["documents", "metadatas", "distances"],
        )
        ids = result.get("ids", [[]])[0]
        documents = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        return [
            RetrievedChunk(
                self._to_chunk(chunk_id, document, metadata),
                1.0 - float(distance),
            )
            for chunk_id, document, metadata, distance in zip(
                ids,
                documents,
                metadatas,
                distances,
                strict=True,
            )
        ]

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks for a document."""

        existing = self._collection.get(where={"document_id": document_id})
        ids = existing.get("ids", [])
        if ids:
            self._collection.delete(ids=ids)
        return len(ids)

    @staticmethod
    def _metadata(chunk: DocumentChunk) -> dict[str, str | int]:
        return {
            "document_id": chunk.document_id,
            "document_hash": chunk.document_hash,
            "filename": chunk.filename,
            "page_number": chunk.page_number,
            "chunk_index": chunk.chunk_index,
        }

    @staticmethod
    def _to_chunk(
        chunk_id: str,
        content: str,
        metadata: dict[str, str | int],
    ) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=chunk_id,
            document_id=str(metadata["document_id"]),
            content=content,
            page_number=int(metadata["page_number"]),
            chunk_index=int(metadata["chunk_index"]),
            document_hash=str(metadata["document_hash"]),
            filename=str(metadata["filename"]),
        )
