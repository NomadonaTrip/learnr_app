"""
Authentication service for user registration and login.
Handles business logic for authentication operations.
"""

from datetime import timedelta
from uuid import UUID
from src.repositories.user_repository import UserRepository
from src.utils.auth import hash_password, verify_password, create_access_token
from src.models.user import User
from src.exceptions import ConflictError, AuthenticationError
from src.config import settings


class AuthService:
    """Service for authentication operations."""

    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

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
