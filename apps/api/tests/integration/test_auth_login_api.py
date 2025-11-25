"""
Integration tests for user login API endpoint.
Tests complete login flow with database, rate limiting, and security features.
"""

import pytest
from httpx import AsyncClient
from jose import jwt
from src.config import settings
from src.db.redis_client import get_redis


@pytest.mark.asyncio
class TestLoginIntegration:
    """Integration tests for POST /v1/auth/login endpoint."""

    async def test_login_success_returns_user_and_token(self, async_client: AsyncClient, db_session):
        """Test successful login returns user object and JWT token."""
        # Register user first
        register_response = await async_client.post(
            "/v1/auth/register",
            json={"email": "logintest@example.com", "password": "SecurePass123"}
        )
        assert register_response.status_code == 201

        # Login
        login_response = await async_client.post(
            "/v1/auth/login",
            json={"email": "logintest@example.com", "password": "SecurePass123"}
        )

        assert login_response.status_code == 200
        data = login_response.json()

        # Verify response structure
        assert "user" in data
        assert "token" in data
        assert data["user"]["email"] == "logintest@example.com"
        assert "id" in data["user"]
        assert "hashed_password" not in data["user"]  # Password not exposed

        # Verify JWT token
        token = data["token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        assert payload["sub"] == data["user"]["id"]

    async def test_login_wrong_password_returns_401(self, async_client: AsyncClient, db_session):
        """Test login with wrong password returns 401 with generic message."""
        # Register user
        await async_client.post(
            "/v1/auth/register",
            json={"email": "wrongpass@example.com", "password": "CorrectPass123"}
        )

        # Try login with wrong password
        response = await async_client.post(
            "/v1/auth/login",
            json={"email": "wrongpass@example.com", "password": "WrongPass456"}
        )

        assert response.status_code == 401
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "AUTHENTICATION_ERROR"
        assert data["error"]["message"] == "Invalid email or password"

    async def test_login_nonexistent_email_returns_401(self, async_client: AsyncClient):
        """Test login with non-existent email returns 401 with generic message."""
        response = await async_client.post(
            "/v1/auth/login",
            json={"email": "notregistered@example.com", "password": "AnyPass123"}
        )

        assert response.status_code == 401
        data = response.json()
        assert data["error"]["message"] == "Invalid email or password"

    async def test_login_case_insensitive_email(self, async_client: AsyncClient, db_session):
        """Test login works with different email case."""
        # Register with lowercase
        await async_client.post(
            "/v1/auth/register",
            json={"email": "casetest@example.com", "password": "SecurePass123"}
        )

        # Login with uppercase
        response = await async_client.post(
            "/v1/auth/login",
            json={"email": "CaseTest@Example.COM", "password": "SecurePass123"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "casetest@example.com"

    async def test_login_error_messages_identical(self, async_client: AsyncClient, db_session):
        """Test error messages are identical for wrong password vs non-existent email."""
        # Register user
        await async_client.post(
            "/v1/auth/register",
            json={"email": "msgtest@example.com", "password": "CorrectPass123"}
        )

        # Wrong password
        response1 = await async_client.post(
            "/v1/auth/login",
            json={"email": "msgtest@example.com", "password": "WrongPass"}
        )

        # Non-existent email
        response2 = await async_client.post(
            "/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPass"}
        )

        # Messages should be identical to prevent user enumeration
        assert response1.json()["error"]["message"] == response2.json()["error"]["message"]
        assert response1.json()["error"]["message"] == "Invalid email or password"

    async def test_login_jwt_token_structure(self, async_client: AsyncClient, db_session):
        """Test JWT token has correct structure and claims."""
        # Register and login
        register_response = await async_client.post(
            "/v1/auth/register",
            json={"email": "jwttest@example.com", "password": "SecurePass123"}
        )
        user_id = register_response.json()["user"]["id"]

        login_response = await async_client.post(
            "/v1/auth/login",
            json={"email": "jwttest@example.com", "password": "SecurePass123"}
        )

        token = login_response.json()["token"]
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

        # Verify token claims
        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

        # Verify 7-day expiration
        exp_delta = payload["exp"] - payload["iat"]
        assert abs(exp_delta - settings.JWT_EXPIRATION_SECONDS) < 5

    async def test_login_timing_attack_prevention(self, async_client: AsyncClient, db_session):
        """Test response times are similar for wrong email vs wrong password."""
        import time

        # Register user
        await async_client.post(
            "/v1/auth/register",
            json={"email": "timing@example.com", "password": "CorrectPass123"}
        )

        # Measure wrong password timing
        start = time.time()
        await async_client.post(
            "/v1/auth/login",
            json={"email": "timing@example.com", "password": "WrongPass"}
        )
        wrong_password_time = time.time() - start

        # Measure non-existent email timing
        start = time.time()
        await async_client.post(
            "/v1/auth/login",
            json={"email": "nonexistent@example.com", "password": "AnyPass"}
        )
        nonexistent_email_time = time.time() - start

        # Times should be within 100ms of each other (bcrypt is slow, so tolerance)
        time_difference = abs(wrong_password_time - nonexistent_email_time)
        assert time_difference < 0.1  # 100ms tolerance


@pytest.mark.asyncio
class TestLoginRateLimiting:
    """Integration tests for login rate limiting."""

    async def test_login_rate_limiting_blocks_after_5_attempts(self, async_client: AsyncClient, db_session):
        """Test rate limiting blocks after 5 failed login attempts."""
        email = "ratelimit@example.com"

        # Register user
        await async_client.post(
            "/v1/auth/register",
            json={"email": email, "password": "CorrectPass123"}
        )

        # Make 5 failed login attempts
        for i in range(5):
            response = await async_client.post(
                "/v1/auth/login",
                json={"email": email, "password": f"WrongPass{i}"}
            )
            assert response.status_code == 401

        # 6th attempt should be rate limited
        response = await async_client.post(
            "/v1/auth/login",
            json={"email": email, "password": "WrongPass5"}
        )

        assert response.status_code == 429
        data = response.json()
        assert data["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after_seconds" in data["error"]["details"]
        assert "Retry-After" in response.headers

        # Cleanup rate limit
        redis = await get_redis()
        await redis.delete(f"rate_limit:login:{email.lower()}")

    async def test_login_rate_limit_resets_after_successful_login(self, async_client: AsyncClient, db_session):
        """Test rate limit counter resets after successful login."""
        email = "resettest@example.com"

        # Register user
        await async_client.post(
            "/v1/auth/register",
            json={"email": email, "password": "CorrectPass123"}
        )

        # Make 3 failed attempts
        for i in range(3):
            await async_client.post(
                "/v1/auth/login",
                json={"email": email, "password": f"WrongPass{i}"}
            )

        # Successful login should reset counter
        response = await async_client.post(
            "/v1/auth/login",
            json={"email": email, "password": "CorrectPass123"}
        )
        assert response.status_code == 200

        # Should be able to make 5 more attempts
        for i in range(5):
            response = await async_client.post(
                "/v1/auth/login",
                json={"email": email, "password": f"WrongPass{i}"}
            )
            # First 5 should be 401, not 429
            assert response.status_code == 401

        # Cleanup
        redis = await get_redis()
        await redis.delete(f"rate_limit:login:{email.lower()}")

    async def test_login_rate_limit_per_email_independent(self, async_client: AsyncClient, db_session):
        """Test rate limits are independent per email address."""
        email1 = "user1@example.com"
        email2 = "user2@example.com"

        # Register both users
        await async_client.post("/v1/auth/register", json={"email": email1, "password": "Pass123"})
        await async_client.post("/v1/auth/register", json={"email": email2, "password": "Pass123"})

        # Use all attempts for email1
        for i in range(5):
            await async_client.post("/v1/auth/login", json={"email": email1, "password": f"Wrong{i}"})

        # email1 should be blocked
        response1 = await async_client.post("/v1/auth/login", json={"email": email1, "password": "Wrong"})
        assert response1.status_code == 429

        # email2 should still be allowed
        response2 = await async_client.post("/v1/auth/login", json={"email": email2, "password": "Pass123"})
        assert response2.status_code == 200

        # Cleanup
        redis = await get_redis()
        await redis.delete(f"rate_limit:login:{email1.lower()}")
        await redis.delete(f"rate_limit:login:{email2.lower()}")

    async def test_login_rate_limit_returns_retry_after_header(self, async_client: AsyncClient, db_session):
        """Test rate limit response includes Retry-After header."""
        email = "retryheader@example.com"

        # Register user
        await async_client.post(
            "/v1/auth/register",
            json={"email": email, "password": "CorrectPass123"}
        )

        # Use all 5 attempts
        for i in range(5):
            await async_client.post(
                "/v1/auth/login",
                json={"email": email, "password": f"WrongPass{i}"}
            )

        # 6th attempt should include Retry-After header
        response = await async_client.post(
            "/v1/auth/login",
            json={"email": email, "password": "WrongPass5"}
        )

        assert response.status_code == 429
        assert "Retry-After" in response.headers
        retry_after = int(response.headers["Retry-After"])
        assert 0 < retry_after <= 900  # Should be within 15-minute window

        # Cleanup
        redis = await get_redis()
        await redis.delete(f"rate_limit:login:{email.lower()}")

    async def test_login_rate_limit_successful_attempts_count(self, async_client: AsyncClient, db_session):
        """Test that failed attempts count toward rate limit, but successful ones reset."""
        email = "counttest@example.com"

        # Register user
        await async_client.post(
            "/v1/auth/register",
            json={"email": email, "password": "CorrectPass123"}
        )

        # Make 4 failed attempts
        for i in range(4):
            response = await async_client.post(
                "/v1/auth/login",
                json={"email": email, "password": f"WrongPass{i}"}
            )
            assert response.status_code == 401

        # 5th attempt with correct password should succeed
        response = await async_client.post(
            "/v1/auth/login",
            json={"email": email, "password": "CorrectPass123"}
        )
        assert response.status_code == 200

        # Counter should be reset, so 5 more failed attempts should be allowed
        for i in range(5):
            response = await async_client.post(
                "/v1/auth/login",
                json={"email": email, "password": f"WrongPass{i}"}
            )
            assert response.status_code == 401

        # Cleanup
        redis = await get_redis()
        await redis.delete(f"rate_limit:login:{email.lower()}")
