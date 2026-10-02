"""Small HTTP client used by the Streamlit frontend."""

from typing import Any

import httpx


class ApiClientError(RuntimeError):
    """User-facing error returned by the backend API."""

    def __init__(
        self,
        message: str,
        code: str = "HTTP_ERROR",
        details: Any | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.details = details
        self.request_id = request_id


class ApiClient:
    """Call the local FastAPI backend."""

    def __init__(self, base_url: str, timeout: float = 60.0) -> None:
        self._client = httpx.Client(base_url=base_url.rstrip("/"), timeout=timeout)

    def create_conversation(self) -> dict[str, Any]:
        response = self._client.post("/conversations")
        self._ensure_success(response)
        return response.json()

    def get_history(self, conversation_id: str) -> dict[str, Any]:
        response = self._client.get(f"/conversations/{conversation_id}/history")
        self._ensure_success(response)
        return response.json()

    def send_message(self, conversation_id: str, content: str) -> dict[str, Any]:
        response = self._client.post(
            f"/conversations/{conversation_id}/messages",
            json={"content": content},
        )
        self._ensure_success(response)
        return response.json()

    def upload_document(self, filename: str, content: bytes) -> dict[str, Any]:
        response = self._client.post(
            "/documents/upload",
            files={"file": (filename, content, "application/pdf")},
        )
        self._ensure_success(response)
        return response.json()

    def list_documents(self) -> list[dict[str, Any]]:
        response = self._client.get("/documents")
        self._ensure_success(response)
        return response.json()

    def index_documents(self) -> dict[str, Any]:
        response = self._client.post("/documents/index")
        self._ensure_success(response)
        return response.json()

    def search_documents(
        self,
        query: str,
        limit: int = 4,
        min_score: float = 0.0,
        document_id: str | None = None,
        page_number: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search indexed chunks with optional source metadata filters."""

        payload: dict[str, Any] = {
            "query": query,
            "limit": limit,
            "min_score": min_score,
        }
        if document_id:
            payload["document_id"] = document_id
        if page_number is not None:
            payload["page_number"] = page_number
        response = self._client.post("/documents/search", json=payload)
        self._ensure_success(response)
        return response.json()

    def delete_document(self, document_id: str) -> None:
        response = self._client.delete(f"/documents/{document_id}")
        self._ensure_success(response)

    @staticmethod
    def _ensure_success(response: httpx.Response) -> None:
        """Raise a stable client error while preserving the API envelope."""

        if response.is_success:
            return
        try:
            payload = response.json().get("error", {})
        except ValueError:
            payload = {}
        raise ApiClientError(
            message=payload.get("message", "Backend request failed"),
            code=payload.get("code", "HTTP_ERROR"),
            details=payload.get("details"),
            request_id=payload.get("request_id"),
        )
