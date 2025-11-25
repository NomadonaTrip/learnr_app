"""
Rate limiting utility using Redis
Implements sliding window rate limiting for API endpoints
"""

from src.db.redis_client import get_redis


async def check_rate_limit(
    key: str,
    max_attempts: int,
    window_seconds: int
) -> tuple[bool, int]:
    """
    Check if rate limit is exceeded using Redis.

    Args:
        key: Redis key for rate limiting (e.g., "rate_limit:login:user@example.com")
        max_attempts: Maximum attempts allowed within the window
        window_seconds: Time window in seconds

    Returns:
        Tuple of (is_allowed: bool, retry_after_seconds: int)
        - is_allowed: True if request is allowed, False if rate limit exceeded
        - retry_after_seconds: Seconds until rate limit resets (0 if allowed)
    """
    redis = await get_redis()

    # Increment counter
    current = await redis.incr(key)

    # Set expiration on first request
    if current == 1:
        await redis.expire(key, window_seconds)

    # Check if over limit
    if current > max_attempts:
        # Get TTL for retry_after
        ttl = await redis.ttl(key)
        return False, ttl if ttl > 0 else window_seconds

    return True, 0


async def reset_rate_limit(key: str) -> None:
    """
    Reset rate limit counter (e.g., after successful login).

    Args:
        key: Redis key for rate limiting
    """
    redis = await get_redis()
    await redis.delete(key)


async def get_remaining_attempts(key: str, max_attempts: int) -> int:
    """
    Get remaining attempts before rate limit is hit.

    Args:
        key: Redis key for rate limiting
        max_attempts: Maximum attempts allowed

    Returns:
        int: Number of remaining attempts (0 if rate limit exceeded)
    """
    redis = await get_redis()
    current = await redis.get(key)

    if current is None:
        return max_attempts

    return max(0, max_attempts - int(current))
