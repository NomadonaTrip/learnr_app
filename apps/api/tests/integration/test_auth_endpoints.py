"""
Sample Integration Test: Authentication Endpoints

This demonstrates advanced API testing patterns:
- User registration
- Login flow
- Password reset
- Protected endpoints
- Error handling
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
class TestUserRegistration:
    """Test user registration endpoint."""

    async def test_register_new_user_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test successful user registration."""
        response = await client.post("/v1/auth/register", json=sample_user_data)

        assert response.status_code == 201

        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert "password" not in data["user"]  # Password should not be returned

    async def test_register_duplicate_email_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test that registering with duplicate email fails."""
        # Register first user
        await client.post("/v1/auth/register", json=sample_user_data)

        # Try to register again with same email
        response = await client.post("/v1/auth/register", json=sample_user_data)

        assert response.status_code == 409  # Conflict for duplicate email
        data = response.json()
        assert "email" in str(data).lower() or "already" in str(data).lower()

    async def test_register_invalid_email_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test that invalid email format fails."""
        invalid_data = {**sample_user_data, "email": "not-an-email"}

        response = await client.post("/v1/auth/register", json=invalid_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "email" in str(data).lower()

    async def test_register_weak_password_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test that weak password fails."""
        weak_data = {**sample_user_data, "password": "123"}

        response = await client.post("/v1/auth/register", json=weak_data)

        assert response.status_code == 422
        data = response.json()
        assert "password" in str(data).lower()

    async def test_register_missing_fields_fails(self, client: AsyncClient, db_session: AsyncSession):
        """Test that missing required fields fails."""
        incomplete_data = {"email": "test@example.com"}  # Missing password

        response = await client.post("/v1/auth/register", json=incomplete_data)

        assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
class TestUserLogin:
    """Test user login endpoint."""

    async def test_login_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test successful login."""
        # Register user first
        await client.post("/v1/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/v1/auth/login", json=login_data)

        assert response.status_code == 200

        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == sample_user_data["email"]

    async def test_login_wrong_password_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test that wrong password fails."""
        # Register user
        await client.post("/v1/auth/register", json=sample_user_data)

        # Try to login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = await client.post("/v1/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        # Response may have 'detail' or 'message' field
        error_text = str(data).lower()
        assert "credentials" in error_text or "password" in error_text or "invalid" in error_text

    async def test_login_nonexistent_user_fails(self, client: AsyncClient, db_session: AsyncSession):
        """Test that login with non-existent email fails."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = await client.post("/v1/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_login_returns_valid_jwt(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test that login returns a valid JWT token."""
        # Register and login
        await client.post("/v1/auth/register", json=sample_user_data)

        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/v1/auth/login", json=login_data)

        assert response.status_code == 200

        data = response.json()
        token = data["token"]

        # JWT should have 3 parts separated by dots
        assert token.count('.') == 2

        # Token should start with eyJ (base64 encoded JSON)
        assert token.startswith('eyJ')


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
@pytest.mark.email
class TestPasswordReset:
    """Test password reset flow."""

    async def test_request_password_reset_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test requesting password reset returns success response."""
        # Register user
        await client.post("/v1/auth/register", json=sample_user_data)

        # Request password reset
        response = await client.post(
            "/v1/auth/forgot-password",
            json={"email": sample_user_data["email"]}
        )

        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        # Email sending is tested via mock in unit tests

    async def test_request_password_reset_nonexistent_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test password reset for non-existent user (security: don't reveal)."""
        response = await client.post(
            "/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )

        # Should return success to prevent email enumeration
        assert response.status_code == 200
        # Email not sent (tested via unit tests with mocks)

    @pytest.mark.skip(reason="Requires actual token generation - covered by test_password_reset_api.py")
    async def test_reset_password_with_valid_token(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test resetting password with valid token."""
        pass

    @pytest.mark.skip(reason="Requires actual token handling - covered by test_password_reset_api.py")
    async def test_reset_password_with_expired_token(self, client: AsyncClient, db_session: AsyncSession):
        """Test that expired token is rejected."""
        pass


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
class TestProtectedEndpoints:
    """Test authentication required for protected endpoints."""

    async def test_access_protected_endpoint_without_auth_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that accessing protected endpoint without auth fails."""
        response = await client.get("/v1/users/me")

        assert response.status_code == 401

    async def test_access_protected_endpoint_with_invalid_token_fails(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that invalid token is rejected."""
        headers = {"Authorization": "Bearer invalid-token"}

        response = await client.get("/v1/users/me", headers=headers)

        assert response.status_code == 401

    async def test_access_protected_endpoint_with_valid_token_success(
        self,
        client: AsyncClient,
        sample_user_data: dict,
        db_session: AsyncSession
    ):
        """Test that valid token allows access."""
        # Register and login
        await client.post("/v1/auth/register", json=sample_user_data)

        login_response = await client.post(
            "/v1/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )

        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Access protected endpoint
        response = await client.get("/v1/users/me", headers=headers)

        assert response.status_code == 200

        data = response.json()
        assert data["email"] == sample_user_data["email"]

    async def test_token_expires_after_7_days(self, client: AsyncClient, db_session: AsyncSession):
        """Test that token expires after 7 days (per PRD FR2.7)."""
        # This would require manipulating time or using an expired token
        # For now, document the requirement
        pass  # TODO: Implement when auth system is created
