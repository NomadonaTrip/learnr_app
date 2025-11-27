"""
Integration tests for user profile endpoints.
Tests authentication-protected user endpoints.
"""

import pytest
from httpx import AsyncClient
from datetime import timedelta
from src.utils.auth import create_access_token
import uuid


@pytest.mark.asyncio
@pytest.mark.integration
class TestGetUserProfile:
    """Test GET /v1/users/me endpoint."""

    async def test_get_user_profile_authenticated(self, client: AsyncClient):
        """Test GET /v1/users/me with valid JWT returns profile."""
        # Register and login
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "profiletest@example.com", "password": "SecurePass123"}
        )
        assert register_response.status_code == 201
        token = register_response.json()["token"]

        # Get profile
        response = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "profiletest@example.com"
        assert "id" in data
        assert "created_at" in data
        assert "hashed_password" not in data  # Password should not be exposed

    async def test_get_user_profile_no_token(self, client: AsyncClient):
        """Test GET /v1/users/me without token returns 401."""
        response = await client.get("/v1/users/me")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert "Authentication required" in data["detail"]

    async def test_get_user_profile_expired_token(self, client: AsyncClient):
        """Test GET /v1/users/me with expired token returns 401."""
        # Create expired token
        expired_token = create_access_token(
            data={"sub": str(uuid.uuid4())},
            expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
        )

        response = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {expired_token}"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_get_user_profile_invalid_token(self, client: AsyncClient):
        """Test GET /v1/users/me with invalid token returns 401."""
        response = await client.get(
            "/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_get_user_profile_malformed_header(self, client: AsyncClient):
        """Test GET /v1/users/me with malformed Authorization header returns 401."""
        # Test without Bearer prefix
        response = await client.get(
            "/v1/users/me",
            headers={"Authorization": "invalid-header-format"}
        )

        assert response.status_code == 401

    async def test_get_user_profile_includes_all_fields(self, client: AsyncClient):
        """Test that user profile includes all expected fields."""
        # Register user
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "fullprofile@example.com", "password": "SecurePass123"}
        )
        token = register_response.json()["token"]

        # Get profile
        response = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all expected fields are present
        expected_fields = [
            "id", "email", "created_at", "is_admin", "dark_mode",
            "exam_date", "target_score", "daily_study_time",
            "knowledge_level", "motivation", "referral_source"
        ]
        for field in expected_fields:
            assert field in data


@pytest.mark.asyncio
@pytest.mark.integration
class TestUpdateUserProfile:
    """Test PUT /v1/users/me endpoint."""

    async def test_update_user_profile_authenticated(self, client: AsyncClient):
        """Test PUT /v1/users/me with valid JWT updates profile."""
        # Register and login
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "updatetest@example.com", "password": "SecurePass123"}
        )
        token = register_response.json()["token"]

        # Update profile
        response = await client.put(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "exam_date": "2025-12-15",
                "target_score": 85,
                "daily_study_time": 60,
                "knowledge_level": "Intermediate",
                "dark_mode": "dark"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["exam_date"] == "2025-12-15"
        assert data["target_score"] == 85
        assert data["daily_study_time"] == 60
        assert data["knowledge_level"] == "Intermediate"
        assert data["dark_mode"] == "dark"

    async def test_update_user_profile_no_token(self, client: AsyncClient):
        """Test PUT /v1/users/me without token returns 401."""
        response = await client.put(
            "/v1/users/me",
            json={"target_score": 85}
        )

        assert response.status_code == 401

    async def test_update_user_profile_partial_update(self, client: AsyncClient):
        """Test that partial updates work (only updating some fields)."""
        # Register user
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "partialupdate@example.com", "password": "SecurePass123"}
        )
        token = register_response.json()["token"]

        # Update only target_score
        response = await client.put(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"target_score": 90}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_score"] == 90
        # Other fields should remain unchanged
        assert data["email"] == "partialupdate@example.com"

    async def test_update_user_profile_invalid_data(self, client: AsyncClient):
        """Test that invalid data is rejected."""
        # Register user
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "invaliddata@example.com", "password": "SecurePass123"}
        )
        token = register_response.json()["token"]

        # Try to update with invalid target_score (must be 0-100)
        response = await client.put(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"target_score": 150}  # Invalid: greater than 100
        )

        assert response.status_code == 422  # Validation error

    async def test_update_user_profile_invalid_knowledge_level(self, client: AsyncClient):
        """Test that invalid knowledge level is rejected."""
        # Register user
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "invalidknowledge@example.com", "password": "SecurePass123"}
        )
        token = register_response.json()["token"]

        # Try to update with invalid knowledge_level
        response = await client.put(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"knowledge_level": "InvalidLevel"}
        )

        assert response.status_code == 422  # Validation error

    async def test_update_user_profile_persists(self, client: AsyncClient):
        """Test that profile updates persist across requests."""
        # Register user
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "persist@example.com", "password": "SecurePass123"}
        )
        token = register_response.json()["token"]

        # Update profile
        await client.put(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"},
            json={"target_score": 95, "dark_mode": "light"}
        )

        # Fetch profile again to verify persistence
        response = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["target_score"] == 95
        assert data["dark_mode"] == "light"


@pytest.mark.asyncio
@pytest.mark.integration
class TestProtectedEndpointWorkflow:
    """Test complete workflow: register → login → access protected endpoint."""

    async def test_protected_endpoint_workflow(self, client: AsyncClient):
        """Test complete workflow: register → login → access protected endpoint."""
        # Register
        register_response = await client.post(
            "/v1/auth/register",
            json={"email": "workflow@example.com", "password": "SecurePass123"}
        )
        assert register_response.status_code == 201

        # Login
        login_response = await client.post(
            "/v1/auth/login",
            json={"email": "workflow@example.com", "password": "SecurePass123"}
        )
        assert login_response.status_code == 200
        token = login_response.json()["token"]

        # Access protected endpoint
        profile_response = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "workflow@example.com"

    async def test_multiple_users_isolated_profiles(self, client: AsyncClient):
        """Test that different users have isolated profiles."""
        # Register first user
        register1 = await client.post(
            "/v1/auth/register",
            json={"email": "user1@example.com", "password": "SecurePass123"}
        )
        token1 = register1.json()["token"]

        # Register second user
        register2 = await client.post(
            "/v1/auth/register",
            json={"email": "user2@example.com", "password": "SecurePass123"}
        )
        token2 = register2.json()["token"]

        # Update first user's profile
        await client.put(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token1}"},
            json={"target_score": 80}
        )

        # Update second user's profile
        await client.put(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token2}"},
            json={"target_score": 90}
        )

        # Verify each user has their own profile
        profile1 = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        profile2 = await client.get(
            "/v1/users/me",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert profile1.json()["target_score"] == 80
        assert profile1.json()["email"] == "user1@example.com"
        assert profile2.json()["target_score"] == 90
        assert profile2.json()["email"] == "user2@example.com"
