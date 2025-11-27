"""
FastAPI dependency injection
Centralized dependencies for routes
"""
import json
import logging
from uuid import UUID

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.db.redis_client import get_redis
from src.db.session import get_db
from src.exceptions import RateLimitError
from src.models.user import User
from src.repositories.user_repository import UserRepository
from src.utils.auth import decode_token
from src.utils.rate_limit import check_rate_limit

logger = logging.getLogger(__name__)

# Cache configuration
USER_CACHE_TTL = 300  # 5 minutes as recommended by QA
AUTH_RATE_LIMIT = 60  # 60 requests per minute per IP
AUTH_RATE_WINDOW = 60  # 60 seconds


async def get_current_user(
    request: Request,
    authorization: str | None = Header(None, alias="Authorization"),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get current authenticated user from JWT token.

    Extracts JWT from Authorization header, validates it, and returns User object.

    **Security Features:**
    - Rate limited to 60 requests per minute per IP address
    - Redis-based token caching (5-minute TTL) to reduce database load
    - Generic error messages to prevent user enumeration

    Args:
        request: FastAPI request object (for IP-based rate limiting)
        authorization: Authorization header value (Bearer {token})
        db: Database session

    Returns:
        User object

    Raises:
        HTTPException 401: If token missing, invalid, expired, or user not found
        HTTPException 429: If rate limit exceeded
    """
    # Rate limiting: 60 requests per minute per IP
    client_ip = request.client.host if request.client else "unknown"
    rate_limit_key = f"rate_limit:auth:{client_ip}"

    try:
        is_allowed, retry_after = await check_rate_limit(
            rate_limit_key,
            AUTH_RATE_LIMIT,
            AUTH_RATE_WINDOW
        )

        if not is_allowed:
            raise RateLimitError(
                message="Too many authentication requests. Please try again later.",
                retry_after_seconds=retry_after
            )
    except RateLimitError:
        # Re-raise rate limit errors
        raise
    except Exception as e:
        # Fail-safe: If Redis is unavailable, log and continue without rate limiting
        logger.warning(f"Rate limiting check failed (Redis unavailable?): {e}")

    # Check Authorization header exists
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract token from "Bearer {token}" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected: Bearer {token}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]

    # Decode and validate token
    payload = decode_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Extract user_id from token
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: missing user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token: malformed user identifier",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e

    # Check Redis cache first (PERF-001 fix)
    cache_key = f"user_cache:{str(user_id)}"
    redis = None

    try:
        redis = await get_redis()
        cached_user_data = await redis.get(cache_key)

        if cached_user_data:
            # Cache hit: deserialize and return user
            user_dict = json.loads(cached_user_data)
            user = User(**user_dict)
            logger.debug(f"Cache hit for user {user_id}")
            return user
    except Exception as e:
        # Fail-safe: If Redis is unavailable, continue to database lookup
        logger.warning(f"Redis cache check failed: {e}")

    # Cache miss: Look up user in database
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    # SEC-002 fix: Use generic error message to prevent user enumeration
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Cache the user data in Redis (5-minute TTL)
    if redis:
        try:
            # Serialize user to JSON for caching
            user_dict = {
                "id": str(user.id),
                "email": user.email,
                "created_at": user.created_at.isoformat() if user.created_at else None,
                "exam_date": user.exam_date.isoformat() if user.exam_date else None,
                "target_score": user.target_score,
                "daily_study_time": user.daily_study_time,
                "knowledge_level": user.knowledge_level,
                "motivation": user.motivation,
                "referral_source": user.referral_source,
                "is_admin": user.is_admin,
                "dark_mode": user.dark_mode
            }
            await redis.setex(cache_key, USER_CACHE_TTL, json.dumps(user_dict))
            logger.debug(f"Cached user {user_id} for {USER_CACHE_TTL} seconds")
        except Exception as e:
            # Fail-safe: Continue even if caching fails
            logger.warning(f"Failed to cache user data: {e}")

    return user
