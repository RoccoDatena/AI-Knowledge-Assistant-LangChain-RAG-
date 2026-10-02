"""Optional Sentence Transformers embedding adapter."""

from importlib import import_module
from typing import Any, Protocol, cast


class Encoder(Protocol):
    """Minimal interface required from a Sentence Transformer model."""

    def encode(
        self,
        texts: list[str] | str,
        *,
        normalize_embeddings: bool,
        convert_to_numpy: bool,
    ) -> Any:
        """Encode text into vectors."""


class SentenceTransformersEmbeddingProvider:
    """Generate semantic embeddings through an optional local model."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        encoder: Encoder | None = None,
    ) -> None:
        self._model_name = model_name
        self._encoder = encoder

    def _get_encoder(self) -> Encoder:
        """Load the model only when the first embedding is requested."""

        if self._encoder is not None:
            return self._encoder
        try:
            module = import_module("sentence_transformers")
            sentence_transformer = module.SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "Sentence Transformers is optional. Install it before using "
                "SentenceTransformersEmbeddingProvider."
            ) from exc
        self._encoder = sentence_transformer(self._model_name)
        return self._encoder

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Encode multiple document chunks with normalized vectors."""
        vectors = self._get_encoder().encode(
            texts, normalize_embeddings=True, convert_to_numpy=True
        )
        return [list(map(float, vector)) for vector in vectors.tolist()]

    def embed_query(self, text: str) -> list[float]:
        """Encode one query with the same model used for documents."""
        vector = self._get_encoder().encode(
            text, normalize_embeddings=True, convert_to_numpy=True
        )
        return cast(list[float], list(map(float, vector.tolist())))
