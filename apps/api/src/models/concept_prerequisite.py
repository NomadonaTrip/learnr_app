"""
ConceptPrerequisite SQLAlchemy model.
Represents prerequisite relationships between concepts for BKT prioritization.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .concept import Concept


class ConceptPrerequisite(Base):
    """
    ConceptPrerequisite model representing prerequisite relationships.

    A prerequisite relationship indicates that one concept should be
    understood before another. This is used by the BKT engine to
    prioritize foundational knowledge and propagate belief updates.

    Relationship Types:
    - 'required': Must understand prerequisite before learning target
    - 'helpful': Understanding prerequisite improves learning but not required
    - 'related': Concepts are related but no strict ordering required
    """
    __tablename__ = "concept_prerequisites"

    # Composite primary key
    concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )
    prerequisite_concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False
    )

    # Relationship strength (0.0-1.0, where 1.0 = must know first)
    strength = Column(Float, nullable=False, default=1.0)

    # Relationship type
    relationship_type = Column(
        String(20),
        nullable=False,
        default="required"
    )

    # Timestamp
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships to Concept model
    concept: Mapped["Concept"] = relationship(
        "Concept",
        foreign_keys=[concept_id],
        back_populates="prerequisites"
    )
    prerequisite_concept: Mapped["Concept"] = relationship(
        "Concept",
        foreign_keys=[prerequisite_concept_id],
        back_populates="dependents"
    )

    def __repr__(self) -> str:
        return (
            f"<ConceptPrerequisite("
            f"concept_id={self.concept_id}, "
            f"prereq_id={self.prerequisite_concept_id}, "
            f"type={self.relationship_type})>"
        )
