"""Tests for LangChain prompt orchestration."""

from datetime import UTC, datetime

from app.application.prompt_builder import ConversationPromptBuilder
from app.domain.entities import Message


def test_prompt_builder_adds_system_instruction_and_preserves_history() -> None:
    """The builder should add policy context without changing conversation order."""

    timestamp = datetime.now(UTC)
    messages = [
        Message("user", "Prima domanda", timestamp),
        Message("assistant", "Prima risposta", timestamp),
        Message("user", "Seconda domanda", timestamp),
    ]

    result = ConversationPromptBuilder().build(messages)

    assert result[0].role == "system"
    assert "non inventare informazioni" in result[0].content
    assert [(message.role, message.content) for message in result[1:]] == [
        ("user", "Prima domanda"),
        ("assistant", "Prima risposta"),
        ("user", "Seconda domanda"),
    ]
