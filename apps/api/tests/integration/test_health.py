"""
Integration tests for health check endpoint.
Tests health endpoint functionality including database connectivity checks.
"""
from datetime import datetime

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_returns_200_with_healthy_status(client: AsyncClient):
    """Test health endpoint returns 200 with healthy status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_includes_timestamp_in_iso8601_format(
    client: AsyncClient,
):
    """Test health endpoint includes timestamp in ISO 8601 format."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Verify timestamp exists and is in ISO 8601 format
    assert "timestamp" in data
    timestamp_str = data["timestamp"]

    # Verify it can be parsed as ISO 8601
    # ISO 8601 format with 'Z' suffix needs conversion for Python parser
    parsed_timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
    assert isinstance(parsed_timestamp, datetime)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_includes_database_status(client: AsyncClient):
    """Test health endpoint includes database connectivity status."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Verify database status is included
    assert "database" in data
    assert "status" in data["database"]
    assert data["database"]["status"] == "connected"

    # Verify response time is included and is a positive integer
    assert "response_time_ms" in data["database"]
    assert isinstance(data["database"]["response_time_ms"], int)
    assert data["database"]["response_time_ms"] >= 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_accessible_without_authentication(
    client: AsyncClient,
):
    """Test health endpoint is accessible without authentication."""
    # Make request without Authorization header
    response = await client.get("/health")

    # Should return 200 OK (not 401 Unauthorized)
    assert response.status_code == 200

    # Should return valid health response
    data = response.json()
    assert data["status"] == "healthy"
    assert "database" in data


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_returns_503_when_database_unavailable(
    client: AsyncClient, monkeypatch
):
    """Test health endpoint returns 503 when database connection fails."""
    from sqlalchemy.exc import OperationalError


    # Create a mock database session that raises an exception
    class MockDBSession:
        async def execute(self, query):
            raise OperationalError("Connection failed", None, None)

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            pass

    # Mock the get_db dependency to return failing session
    async def mock_get_db():
        async with MockDBSession() as session:
            yield session

    # Patch the dependency in the app
    from src.main import app
    from src.routes.health import get_db as health_get_db

    app.dependency_overrides[health_get_db] = mock_get_db

    try:
        # Make request with mocked database failure
        response = await client.get("/health")

        # Should return 503 Service Unavailable
        assert response.status_code == 503

        data = response.json()
        assert data["status"] == "unhealthy"
        assert data["database"]["status"] == "disconnected"
        assert "error" in data["database"]
    finally:
        # Clean up override
        app.dependency_overrides.clear()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_database_response_time(client: AsyncClient):
    """Test health endpoint measures database response time."""
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()

    # Response time should be present and reasonable (< 1 second = 1000ms)
    response_time = data["database"]["response_time_ms"]
    assert isinstance(response_time, int)
    assert 0 <= response_time < 1000  # Should be very fast for simple SELECT 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_health_endpoint_returns_json_content_type(client: AsyncClient):
    """Test health endpoint returns JSON content type."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
