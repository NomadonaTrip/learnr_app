"""
User SQLAlchemy model.
Represents the users table with embedded onboarding data fields.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Column, Date, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .enrollment import Enrollment


class User(Base):
    """
    User model with embedded onboarding data.

    Following architecture decision to use single table instead of separate
    onboarding_data table for 1:1 relationship simplicity.
    """
    __tablename__ = "users"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Onboarding data (embedded, all nullable initially)
    exam_date = Column(Date, nullable=True)
    target_score = Column(Integer, nullable=True)
    daily_study_time = Column(Integer, nullable=True)  # in minutes
    knowledge_level = Column(String(50), nullable=True)
    motivation = Column(Text, nullable=True)
    referral_source = Column(String(50), nullable=True)

    # System fields
    is_admin = Column(Boolean, nullable=False, default=False)
    dark_mode = Column(String(10), nullable=False, default='auto')

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    enrollments: Mapped[list["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            'target_score IS NULL OR (target_score BETWEEN 0 AND 100)',
            name='check_target_score_range'
        ),
        CheckConstraint(
            "knowledge_level IS NULL OR knowledge_level IN ('Beginner', 'Intermediate', 'Advanced')",
            name='check_knowledge_level'
        ),
        CheckConstraint(
            "referral_source IS NULL OR referral_source IN ('Search', 'Friend', 'Social', 'Other')",
            name='check_referral_source'
        ),
        CheckConstraint(
            "dark_mode IN ('light', 'dark', 'auto')",
            name='check_dark_mode'
        ),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email})>"
