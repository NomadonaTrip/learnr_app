"""
Unit tests for rate limiting utility.
Tests Redis-based rate limiting functionality.
"""

import pytest
from src.utils.rate_limit import check_rate_limit, reset_rate_limit, get_remaining_attempts
from src.db.redis_client import get_redis


@pytest.mark.asyncio
async def test_rate_limit_allows_under_threshold():
    """Test rate limit allows requests under threshold."""
    key = "test:rate_limit:user1"

    # First 5 attempts should be allowed
    for i in range(5):
        is_allowed, _ = await check_rate_limit(key, max_attempts=5, window_seconds=60)
        assert is_allowed is True

    # Cleanup
    redis = await get_redis()
    await redis.delete(key)


@pytest.mark.asyncio
async def test_rate_limit_blocks_over_threshold():
    """Test rate limit blocks requests over threshold."""
    key = "test:rate_limit:user2"

    # First 5 attempts allowed
    for i in range(5):
        await check_rate_limit(key, max_attempts=5, window_seconds=60)

    # 6th attempt should be blocked
    is_allowed, retry_after = await check_rate_limit(key, max_attempts=5, window_seconds=60)
    assert is_allowed is False
    assert retry_after > 0

    # Cleanup
    redis = await get_redis()
    await redis.delete(key)


@pytest.mark.asyncio
async def test_rate_limit_reset():
    """Test rate limit can be reset."""
    key = "test:rate_limit:user3"

    # Make some requests
    await check_rate_limit(key, max_attempts=5, window_seconds=60)
    await check_rate_limit(key, max_attempts=5, window_seconds=60)

    # Reset
    await reset_rate_limit(key)

    # Should be able to make requests again
    remaining = await get_remaining_attempts(key, max_attempts=5)
    assert remaining == 5


@pytest.mark.asyncio
async def test_rate_limit_get_remaining_attempts():
    """Test getting remaining attempts before rate limit."""
    key = "test:rate_limit:user4"

    # Initially should have all attempts available
    remaining = await get_remaining_attempts(key, max_attempts=5)
    assert remaining == 5

    # After 2 requests, should have 3 remaining
    await check_rate_limit(key, max_attempts=5, window_seconds=60)
    await check_rate_limit(key, max_attempts=5, window_seconds=60)
    remaining = await get_remaining_attempts(key, max_attempts=5)
    assert remaining == 3

    # Cleanup
    redis = await get_redis()
    await redis.delete(key)


@pytest.mark.asyncio
async def test_rate_limit_returns_correct_retry_after():
    """Test that retry_after is correctly returned when rate limit exceeded."""
    key = "test:rate_limit:user5"

    # Use first 5 attempts
    for i in range(5):
        await check_rate_limit(key, max_attempts=5, window_seconds=60)

    # 6th attempt should be blocked with retry_after
    is_allowed, retry_after = await check_rate_limit(key, max_attempts=5, window_seconds=60)
    assert is_allowed is False
    assert 0 < retry_after <= 60  # Should be within window

    # Cleanup
    redis = await get_redis()
    await redis.delete(key)


@pytest.mark.asyncio
async def test_rate_limit_different_keys_independent():
    """Test that rate limits for different keys are independent."""
    key1 = "test:rate_limit:user_a"
    key2 = "test:rate_limit:user_b"

    # Use all attempts for key1
    for i in range(5):
        await check_rate_limit(key1, max_attempts=5, window_seconds=60)

    # key1 should be blocked
    is_allowed_1, _ = await check_rate_limit(key1, max_attempts=5, window_seconds=60)
    assert is_allowed_1 is False

    # key2 should still be allowed
    is_allowed_2, _ = await check_rate_limit(key2, max_attempts=5, window_seconds=60)
    assert is_allowed_2 is True

    # Cleanup
    redis = await get_redis()
    await redis.delete(key1)
    await redis.delete(key2)
