"""Retrieval use case independent from LLM generation."""

from app.domain.entities import RetrievedChunk
from app.domain.ports import EmbeddingProvider, VectorStore


class RetrievalService:
    """Retrieve relevant document chunks for a user query."""

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ) -> None:
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store

    def search(
        self,
        query: str,
        limit: int = 4,
        min_score: float = 0.0,
        metadata_filter: dict[str, str] | None = None,
    ) -> list[RetrievedChunk]:
        """Return chunks meeting the requested relevance threshold."""

        if not query.strip():
            return []
        results = self._vector_store.search(
            self._embedding_provider.embed_query(query),
            limit=limit,
            metadata_filter=metadata_filter,
        )
        return [result for result in results if result.score >= min_score]
