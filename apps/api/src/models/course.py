"""
Course SQLAlchemy model.
Represents the courses table for multi-course support.
"""
import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .concept import Concept
    from .enrollment import Enrollment
    from .question import Question
    from .reading_chunk import ReadingChunk


class Course(Base):
    """
    Course model representing certification preparation courses.

    Each course has its own set of knowledge areas stored as JSONB,
    allowing flexible configuration per certification type.
    """
    __tablename__ = "courses"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Course identification
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    corpus_name = Column(String(100), nullable=True)

    # Knowledge areas as JSONB array
    # Each element: {"id": str, "name": str, "short_name": str, "display_order": int, "color": str}
    knowledge_areas = Column(JSONB, nullable=False)

    # BKT thresholds
    default_diagnostic_count = Column(Integer, nullable=False, default=12)
    mastery_threshold = Column(Float, nullable=False, default=0.8)
    gap_threshold = Column(Float, nullable=False, default=0.5)
    confidence_threshold = Column(Float, nullable=False, default=0.7)

    # Display settings
    icon_url = Column(String(500), nullable=True)
    color_hex = Column(String(7), nullable=True)

    # Status flags
    is_active = Column(Boolean, nullable=False, default=True)
    is_public = Column(Boolean, nullable=False, default=True)

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
    enrollments: Mapped[List["Enrollment"]] = relationship(
        "Enrollment",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    concepts: Mapped[List["Concept"]] = relationship(
        "Concept",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="course",
        cascade="all, delete-orphan"
    )
    reading_chunks: Mapped[List["ReadingChunk"]] = relationship(
        "ReadingChunk",
        back_populates="course",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Course(id={self.id}, slug={self.slug}, name={self.name})>"
