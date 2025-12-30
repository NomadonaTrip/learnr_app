"""
QuizResponse SQLAlchemy model.
Represents individual question responses within a quiz session.
Used for tracking answered questions and filtering in question selection.

Story 4.3: Answer Submission and Immediate Feedback
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .question import Question
    from .quiz_session import QuizSession
    from .review_response import ReviewResponse
    from .user import User


class QuizResponse(Base):
    """
    QuizResponse model for tracking individual question answers in quiz sessions.

    Records each question answered during a quiz session, enabling:
    - Session progress tracking
    - Recency filtering (exclude recently answered questions)
    - Session-level deduplication (no repeats within session)
    - Performance analytics
    - Idempotent answer submission via request_id

    Story 4.3: Answer Submission and Immediate Feedback
    """
    __tablename__ = "quiz_responses"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("quiz_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Response data
    selected_answer = Column(String(1), nullable=False)  # A, B, C, or D
    is_correct = Column(Boolean, nullable=False)
    time_taken_ms = Column(Integer, nullable=True)  # Time taken to answer in milliseconds

    # Idempotency key (Story 4.3)
    request_id = Column(UUID(as_uuid=True), nullable=True, unique=True, index=True)

    # Bayesian belief tracking (Story 4.3/4.4)
    info_gain_actual = Column(Float, nullable=True)  # Actual entropy reduction from this answer
    belief_updates = Column(JSONB, nullable=True)  # Snapshot of concept updates

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="quiz_responses")
    session: Mapped["QuizSession"] = relationship("QuizSession", back_populates="responses")
    question: Mapped["Question"] = relationship("Question", back_populates="quiz_responses")
    review_response: Mapped["ReviewResponse"] = relationship(
        "ReviewResponse",
        back_populates="original_response",
        uselist=False
    )

    # Table constraints and indexes
    __table_args__ = (
        # Check constraint for valid answer values
        CheckConstraint(
            "selected_answer IN ('A', 'B', 'C', 'D')",
            name="ck_quiz_responses_selected_answer",
        ),
        # Index for recency filtering: get questions answered by user within time window
        Index("idx_quiz_responses_user_created", "user_id", "created_at"),
        # Index for session filtering: get questions answered in a session
        Index("idx_quiz_responses_session", "session_id"),
        # Composite index for efficient question lookups per user
        Index("idx_quiz_responses_user_question", "user_id", "question_id"),
        # Index for idempotency lookups
        Index("idx_quiz_responses_request_id", "request_id"),
    )

    def __repr__(self) -> str:
        return (
            f"<QuizResponse(id={self.id}, session_id={self.session_id}, "
            f"question_id={self.question_id}, is_correct={self.is_correct})>"
        )
