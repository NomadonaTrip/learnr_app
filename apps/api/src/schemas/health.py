"""Health check response schemas."""
from pydantic import BaseModel


class DatabaseHealth(BaseModel):
    """Database health status."""

    status: str  # "connected" or "disconnected"
    response_time_ms: int | None = None
    error: str | None = None

    class Config:
        """Pydantic config with example."""

        json_schema_extra = {
            "example": {"status": "connected", "response_time_ms": 5}
        }


class QdrantHealth(BaseModel):
    """Qdrant vector database health status."""

    status: str  # "connected" or "disconnected"
    response_time_ms: int | None = None
    collections_count: int | None = None
    error: str | None = None

    class Config:
        """Pydantic config with example."""

        json_schema_extra = {
            "example": {
                "status": "connected",
                "response_time_ms": 10,
                "collections_count": 2
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str  # "healthy" or "unhealthy"
    timestamp: str  # ISO 8601 format
    database: DatabaseHealth
    qdrant: QdrantHealth

    class Config:
        """Pydantic config with example."""

        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-21T10:30:00.123456Z",
                "database": {"status": "connected", "response_time_ms": 5},
                "qdrant": {
                    "status": "connected",
                    "response_time_ms": 10,
                    "collections_count": 2
                }
            }
        }
