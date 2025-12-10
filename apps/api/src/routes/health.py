"""Health check endpoint."""
from datetime import datetime, timezone
import time

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.session import get_db
from src.db.qdrant_client import get_qdrant
from src.schemas.health import DatabaseHealth, QdrantHealth, HealthResponse

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
                        "qdrant": {
                            "status": "connected",
                            "response_time_ms": 10,
                            "collections_count": 2
                        }
                    }
                }
            },
        },
        503: {
            "description": "API is unhealthy (database or Qdrant connection failed)",
            "content": {
                "application/json": {
                    "example": {
                        "status": "unhealthy",
                        "timestamp": "2025-11-21T10:30:00.123456Z",
                        "database": {
                            "status": "connected",
                            "response_time_ms": 5
                        },
                        "qdrant": {
                            "status": "disconnected",
                            "error": "Connection timeout",
                        }
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
    - Qdrant vector database connection is healthy

    **No authentication required** - publicly accessible for monitoring tools.

    Returns 200 if all services healthy, 503 if any service connection fails.
    """
    timestamp = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    # Check database connectivity
    database_status = "unknown"
    database_response_time_ms = None
    database_error = None

    try:
        start_time = time.time()
        await db.execute(text("SELECT 1"))
        database_response_time_ms = int((time.time() - start_time) * 1000)
        database_status = "connected"
    except Exception as e:
        database_status = "disconnected"
        database_error = str(e)

    # Check Qdrant connectivity
    qdrant_status = "unknown"
    qdrant_response_time_ms = None
    qdrant_collections_count = None
    qdrant_collections = None
    qdrant_error = None

    try:
        start_time = time.time()
        qdrant_client = get_qdrant()
        collections = await qdrant_client.get_collections()
        qdrant_response_time_ms = int((time.time() - start_time) * 1000)
        qdrant_status = "connected"
        qdrant_collections_count = len(collections.collections)
        qdrant_collections = [col.name for col in collections.collections]
    except Exception as e:
        qdrant_status = "disconnected"
        qdrant_error = str(e)

    # Determine overall health status
    overall_status = "healthy" if (
        database_status == "connected" and qdrant_status == "connected"
    ) else "unhealthy"

    # Build response
    health_response = HealthResponse(
        status=overall_status,
        timestamp=timestamp,
        database=DatabaseHealth(
            status=database_status,
            response_time_ms=database_response_time_ms,
            error=database_error
        ),
        qdrant=QdrantHealth(
            status=qdrant_status,
            response_time_ms=qdrant_response_time_ms,
            collections_count=qdrant_collections_count,
            collections=qdrant_collections,
            error=qdrant_error
        )
    )

    # Return 503 if any service is down
    if overall_status == "unhealthy":
        return Response(
            content=health_response.json(),
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            media_type="application/json",
        )

    return health_response
