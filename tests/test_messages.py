"""Tests for the conversational message endpoint."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.application.rag import Citation, RagAnswer
from app.application.retrieval import RetrievalService
from app.infrastructure.embeddings.hashing_embedding_provider import (
    HashingEmbeddingProvider,
)
from app.infrastructure.persistence.json_conversation_repository import (
    JsonConversationRepository,
)
from app.infrastructure.vector_store.in_memory_vector_store import InMemoryVectorStore
from app.interfaces.api.conversation_routes import (
    get_conversation_repository,
    get_rag_service,
)
from app.interfaces.api.search_routes import get_retrieval_service
from app.main import app


def test_send_message_persists_user_and_assistant_messages(tmp_path: Path) -> None:
    """A chat request should persist both sides of the exchange."""

    app.dependency_overrides[get_conversation_repository] = lambda: (
        JsonConversationRepository(tmp_path)
    )
    app.dependency_overrides[get_retrieval_service] = lambda: RetrievalService(
        HashingEmbeddingProvider(), InMemoryVectorStore()
    )

    try:
        with TestClient(app) as client:
            conversation_id = client.post("/conversations").json()["conversation_id"]
            response = client.post(
                f"/conversations/{conversation_id}/messages",
                json={"content": "Che cosa puoi fare?"},
            )
            history = client.get(f"/conversations/{conversation_id}/history").json()

        assert response.status_code == 201
        assert response.json()["assistant_message"]["content"] == (
            "Informazione non trovata nei documenti."
        )
        assert response.json()["grounded"] is False
        assert response.json()["sources"] == []
        assert history["message_count"] == 2
        assert [message["role"] for message in history["messages"]] == [
            "user",
            "assistant",
        ]
        assert history["messages"][1]["grounded"] is False
        assert history["messages"][1]["sources"] == []
    finally:
        app.dependency_overrides.clear()


def test_send_message_to_unknown_conversation_returns_not_found() -> None:
    """Unknown conversation IDs should not create orphan messages."""

    with TestClient(app) as client:
        response = client.post(
            "/conversations/00000000-0000-0000-0000-000000000000/messages",
            json={"content": "Test"},
        )

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"
    assert response.json()["error"]["message"] == "Conversation not found"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_empty_message_is_rejected() -> None:
    """The API should reject empty user messages before persistence."""

    with TestClient(app) as client:
        response = client.post(
            "/conversations/00000000-0000-0000-0000-000000000000/messages",
            json={"content": ""},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_grounded_sources_survive_history_reload(tmp_path: Path) -> None:
    """A refreshed history must retain grounded status and source metadata."""

    class FixedRagService:
        def answer(self, question: str, history: list) -> RagAnswer:
            del question, history
            return RagAnswer(
                answer="Risposta verificata",
                grounded=True,
                citations=[
                    Citation(
                        document_id="doc-1",
                        filename="manuale.pdf",
                        page_number=7,
                        chunk_id="doc-1:3",
                        score=0.91,
                    )
                ],
            )

    app.dependency_overrides[get_conversation_repository] = lambda: (
        JsonConversationRepository(tmp_path)
    )
    app.dependency_overrides[get_rag_service] = lambda: FixedRagService()

    try:
        with TestClient(app) as client:
            conversation_id = client.post("/conversations").json()["conversation_id"]
            response = client.post(
                f"/conversations/{conversation_id}/messages",
                json={"content": "Qual è il requisito?"},
            )
            assert response.status_code == 201

        with TestClient(app) as refreshed_client:
            history = refreshed_client.get(
                f"/conversations/{conversation_id}/history"
            ).json()

        assistant = history["messages"][1]
        assert assistant["content"] == "Risposta verificata"
        assert assistant["grounded"] is True
        assert assistant["sources"] == [
            {
                "document_id": "doc-1",
                "filename": "manuale.pdf",
                "page_number": 7,
                "chunk_id": "doc-1:3",
                "score": 0.91,
            }
        ]
    finally:
        app.dependency_overrides.clear()
