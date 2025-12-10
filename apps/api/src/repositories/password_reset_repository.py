"""
Password Reset Token repository for database operations on PasswordResetToken model.
Implements repository pattern for data access.
"""

from datetime import datetime, timedelta, timezone
from uuid import UUID
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    """Repository for PasswordResetToken database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_token(self, user_id: UUID, expires_in_hours: int = 1) -> PasswordResetToken:
        """
        Create new password reset token for user.

        Args:
            user_id: User UUID
            expires_in_hours: Token expiration time in hours (default: 1)

        Returns:
            Created PasswordResetToken model
        """
        token = PasswordResetToken(
            user_id=user_id,
            token=uuid.uuid4(),
            expires_at=datetime.now(timezone.utc) + timedelta(hours=expires_in_hours)
        )

        self.session.add(token)
        await self.session.commit()
        await self.session.refresh(token)

        return token

    async def get_valid_token(self, token: str) -> PasswordResetToken | None:
        """
        Get valid (not expired, not used) password reset token.

        Args:
            token: Token UUID string

        Returns:
            PasswordResetToken if valid, None otherwise
        """
        try:
            token_uuid = UUID(token)
        except (ValueError, AttributeError, TypeError):
            return None

        result = await self.session.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.token == token_uuid,
                    PasswordResetToken.used_at.is_(None),
                    PasswordResetToken.expires_at > datetime.now(timezone.utc)
                )
            )
        )

        return result.scalar_one_or_none()

    async def get_token(self, token: str) -> PasswordResetToken | None:
        """
        Get password reset token (regardless of expiration/used status).

        Args:
            token: Token UUID string

        Returns:
            PasswordResetToken if found, None otherwise
        """
        try:
            token_uuid = UUID(token)
        except (ValueError, AttributeError, TypeError):
            return None

        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token_uuid)
        )

        return result.scalar_one_or_none()

    async def mark_token_used(self, token: str) -> None:
        """
        Mark token as used.

        Args:
            token: Token UUID string
        """
        token_uuid = UUID(token)
        result = await self.session.execute(
            select(PasswordResetToken).where(PasswordResetToken.token == token_uuid)
        )
        token_obj = result.scalar_one_or_none()

        if token_obj:
            token_obj.used_at = datetime.now(timezone.utc)
            await self.session.commit()

    async def invalidate_user_tokens(self, user_id: UUID) -> None:
        """
        Mark all user's unused tokens as used (invalidate).

        Args:
            user_id: User UUID
        """
        result = await self.session.execute(
            select(PasswordResetToken).where(
                and_(
                    PasswordResetToken.user_id == user_id,
                    PasswordResetToken.used_at.is_(None)
                )
            )
        )
        tokens = result.scalars().all()

        for token in tokens:
            token.used_at = datetime.now(timezone.utc)

        await self.session.commit()
