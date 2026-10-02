"""Tests for lightweight embeddings and vector retrieval."""

from app.domain.entities import DocumentChunk
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore


def _chunk(chunk_id: str, content: str, page_number: int) -> DocumentChunk:
    return DocumentChunk(
        chunk_id=chunk_id,
        document_id="doc-1",
        content=content,
        page_number=page_number,
        chunk_index=page_number - 1,
        document_hash="hash-1",
    )


def test_hashing_embeddings_are_deterministic() -> None:
    """The same input should always produce the same normalized vector."""

    provider = HashingEmbeddingProvider(dimensions=64)

    first = provider.embed_query("gestione delle conversazioni")
    second = provider.embed_query("gestione delle conversazioni")

    assert first == second
    assert len(first) == 64


def test_vector_store_returns_relevant_chunks_and_applies_filter() -> None:
    """Search should rank similar content and honor page metadata filters."""

    provider = HashingEmbeddingProvider(dimensions=128)
    store = InMemoryVectorStore()
    chunks = [
        _chunk("one", "gestione delle conversazioni utente", 1),
        _chunk("two", "configurazione del server web", 2),
    ]
    store.add(chunks, provider.embed_documents([chunk.content for chunk in chunks]))

    results = store.search(provider.embed_query("conversazioni utente"), limit=2)
    filtered = store.search(
        provider.embed_query("conversazioni utente"),
        limit=2,
        metadata_filter={"page_number": "2"},
    )

    assert results[0].chunk.chunk_id == "one"
    assert len(filtered) == 1
    assert filtered[0].chunk.chunk_id == "two"
