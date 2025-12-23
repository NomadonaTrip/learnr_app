"""
Integration tests for password reset API endpoints.
Tests complete password reset flow including email sending, token validation, and password updates.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from src.models.password_reset_token import PasswordResetToken


@pytest.mark.asyncio
class TestPasswordResetIntegration:
    """Integration tests for password reset endpoints."""

    async def test_forgot_password_success(self, async_client: AsyncClient, db_session):
        """Test forgot password request returns success message."""
        # Register user first
        register_response = await async_client.post(
            "/v1/auth/register",
            json={"email": "forgottest@example.com", "password": "OldPass123"}
        )
        assert register_response.status_code == 201

        # Request password reset
        response = await async_client.post(
            "/v1/auth/forgot-password",
            json={"email": "forgottest@example.com"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "If your email is registered" in data["message"]

    async def test_forgot_password_nonexistent_email_no_error(self, async_client: AsyncClient, db_session):
        """Test forgot password with non-existent email returns success (no enumeration)."""
        response = await async_client.post(
            "/v1/auth/forgot-password",
            json={"email": "nonexistent@example.com"}
        )

        # Should still return 200 to prevent email enumeration
        assert response.status_code == 200
        data = response.json()
        assert "If your email is registered" in data["message"]

    async def test_password_reset_full_flow(self, async_client: AsyncClient, db_session):
        """Test complete password reset flow from request to login with new password."""
        # Register user
        register_response = await async_client.post(
            "/v1/auth/register",
            json={"email": "resetflow@example.com", "password": "OldPass123"}
        )
        assert register_response.status_code == 201
        user_id = register_response.json()["user"]["id"]

        # Request password reset
        forgot_response = await async_client.post(
            "/v1/auth/forgot-password",
            json={"email": "resetflow@example.com"}
        )
        assert forgot_response.status_code == 200

        # Get token from database (simulate email)
        result = await db_session.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == UUID(user_id))
            .order_by(PasswordResetToken.created_at.desc())
        )
        reset_token = result.scalar_one()

        # Reset password with token
        reset_response = await async_client.post(
            "/v1/auth/reset-password",
            json={
                "token": str(reset_token.token),
                "new_password": "NewPass456"
            }
        )
        assert reset_response.status_code == 200
        assert "Password reset successful" in reset_response.json()["message"]

        # Verify old password doesn't work
        old_login = await async_client.post(
            "/v1/auth/login",
            json={"email": "resetflow@example.com", "password": "OldPass123"}
        )
        assert old_login.status_code == 401

        # Verify new password works
        new_login = await async_client.post(
            "/v1/auth/login",
            json={"email": "resetflow@example.com", "password": "NewPass456"}
        )
        assert new_login.status_code == 200

    async def test_reset_password_invalid_token(self, async_client: AsyncClient, db_session):
        """Test reset password with invalid token returns 400."""
        response = await async_client.post(
            "/v1/auth/reset-password",
            json={
                "token": "00000000-0000-0000-0000-000000000000",
                "new_password": "NewPass456"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "TOKEN_INVALID"

    async def test_reset_password_weak_password(self, async_client: AsyncClient, db_session):
        """Test reset password with weak password fails validation."""
        response = await async_client.post(
            "/v1/auth/reset-password",
            json={
                "token": "550e8400-e29b-41d4-a716-446655440000",
                "new_password": "weak"
            }
        )

        # Should fail Pydantic validation
        assert response.status_code == 422

    async def test_reset_password_token_used_twice(self, async_client: AsyncClient, db_session):
        """Test using same reset token twice fails."""
        # Register user
        register_response = await async_client.post(
            "/v1/auth/register",
            json={"email": "doubleuse@example.com", "password": "OldPass123"}
        )
        user_id = register_response.json()["user"]["id"]

        # Request password reset
        await async_client.post(
            "/v1/auth/forgot-password",
            json={"email": "doubleuse@example.com"}
        )

        # Get token
        result = await db_session.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == UUID(user_id))
        )
        reset_token = result.scalar_one()

        # Use token first time
        first_response = await async_client.post(
            "/v1/auth/reset-password",
            json={
                "token": str(reset_token.token),
                "new_password": "NewPass456"
            }
        )
        assert first_response.status_code == 200

        # Try to use token second time
        second_response = await async_client.post(
            "/v1/auth/reset-password",
            json={
                "token": str(reset_token.token),
                "new_password": "AnotherPass789"
            }
        )

        assert second_response.status_code == 400
        data = second_response.json()
        assert data["error"]["code"] == "TOKEN_ALREADY_USED"

    async def test_reset_password_expired_token(self, async_client: AsyncClient, db_session):
        """Test reset password with expired token returns 400 with TOKEN_EXPIRED error."""
        # Register user
        register_response = await async_client.post(
            "/v1/auth/register",
            json={"email": "expiredtoken@example.com", "password": "OldPass123"}
        )
        user_id = register_response.json()["user"]["id"]

        # Create expired token manually (expired 2 hours ago)
        import uuid
        expired_token = PasswordResetToken(
            id=uuid.uuid4(),
            user_id=UUID(user_id),
            token=uuid.uuid4(),
            created_at=datetime.now(UTC) - timedelta(hours=3),
            expires_at=datetime.now(UTC) - timedelta(hours=2),
            used_at=None
        )
        db_session.add(expired_token)
        await db_session.commit()
        await db_session.refresh(expired_token)

        # Try to reset password with expired token
        response = await async_client.post(
            "/v1/auth/reset-password",
            json={
                "token": str(expired_token.token),
                "new_password": "NewPass456"
            }
        )

        # Should return 400 with TOKEN_EXPIRED error code
        assert response.status_code == 400
        data = response.json()
        assert data["error"]["code"] == "TOKEN_EXPIRED"
        assert "expired" in data["error"]["message"].lower()

    async def test_forgot_password_rate_limiting(self, async_client: AsyncClient, db_session):
        """Test forgot password rate limiting (10 requests per hour per IP)."""
        # Make 10 requests (at the limit)
        for i in range(10):
            response = await async_client.post(
                "/v1/auth/forgot-password",
                json={"email": f"ratelimit{i}@example.com"}
            )
            # All should succeed
            assert response.status_code == 200

        # 11th request should be rate limited
        response = await async_client.post(
            "/v1/auth/forgot-password",
            json={"email": "ratelimit11@example.com"}
        )

        # Should return 429 Too Many Requests
        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
