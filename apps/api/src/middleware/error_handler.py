"""
Global exception handlers for the LearnR API.
Provides consistent error response format across all endpoints.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone
import uuid
from src.exceptions import (
    ConflictError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError
)


async def conflict_error_handler(request: Request, exc: ConflictError) -> JSONResponse:
    """Handle 409 Conflict errors."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": "CONFLICT_ERROR",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": str(uuid.uuid4())
            }
        }
    )


async def validation_error_handler(request: Request, exc: ValidationError) -> JSONResponse:
    """Handle 400 Bad Request errors."""
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": str(uuid.uuid4())
            }
        }
    )


async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
    """Handle 500 Internal Server Error."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "DATABASE_ERROR",
                "message": "An internal error occurred",
                "details": {},
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": str(uuid.uuid4())
            }
        }
    )


async def authentication_error_handler(request: Request, exc: AuthenticationError) -> JSONResponse:
    """Handle 401 Unauthorized errors."""
    return JSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={
            "error": {
                "code": "AUTHENTICATION_ERROR",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": str(uuid.uuid4())
            }
        }
    )


async def authorization_error_handler(request: Request, exc: AuthorizationError) -> JSONResponse:
    """Handle 403 Forbidden errors."""
    return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={
            "error": {
                "code": "AUTHORIZATION_ERROR",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": str(uuid.uuid4())
            }
        }
    )


async def not_found_error_handler(request: Request, exc: NotFoundError) -> JSONResponse:
    """Handle 404 Not Found errors."""
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": {
                "code": "NOT_FOUND_ERROR",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": str(uuid.uuid4())
            }
        }
    )


async def rate_limit_error_handler(request: Request, exc: RateLimitError) -> JSONResponse:
    """Handle 429 Rate Limit Exceeded errors."""
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": exc.message,
                "details": exc.details,
                "timestamp": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
                "request_id": str(uuid.uuid4())
            }
        },
        headers={
            "Retry-After": str(exc.retry_after_seconds)
        }
    )
