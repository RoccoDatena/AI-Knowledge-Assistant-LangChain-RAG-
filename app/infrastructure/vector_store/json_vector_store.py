"""Persistent JSON vector store used when ChromaDB is unavailable."""

import json
import math
from pathlib import Path
from typing import Any, cast

from app.domain.entities import DocumentChunk, RetrievedChunk
from app.infrastructure.persistence.atomic_file import atomic_write_text


class JsonVectorStore:
    """Persist vectors and chunk metadata in a local JSON file."""

    def __init__(self, file_path: Path) -> None:
        self._file_path = file_path
        self._file_path.parent.mkdir(parents=True, exist_ok=True)

    def add(self, chunks: list[DocumentChunk], embeddings: list[list[float]]) -> None:
        """Add or replace vectors by deterministic chunk ID."""

        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have the same length")
        records = self._load()
        for chunk, embedding in zip(chunks, embeddings, strict=True):
            records[chunk.chunk_id] = {
                "chunk": {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "content": chunk.content,
                    "page_number": chunk.page_number,
                    "chunk_index": chunk.chunk_index,
                    "document_hash": chunk.document_hash,
                    "filename": chunk.filename,
                },
                "embedding": embedding,
            }
        self._save(records)

    def search(
        self,
        query_embedding: list[float],
        limit: int = 4,
        metadata_filter: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return cosine-ranked chunks with optional metadata filters."""

        results: list[RetrievedChunk] = []
        for record in self._load().values():
            chunk = self._to_chunk(record["chunk"])
            if not self._matches_filter(chunk, metadata_filter):
                continue
            results.append(
                RetrievedChunk(
                    chunk,
                    self._cosine(query_embedding, record["embedding"]),
                )
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return results[: max(0, limit)]

    def delete_by_document_id(self, document_id: str) -> int:
        """Delete all vectors belonging to a document."""

        records = self._load()
        matching_ids = [
            chunk_id
            for chunk_id, record in records.items()
            if record["chunk"]["document_id"] == document_id
        ]
        for chunk_id in matching_ids:
            del records[chunk_id]
        self._save(records)
        return len(matching_ids)

    def _load(self) -> dict[str, dict[str, Any]]:
        if not self._file_path.is_file():
            return {}
        payload = json.loads(self._file_path.read_text(encoding="utf-8"))
        return cast(dict[str, dict[str, Any]], payload)

    def _save(self, records: dict[str, dict[str, Any]]) -> None:
        atomic_write_text(
            self._file_path, json.dumps(records, indent=2, ensure_ascii=False)
        )

    @staticmethod
    def _to_chunk(payload: dict[str, Any]) -> DocumentChunk:
        return DocumentChunk(
            chunk_id=str(payload["chunk_id"]),
            document_id=str(payload["document_id"]),
            content=str(payload["content"]),
            page_number=int(payload["page_number"]),
            chunk_index=int(payload["chunk_index"]),
            document_hash=str(payload["document_hash"]),
            filename=str(payload.get("filename", "")),
        )

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
