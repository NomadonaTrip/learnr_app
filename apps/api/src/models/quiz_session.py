"""
QuizSession SQLAlchemy model.
Represents the quiz_sessions table for adaptive quiz engine sessions.
"""
import uuid
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .enrollment import Enrollment
    from .quiz_response import QuizResponse
    from .user import User


class QuizSession(Base):
    """
    QuizSession model for adaptive quiz sessions.

    Tracks session state, progress, and configuration for the adaptive quiz engine.
    Uses derived status pattern (computed from ended_at and is_paused columns).
    """
    __tablename__ = "quiz_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    enrollment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Session timestamps
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Session configuration
    session_type = Column(
        String(50),
        nullable=False,
        default="adaptive"
    )
    question_strategy = Column(
        String(50),
        nullable=False,
        default="max_info_gain"
    )
    knowledge_area_filter = Column(String(50), nullable=True)

    # Target concept IDs for focused_concept sessions (JSONB array of UUID strings)
    target_concept_ids = Column(JSONB, nullable=True, default=[])

    # Session target (fixed-length sessions for habit-forming consistency)
    question_target = Column(Integer, nullable=False, default=10)

    # Progress tracking
    total_questions = Column(Integer, nullable=False, default=0)
    correct_count = Column(Integer, nullable=False, default=0)

    # State
    is_paused = Column(Boolean, nullable=False, default=False)

    # Optimistic locking
    version = Column(Integer, nullable=False, default=1)

    # Auto-managed timestamp for expiration checking
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quiz_sessions")
    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="quiz_sessions")
    responses: Mapped[list["QuizResponse"]] = relationship(
        "QuizResponse",
        back_populates="session",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "session_type IN ('diagnostic', 'adaptive', 'focused', 'focused_ka', 'focused_concept', 'review')",
            name="check_quiz_session_type"
        ),
        CheckConstraint(
            "question_strategy IN ('max_info_gain', 'max_uncertainty', 'prerequisite_first', 'balanced')",
            name="check_quiz_question_strategy"
        ),
        CheckConstraint(
            "question_target BETWEEN 10 AND 15",
            name="check_quiz_session_question_target"
        ),
    )

    @property
    def is_active(self) -> bool:
        """Check if session is currently active (not ended and not paused)."""
        return self.ended_at is None and not self.is_paused

    @property
    def status(self) -> str:
        """
        Derive session status from database columns.

        Returns:
            'active': Session is ongoing
            'paused': Session is paused
            'completed': Session has been ended
            'expired': Session has timed out (2+ hours of inactivity)
        """
        if self.ended_at is not None:
            return "completed"

        # Check for expiration (2 hours of inactivity)
        timeout = timedelta(hours=2)
        now = datetime.now(UTC)
        updated = self.updated_at
        if updated.tzinfo is None:
            updated = updated.replace(tzinfo=UTC)
        if now > updated + timeout:
            return "expired"

        if self.is_paused:
            return "paused"

        return "active"

    @property
    def accuracy(self) -> float:
        """Calculate session accuracy as percentage (0.0-100.0)."""
        if self.total_questions == 0:
            return 0.0
        return (self.correct_count / self.total_questions) * 100.0

    def __repr__(self) -> str:
        return (
            f"<QuizSession(id={self.id}, user_id={self.user_id}, "
            f"type={self.session_type}, status={self.status})>"
        )
