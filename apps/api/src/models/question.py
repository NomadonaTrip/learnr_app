"""
Question SQLAlchemy model.
Represents the questions table for course exam questions with multi-course support.
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
    Text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func, text

from ..db.session import Base

if TYPE_CHECKING:
    from .concept import Concept
    from .course import Course
    from .question_concept import QuestionConcept
    from .quiz_response import QuizResponse


class Question(Base):
    """
    Question model for course exam questions with multi-course support.

    Stores vendor-provided or LLM-generated questions with metadata
    including knowledge area, difficulty, and IRT parameters for
    adaptive learning.
    """

    __tablename__ = "questions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to course (multi-course support)
    course_id = Column(
        UUID(as_uuid=True),
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Question content
    question_text = Column(Text, nullable=False)
    options = Column(JSONB, nullable=False)  # {"A": "...", "B": "...", "C": "...", "D": "..."}
    correct_answer = Column(String(1), nullable=False)
    explanation = Column(Text, nullable=False)

    # Metadata - multi-course aware
    knowledge_area_id = Column(String(50), nullable=False)  # References course.knowledge_areas[].id
    difficulty = Column(Float, nullable=False, default=0.0)  # IRT b-parameter (-3.0 to +3.0)
    difficulty_label = Column(String(10), nullable=True)  # Human-readable: Easy/Medium/Hard
    source = Column(String(50), nullable=False, default="vendor")
    corpus_reference = Column(String(100), nullable=True)  # Generic reference (BABOK, PMBOK, etc.)

    # Secondary tags for filtering/analysis (not primary assessment dimensions)
    # BABOK Perspectives (Chapter 10): Agile, BI, IT, BPM
    perspectives = Column(ARRAY(String), nullable=True, default=[])
    # BABOK Underlying Competencies (Chapter 9): Analytical, Communication, etc.
    competencies = Column(ARRAY(String), nullable=True, default=[])

    # IRT parameters for adaptive learning
    discrimination = Column(Float, nullable=False, default=1.0)  # IRT discrimination parameter
    guess_rate = Column(Float, nullable=False, default=0.25)  # P(correct | not mastered)
    slip_rate = Column(Float, nullable=False, default=0.10)  # P(incorrect | mastered)

    # Calibration statistics
    times_asked = Column(Integer, nullable=False, default=0)
    times_correct = Column(Integer, nullable=False, default=0)

    # Active status
    is_active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    course: Mapped["Course"] = relationship("Course", back_populates="questions")

    # Many-to-many with concepts via junction table
    question_concepts: Mapped[list["QuestionConcept"]] = relationship(
        "QuestionConcept",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    # Responses to this question
    quiz_responses: Mapped[list["QuizResponse"]] = relationship(
        "QuizResponse",
        back_populates="question",
        cascade="all, delete-orphan"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "correct_answer IN ('A', 'B', 'C', 'D')",
            name="ck_questions_correct_answer",
        ),
        CheckConstraint(
            "difficulty >= -3.0 AND difficulty <= 3.0",
            name="ck_questions_difficulty_range",
        ),
        CheckConstraint(
            "guess_rate >= 0.0 AND guess_rate <= 1.0",
            name="ck_questions_guess_rate_range",
        ),
        CheckConstraint(
            "slip_rate >= 0.0 AND slip_rate <= 1.0",
            name="ck_questions_slip_rate_range",
        ),
        Index("idx_questions_course_ka", "course_id", "knowledge_area_id"),
        Index(
            "idx_questions_text_hash_unique",
            text("md5(question_text)"),
            unique=True,
            postgresql_using="btree",
        ),
        Index(
            "idx_questions_active",
            "is_active",
            postgresql_where=text("is_active = true"),
        ),
    )

    @property
    def concepts(self) -> list["Concept"]:
        """Get list of concepts this question maps to."""
        return [qc.concept for qc in self.question_concepts]

    @property
    def empirical_difficulty(self) -> float:
        """Calculate empirical difficulty from response data."""
        if self.times_asked == 0:
            return self.difficulty
        return 1.0 - (self.times_correct / self.times_asked)

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, course_id={self.course_id}, ka={self.knowledge_area_id})>"
