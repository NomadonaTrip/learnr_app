"""
Unit tests for authentication dependencies.
Tests get_current_user with rate limiting and caching.
"""

import uuid
from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from src.dependencies import get_current_user
from src.models.user import User
from src.utils.auth import create_access_token


# Mock Request object for tests
class MockRequest:
    """Mock FastAPI Request object for testing."""
    def __init__(self, client_host="127.0.0.1"):
        self.client = MagicMock()
        self.client.host = client_host


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    """Test get_current_user with valid token and existing user."""
    # Create test user
    user_id = uuid.uuid4()
    test_user = User(
        id=user_id,
        email="test@example.com",
        hashed_password="hashed_password"
    )

    # Create valid token
    token = create_access_token(data={"sub": str(user_id)})
    authorization = f"Bearer {token}"

    # Mock database session and request
    mock_db = AsyncMock()
    mock_request = MockRequest()

    # Mock rate limiting and Redis
    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit, \
         patch('src.dependencies.get_redis', new_callable=AsyncMock) as mock_redis, \
         patch('src.dependencies.UserRepository') as mock_repo_class:

        # Configure mocks
        mock_rate_limit.return_value = (True, 0)  # Rate limit not exceeded
        mock_redis_instance = AsyncMock()
        mock_redis_instance.get = AsyncMock(return_value=None)  # Cache miss
        mock_redis_instance.setex = AsyncMock()
        mock_redis.return_value = mock_redis_instance

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_by_id = AsyncMock(return_value=test_user)
        mock_repo_class.return_value = mock_repo_instance

        user = await get_current_user(mock_request, authorization, mock_db)

        assert user.id == test_user.id
        assert user.email == test_user.email


@pytest.mark.asyncio
async def test_get_current_user_missing_header():
    """Test get_current_user without Authorization header raises 401."""
    mock_db = AsyncMock()
    mock_request = MockRequest()

    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 0)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, None, mock_db)

        assert exc_info.value.status_code == 401
        assert "Authentication required" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_invalid_header_format():
    """Test get_current_user with invalid header format raises 401."""
    mock_db = AsyncMock()
    mock_request = MockRequest()

    # Test various invalid formats
    invalid_headers = [
        "InvalidToken",  # Missing Bearer prefix
        "Bearer",  # Missing token
        "Bearer token1 token2 extra",  # Too many parts
    ]

    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 0)

        for invalid_header in invalid_headers:
            with pytest.raises(HTTPException) as exc_info:
                await get_current_user(mock_request, invalid_header, mock_db)

            assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """Test get_current_user with invalid token raises 401."""
    mock_db = AsyncMock()
    mock_request = MockRequest()
    authorization = "Bearer invalid.token.here"

    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 0)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization, mock_db)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_expired_token():
    """Test get_current_user with expired token raises 401."""
    from datetime import timedelta

    # Create expired token
    expired_token = create_access_token(
        data={"sub": str(uuid.uuid4())},
        expires_delta=timedelta(seconds=-1)  # Expired 1 second ago
    )
    authorization = f"Bearer {expired_token}"
    mock_db = AsyncMock()
    mock_request = MockRequest()

    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 0)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization, mock_db)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_user_not_found():
    """Test get_current_user with valid token but non-existent user raises 401 with generic message."""
    # Create valid token
    user_id = uuid.uuid4()
    token = create_access_token(data={"sub": str(user_id)})
    authorization = f"Bearer {token}"
    mock_db = AsyncMock()
    mock_request = MockRequest()

    # Mock rate limiting, Redis, and UserRepository
    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit, \
         patch('src.dependencies.get_redis', new_callable=AsyncMock) as mock_redis, \
         patch('src.dependencies.UserRepository') as mock_repo_class:

        mock_rate_limit.return_value = (True, 0)
        mock_redis_instance = AsyncMock()
        mock_redis_instance.get = AsyncMock(return_value=None)
        mock_redis.return_value = mock_redis_instance

        mock_repo_instance = MagicMock()
        mock_repo_instance.get_by_id = AsyncMock(return_value=None)  # User not found
        mock_repo_class.return_value = mock_repo_instance

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization, mock_db)

        assert exc_info.value.status_code == 401
        # SEC-002 fix: Generic error message to prevent user enumeration
        assert "Invalid or expired token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_token_missing_sub_claim():
    """Test get_current_user with token missing 'sub' claim raises 401."""
    from datetime import datetime, timedelta

    from jose import jwt

    from src.config import settings

    # Create token without 'sub' claim
    payload = {
        "exp": datetime.now(UTC) + timedelta(days=1),
        "iat": datetime.now(UTC)
        # Missing 'sub' claim
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    authorization = f"Bearer {token}"
    mock_db = AsyncMock()
    mock_request = MockRequest()

    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 0)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization, mock_db)

        assert exc_info.value.status_code == 401
        assert "Invalid or expired token" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_token_malformed_user_id():
    """Test get_current_user with malformed user_id in token raises 401."""
    from datetime import datetime, timedelta

    from jose import jwt

    from src.config import settings

    # Create token with invalid UUID format
    payload = {
        "sub": "not-a-valid-uuid",
        "exp": datetime.now(UTC) + timedelta(days=1),
        "iat": datetime.now(UTC)
    }
    token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    authorization = f"Bearer {token}"
    mock_db = AsyncMock()
    mock_request = MockRequest()

    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
        mock_rate_limit.return_value = (True, 0)

        with pytest.raises(HTTPException) as exc_info:
            await get_current_user(mock_request, authorization, mock_db)

        assert exc_info.value.status_code == 401
        assert "malformed user identifier" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_get_current_user_rate_limit_exceeded():
    """Test get_current_user with rate limit exceeded raises 429."""
    from src.exceptions import RateLimitError

    mock_db = AsyncMock()
    mock_request = MockRequest()
    token = create_access_token(data={"sub": str(uuid.uuid4())})
    authorization = f"Bearer {token}"

    with patch('src.dependencies.check_rate_limit', new_callable=AsyncMock) as mock_rate_limit:
        # Simulate rate limit exceeded
        mock_rate_limit.return_value = (False, 30)  # Not allowed, retry after 30 seconds

        with pytest.raises(RateLimitError) as exc_info:
            await get_current_user(mock_request, authorization, mock_db)

        assert exc_info.value.retry_after_seconds == 30
