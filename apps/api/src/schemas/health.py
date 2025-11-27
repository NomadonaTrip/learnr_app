"""Health check response schemas."""
from pydantic import BaseModel


class DatabaseHealth(BaseModel):
    """Database health status."""

    status: str  # "connected" or "disconnected"
    response_time_ms: int | None = None
    error: str | None = None

    class Config:
        """Pydantic config with example."""

        schema_extra = {
            "example": {"status": "connected", "response_time_ms": 5}
        }


class HealthResponse(BaseModel):
    """Health check response."""

    status: str  # "healthy" or "unhealthy"
    timestamp: str  # ISO 8601 format
    database: DatabaseHealth

    class Config:
        """Pydantic config with example."""

        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-21T10:30:00.123456Z",
                "database": {"status": "connected", "response_time_ms": 5},
            }
        }
