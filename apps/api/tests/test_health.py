"""
Sample API Test: Health Check Endpoint

This demonstrates basic API testing patterns:
- Simple GET request
- Status code validation
- Response structure validation
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.api
async def test_health_check_returns_200(client: AsyncClient):
    """Test that health endpoint returns 200 OK."""
    response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
@pytest.mark.api
async def test_health_check_response_structure(client: AsyncClient):
    """Test that health endpoint returns correct JSON structure."""
    response = await client.get("/health")

    assert response.status_code == 200

    data = response.json()
    assert "status" in data
    assert data["status"] == "healthy"


@pytest.mark.asyncio
@pytest.mark.api
async def test_health_check_content_type(client: AsyncClient):
    """Test that health endpoint returns JSON content type."""
    response = await client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]
