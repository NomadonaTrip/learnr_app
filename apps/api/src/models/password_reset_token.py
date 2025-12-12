"""
Password Reset Token SQLAlchemy model.
Represents password reset tokens for secure password recovery flow.
"""
import uuid
from datetime import UTC, datetime

from sqlalchemy import Column, DateTime, ForeignKey, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from ..db.session import Base


class PasswordResetToken(Base):
    """
    Password reset token model for password recovery flow.

    Tokens are single-use and expire after 1 hour for security.
    Multiple tokens can exist per user (if requested multiple times).
    """
    __tablename__ = "password_reset_tokens"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to users table
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
        index=True
    )

    # Reset token (UUID, unique)
    token = Column(
        UUID(as_uuid=True),
        unique=True,
        nullable=False,
        default=uuid.uuid4,
        index=True
    )

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=False,
        index=True
    )

    used_at = Column(
        DateTime(timezone=True),
        nullable=True
    )

    # Table indexes
    __table_args__ = (
        Index('idx_password_reset_tokens_user_id', 'user_id'),
        Index('idx_password_reset_tokens_token', 'token'),
        Index('idx_password_reset_tokens_expires_at', 'expires_at'),
    )

    def is_valid(self) -> bool:
        """
        Check if token is valid (not expired, not used).

        Returns:
            True if token can be used for password reset, False otherwise
        """
        return (
            self.used_at is None and
            self.expires_at > datetime.now(UTC)
        )

    def __repr__(self) -> str:
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id}, used={self.used_at is not None})>"
