"""
Integration tests for Users API endpoints.
Tests GET /v1/users/me and PUT /v1/users/me endpoints.
"""
import pytest
from uuid import uuid4
from datetime import date

from src.models.user import User
from src.utils.auth import create_access_token, hash_password


@pytest.fixture
async def test_user(db_session):
    """Create a test user for API tests."""
    user = User(
        email=f"testuser-{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("SecurePassword123!"),
        exam_date=date(2025, 6, 15),
        target_score=80,
        daily_study_time=60,
        knowledge_level="Intermediate",
        motivation="certification",
        referral_source="Search",
        dark_mode="auto",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_token(test_user):
    """Generate auth token for test user."""
    return create_access_token({"sub": str(test_user.id)})


@pytest.fixture
def user_auth_headers(auth_token):
    """Auth headers for API requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.mark.asyncio
class TestGetUserProfile:
    """Tests for GET /v1/users/me endpoint."""

    async def test_get_profile_success(self, client, test_user, user_auth_headers):
        """Test getting user profile returns user data."""
        response = await client.get("/v1/users/me", headers=user_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert data["email"] == test_user.email
        assert data["target_score"] == 80
        assert data["daily_study_time"] == 60
        assert data["knowledge_level"] == "Intermediate"

    async def test_get_profile_includes_onboarding_data(self, client, test_user, user_auth_headers):
        """Test profile includes onboarding fields."""
        response = await client.get("/v1/users/me", headers=user_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "exam_date" in data
        assert "knowledge_level" in data
        assert "motivation" in data
        assert "referral_source" in data
        assert "dark_mode" in data

    async def test_get_profile_requires_auth(self, client):
        """Test getting profile without auth returns 401."""
        response = await client.get("/v1/users/me")

        assert response.status_code == 401

    async def test_get_profile_invalid_token(self, client):
        """Test getting profile with invalid token returns 401."""
        response = await client.get(
            "/v1/users/me",
            headers={"Authorization": "Bearer invalid-token"}
        )

        assert response.status_code == 401

    async def test_get_profile_excludes_password(self, client, test_user, user_auth_headers):
        """Test profile response does not include password."""
        response = await client.get("/v1/users/me", headers=user_auth_headers)

        assert response.status_code == 200
        data = response.json()

        assert "password" not in data
        assert "hashed_password" not in data


@pytest.mark.asyncio
class TestUpdateUserProfile:
    """Tests for PUT /v1/users/me endpoint."""

    async def test_update_profile_success(self, client, test_user, user_auth_headers):
        """Test updating user profile."""
        update_data = {
            "target_score": 90,
            "daily_study_time": 90,
        }

        response = await client.put(
            "/v1/users/me",
            headers=user_auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["target_score"] == 90
        assert data["daily_study_time"] == 90

    async def test_update_exam_date(self, client, test_user, user_auth_headers):
        """Test updating exam date."""
        update_data = {"exam_date": "2025-12-31"}

        response = await client.put(
            "/v1/users/me",
            headers=user_auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["exam_date"] == "2025-12-31"

    async def test_update_knowledge_level(self, client, test_user, user_auth_headers):
        """Test updating knowledge level."""
        update_data = {"knowledge_level": "Advanced"}

        response = await client.put(
            "/v1/users/me",
            headers=user_auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["knowledge_level"] == "Advanced"

    async def test_update_dark_mode(self, client, test_user, user_auth_headers):
        """Test updating dark mode preference."""
        update_data = {"dark_mode": "dark"}

        response = await client.put(
            "/v1/users/me",
            headers=user_auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["dark_mode"] == "dark"

    async def test_update_profile_partial(self, client, test_user, user_auth_headers):
        """Test partial update only changes specified fields."""
        original_target = test_user.target_score

        update_data = {"daily_study_time": 120}

        response = await client.put(
            "/v1/users/me",
            headers=user_auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        assert data["daily_study_time"] == 120
        assert data["target_score"] == original_target  # Unchanged

    async def test_update_profile_requires_auth(self, client):
        """Test updating profile without auth returns 401."""
        response = await client.put(
            "/v1/users/me",
            json={"target_score": 85}
        )

        assert response.status_code == 401

    async def test_update_profile_empty_body(self, client, test_user, user_auth_headers):
        """Test update with empty body succeeds (no changes)."""
        response = await client.put(
            "/v1/users/me",
            headers=user_auth_headers,
            json={}
        )

        assert response.status_code == 200

    async def test_update_profile_returns_updated_data(self, client, test_user, user_auth_headers):
        """Test update returns the updated user data."""
        update_data = {
            "target_score": 95,
            "motivation": "career growth",
        }

        response = await client.put(
            "/v1/users/me",
            headers=user_auth_headers,
            json=update_data
        )

        assert response.status_code == 200
        data = response.json()

        # Verify returned data reflects updates
        assert data["target_score"] == 95
        assert data["motivation"] == "career growth"

        # Verify data is persisted by fetching again
        get_response = await client.get("/v1/users/me", headers=user_auth_headers)
        get_data = get_response.json()

        assert get_data["target_score"] == 95
        assert get_data["motivation"] == "career growth"
