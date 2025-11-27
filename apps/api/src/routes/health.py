"""Health check endpoint."""
from datetime import datetime
import time

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.schemas.health import DatabaseHealth, HealthResponse

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check endpoint",
    description="Check API and database health status. Does not require authentication.",
    responses={
        200: {
            "description": "API is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "healthy",
                        "timestamp": "2025-11-21T10:30:00.123456Z",
                        "database": {
                            "status": "connected",
                            "response_time_ms": 5,
                        },
                    }
                }
            },
        },
        503: {
            "description": "API is unhealthy (database connection failed)",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2025-11-21T10:30:00.123456Z",
                        "database": {
                            "status": "disconnected",
                            "error": "Connection timeout",
                        },
                    }
                }
            },
        },
    },
)
async def health_check(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint for monitoring and load balancers.

    Verifies:
    - API is running
    - Database connection is healthy

    **No authentication required** - publicly accessible for monitoring tools.

    Returns 200 if healthy, 503 if database connection fails.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Check database connectivity
    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        response_time_ms = int((time.time() - start_time) * 1000)

        return HealthResponse(
            status="healthy",
            timestamp=timestamp,
            database=DatabaseHealth(
                status="connected", response_time_ms=response_time_ms
            ),
        )
    except Exception as e:
        # Database connection failed - return 503
        response_data = HealthResponse(
            status="unhealthy",
            timestamp=timestamp,
            database=DatabaseHealth(status="disconnected", error=str(e)),
        )
        return Response(
            content=response_data.json(),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )
