import time
import uuid
import logging
from typing import Callable
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy.exc import SQLAlchemyError

from backend.app.core.logging import logger

SENSITIVE_HEADERS = {"authorization", "cookie", "set-cookie", "x-api-key"}


async def request_context_and_security_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware that:
    1. Extracts or generates a unique X-Request-ID.
    2. Measures request execution duration.
    3. Adds HTTP Security headers (X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Cache-Control).
    4. Emits structured production-safe access logs (redacting authorization/passwords).
    """
    request_id = request.headers.get("X-Request-ID")
    if not request_id:
        request_id = str(uuid.uuid4())

    request.state.request_id = request_id
    start_time = time.time()

    try:
        response = await call_next(request)
    except Exception as exc:
        duration_ms = round((time.time() - start_time) * 1000, 2)
        logger.error(
            f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": 500,
                "duration_ms": duration_ms,
            },
            exc_info=True
        )
        raise exc

    duration_ms = round((time.time() - start_time) * 1000, 2)

    # Attach response headers
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.path.startswith("/api") and not request.url.path.startswith("/api/health"):
        response.headers["Cache-Control"] = "no-store, max-age=0"

    # Structured request logging
    logger.info(
        f"{request.method} {request.url.path} HTTP/{request.scope.get('http_version', '1.1')} {response.status_code} {duration_ms}ms",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "status_code": response.status_code,
            "duration_ms": duration_ms,
        }
    )

    return response


# Global Exception Handlers
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    code_str = f"HTTP_{exc.status_code}"

    # Determine error code label
    if exc.status_code == status.HTTP_401_UNAUTHORIZED:
        code_str = "UNAUTHORIZED"
    elif exc.status_code == status.HTTP_403_FORBIDDEN:
        code_str = "FORBIDDEN"
    elif exc.status_code == status.HTTP_404_NOT_FOUND:
        code_str = "NOT_FOUND"
    elif exc.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        code_str = "TOO_MANY_REQUESTS"

    headers = getattr(exc, "headers", None) or {}
    headers["X-Request-ID"] = request_id

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "error": {
                "code": code_str,
                "message": str(exc.detail),
                "request_id": request_id
            }
        },
        headers=headers
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation error",
                "details": exc.errors(),
                "request_id": request_id
            }
        },
        headers={"X-Request-ID": request_id}
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(f"Sanitizing uncaught 500 exception [request_id={request_id}]: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "An internal server error occurred. Please contact system support.",
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred.",
                "request_id": request_id
            }
        },
        headers={"X-Request-ID": request_id}
    )
