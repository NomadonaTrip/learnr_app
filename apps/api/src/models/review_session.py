"""
ReviewSession SQLAlchemy model.
Represents the review_sessions table for post-quiz review sessions.

Story 4.9: Post-Session Review Mode
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .quiz_session import QuizSession
    from .review_response import ReviewResponse
    from .user import User


class ReviewSession(Base):
    """
    ReviewSession model for post-quiz review sessions.

    Tracks review sessions where users re-answer questions they got wrong
    during a quiz session, enabling reinforcement learning.

    Story 4.9: Post-Session Review Mode
    """
    __tablename__ = "review_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    original_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Review targets
    question_ids = Column(JSONB, nullable=False)  # Array of question UUIDs to review
    total_to_review = Column(Integer, nullable=False)

    # Progress tracking
    reviewed_count = Column(Integer, nullable=False, default=0)
    reinforced_count = Column(Integer, nullable=False, default=0)
    still_incorrect_count = Column(Integer, nullable=False, default=0)

    # Status
    status = Column(String(20), nullable=False, default="pending", index=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="review_sessions")
    original_session: Mapped["QuizSession"] = relationship(
        "QuizSession",
        back_populates="review_sessions"
    )
    responses: Mapped[list["ReviewResponse"]] = relationship(
        "ReviewResponse",
        back_populates="review_session",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'in_progress', 'completed', 'skipped')",
            name="check_review_session_status"
        ),
    )

    @property
    def reinforcement_rate(self) -> float:
        """Calculate reinforcement rate as a decimal (0.0-1.0)."""
        if self.reviewed_count == 0:
            return 0.0
        return self.reinforced_count / self.reviewed_count

    def __repr__(self) -> str:
        return (
            f"<ReviewSession(id={self.id}, user_id={self.user_id}, "
            f"status={self.status}, reviewed={self.reviewed_count}/{self.total_to_review})>"
        )
