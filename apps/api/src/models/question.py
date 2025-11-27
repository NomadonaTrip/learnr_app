"""
Question SQLAlchemy model.
Represents the questions table for CBAP exam questions.
"""
import uuid

from sqlalchemy import (
    TIMESTAMP,
    CheckConstraint,
    Column,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from ..db.session import Base


class Question(Base):
    """
    Question model for CBAP exam questions.

    Stores vendor-provided or LLM-generated questions with metadata
    including knowledge area, difficulty, and concept tags.
    """

    __tablename__ = "questions"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Question content
    question_text = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)
    explanation = Column(Text, nullable=False)

    # Metadata
    ka = Column(String(100), nullable=False)  # Knowledge Area
    difficulty = Column(String(20), nullable=False)
    concept_tags = Column(JSONB, nullable=False, default=list)
    source = Column(String(50), nullable=False, default="vendor")
    babok_reference = Column(String(100), nullable=True)

    # Analytics
    times_seen = Column(Integer, nullable=False, default=0)
    avg_correct_rate = Column(Float, nullable=False, default=0.0)

    # Timestamps
    created_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP,
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "correct_answer IN ('A', 'B', 'C', 'D')",
            name="check_correct_answer",
        ),
        CheckConstraint(
            "difficulty IN ('Easy', 'Medium', 'Hard')",
            name="check_difficulty",
        ),
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, ka={self.ka}, difficulty={self.difficulty})>"
