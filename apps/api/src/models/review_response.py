"""
ReviewResponse SQLAlchemy model.
Represents individual review responses within a review session.

Story 4.9: Post-Session Review Mode
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, CheckConstraint, Column, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .question import Question
    from .quiz_response import QuizResponse
    from .review_session import ReviewSession
    from .user import User


class ReviewResponse(Base):
    """
    ReviewResponse model for tracking individual review answers.

    Records each question re-answered during a review session, enabling:
    - Reinforcement tracking (incorrect → correct)
    - Belief updates with reinforcement modifiers
    - Review session progress

    Story 4.9: Post-Session Review Mode
    """
    __tablename__ = "review_responses"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    review_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("review_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    original_response_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quiz_responses.id"),
        nullable=False
    )

    # Response data
    selected_answer = Column(String(1), nullable=False)  # A, B, C, or D
    is_correct = Column(Boolean, nullable=False)
    was_reinforced = Column(Boolean, nullable=False, default=False)  # True if incorrect→correct

    # Belief tracking
    belief_updates = Column(JSONB, nullable=True)  # Snapshot of concept updates

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    review_session: Mapped["ReviewSession"] = relationship(
        "ReviewSession",
        back_populates="responses"
    )
    user: Mapped["User"] = relationship("User", back_populates="review_responses")
    question: Mapped["Question"] = relationship("Question", back_populates="review_responses")
    original_response: Mapped["QuizResponse"] = relationship(
        "QuizResponse",
        back_populates="review_response"
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "selected_answer IN ('A', 'B', 'C', 'D')",
            name="ck_review_responses_selected_answer"
        ),
        Index("idx_review_responses_session", "review_session_id"),
        Index("idx_review_responses_user", "user_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewResponse(id={self.id}, review_session_id={self.review_session_id}, "
            f"question_id={self.question_id}, is_correct={self.is_correct}, "
            f"was_reinforced={self.was_reinforced})>"
        )
