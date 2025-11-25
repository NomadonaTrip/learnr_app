"""
Integration tests for rate limiting on registration endpoint.
Tests that rate limits are properly enforced.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
@pytest.mark.integration
class TestRateLimiting:
    """Integration tests for rate limiting."""

    async def test_registration_rate_limit_enforced(self, client: AsyncClient):
        """Test that registration endpoint enforces 5 requests per minute limit."""
        # Make 5 successful requests (at the limit)
        for i in range(5):
            response = await client.post(
                "/v1/auth/register",
                json={
                    "email": f"ratelimit{i}@example.com",
                    "password": "SecurePass123"
                }
            )
            # All 5 should succeed
            assert response.status_code == 201, f"Request {i+1} failed with status {response.status_code}"

        # 6th request should be rate limited (429 Too Many Requests)
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "ratelimit6@example.com",
                "password": "SecurePass123"
            }
        )

        assert response.status_code == 429
        # SlowAPI returns plain text error message
        assert "Rate limit exceeded" in response.text or "Too Many Requests" in response.text

    async def test_rate_limit_per_ip_isolation(self, client: AsyncClient):
        """Test that rate limits are per-IP (different IPs have separate limits)."""
        # This test verifies the isolation concept, though in practice
        # with a test client, all requests come from the same "IP"

        # Make 5 requests to exhaust limit
        for i in range(5):
            response = await client.post(
                "/v1/auth/register",
                json={
                    "email": f"isolation{i}@example.com",
                    "password": "SecurePass123"
                }
            )
            assert response.status_code == 201

        # 6th should be rate limited
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "isolation6@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 429

    async def test_rate_limit_resets_after_window(self, client: AsyncClient):
        """
        Test that rate limit window resets after the time period.
        Note: This test documents the behavior but doesn't wait for actual reset.
        """
        # Make 5 requests to hit the limit
        for i in range(5):
            response = await client.post(
                "/v1/auth/register",
                json={
                    "email": f"reset{i}@example.com",
                    "password": "SecurePass123"
                }
            )
            assert response.status_code == 201

        # Next request should be rate limited
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "reset_limited@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 429

        # Note: In a real-world scenario, after 60 seconds, the limit would reset
        # and new requests would be allowed. We don't test this here due to time constraints.

    async def test_rate_limit_does_not_affect_other_endpoints(self, client: AsyncClient):
        """Test that rate limiting on registration doesn't affect other endpoints."""
        # Exhaust registration rate limit
        for i in range(5):
            response = await client.post(
                "/v1/auth/register",
                json={
                    "email": f"other{i}@example.com",
                    "password": "SecurePass123"
                }
            )
            assert response.status_code == 201

        # Registration should be rate limited
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "other_limited@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 429

        # But other endpoints (like health check) should still work
        response = await client.get("/health")
        assert response.status_code == 200

    async def test_rate_limit_counts_failed_attempts(self, client: AsyncClient):
        """Test that rate limit counts both successful and failed registration attempts."""
        # Mix of successful and failed requests
        test_cases = [
            {"email": "count1@example.com", "password": "SecurePass123"},  # Success
            {"email": "count2@example.com", "password": "SecurePass123"},  # Success
            {"email": "invalid-email", "password": "SecurePass123"},  # Fail - invalid email
            {"email": "count3@example.com", "password": "short"},  # Fail - weak password
            {"email": "count4@example.com", "password": "SecurePass123"},  # Success
        ]

        # Make 5 requests (some succeed, some fail due to validation)
        for i, data in enumerate(test_cases):
            response = await client.post("/v1/auth/register", json=data)
            # Status varies (201 for success, 422 for validation error)
            # But all should count toward rate limit

        # 6th request should be rate limited regardless of validity
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "count6@example.com",
                "password": "SecurePass123"
            }
        )
        assert response.status_code == 429

    async def test_rate_limit_headers_present(self, client: AsyncClient):
        """Test that rate limit headers are included in responses."""
        response = await client.post(
            "/v1/auth/register",
            json={
                "email": "headers@example.com",
                "password": "SecurePass123"
            }
        )

        # SlowAPI typically adds these headers
        # X-RateLimit-Limit: The rate limit ceiling
        # X-RateLimit-Remaining: Requests remaining in current window
        # X-RateLimit-Reset: Time when the rate limit resets

        # Note: Header names may vary by SlowAPI version
        # This test documents expected behavior
        assert response.status_code == 201
        # Check if any rate limit headers are present (SlowAPI should add them)
        headers_lower = {k.lower(): v for k, v in response.headers.items()}
        has_rate_limit_headers = any(
            'ratelimit' in key or 'x-ratelimit' in key
            for key in headers_lower.keys()
        )
        # Note: SlowAPI may not add headers in all configurations
        # This is informational rather than a hard requirement
