"""
ConceptUnlockEvent SQLAlchemy model.
Tracks when concepts are unlocked for users based on prerequisite mastery.
Story 4.11: Prerequisite-Based Curriculum Navigation
"""
from typing import TYPE_CHECKING

from sqlalchemy import Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .concept import Concept
    from .user import User


class ConceptUnlockEvent(Base):
    """
    ConceptUnlockEvent model representing when a concept becomes unlocked.

    A concept is unlocked when all its prerequisite concepts have been
    mastered (P(mastery) > threshold AND confidence > threshold).
    """
    __tablename__ = "concept_unlock_events"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
        nullable=False
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="CASCADE"),
        nullable=False
    )
    # Which prerequisite's mastery triggered this unlock (optional)
    prerequisite_concept_id = Column(
        UUID(as_uuid=True),
        ForeignKey("concepts.id", ondelete="SET NULL"),
        nullable=True
    )
    unlocked_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="unlock_events")
    concept: Mapped["Concept"] = relationship(
        "Concept",
        foreign_keys=[concept_id],
        back_populates="unlock_events"
    )
    prerequisite_concept: Mapped["Concept"] = relationship(
        "Concept",
        foreign_keys=[prerequisite_concept_id]
    )

    def __repr__(self) -> str:
        return (
            f"<ConceptUnlockEvent("
            f"user_id={self.user_id}, "
            f"concept_id={self.concept_id}, "
            f"unlocked_at={self.unlocked_at})>"
        )
