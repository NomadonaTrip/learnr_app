"""
User repository for database operations on User model.
Implements repository pattern for data access.
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from uuid import UUID
from src.models.user import User
from src.exceptions import ConflictError, DatabaseError


class UserRepository:
    """Repository for User database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_user(self, email: str, hashed_password: str) -> User:
        """
        Create new user in database.

        Args:
            email: User email (unique)
            hashed_password: bcrypt-hashed password

        Returns:
            Created User model

        Raises:
            ConflictError: If email already exists
            DatabaseError: If database operation fails
        """
        user = User(
            email=email.lower(),  # Normalize email to lowercase
            hashed_password=hashed_password
        )

        try:
            self.session.add(user)
            await self.session.commit()
            await self.session.refresh(user)
            return user
        except IntegrityError as e:
            await self.session.rollback()
            if "unique constraint" in str(e).lower():
                raise ConflictError(f"Email {email} already registered")
            raise DatabaseError("Failed to create user")

    async def get_by_email(self, email: str) -> User | None:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.email == email.lower())
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: UUID) -> User | None:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
