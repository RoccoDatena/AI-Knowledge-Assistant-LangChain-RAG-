"""Tests for conversation metadata persistence."""

from datetime import UTC, datetime
from pathlib import Path

from app.domain.entities import Message, MessageSource
from app.infrastructure.persistence.json_conversation_repository import (
    JsonConversationRepository,
)


def test_repository_round_trips_grounding_sources(tmp_path: Path) -> None:
    """Grounding metadata and citations survive a JSON persistence round trip."""

    repository = JsonConversationRepository(tmp_path)
    conversation = repository.create()
    source = MessageSource(
        document_id="doc-1",
        filename="manual.pdf",
        page_number=4,
        chunk_id="doc-1:2",
        score=0.87,
    )

    repository.add_message(
        conversation.conversation_id,
        Message(
            role="assistant",
            content="Risposta grounded",
            created_at=datetime.now(UTC),
            grounded=True,
            sources=[source],
        ),
    )

    loaded = repository.get(conversation.conversation_id)

    assert loaded is not None
    assert loaded.messages[0].grounded is True
    assert loaded.messages[0].sources == [source]
