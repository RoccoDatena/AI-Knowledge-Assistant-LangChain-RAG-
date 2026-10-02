"""Tests for API diagnostics endpoints."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_check_returns_service_status() -> None:
    """The health endpoint should expose a stable, machine-readable response."""

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "service": "ai-knowledge-assistant-api",
        "llm_provider": "mock",
    }


def test_readiness_check_returns_configured_dependencies() -> None:
    """Readiness should expose the selected provider boundaries."""

    response = client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "checks": {
            "configuration": "ok",
            "llm_provider": "mock",
            "vector_store": "json",
        },
    }


def test_readiness_check_rejects_invalid_configuration(monkeypatch) -> None:
    """Readiness should fail clearly when an unsupported provider is configured."""

    monkeypatch.setenv("LLM_PROVIDER", "unsupported")

    response = client.get("/health/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"
    assert "Unsupported LLM_PROVIDER" in response.json()["checks"]["configuration"]


def test_unexpected_errors_use_safe_error_contract() -> None:
    """Unexpected exceptions should not expose implementation details."""

    def exploding_endpoint() -> None:
        raise RuntimeError("secret implementation detail")

    app.add_api_route("/test-unexpected-error", exploding_endpoint, methods=["GET"])
    with TestClient(app, raise_server_exceptions=False) as test_client:
        response = test_client.get("/test-unexpected-error")

    assert response.status_code == 500
    assert response.json()["error"]["code"] == "INTERNAL_ERROR"
    assert response.json()["error"]["message"] == "Internal server error"
    assert "secret implementation detail" not in response.text


def test_health_preserves_client_request_id() -> None:
    """External gateway IDs should remain traceable across the API."""

    request_id = "gateway-request-123"

    with TestClient(app) as test_client:
        response = test_client.get("/health", headers={"X-Request-ID": request_id})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == request_id
