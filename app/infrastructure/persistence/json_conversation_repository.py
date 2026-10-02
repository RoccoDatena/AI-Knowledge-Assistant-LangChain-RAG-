"""JSON file persistence for conversations."""

import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

from app.domain.entities import Conversation, Message
from app.domain.ports import ConversationRepository
from app.infrastructure.persistence.atomic_file import atomic_write_text


class JsonConversationRepository(ConversationRepository):
    """Store one conversation per JSON file."""

    def __init__(self, storage_path: Path) -> None:
        self._storage_path = storage_path
        self._storage_path.mkdir(parents=True, exist_ok=True)

    def create(self) -> Conversation:
        """Create and persist a new conversation."""

        conversation = Conversation(
            conversation_id=str(uuid4()),
            created_at=datetime.now(UTC),
        )
        self._write(conversation)
        return conversation

    def get(self, conversation_id: str) -> Conversation | None:
        """Load a conversation by UUID, returning ``None`` if absent."""

        try:
            safe_id = str(UUID(conversation_id))
        except ValueError:
            return None

        file_path = self._storage_path / f"{safe_id}.json"
        if not file_path.is_file():
            return None

        payload = json.loads(file_path.read_text(encoding="utf-8"))
        messages = [
            Message(
                role=item["role"],
                content=item["content"],
                created_at=datetime.fromisoformat(item["created_at"]),
            )
            for item in payload.get("messages", [])
        ]
        return Conversation(
            conversation_id=payload["conversation_id"],
            created_at=datetime.fromisoformat(payload["created_at"]),
            messages=messages,
        )

    def add_message(
        self,
        conversation_id: str,
        message: Message,
    ) -> Conversation | None:
        """Append a message to an existing conversation."""

        conversation = self.get(conversation_id)
        if conversation is None:
            return None

        conversation.messages.append(message)
        self._write(conversation)
        return conversation

    def _write(self, conversation: Conversation) -> None:
        """Serialize a conversation using an explicit, stable JSON shape."""

        payload = {
            "conversation_id": conversation.conversation_id,
            "created_at": conversation.created_at.isoformat(),
            "messages": [
                {
                    "role": message.role,
                    "content": message.content,
                    "created_at": message.created_at.isoformat(),
                }
                for message in conversation.messages
            ],
        }
        file_path = self._storage_path / f"{conversation.conversation_id}.json"
        atomic_write_text(file_path, json.dumps(payload, indent=2, ensure_ascii=False))
