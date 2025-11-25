"""
Integration tests for user registration API endpoint.
Tests the full registration flow from HTTP request to database.
"""

import pytest
from httpx import AsyncClient
from jose import jwt
from src.config import settings
from src.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.integration
class TestUserRegistrationAPI:
    """Integration tests for POST /v1/auth/register endpoint."""

    async def test_register_success(self, client: AsyncClient, db_session: AsyncSession):
        """Test successful user registration returns 201 with user and token."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "test@example.com",
                "password": "SecurePass123"
            }
        )

        assert response.status_code == 201

        data = response.json()

        # Verify response structure
        assert "user" in data
        assert "token" in data

        # Verify user data
        user = data["user"]
        assert user["email"] == "test@example.com"
        assert "id" in user
        assert "created_at" in user
        assert "hashed_password" not in user  # Password should not be exposed

        # Verify default values
        assert user["is_admin"] is False
        assert user["dark_mode"] == "auto"
        assert user["exam_date"] is None
        assert user["target_score"] is None

        # Verify token exists
        assert isinstance(data["token"], str)
        assert len(data["token"]) > 0

    async def test_register_creates_user_in_database(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that registration actually creates user record in database."""
        email = "dbtest@example.com"
        response = await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "SecurePass123"}
        )

        assert response.status_code == 201

        # Verify user exists in database
        user_repo = UserRepository(db_session)
        user = await user_repo.get_by_email(email)

        assert user is not None
        assert user.email == email
        assert user.hashed_password.startswith("$2b$")  # bcrypt hash

    async def test_register_password_is_hashed(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that password is hashed in database, not stored as plaintext."""
        password = "SecurePass123"
        response = await client.post(
            "/v1/auth/register",
            json={"email": "hashtest@example.com", "password": password}
        )

        assert response.status_code == 201

        # Query database directly
        user_repo = UserRepository(db_session)
        user = await user_repo.get_by_email("hashtest@example.com")

        # Verify password is NOT plaintext
        assert user.hashed_password != password
        assert len(user.hashed_password) == 60  # bcrypt hash length
        assert user.hashed_password.startswith("$2b$")

    async def test_register_duplicate_email_returns_409(
        self,
        client: AsyncClient
    ):
        """Test that duplicate email returns 409 Conflict."""
        email = "duplicate@example.com"

        # Register first user
        response1 = await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "SecurePass123"}
        )
        assert response1.status_code == 201

        # Try to register again with same email
        response2 = await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "DifferentPass456"}
        )

        assert response2.status_code == 409

        data = response2.json()
        assert "error" in data
        assert data["error"]["code"] == "CONFLICT_ERROR"
        assert "already registered" in data["error"]["message"].lower()
        assert "timestamp" in data["error"]
        assert "request_id" in data["error"]

    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        """Test that invalid email format returns 422 Unprocessable Entity."""
        response = await client.post(
            "/v1/auth/register",
            json={"email": "not-an-email", "password": "SecurePass123"}
        )

        assert response.status_code == 422

    async def test_register_weak_password_returns_422(self, client: AsyncClient):
        """Test that weak password returns 422."""
        # Test password too short (< 8 chars)
        response = await client.post(
            "/v1/auth/register",
            json={"email": "test@example.com", "password": "short"}
        )

        assert response.status_code == 422

    async def test_register_password_no_number_returns_422(self, client: AsyncClient):
        """Test that password without number returns 422."""
        response = await client.post(
            "/v1/auth/register",
            json={"email": "test@example.com", "password": "NoNumberPass"}
        )

        assert response.status_code == 422

    async def test_register_password_no_letter_returns_422(self, client: AsyncClient):
        """Test that password without letter returns 422."""
        response = await client.post(
            "/v1/auth/register",
            json={"email": "test@example.com", "password": "12345678"}
        )

        assert response.status_code == 422

    async def test_register_jwt_token_valid(self, client: AsyncClient):
        """Test that returned JWT token can be decoded and contains user_id."""
        response = await client.post(
            "/v1/auth/register",
            json={"email": "jwttest@example.com", "password": "SecurePass123"}
        )

        assert response.status_code == 201

        data = response.json()
        token = data["token"]
        user_id = data["user"]["id"]

        # Decode token
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify payload contains user_id
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

    async def test_register_jwt_token_7_day_expiration(self, client: AsyncClient):
        """Test that JWT token has 7-day expiration."""
        response = await client.post(
            "/v1/auth/register",
            json={"email": "exptest@example.com", "password": "SecurePass123"}
        )

        assert response.status_code == 201

        token = response.json()["token"]
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify expiration is approximately 7 days (604800 seconds)
        exp_delta = payload["exp"] - payload["iat"]
        assert abs(exp_delta - settings.JWT_EXPIRATION_SECONDS) < 5

    async def test_register_email_case_insensitive(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that email is stored lowercase and duplicate check is case-insensitive."""
        # Register with mixed case
        response1 = await client.post(
            "/v1/auth/register",
            json={"email": "Test@Example.COM", "password": "SecurePass123"}
        )

        assert response1.status_code == 201

        # Verify email is stored lowercase
        user_repo = UserRepository(db_session)
        user = await user_repo.get_by_email("test@example.com")
        assert user is not None
        assert user.email == "test@example.com"

        # Try to register with different case - should fail
        response2 = await client.post(
            "/v1/auth/register",
            json={"email": "test@example.com", "password": "DifferentPass456"}
        )

        assert response2.status_code == 409

    async def test_register_missing_email_returns_422(self, client: AsyncClient):
        """Test that missing email returns 422."""
        response = await client.post(
            "/v1/auth/register",
            json={"password": "SecurePass123"}
        )

        assert response.status_code == 422

    async def test_register_missing_password_returns_422(self, client: AsyncClient):
        """Test that missing password returns 422."""
        response = await client.post(
            "/v1/auth/register",
            json={"email": "test@example.com"}
        )

        assert response.status_code == 422

    async def test_register_empty_body_returns_422(self, client: AsyncClient):
        """Test that empty request body returns 422."""
        response = await client.post("/v1/auth/register", json={})

        assert response.status_code == 422

    async def test_register_error_response_format(self, client: AsyncClient):
        """Test that error responses match architecture format."""
        # Trigger duplicate email error
        email = "errorformat@example.com"
        await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "SecurePass123"}
        )

        response = await client.post(
            "/v1/auth/register",
            json={"email": email, "password": "SecurePass123"}
        )

        assert response.status_code == 409

        data = response.json()

        # Verify error format
        assert "error" in data
        error = data["error"]

        assert "code" in error
        assert "message" in error
        assert "details" in error
        assert "timestamp" in error
        assert "request_id" in error

        # Verify timestamp format (ISO 8601)
        assert "T" in error["timestamp"]
        assert error["timestamp"].endswith("Z")

    async def test_register_multiple_users_sequential(self, client: AsyncClient):
        """Test that multiple users can register successfully."""
        users = [
            {"email": "user1@example.com", "password": "SecurePass123"},
            {"email": "user2@example.com", "password": "SecurePass456"},
            {"email": "user3@example.com", "password": "SecurePass789"}
        ]

        for user_data in users:
            response = await client.post("/v1/auth/register", json=user_data)
            assert response.status_code == 201

            data = response.json()
            assert data["user"]["email"] == user_data["email"]
            assert len(data["token"]) > 0
