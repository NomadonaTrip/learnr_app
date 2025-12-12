"""
ReadingChunk SQLAlchemy model.
Represents chunked reading content from course materials (e.g., BABOK v3).
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .course import Course


class ReadingChunk(Base):
    """
    ReadingChunk model representing parsed and chunked reading content.

    Each chunk is scoped to a course and contains text extracted from
    the course corpus (e.g., BABOK PDF). Chunks are linked to concepts
    via the concept_ids array for semantic retrieval.
    """
    __tablename__ = "reading_chunks"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to course (multi-course support)
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Chunk content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # Reference to source material section (generic for any corpus)
    corpus_section = Column(String(50), nullable=False, index=True)

    # Reference to course.knowledge_areas[].id
    knowledge_area_id = Column(String(50), nullable=False)

    # Array of concept UUIDs this chunk is linked to
    concept_ids = Column(
        ARRAY(UUID(as_uuid=True)),
        nullable=False,
        server_default='{}',
        index=True  # GIN index for array queries
    )

    # Metadata
    estimated_read_time_minutes = Column(Integer, nullable=False, default=5)
    chunk_index = Column(Integer, nullable=False, default=0)  # Order within section

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
    course: Mapped["Course"] = relationship("Course", back_populates="reading_chunks")

    def __repr__(self) -> str:
        return f"<ReadingChunk(id={self.id}, title={self.title[:30]}, course_id={self.course_id})>"

    @property
    def word_count(self) -> int:
        """Calculate word count from content."""
        return len(self.content.split())

    @property
    def computed_read_time(self) -> int:
        """
        Compute read time based on word count.
        Average reading speed: 200 words per minute.
        Returns minimum of 1 minute.
        """
        read_time = max(1, self.word_count // 200)
        return read_time
