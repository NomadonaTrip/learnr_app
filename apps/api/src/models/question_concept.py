"""
QuestionConcept SQLAlchemy model.
Represents the many-to-many relationship between questions and concepts.
"""
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .concept import Concept
    from .question import Question


class QuestionConcept(Base):
    """
    Junction table linking questions to concepts.

    Each question can map to 1-5 concepts with a relevance score
    indicating how directly the question tests that concept.

    Relevance scores:
    - 1.0: Question directly tests this concept (primary focus)
    - 0.7-0.9: Question significantly involves this concept
    - 0.5-0.6: Question indirectly relates to this concept
    """

    __tablename__ = "question_concepts"

    # Composite primary key
    question_id = Column(
        UUID(as_uuid=True),
        ForeignKey("questions.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    # Relevance score (0.0-1.0)
    relevance = Column(Float, nullable=False, default=1.0)

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="question_concepts"
    )
    concept: Mapped["Concept"] = relationship(
        "Concept",
        back_populates="question_concepts"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "relevance >= 0.0 AND relevance <= 1.0",
            name="ck_question_concepts_relevance_range",
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<QuestionConcept(question_id={self.question_id}, "
            f"concept_id={self.concept_id}, relevance={self.relevance})>"
        )
