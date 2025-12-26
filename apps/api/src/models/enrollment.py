"""
Enrollment SQLAlchemy model.
Represents user-course relationships with enrollment metadata.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .course import Course
    from .diagnostic_session import DiagnosticSession
    from .quiz_session import QuizSession
    from .reading_queue import ReadingQueue
    from .user import User


class Enrollment(Base):
    """
    Enrollment model representing a user's enrollment in a course.

    Tracks enrollment status, study goals, and progress.
    """
    __tablename__ = "enrollments"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Study goals (copied from user preferences per enrollment)
    exam_date = Column(Date, nullable=True)
    target_score = Column(Integer, nullable=True)
    daily_study_time = Column(Integer, nullable=True)  # in minutes

    # Enrollment tracking
    enrolled_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    last_activity_at = Column(DateTime(timezone=True), nullable=True)

    # Status
    status = Column(String(20), nullable=False, default='active')
    completion_percentage = Column(Float, nullable=False, default=0.0)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="enrollments")
    course: Mapped["Course"] = relationship("Course", back_populates="enrollments")
    diagnostic_sessions: Mapped[list["DiagnosticSession"]] = relationship(
        "DiagnosticSession",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )
    quiz_sessions: Mapped[list["QuizSession"]] = relationship(
        "QuizSession",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )
    reading_queue_items: Mapped[list["ReadingQueue"]] = relationship(
        "ReadingQueue",
        back_populates="enrollment",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        UniqueConstraint('user_id', 'course_id', name='uq_enrollments_user_course'),
        CheckConstraint(
            "status IN ('active', 'paused', 'completed', 'archived')",
            name='check_enrollment_status'
        ),
    )

    def __repr__(self) -> str:
        return f"<Enrollment(id={self.id}, user_id={self.user_id}, course_id={self.course_id}, status={self.status})>"
