"""OpenRouter adapter using the OpenAI-compatible chat completions API."""

import httpx

from app.core.config import Settings
from app.domain.entities import Message


class LLMProviderError(RuntimeError):
    """Raised when an LLM provider cannot generate a response."""


class OpenRouterAdapter:
    """Translate domain messages into an OpenRouter API request."""

    def __init__(
        self,
        settings: Settings,
        client: httpx.Client | None = None,
    ) -> None:
        if not settings.openrouter_api_key:
            raise LLMProviderError("OPENROUTER_API_KEY is not configured")

        self._settings = settings
        self._client = client or httpx.Client(timeout=settings.request_timeout_seconds)

    def generate(self, messages: list[Message]) -> str:
        """Generate a response using OpenRouter chat completions."""

        payload = {
            "model": self._settings.openrouter_model,
            "messages": [
                {"role": message.role, "content": message.content}
                for message in messages
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._settings.openrouter_api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/RoccoDatena/AI-Knowledge-Assistant-LangChain-RAG-",
            "X-Title": "AI Knowledge Assistant",
        }

        try:
            response = self._client.post(
                f"{self._settings.openrouter_base_url}/chat/completions",
                headers=headers,
                json=payload,
            )
            response.raise_for_status()
            response_payload = response.json()
            content = response_payload["choices"][0]["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Provider returned empty content")
            return content
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
            raise LLMProviderError("OpenRouter request failed") from exc
