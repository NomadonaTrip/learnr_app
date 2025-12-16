"""
BeliefState SQLAlchemy model.
Represents user knowledge belief states for BKT (Bayesian Knowledge Tracing).
Uses Beta distribution parameters (alpha, beta) to model mastery probability.
"""
import uuid
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, Column, DateTime, Float, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.sql import func

from ..db.session import Base

if TYPE_CHECKING:
    from .concept import Concept
    from .user import User


class BeliefState(Base):
    """
    BeliefState model representing user's knowledge belief for a concept.

    Uses Beta distribution parameters to model mastery probability:
    - Beta(1, 1) = Uniform[0, 1] = Uninformative prior (no knowledge about user)
    - Mean = alpha / (alpha + beta)
    - Confidence = (alpha + beta) / (alpha + beta + 2)

    Key invariants:
    - alpha > 0 (enforced by CHECK constraint)
    - beta > 0 (enforced by CHECK constraint)
    - One belief state per (user_id, concept_id) pair (enforced by UNIQUE constraint)
    """
    __tablename__ = "belief_states"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign keys
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

    # Beta distribution parameters
    # Default: Beta(1, 1) = Uniform[0, 1] = uninformative prior
    alpha = Column(Float, nullable=False, default=1.0)
    beta = Column(Float, nullable=False, default=1.0)

    # Tracking fields
    last_response_at = Column(DateTime(timezone=True), nullable=True)
    response_count = Column(Integer, nullable=False, default=0)

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
    user: Mapped["User"] = relationship("User", back_populates="belief_states")
    concept: Mapped["Concept"] = relationship("Concept", back_populates="belief_states")

    # Table constraints and indexes
    __table_args__ = (
        # Unique constraint: one belief state per user-concept pair
        Index(
            "uq_belief_states_user_concept",
            "user_id",
            "concept_id",
            unique=True
        ),
        # Performance indexes
        Index("idx_belief_states_user", "user_id"),
        Index("idx_belief_states_updated", "updated_at"),
        # Check constraints for valid Beta distribution parameters
        CheckConstraint("alpha > 0", name="check_belief_alpha_positive"),
        CheckConstraint("beta > 0", name="check_belief_beta_positive"),
    )

    def __repr__(self) -> str:
        return (
            f"<BeliefState(id={self.id}, user_id={self.user_id}, "
            f"concept_id={self.concept_id}, alpha={self.alpha}, beta={self.beta})>"
        )

    @property
    def mean(self) -> float:
        """Calculate mean mastery probability: alpha / (alpha + beta)."""
        return self.alpha / (self.alpha + self.beta)

    @property
    def confidence(self) -> float:
        """Calculate confidence level: (alpha + beta) / (alpha + beta + 2)."""
        total = self.alpha + self.beta
        return total / (total + 2)

    @property
    def status(self) -> str:
        """
        Classify belief state based on mean and confidence.

        Returns one of:
        - "mastered": mean >= 0.8 and confidence >= 0.7
        - "gap": mean < 0.5 and confidence >= 0.7
        - "borderline": 0.5 <= mean < 0.8 and confidence >= 0.7
        - "uncertain": confidence < 0.7
        """
        if self.confidence < 0.7:
            return "uncertain"
        if self.mean >= 0.8:
            return "mastered"
        if self.mean < 0.5:
            return "gap"
        return "borderline"
