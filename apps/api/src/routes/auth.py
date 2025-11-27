"""
Authentication routes for user registration and login.
"""

import logging
from fastapi import APIRouter, Depends, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserCreate
from src.schemas.auth import (
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    ForgotPasswordRequest,
    ForgotPasswordResponse,
    ResetPasswordRequest,
    ResetPasswordResponse,
)
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.repositories.password_reset_repository import PasswordResetRepository
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


@router.post(
    "/forgot-password",
    response_model=ForgotPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Request password reset",
    description="Request password reset email. Returns success regardless of email existence to prevent enumeration. Rate limited to 10 requests per hour per IP."
)
async def forgot_password(
    request: Request,
    forgot_data: ForgotPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> ForgotPasswordResponse:
    """
    Request password reset email.

    - **email**: Email address to send reset link

    **Security:** Returns same success message whether email exists or not
    to prevent user enumeration.

    **Rate Limiting:** 10 requests per hour per IP address.
    """
    # Rate limit by IP address (10 requests per hour)
    client_ip = request.client.host
    rate_limit_key = f"rate_limit:forgot_password:{client_ip}"

    try:
        is_allowed, retry_after = await check_rate_limit(
            rate_limit_key,
            max_attempts=10,
            window_seconds=3600  # 1 hour
        )

        if not is_allowed:
            raise RateLimitError(
                "Too many password reset requests. Please try again later.",
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
                "ip": client_ip,
                "endpoint": "forgot_password",
                "security_event": "rate_limit_failure"
            }
        )

    # Initialize repositories and service
    user_repo = UserRepository(db)
    reset_token_repo = PasswordResetRepository(db)
    auth_service = AuthService(user_repo, reset_token_repo)

    # Request password reset (always returns success)
    await auth_service.request_password_reset(forgot_data.email)

    return ForgotPasswordResponse(
        message="If your email is registered, you will receive a password reset link shortly."
    )


@router.post(
    "/reset-password",
    response_model=ResetPasswordResponse,
    status_code=status.HTTP_200_OK,
    summary="Reset password with token",
    description="Reset password using valid reset token received via email."
)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: AsyncSession = Depends(get_db)
) -> ResetPasswordResponse:
    """
    Reset password with token from email.

    - **token**: Reset token from email link (UUID)
    - **new_password**: New password (min 8 chars, letter + number)

    Returns success message. User must log in with new password (no JWT returned).

    Raises:
    - **400 Bad Request**: Token expired, invalid, or already used
    - **422 Unprocessable Entity**: Weak password
    """
    # Initialize repositories and service
    user_repo = UserRepository(db)
    reset_token_repo = PasswordResetRepository(db)
    auth_service = AuthService(user_repo, reset_token_repo)

    # Reset password
    await auth_service.reset_password(reset_data.token, reset_data.new_password)

    return ResetPasswordResponse(
        message="Password reset successful. Please log in with your new password."
    )
