"""Tests for environment configuration validation."""

import pytest

from app.core.config import Settings


def test_valid_settings_are_returned() -> None:
    settings = Settings()

    assert settings.validate() is settings


def test_dataclass_defaults_are_stable() -> None:
    """Settings defaults must not depend on import-time environment state."""

    settings = Settings()

    assert settings.llm_provider == "mock"
    assert settings.vector_store == "json"


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("llm_provider", "unknown", "Unsupported LLM_PROVIDER"),
        ("vector_store", "unknown", "Unsupported VECTOR_STORE"),
        ("embedding_provider", "unknown", "Unsupported EMBEDDING_PROVIDER"),
        ("request_timeout_seconds", 0, "must be positive"),
        ("rag_min_score", 1.1, "between 0 and 1"),
        ("max_upload_bytes", 0, "must be positive"),
    ],
)
def test_invalid_settings_fail_fast(field: str, value: object, message: str) -> None:
    settings = Settings(**{field: value})

    with pytest.raises(ValueError, match=message):
        settings.validate()


def test_openrouter_requires_api_key() -> None:
    settings = Settings(llm_provider="openrouter", openrouter_api_key=None)

    with pytest.raises(ValueError, match="OPENROUTER_API_KEY"):
        settings.validate()
