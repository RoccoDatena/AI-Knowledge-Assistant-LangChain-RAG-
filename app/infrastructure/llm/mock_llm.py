"""Deterministic LLM adapter used for local development and tests."""

from app.domain.entities import Message


class MockLLM:
    """Return a predictable response without calling an external service."""

    def generate(self, messages: list[Message]) -> str:
        """Generate a transparent response from the latest user message."""

        latest_user_message = next(
            message.content for message in reversed(messages) if message.role == "user"
        )
        return f"Risposta simulata per: {latest_user_message}"
