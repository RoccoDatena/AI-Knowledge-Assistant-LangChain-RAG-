"""Tests for the optional semantic embedding adapter."""

from typing import Any

from app.infrastructure.embeddings.sentence_transformers_provider import (
    SentenceTransformersEmbeddingProvider,
)


class FakeVector:
    """Tiny numpy-like result used without numpy or a downloaded model."""

    def __init__(self, values: list[list[float]] | list[float]) -> None:
        self._values = values

    def tolist(self) -> list[Any]:
        return self._values


class FakeEncoder:
    """Test double for the Sentence Transformer encoder contract."""

    def encode(self, texts: Any, **kwargs: Any) -> FakeVector:
        assert kwargs == {
            "normalize_embeddings": True,
            "convert_to_numpy": True,
        }
        if isinstance(texts, list):
            return FakeVector([[1.0, 0.0] for _ in texts])
        return FakeVector([1.0, 0.0])


def test_adapter_supports_injected_encoder_without_optional_dependency() -> None:
    """The adapter remains testable without downloading a model."""

    provider = SentenceTransformersEmbeddingProvider(encoder=FakeEncoder())

    assert provider.embed_documents(["uno", "due"]) == [[1.0, 0.0], [1.0, 0.0]]
    assert provider.embed_query("domanda") == [1.0, 0.0]


def test_adapter_passes_offline_mode_to_sentence_transformers(monkeypatch: Any) -> None:
    """Offline mode must prevent model metadata network checks."""

    captured: dict[str, Any] = {}

    class FakeSentenceTransformer:
        def __init__(self, model_name: str, **kwargs: Any) -> None:
            captured["model_name"] = model_name
            captured.update(kwargs)

        def encode(self, texts: Any, **kwargs: Any) -> FakeVector:
            if isinstance(texts, list):
                return FakeVector([[1.0, 0.0] for _ in texts])
            return FakeVector([1.0, 0.0])

    class FakeModule:
        SentenceTransformer = FakeSentenceTransformer

    monkeypatch.setattr(
        "app.infrastructure.embeddings.sentence_transformers_provider.import_module",
        lambda _: FakeModule,
    )

    provider = SentenceTransformersEmbeddingProvider(
        model_name="cached-model", local_files_only=True
    )
    provider.embed_query("domanda")

    assert captured == {"model_name": "cached-model", "local_files_only": True}
