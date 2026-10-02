"""Runtime-owned vector dependencies for the current process."""

from pathlib import Path

from app.core.config import get_settings
from app.domain.ports import EmbeddingProvider, VectorStore
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.embeddings.sentence_transformers_provider import (
    SentenceTransformersEmbeddingProvider,
)
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore
from app.infrastructure.vector_store.json_vector_store import JsonVectorStore

_settings = get_settings()
_embedding_provider: EmbeddingProvider
if _settings.embedding_provider == "sentence_transformers":
    _embedding_provider = SentenceTransformersEmbeddingProvider(
        model_name=_settings.embedding_model
    )
else:
    _embedding_provider = HashingEmbeddingProvider()
_vector_store = (
    JsonVectorStore(Path(_settings.data_directory) / "vector_store" / "vectors.json")
    if _settings.vector_store == "json"
    else InMemoryVectorStore()
)


def get_embedding_provider() -> EmbeddingProvider:
    """Return the process-wide embedding provider."""

    return _embedding_provider


def get_vector_store() -> VectorStore:
    """Return the process-wide vector store."""

    return _vector_store
