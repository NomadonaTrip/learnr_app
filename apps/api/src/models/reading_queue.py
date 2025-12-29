"""
ReadingQueue SQLAlchemy model.
Represents queued reading materials for users triggered by quiz answer submissions.
Story 5.5: Background Reading Queue Population
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .concept import Concept
    from .enrollment import Enrollment
    from .question import Question
    from .reading_chunk import ReadingChunk
    from .user import User


class ReadingQueue(Base):
    """
    ReadingQueue model representing queued reading materials for a user.

    Reading items are automatically added to the queue when users answer
    questions, with priority based on correctness and competency level.
    """
    __tablename__ = "reading_queue"

    __table_args__ = (
        Index("idx_reading_queue_user", "user_id"),
        Index("idx_reading_queue_enrollment", "enrollment_id"),
        Index("idx_reading_queue_enrollment_status", "enrollment_id", "status"),
        UniqueConstraint("enrollment_id", "chunk_id", name="uq_reading_queue_enrollment_chunk"),
    )

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    enrollment_id = Column(
        UUID(as_uuid=True),
        ForeignKey("enrollments.id", ondelete="CASCADE"),
        nullable=False,
    )
    chunk_id = Column(
        UUID(as_uuid=True),
        ForeignKey("reading_chunks.id", ondelete="CASCADE"),
        nullable=False,
    )
    triggered_by_question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="SET NULL"),
        nullable=True,
    )
    triggered_by_concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Priority and status
    priority = Column(String(10), nullable=False, default="Medium")
    status = Column(String(20), nullable=False, default="unread")

    # Timestamps
    added_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    first_opened_at = Column(DateTime(timezone=True), nullable=True)
    dismissed_at = Column(DateTime(timezone=True), nullable=True)

    # Engagement tracking
    times_opened = Column(Integer, nullable=False, default=0)
    total_reading_time_seconds = Column(Integer, nullable=False, default=0)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="reading_queue_items")
    enrollment: Mapped["Enrollment"] = relationship("Enrollment", back_populates="reading_queue_items")
    chunk: Mapped["ReadingChunk"] = relationship("ReadingChunk")
    triggered_by_question: Mapped["Question"] = relationship("Question")
    triggered_by_concept: Mapped["Concept"] = relationship("Concept")

    def __repr__(self) -> str:
        return f"<ReadingQueue(id={self.id}, user_id={self.user_id}, chunk_id={self.chunk_id}, priority={self.priority})>"

    @property
    def priority_order(self) -> int:
        """Return numeric priority for sorting (lower = higher priority)."""
        priority_map = {"High": 0, "Medium": 1, "Low": 2}
        return priority_map.get(self.priority, 1)
