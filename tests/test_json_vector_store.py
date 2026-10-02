"""Tests for persistent JSON vector storage."""

from app.domain.entities import DocumentChunk
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.vector_store.json_vector_store import JsonVectorStore


def test_json_vector_store_survives_new_instance(tmp_path) -> None:
    """Stored vectors should be searchable after recreating the adapter."""

    provider = HashingEmbeddingProvider(dimensions=64)
    path = tmp_path / "vectors.json"
    chunk = DocumentChunk(
        chunk_id="doc-1:0",
        document_id="doc-1",
        content="conversazioni persistenti",
        page_number=1,
        chunk_index=0,
        document_hash="hash",
        filename="manual.pdf",
    )
    JsonVectorStore(path).add([chunk], provider.embed_documents([chunk.content]))

    results = JsonVectorStore(path).search(provider.embed_query("persistenti"))

    assert results[0].chunk.filename == "manual.pdf"
    assert results[0].chunk.document_id == "doc-1"
