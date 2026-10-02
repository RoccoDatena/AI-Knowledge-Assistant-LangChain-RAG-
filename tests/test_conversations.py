"""Tests for conversation lifecycle endpoints."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.infrastructure.persistence.json_conversation_repository import (
    JsonConversationRepository,
)
from app.interfaces.api.conversation_routes import get_conversation_repository
from app.main import app


def test_create_and_read_conversation_history(tmp_path: Path) -> None:
    """A created conversation should be persisted and readable."""

    app.dependency_overrides[get_conversation_repository] = lambda: (
        JsonConversationRepository(tmp_path)
    )

    try:
        with TestClient(app) as client:
            create_response = client.post("/conversations")
            assert create_response.status_code == 201

            conversation_id = create_response.json()["conversation_id"]
            history_response = client.get(f"/conversations/{conversation_id}/history")

        assert history_response.status_code == 200
        assert history_response.json()["conversation_id"] == conversation_id
        assert history_response.json()["messages"] == []
    finally:
        app.dependency_overrides.clear()


def test_unknown_conversation_returns_not_found() -> None:
    """An unknown conversation ID should return a clear 404 response."""

    with TestClient(app) as client:
        response = client.get(
            "/conversations/00000000-0000-0000-0000-000000000000/history"
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "Conversation not found"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]
