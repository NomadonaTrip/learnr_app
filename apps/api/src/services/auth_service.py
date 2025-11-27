"""
Authentication service for user registration and login.
Handles business logic for authentication operations.
"""

import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select

from src.config import settings
from src.exceptions import (
    AuthenticationError,
    ConflictError,
    TokenAlreadyUsedError,
    TokenExpiredError,
    TokenInvalidError,
)
from src.models.password_reset_token import PasswordResetToken
from src.models.user import User
from src.repositories.password_reset_repository import PasswordResetRepository
from src.repositories.user_repository import UserRepository
from src.services.email_service import EmailService
from src.utils.auth import create_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repo: UserRepository, reset_token_repo: PasswordResetRepository = None):
        self.user_repo = user_repo
        self.reset_token_repo = reset_token_repo
        self.email_service = EmailService()

    async def register_user(self, email: str, password: str) -> tuple[User, str]:
        """
        Register new user account.

        Args:
            email: User email (validated by Pydantic)
            password: Plain text password (validated by Pydantic)

        Returns:
            Tuple of (User model, JWT token)

        Raises:
            ConflictError: If email already exists
        """
        # Check if user already exists
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise ConflictError(f"Email {email} already registered")

        # Hash password
        hashed_password = hash_password(password)

        # Create user
        user = await self.user_repo.create_user(email, hashed_password)

        # Generate JWT token
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
        )

        return user, access_token

    async def login_user(self, email: str, password: str) -> tuple[User, str]:
        """
        Authenticate user with email and password.

        Security: Uses timing-safe password comparison and generic error messages
        to prevent user enumeration attacks. Always performs password verification
        even if user not found to maintain constant timing.

        Args:
            email: User email (case-insensitive)
            password: Plain text password

        Returns:
            Tuple of (User model, JWT token)

        Raises:
            AuthenticationError: If authentication fails (generic message for security)
        """
        # Look up user (case-insensitive)
        user = await self.user_repo.get_by_email(email)

        # Timing-safe authentication check
        # Always verify password even if user not found to prevent timing attacks
        if user is None:
            # Perform dummy hash verification to maintain constant timing
            # Using a known bcrypt hash format to ensure timing is similar
            verify_password(
                "dummy_password_for_timing_safety",
                "$2b$12$dummyhashformaintainingtimingsafety.abcdefghijklmnopqrstuvwxyz"
            )
            raise AuthenticationError("Invalid email or password")

        # Verify password (bcrypt.verify is timing-safe)
        if not verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password")

        # Generate JWT token (same as registration)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
        )

        return user, access_token

    async def request_password_reset(self, email: str) -> None:
        """
        Request password reset. Always returns success to prevent email enumeration.

        Security: Email sent even if user doesn't exist (but no token created).

        Args:
            email: User email address
        """
        # Look up user
        user = await self.user_repo.get_by_email(email.lower())

        if user:
            # Create reset token
            reset_token = await self.reset_token_repo.create_token(user.id, expires_in_hours=1)

            # Send email
            email_sent = await self.email_service.send_password_reset_email(
                to_email=user.email,
                reset_token=str(reset_token.token)
            )

            if not email_sent:
                logger.error(f"Failed to send password reset email to {user.email}")
        else:
            # User doesn't exist - send email anyway to prevent enumeration
            # But don't create token
            await self.email_service.send_password_reset_email(
                to_email=email,
                reset_token="00000000-0000-0000-0000-000000000000"  # Dummy token, link won't work
            )
            logger.info(f"Password reset requested for non-existent email: {email}")

        # Always return success (no indication of whether user exists)

    async def reset_password(self, token: str, new_password: str) -> None:
        """
        Reset user password with valid token.

        Args:
            token: Password reset token UUID
            new_password: New password (validated by Pydantic)

        Raises:
            TokenInvalidError: If token doesn't exist
            TokenExpiredError: If token is expired
            TokenAlreadyUsedError: If token already used
        """
        # Validate token
        reset_token = await self.reset_token_repo.get_valid_token(token)

        if reset_token is None:
            # Check if token exists but is invalid
            existing_token = await self.reset_token_repo.get_token(token)

            if existing_token:
                if existing_token.used_at is not None:
                    raise TokenAlreadyUsedError("This password reset token has already been used.")
                elif existing_token.expires_at < datetime.now(timezone.utc):
                    raise TokenExpiredError("Password reset token has expired. Please request a new one.")

            # Token doesn't exist or is invalid
            raise TokenInvalidError("Invalid password reset token.")

        # Get user
        user = await self.user_repo.get_by_id(reset_token.user_id)
        if not user:
            raise TokenInvalidError("Invalid password reset token.")

        # Hash new password
        hashed_password = hash_password(new_password)

        # Update user password
        user.hashed_password = hashed_password
        await self.user_repo.session.commit()

        # Mark token as used
        await self.reset_token_repo.mark_token_used(token)

        # Invalidate all other tokens for this user
        await self.reset_token_repo.invalidate_user_tokens(user.id)

        logger.info(f"Password reset successful for user {user.id}")
