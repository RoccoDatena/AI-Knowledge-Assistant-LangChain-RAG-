"""Tests for retrieval orchestration and search filtering."""

from app.application.retrieval import RetrievalService
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore
from tests.test_vector_search import _chunk


def test_retrieval_service_applies_minimum_score() -> None:
    """Low-confidence results should be removed before reaching the API."""

    provider = HashingEmbeddingProvider(dimensions=128)
    store = InMemoryVectorStore()
    chunk = _chunk("one", "gestione delle conversazioni", 1)
    store.add([chunk], provider.embed_documents([chunk.content]))
    service = RetrievalService(provider, store)

    assert service.search("conversazioni", min_score=1.1) == []
    assert service.search("conversazioni", min_score=0.0)[0].chunk.chunk_id == "one"
