"""
DiagnosticSession SQLAlchemy model.
Represents diagnostic assessment session state for resumable diagnostics.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    DateTime,
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
    from .enrollment import Enrollment
    from .user import User


class DiagnosticSession(Base):
    """
    DiagnosticSession model for tracking diagnostic assessment state.

    Enables users to resume interrupted diagnostic assessments.
    Only one active session per enrollment is allowed.

    Status values:
    - in_progress: Session is active and user is answering questions
    - completed: All questions answered, session finished normally
    - expired: Session timed out (>30 min inactive)
    - reset: Session was manually reset by user
    """

    __tablename__ = "diagnostic_sessions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    enrollment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Session data
    question_ids = Column(JSONB, nullable=False)  # List[str] of question UUIDs in order
    current_index = Column(Integer, nullable=False, default=0)
    status = Column(String(20), nullable=False, default="in_progress")

    # Timestamps
    started_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="diagnostic_sessions")
    enrollment: Mapped["Enrollment"] = relationship(
        "Enrollment", back_populates="diagnostic_sessions"
    )

    # Table constraints and indexes
    __table_args__ = (
        CheckConstraint(
            "status IN ('in_progress', 'completed', 'expired', 'reset')",
            name="diagnostic_session_status_check",
        ),
        CheckConstraint(
            "current_index >= 0",
            name="diagnostic_session_index_check",
        ),
        # Partial unique index: only one active session per enrollment
        Index(
            "idx_diagnostic_sessions_active_enrollment",
            "enrollment_id",
            unique=True,
            postgresql_where=(Column("status") == "in_progress"),
        ),
        # Index for stale session cleanup
        Index(
            "idx_diagnostic_sessions_stale",
            "started_at",
            postgresql_where=(Column("status") == "in_progress"),
        ),
    )

    @property
    def questions_total(self) -> int:
        """Total number of questions in this session."""
        return len(self.question_ids) if self.question_ids else 0

    @property
    def questions_remaining(self) -> int:
        """Number of questions remaining to answer."""
        return max(0, self.questions_total - self.current_index)

    @property
    def is_complete(self) -> bool:
        """Check if session is completed."""
        return self.status == "completed"

    def __repr__(self) -> str:
        return (
            f"<DiagnosticSession(id={self.id}, user_id={self.user_id}, "
            f"enrollment_id={self.enrollment_id}, status={self.status}, "
            f"progress={self.current_index}/{self.questions_total})>"
        )
