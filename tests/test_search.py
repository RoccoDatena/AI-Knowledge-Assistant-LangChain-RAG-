"""Tests for search request validation at the API boundary."""

from fastapi.testclient import TestClient

from app.domain.entities import DocumentChunk, RetrievedChunk
from app.interfaces.api.search_routes import get_retrieval_service
from app.main import app


class RecordingRetrieval:
    """Capture the search contract sent by the HTTP route."""

    def __init__(self) -> None:
        self.metadata_filter: dict[str, str] | None = None

    def search(
        self,
        query: str,
        limit: int,
        min_score: float,
        metadata_filter: dict[str, str] | None,
    ) -> list[RetrievedChunk]:
        _ = (query, limit, min_score)
        self.metadata_filter = metadata_filter
        chunk = DocumentChunk(
            chunk_id="doc-1:0",
            document_id="doc-1",
            content="Contenuto di test",
            page_number=2,
            chunk_index=0,
            document_hash="hash",
        )
        return [RetrievedChunk(chunk, 0.9)]


def test_search_rejects_empty_query_with_structured_error() -> None:
    with TestClient(app) as client:
        response = client.post("/documents/search", json={"query": ""})

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert response.json()["error"]["request_id"] == response.headers["X-Request-ID"]


def test_search_rejects_invalid_limit_and_page() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/documents/search",
            json={"query": "manuale", "limit": 21, "page_number": 0},
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert len(response.json()["error"]["details"]) == 2


def test_search_translates_metadata_filters_for_retrieval() -> None:
    """Document and page filters should reach the retrieval application service."""

    retrieval = RecordingRetrieval()
    app.dependency_overrides[get_retrieval_service] = lambda: retrieval
    try:
        with TestClient(app) as client:
            response = client.post(
                "/documents/search",
                json={
                    "query": "backup",
                    "document_id": "doc-1",
                    "page_number": 2,
                },
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert retrieval.metadata_filter == {"document_id": "doc-1", "page_number": "2"}
    assert response.json()[0]["page_number"] == 2
