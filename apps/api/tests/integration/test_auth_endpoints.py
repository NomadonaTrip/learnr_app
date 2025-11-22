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


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
class TestUserRegistration:
    """Test user registration endpoint."""

    async def test_register_new_user_success(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test successful user registration."""
        response = await client.post("/api/auth/register", json=sample_user_data)

        assert response.status_code == 201

        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert "password" not in data["user"]  # Password should not be returned

    async def test_register_duplicate_email_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test that registering with duplicate email fails."""
        # Register first user
        await client.post("/api/auth/register", json=sample_user_data)

        # Try to register again with same email
        response = await client.post("/api/auth/register", json=sample_user_data)

        assert response.status_code == 400
        data = response.json()
        assert "email" in data["detail"].lower()

    async def test_register_invalid_email_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test that invalid email format fails."""
        invalid_data = {**sample_user_data, "email": "not-an-email"}

        response = await client.post("/api/auth/register", json=invalid_data)

        assert response.status_code == 422  # Validation error
        data = response.json()
        assert "email" in str(data).lower()

    async def test_register_weak_password_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test that weak password fails."""
        weak_data = {**sample_user_data, "password": "123"}

        response = await client.post("/api/auth/register", json=weak_data)

        assert response.status_code == 422
        data = response.json()
        assert "password" in str(data).lower()

    async def test_register_missing_fields_fails(self, client: AsyncClient):
        """Test that missing required fields fails."""
        incomplete_data = {"email": "test@example.com"}  # Missing password

        response = await client.post("/api/auth/register", json=incomplete_data)

        assert response.status_code == 422


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
class TestUserLogin:
    """Test user login endpoint."""

    async def test_login_success(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test successful login."""
        # Register user first
        await client.post("/api/auth/register", json=sample_user_data)

        # Login
        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 200

        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == sample_user_data["email"]

    async def test_login_wrong_password_fails(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test that wrong password fails."""
        # Register user
        await client.post("/api/auth/register", json=sample_user_data)

        # Try to login with wrong password
        login_data = {
            "email": sample_user_data["email"],
            "password": "WrongPassword123!"
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401
        data = response.json()
        assert "credentials" in data["detail"].lower() or "password" in data["detail"].lower()

    async def test_login_nonexistent_user_fails(self, client: AsyncClient):
        """Test that login with non-existent email fails."""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = await client.post("/api/auth/login", json=login_data)

        assert response.status_code == 401

    async def test_login_returns_valid_jwt(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test that login returns a valid JWT token."""
        # Register and login
        await client.post("/api/auth/register", json=sample_user_data)

        login_data = {
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        }
        response = await client.post("/api/auth/login", json=login_data)

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
        mock_email_service
    ):
        """Test requesting password reset sends email."""
        # Register user
        await client.post("/api/auth/register", json=sample_user_data)

        # Request password reset
        response = await client.post(
            "/api/auth/reset-password",
            json={"email": sample_user_data["email"]}
        )

        assert response.status_code == 200

        data = response.json()
        assert "message" in data
        assert "email" in data["message"].lower()

        # Verify email was sent (using mock)
        sent_emails = mock_email_service.get_sent_emails()
        assert len(sent_emails) == 1
        assert sent_emails[0]["to"] == sample_user_data["email"]
        assert "reset" in sent_emails[0]["subject"].lower()

    async def test_request_password_reset_nonexistent_user(
        self,
        client: AsyncClient,
        mock_email_service
    ):
        """Test password reset for non-existent user (security: don't reveal)."""
        response = await client.post(
            "/api/auth/reset-password",
            json={"email": "nonexistent@example.com"}
        )

        # Should return success to prevent email enumeration
        assert response.status_code == 200

        # But no email should be sent
        sent_emails = mock_email_service.get_sent_emails()
        assert len(sent_emails) == 0

    async def test_reset_password_with_valid_token(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test resetting password with valid token."""
        # Register user
        await client.post("/api/auth/register", json=sample_user_data)

        # Request reset
        await client.post(
            "/api/auth/reset-password",
            json={"email": sample_user_data["email"]}
        )

        # TODO: Extract token from email (for now, use mock token)
        reset_token = "mock-reset-token"

        # Reset password
        new_password = "NewSecurePassword123!"
        response = await client.post(
            "/api/auth/reset-password/confirm",
            json={
                "token": reset_token,
                "new_password": new_password
            }
        )

        assert response.status_code == 200

        # Verify can login with new password
        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": new_password
            }
        )

        assert login_response.status_code == 200

    async def test_reset_password_with_expired_token(self, client: AsyncClient):
        """Test that expired token is rejected."""
        expired_token = "expired-token"

        response = await client.post(
            "/api/auth/reset-password/confirm",
            json={
                "token": expired_token,
                "new_password": "NewPassword123!"
            }
        )

        assert response.status_code == 400 or response.status_code == 401
        data = response.json()
        assert "token" in data["detail"].lower() or "expired" in data["detail"].lower()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.auth
class TestProtectedEndpoints:
    """Test authentication required for protected endpoints."""

    async def test_access_protected_endpoint_without_auth_fails(
        self,
        client: AsyncClient
    ):
        """Test that accessing protected endpoint without auth fails."""
        response = await client.get("/api/me")

        assert response.status_code == 401

    async def test_access_protected_endpoint_with_invalid_token_fails(
        self,
        client: AsyncClient
    ):
        """Test that invalid token is rejected."""
        headers = {"Authorization": "Bearer invalid-token"}

        response = await client.get("/api/me", headers=headers)

        assert response.status_code == 401

    async def test_access_protected_endpoint_with_valid_token_success(
        self,
        client: AsyncClient,
        sample_user_data: dict
    ):
        """Test that valid token allows access."""
        # Register and login
        await client.post("/api/auth/register", json=sample_user_data)

        login_response = await client.post(
            "/api/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"]
            }
        )

        token = login_response.json()["token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Access protected endpoint
        response = await client.get("/api/me", headers=headers)

        assert response.status_code == 200

        data = response.json()
        assert data["email"] == sample_user_data["email"]

    async def test_token_expires_after_7_days(self, client: AsyncClient):
        """Test that token expires after 7 days (per PRD FR2.7)."""
        # This would require manipulating time or using an expired token
        # For now, document the requirement
        pass  # TODO: Implement when auth system is created
