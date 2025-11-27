"""
Redis client configuration and connection management
Provides async Redis connection for caching and rate limiting
"""

import asyncio
from redis.asyncio import Redis
from src.config import settings

# Global Redis client instance
redis_client: Redis | None = None
_redis_lock = asyncio.Lock()


async def get_redis() -> Redis:
    """
    Get Redis client instance (singleton pattern with thread-safety).

    Thread-safe singleton implementation using async lock to prevent
    race conditions when multiple concurrent requests initialize the client.

    Returns:
        Redis: Async Redis client instance
    """
    global redis_client

    # Fast path: return existing client without acquiring lock
    if redis_client is not None:
        return redis_client

    # Slow path: acquire lock and initialize
    async with _redis_lock:
        # Double-check after acquiring lock (another coroutine may have initialized)
        if redis_client is None:
            redis_client = Redis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5,
            )

    return redis_client


async def close_redis() -> None:
    """
    Close Redis connection and cleanup.
    Should be called during application shutdown.
    """
    global redis_client
    if redis_client:
        await redis_client.close()
        redis_client = None


async def test_redis_connection() -> bool:
    """
    Test Redis connection by executing a PING command.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        redis = await get_redis()
        result = await redis.ping()
        return result
    except Exception as e:
        print(f"Redis connection test failed: {e}")
        return False
