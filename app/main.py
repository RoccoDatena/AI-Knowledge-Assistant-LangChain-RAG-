"""FastAPI application entry point."""

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from starlette.middleware.base import RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.infrastructure.llm.openrouter_adapter import LLMProviderError
from app.interfaces.api.conversation_routes import router as conversation_router
from app.interfaces.api.document_routes import router as document_router
from app.interfaces.api.errors import (
    http_exception_handler,
    unexpected_exception_handler,
    validation_exception_handler,
)
from app.interfaces.api.search_routes import router as search_router

configure_logging()
logger = logging.getLogger(__name__)


class HealthResponse(BaseModel):
    """Response returned by the health check endpoint."""

    status: str
    service: str
    llm_provider: str


class ReadinessResponse(BaseModel):
    """Response returned by the readiness probe."""

    status: str
    checks: dict[str, str]


app = FastAPI(
    title="AI Knowledge Assistant API",
    description="REST API for a document-grounded conversational assistant.",
    version="0.1.0",
)

app.include_router(conversation_router)
app.include_router(document_router)
app.include_router(search_router)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unexpected_exception_handler)


@app.middleware("http")
async def request_logging_middleware(
    request: Request,
    call_next: RequestResponseEndpoint,
) -> Response:
    """Log request method, path, status, and duration."""

    started_at = perf_counter()
    request_id = request.headers.get("X-Request-ID") or str(uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    duration_ms = round((perf_counter() - started_at) * 1000, 2)
    logger.info(
        "http_request method=%s path=%s status=%s duration_ms=%s",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
        extra={"request_id": request_id},
    )
    return response


@app.get("/health", response_model=HealthResponse, tags=["diagnostics"])
def health_check() -> HealthResponse:
    """Return the current availability of the API service."""

    return HealthResponse(
        status="ok",
        service="ai-knowledge-assistant-api",
        llm_provider=get_settings().llm_provider,
    )


@app.get("/health/ready", response_model=ReadinessResponse, tags=["diagnostics"])
def readiness_check() -> JSONResponse | ReadinessResponse:
    """Verify that application configuration is ready for traffic."""

    try:
        settings = get_settings().validate()
    except ValueError as exc:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "checks": {"configuration": str(exc)},
            },
        )
    return ReadinessResponse(
        status="ready",
        checks={
            "configuration": "ok",
            "llm_provider": settings.llm_provider,
            "vector_store": settings.vector_store,
        },
    )


@app.exception_handler(LLMProviderError)
async def llm_provider_error_handler(
    request: Request,
    exc: LLMProviderError,
) -> JSONResponse:
    """Return a safe gateway error for provider failures."""

    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "llm_provider_error request_id=%s",
        request_id,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    response = JSONResponse(
        status_code=502,
        content={
            "error": {
                "code": "PROVIDER_ERROR",
                "message": str(exc),
                "details": None,
                "request_id": request_id,
            }
        },
    )
    if request_id:
        response.headers["X-Request-ID"] = request_id
    return response
