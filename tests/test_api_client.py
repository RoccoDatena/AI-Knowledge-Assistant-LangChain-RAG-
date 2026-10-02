"""Tests for the frontend HTTP client error contract."""

import httpx
import pytest

from frontend.api_client import ApiClient, ApiClientError


def test_client_preserves_backend_error_envelope() -> None:
    """Backend error codes should remain available to the UI."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            404,
            json={
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Conversation not found",
                    "details": None,
                    "request_id": "a-request-correlation-id",
                }
            },
            request=request,
        )

    client = ApiClient("http://test")
    client._client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://test"
    )

    with pytest.raises(ApiClientError) as raised:
        client.get_history("missing")

    assert raised.value.code == "NOT_FOUND"
    assert str(raised.value) == "Conversation not found"
    assert raised.value.request_id == "a-request-correlation-id"


def test_client_searches_with_metadata_filters() -> None:
    """The UI client should forward document and page filters to the API."""

    def handler(request: httpx.Request) -> httpx.Response:
        payload = request.read()
        assert b'"document_id":"doc-1"' in payload
        assert b'"page_number":2' in payload
        return httpx.Response(200, json=[{"chunk_id": "doc-1:0"}], request=request)

    client = ApiClient("http://test")
    client._client = httpx.Client(
        transport=httpx.MockTransport(handler), base_url="http://test"
    )

    result = client.search_documents("backup", document_id="doc-1", page_number=2)

    assert result == [{"chunk_id": "doc-1:0"}]
