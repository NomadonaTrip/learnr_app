"""
Concept SQLAlchemy model.
Represents discrete, testable concepts extracted from course materials.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .concept_prerequisite import ConceptPrerequisite
    from .course import Course
    from .question_concept import QuestionConcept


class Concept(Base):
    """
    Concept model representing testable knowledge units.

    Each concept is scoped to a course and references a knowledge area
    defined in that course's JSONB configuration. This supports multi-course
    architecture where different certifications have different concept sets.
    """
    __tablename__ = "concepts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to course (multi-course support)
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Concept identification
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Reference to source material section (generic for any corpus)
    corpus_section_ref = Column(String(50), nullable=True, index=True)

    # Reference to course.knowledge_areas[].id
    knowledge_area_id = Column(String(50), nullable=False)

    # BKT-related attributes
    difficulty_estimate = Column(Float, nullable=False, default=0.5)
    prerequisite_depth = Column(Integer, nullable=False, default=0)

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
    course: Mapped["Course"] = relationship("Course", back_populates="concepts")

    # Prerequisite relationships (concepts that must be learned before this one)
    prerequisites: Mapped[list["ConceptPrerequisite"]] = relationship(
        "ConceptPrerequisite",
        foreign_keys="ConceptPrerequisite.concept_id",
        back_populates="concept",
        cascade="all, delete-orphan"
    )

    # Dependent relationships (concepts that depend on this one)
    dependents: Mapped[list["ConceptPrerequisite"]] = relationship(
        "ConceptPrerequisite",
        foreign_keys="ConceptPrerequisite.prerequisite_concept_id",
        back_populates="prerequisite_concept",
        cascade="all, delete-orphan"
    )

    # Many-to-many with questions via junction table
    question_concepts: Mapped[list["QuestionConcept"]] = relationship(
        "QuestionConcept",
        back_populates="concept",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Concept(id={self.id}, name={self.name}, course_id={self.course_id})>"
