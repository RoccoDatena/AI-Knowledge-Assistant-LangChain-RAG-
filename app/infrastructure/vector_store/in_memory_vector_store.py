"""In-memory vector store used while ChromaDB is unavailable."""

import math
from dataclasses import dataclass

from app.domain.entities import DocumentChunk, RetrievedChunk


@dataclass(frozen=True)
class _StoredVector:
    chunk: DocumentChunk
    embedding: list[float]


class InMemoryVectorStore:
    """Perform cosine similarity search without external services."""

    def __init__(self) -> None:
        self._records: dict[str, _StoredVector] = {}

    def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Add or replace vectors by chunk ID."""

        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have the same length")
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            self._records[chunk.chunk_id] = _StoredVector(chunk, embedding)

    def search(
        self,
        query_embedding: list[float],
        limit: int = 4,
        metadata_filter: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return top cosine matches, optionally filtered by metadata."""

        candidates = [
            record
            for record in self._records.values()
            if self._matches_filter(record.chunk, metadata_filter)
        ]
        ranked = sorted(
            (
                RetrievedChunk(
                    record.chunk, self._cosine(query_embedding, record.embedding)
                )
                for record in candidates
            ),
            key=lambda item: item.score,
            reverse=True,
        )
        return ranked[: max(0, limit)]

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all chunks belonging to a document."""

        matching_ids = [
            chunk_id
            for chunk_id, record in self._records.items()
            if record.chunk.document_id == document_id
        ]
        for chunk_id in matching_ids:
            del self._records[chunk_id]
        return len(matching_ids)

    @staticmethod
    def _matches_filter(
        chunk: DocumentChunk,
        metadata_filter: dict[str, str] | None,
    ) -> bool:
        if not metadata_filter:
            return True
        values = {
            "document_id": chunk.document_id,
            "document_hash": chunk.document_hash,
            "page_number": str(chunk.page_number),
            "filename": chunk.filename,
        }
        return all(values.get(key) == value for key, value in metadata_filter.items())

    @staticmethod
    def _cosine(left: list[float], right: list[float]) -> float:
        if len(left) != len(right):
            raise ValueError("Embedding dimensions must match")
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if left_norm == 0 or right_norm == 0:
            return 0.0
        return sum(a * b for a, b in zip(left, right, strict=True)) / (
            left_norm * right_norm
        )
