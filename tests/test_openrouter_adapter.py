"""Unit tests for the OpenRouter provider adapter."""

import json
from datetime import UTC, datetime

import httpx
import pytest

from app.core.config import Settings
from app.domain.entities import Message
from app.infrastructure.llm.openrouter_adapter import (
    LLMProviderError,
    OpenRouterAdapter,
)


def test_openrouter_adapter_maps_messages_and_response() -> None:
    """The adapter should translate the provider response to plain text."""

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url == "https://test.example/v1/chat/completions"
        assert request.headers["Authorization"] == "Bearer test-key"
        assert json.loads(request.content) == {
            "model": "openrouter/free",
            "messages": [{"role": "user", "content": "Ciao"}],
        }
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": "Risposta remota"}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = Settings(
        llm_provider="openrouter",
        openrouter_api_key="test-key",
        openrouter_model="openrouter/free",
        openrouter_base_url="https://test.example/v1",
    )
    adapter = OpenRouterAdapter(settings, client=client)

    result = adapter.generate([Message("user", "Ciao", datetime.now(UTC))])

    assert result == "Risposta remota"


def test_openrouter_adapter_requires_api_key() -> None:
    """A remote provider must fail fast when no secret is configured."""

    settings = Settings(llm_provider="openrouter", openrouter_api_key=None)

    with pytest.raises(LLMProviderError, match="OPENROUTER_API_KEY"):
        OpenRouterAdapter(settings)


def test_openrouter_adapter_wraps_provider_errors() -> None:
    """Transport and malformed-response errors should use the domain exception."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"error": "temporarily unavailable"})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = Settings(llm_provider="openrouter", openrouter_api_key="test-key")
    adapter = OpenRouterAdapter(settings, client=client)

    with pytest.raises(LLMProviderError, match="OpenRouter request failed"):
        adapter.generate([])


@pytest.mark.parametrize(
    "content",
    [None, ""],
)
def test_openrouter_adapter_rejects_empty_content(content: object) -> None:
    """Empty provider output must not reach the conversation layer."""

    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"choices": [{"message": {"content": content}}]},
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    settings = Settings(llm_provider="openrouter", openrouter_api_key="test-key")
    adapter = OpenRouterAdapter(settings, client=client)

    with pytest.raises(LLMProviderError, match="OpenRouter request failed"):
        adapter.generate([])
