"""
Authentication routes for user registration and login.
"""

import logging
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserCreate
from src.schemas.auth import RegisterResponse, LoginRequest, LoginResponse
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.db.session import get_db
from src.config import settings
from src.utils.rate_limiter import limiter
from src.utils.rate_limit import check_rate_limit, reset_rate_limit
from src.exceptions import RateLimitError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user account",
    description="Create a new user account with email and password. Returns user object and JWT token. Rate limited to 5 requests per minute per IP address."
)
@limiter.limit(settings.REGISTRATION_RATE_LIMIT)
async def register(
    request: Request,
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
) -> RegisterResponse:
    """
    Register new user account.

    - **email**: Valid email address (unique)
    - **password**: Minimum 8 characters, must contain letter and number

    Returns user object (without password) and JWT token with 7-day expiration.

    Raises:
    - **409 Conflict**: Email already registered
    - **422 Unprocessable Entity**: Invalid email format or weak password
    """
    # Initialize repository and service
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    # Register user
    user, token = await auth_service.register_user(user_data.email, user_data.password)

    # Return response
    return RegisterResponse(
        user=user,
        token=token
    )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    description="Authenticate with email and password. Rate limited to 5 attempts per 15 minutes per email address."
)
async def login(
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db)
) -> LoginResponse:
    """
    Authenticate user and return JWT token.

    - **email**: Registered email address (case-insensitive)
    - **password**: User password

    **Rate Limiting:** 5 attempts per 15 minutes per email address.
    After 5 failed attempts, returns 429 with retry_after_seconds.

    **Security:** Returns generic "Invalid email or password" message
    to prevent user enumeration attacks.

    Raises:
    - **401 Unauthorized**: Invalid email or password
    - **429 Too Many Requests**: Rate limit exceeded (5 attempts per 15 minutes)
    """
    # Check rate limit (5 attempts per 15 minutes per email)
    # Fail-safe: Allow requests if Redis is unavailable (with logging)
    rate_limit_key = f"rate_limit:login:{login_data.email.lower()}"

    try:
        is_allowed, retry_after = await check_rate_limit(
            rate_limit_key,
            max_attempts=5,
            window_seconds=900  # 15 minutes
        )

        if not is_allowed:
            raise RateLimitError(
                "Too many login attempts. Please try again later.",
                retry_after_seconds=retry_after
            )
    except RateLimitError:
        # Re-raise rate limit errors (these are expected)
        raise
    except Exception as e:
        # Redis connection failure or other unexpected errors
        # Fail-safe: Allow request but log for monitoring
        logger.error(
            "Rate limiting check failed - allowing request (fail-safe mode)",
            extra={
                "error": str(e),
                "email": login_data.email.lower(),
                "endpoint": "login",
                "security_event": "rate_limit_failure"
            }
        )
        # TODO: Consider implementing circuit breaker pattern or in-memory fallback

    # Initialize repository and service
    user_repo = UserRepository(db)
    auth_service = AuthService(user_repo)

    # Authenticate user
    user, token = await auth_service.login_user(login_data.email, login_data.password)

    # Reset rate limit on successful login (with error handling)
    try:
        await reset_rate_limit(rate_limit_key)
    except Exception as e:
        # Log but don't fail the request if reset fails
        logger.warning(
            "Failed to reset rate limit after successful login",
            extra={
                "error": str(e),
                "email": login_data.email.lower(),
                "endpoint": "login"
            }
        )

    # Return response
    return LoginResponse(
        user=user,
        token=token
    )
