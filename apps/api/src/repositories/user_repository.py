"""
User repository for database operations on User model.
Implements repository pattern for data access.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import ConflictError, DatabaseError
from src.models.user import User


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
                raise ConflictError(f"Email {email} already registered") from e
            raise DatabaseError("Failed to create user") from e

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

    async def get_by_id_for_update(self, user_id: UUID) -> User | None:
        """
        Get user by ID with row lock for concurrent access safety.

        Args:
            user_id: User UUID

        Returns:
            User model if found, None otherwise
        """
        result = await self.session.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        return result.scalar_one_or_none()

    async def increment_quiz_stats(
        self,
        user_id: UUID,
        questions_answered: int,
        duration_seconds: int,
    ) -> User:
        """
        Atomically increment user's quiz completion statistics.
        Story 4.7: Fixed-Length Session Auto-Completion

        Args:
            user_id: User UUID
            questions_answered: Number of questions answered in the session
            duration_seconds: Session duration in seconds

        Returns:
            Updated User model

        Raises:
            ValueError: If user not found
        """
        user = await self.get_by_id_for_update(user_id)
        if not user:
            raise ValueError(f"User {user_id} not found")

        user.quizzes_completed += 1
        user.total_questions_answered += questions_answered
        user.total_time_spent_seconds += duration_seconds

        await self.session.flush()
        await self.session.refresh(user)

        return user
