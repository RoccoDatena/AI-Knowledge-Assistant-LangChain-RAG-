"""Shared API error responses and exception handlers."""

import logging
from typing import Any

from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ApiError(BaseModel):
    """Stable error envelope exposed to API clients."""

    code: str
    message: str
    details: Any | None = None
    request_id: str | None = None


def error_response(
    status_code: int,
    code: str,
    message: str,
    details: Any | None = None,
    request_id: str | None = None,
) -> JSONResponse:
    """Build the common JSON error representation."""

    return JSONResponse(
        status_code=status_code,
        content={
            "error": ApiError(
                code=code,
                message=message,
                details=details,
                request_id=request_id,
            ).model_dump()
        },
    )


async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Normalize explicit HTTP errors raised by route handlers."""

    if not isinstance(exc, HTTPException):
        return error_response(500, "INTERNAL_ERROR", "Internal server error")
    detail = exc.detail if isinstance(exc.detail, str) else "Request failed"
    return error_response(
        exc.status_code,
        _code_for_status(exc.status_code),
        detail,
        request_id=getattr(request.state, "request_id", None),
    )


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Normalize Pydantic request validation errors."""

    if not isinstance(exc, RequestValidationError):
        return error_response(500, "INTERNAL_ERROR", "Internal server error")
    return error_response(
        422,
        "VALIDATION_ERROR",
        "Request validation failed",
        details=exc.errors(),
        request_id=getattr(request.state, "request_id", None),
    )


async def unexpected_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Return a safe response for unexpected application failures."""

    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "unexpected_application_error request_id=%s",
        request_id,
        exc_info=(type(exc), exc, exc.__traceback__),
    )
    return error_response(
        500,
        "INTERNAL_ERROR",
        "Internal server error",
        request_id=request_id,
    )


def _code_for_status(status_code: int) -> str:
    """Return a predictable code for common HTTP failures."""

    return {
        400: "BAD_REQUEST",
        404: "NOT_FOUND",
        409: "CONFLICT",
        413: "PAYLOAD_TOO_LARGE",
        422: "UNPROCESSABLE_ENTITY",
        502: "PROVIDER_ERROR",
    }.get(status_code, "HTTP_ERROR")
