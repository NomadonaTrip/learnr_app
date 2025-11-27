"""
Integration tests for API documentation.
Tests OpenAPI specification completeness and accuracy.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
async def test_swagger_ui_accessible(client: AsyncClient):
    """Test Swagger UI is accessible at /docs."""
    response = await client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"swagger-ui" in response.content


@pytest.mark.asyncio
@pytest.mark.integration
async def test_redoc_accessible(client: AsyncClient):
    """Test ReDoc is accessible at /redoc."""
    response = await client.get("/redoc")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert b"redoc" in response.content.lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_json_accessible(client: AsyncClient):
    """Test OpenAPI JSON spec is accessible."""
    response = await client.get("/openapi.json")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]

    spec = response.json()
    assert "openapi" in spec
    assert "info" in spec
    assert "paths" in spec


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_spec_includes_all_endpoints(client: AsyncClient):
    """Test OpenAPI spec includes all implemented endpoints from Stories 1.3-1.6."""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Check authentication endpoints (Story 1.3, 1.4, 1.5)
    assert "/v1/auth/register" in spec["paths"]
    assert "/v1/auth/login" in spec["paths"]
    assert "/v1/auth/forgot-password" in spec["paths"]
    assert "/v1/auth/reset-password" in spec["paths"]

    # Check user endpoints (Story 1.6)
    assert "/v1/users/me" in spec["paths"]

    # Check health endpoint (Story 1.7)
    assert "/health" in spec["paths"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_spec_includes_security_scheme(client: AsyncClient):
    """Test OpenAPI spec includes JWT Bearer security scheme."""
    response = await client.get("/openapi.json")
    spec = response.json()

    assert "components" in spec
    assert "securitySchemes" in spec["components"]
    assert "BearerAuth" in spec["components"]["securitySchemes"]

    bearer_auth = spec["components"]["securitySchemes"]["BearerAuth"]
    assert bearer_auth["type"] == "http"
    assert bearer_auth["scheme"] == "bearer"
    assert bearer_auth["bearerFormat"] == "JWT"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_spec_endpoint_request_schemas(client: AsyncClient):
    """Test OpenAPI spec includes request schemas."""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Check register endpoint has request body schema
    register_endpoint = spec["paths"]["/v1/auth/register"]["post"]
    assert "requestBody" in register_endpoint
    assert "content" in register_endpoint["requestBody"]
    assert "application/json" in register_endpoint["requestBody"]["content"]

    # Check login endpoint has request body schema
    login_endpoint = spec["paths"]["/v1/auth/login"]["post"]
    assert "requestBody" in login_endpoint


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_spec_endpoint_response_schemas(client: AsyncClient):
    """Test OpenAPI spec includes response schemas."""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Check register endpoint has response schema
    register_endpoint = spec["paths"]["/v1/auth/register"]["post"]
    assert "responses" in register_endpoint
    assert "201" in register_endpoint["responses"]

    # Check login endpoint has response schema
    login_endpoint = spec["paths"]["/v1/auth/login"]["post"]
    assert "responses" in login_endpoint
    assert "200" in login_endpoint["responses"]

    # Check health endpoint has response schemas for 200 and 503
    health_endpoint = spec["paths"]["/health"]["get"]
    assert "responses" in health_endpoint
    assert "200" in health_endpoint["responses"]
    assert "503" in health_endpoint["responses"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_spec_has_api_metadata(client: AsyncClient):
    """Test OpenAPI spec includes API metadata."""
    response = await client.get("/openapi.json")
    spec = response.json()

    assert "info" in spec
    assert spec["info"]["title"] == "LearnR API"
    assert spec["info"]["version"] == "1.0.0"
    assert "description" in spec["info"]
    assert "contact" in spec["info"]
    assert "license" in spec["info"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_spec_endpoint_summaries(client: AsyncClient):
    """Test OpenAPI spec includes endpoint summaries."""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Check register endpoint has summary
    register_endpoint = spec["paths"]["/v1/auth/register"]["post"]
    assert "summary" in register_endpoint
    assert len(register_endpoint["summary"]) > 0

    # Check health endpoint has summary
    health_endpoint = spec["paths"]["/health"]["get"]
    assert "summary" in health_endpoint
    assert "Health check" in health_endpoint["summary"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_openapi_spec_endpoint_tags(client: AsyncClient):
    """Test OpenAPI spec includes endpoint tags for organization."""
    response = await client.get("/openapi.json")
    spec = response.json()

    # Check authentication endpoints have authentication tag
    register_endpoint = spec["paths"]["/v1/auth/register"]["post"]
    assert "tags" in register_endpoint
    assert "authentication" in register_endpoint["tags"]

    # Check user endpoints have users tag
    users_me_endpoint = spec["paths"]["/v1/users/me"]["get"]
    assert "tags" in users_me_endpoint
    assert "users" in users_me_endpoint["tags"]

    # Check health endpoint has health tag
    health_endpoint = spec["paths"]["/health"]["get"]
    assert "tags" in health_endpoint
    assert "health" in health_endpoint["tags"]
