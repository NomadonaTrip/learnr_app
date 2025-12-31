"""
Pydantic schemas for BeliefState model.
Handles validation and serialization for belief state data used in BKT.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, computed_field


class BeliefStatus(str, Enum):
    """Classification of belief state based on mean and confidence."""

    MASTERED = "mastered"
    GAP = "gap"
    BORDERLINE = "borderline"
    UNCERTAIN = "uncertain"


# Thresholds for classification
MASTERY_THRESHOLD = 0.8
GAP_THRESHOLD = 0.5
CONFIDENCE_THRESHOLD = 0.7


class BeliefStateBase(BaseModel):
    """Base schema with core belief state fields."""

    alpha: float = Field(
        default=1.0,
        gt=0,
        description="Beta distribution alpha parameter (must be > 0)"
    )
    beta: float = Field(
        default=1.0,
        gt=0,
        description="Beta distribution beta parameter (must be > 0)"
    )
    response_count: int = Field(
        default=0,
        ge=0,
        description="Number of responses for this concept"
    )


class BeliefStateCreate(BeliefStateBase):
    """Schema for creating a new belief state."""

    user_id: UUID = Field(..., description="UUID of the user")
    concept_id: UUID = Field(..., description="UUID of the concept")


class BeliefStateUpdate(BaseModel):
    """Schema for updating an existing belief state."""

    alpha: float | None = Field(None, gt=0)
    beta: float | None = Field(None, gt=0)
    last_response_at: datetime | None = None
    response_count: int | None = Field(None, ge=0)


class BeliefStateResponse(BeliefStateBase):
    """Schema for belief state response with all fields and computed properties."""

    id: UUID
    user_id: UUID
    concept_id: UUID
    last_response_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @computed_field
    @property
    def mean(self) -> float:
        """Calculate mean mastery probability: alpha / (alpha + beta)."""
        return round(self.alpha / (self.alpha + self.beta), 4)

    @computed_field
    @property
    def confidence(self) -> float:
        """Calculate confidence level: (alpha + beta) / (alpha + beta + 2)."""
        total = self.alpha + self.beta
        return round(total / (total + 2), 4)

    @computed_field
    @property
    def status(self) -> BeliefStatus:
        """Classify belief state based on mean and confidence."""
        confidence = self.alpha + self.beta
        confidence_level = confidence / (confidence + 2)
        mean = self.alpha / (self.alpha + self.beta)

        if confidence_level < CONFIDENCE_THRESHOLD:
            return BeliefStatus.UNCERTAIN
        if mean >= MASTERY_THRESHOLD:
            return BeliefStatus.MASTERED
        if mean < GAP_THRESHOLD:
            return BeliefStatus.GAP
        return BeliefStatus.BORDERLINE


class BeliefStateInDB(BeliefStateResponse):
    """Schema for belief state as stored in database (same as response)."""

    pass


class BeliefInitializationStatus(BaseModel):
    """Schema for belief initialization status endpoint response."""

    initialized: bool = Field(
        ...,
        description="True if belief states exist for this user"
    )
    total_concepts: int = Field(
        ...,
        description="Total concepts in the course corpus"
    )
    belief_count: int = Field(
        ...,
        description="Number of belief_states records for the user"
    )
    coverage_percentage: float = Field(
        ...,
        ge=0,
        le=100,
        description="Percentage of concepts with belief states"
    )
    created_at: datetime | None = Field(
        None,
        description="When initialization occurred (earliest belief created_at)"
    )


class InitializationResult(BaseModel):
    """Result of belief initialization operation."""

    success: bool
    already_initialized: bool = False
    belief_count: int = 0
    duration_ms: float = 0
    message: str = ""
    enrollment_id: UUID | None = None


class BeliefSummary(BaseModel):
    """Summary of user's belief states for a course."""

    user_id: UUID
    course_id: UUID
    total_beliefs: int
    mastered_count: int = Field(..., description="Beliefs with status=mastered")
    gap_count: int = Field(..., description="Beliefs with status=gap")
    borderline_count: int = Field(..., description="Beliefs with status=borderline")
    uncertain_count: int = Field(..., description="Beliefs with status=uncertain")
    average_mean: float = Field(..., description="Average mastery across all beliefs")


class BeliefStateWithConcept(BeliefStateResponse):
    """Belief state with embedded concept information."""

    concept_name: str
    concept_knowledge_area_id: str


# ============================================================================
# Belief Update Schemas (Story 4.4)
# ============================================================================


class BeliefUpdateResult(BaseModel):
    """Result of updating a single concept's belief state."""

    concept_id: UUID = Field(..., description="UUID of the concept")
    concept_name: str = Field(..., description="Name of the concept")
    old_alpha: float = Field(..., description="Alpha before update")
    old_beta: float = Field(..., description="Beta before update")
    new_alpha: float = Field(..., description="Alpha after update")
    new_beta: float = Field(..., description="Beta after update")
    is_direct: bool = Field(
        default=True,
        description="True if directly updated (from question), False if propagated from prerequisites"
    )

    @computed_field
    @property
    def old_mean(self) -> float:
        """Mean mastery before update."""
        return round(self.old_alpha / (self.old_alpha + self.old_beta), 4)

    @computed_field
    @property
    def new_mean(self) -> float:
        """Mean mastery after update."""
        return round(self.new_alpha / (self.new_alpha + self.new_beta), 4)

    @computed_field
    @property
    def old_confidence(self) -> float:
        """Confidence before update."""
        total = self.old_alpha + self.old_beta
        return round(total / (total + 2), 4)

    @computed_field
    @property
    def new_confidence(self) -> float:
        """Confidence after update."""
        total = self.new_alpha + self.new_beta
        return round(total / (total + 2), 4)


class BeliefUpdaterResponse(BaseModel):
    """Response from BeliefUpdater.update_beliefs()."""

    updates: list[BeliefUpdateResult] = Field(
        default_factory=list,
        description="List of belief updates (both direct and propagated)"
    )
    info_gain_actual: float = Field(
        default=0.0,
        ge=0,
        description="Actual information gain from this response (entropy reduction)"
    )
    concepts_updated_count: int = Field(
        default=0,
        ge=0,
        description="Total number of concepts updated"
    )
    direct_updates_count: int = Field(
        default=0,
        ge=0,
        description="Number of concepts directly tested by the question"
    )
    propagated_updates_count: int = Field(
        default=0,
        ge=0,
        description="Number of prerequisite concepts with propagated updates"
    )
    processing_time_ms: float = Field(
        default=0.0,
        ge=0,
        description="Time taken for belief update in milliseconds"
    )

    def to_belief_updates_jsonb(self) -> list[dict]:
        """
        Convert updates to JSONB format for storage in responses table.

        Returns format expected by belief_updates column.
        """
        return [
            {
                "concept_id": str(u.concept_id),
                "concept_name": u.concept_name,
                "old_alpha": u.old_alpha,
                "old_beta": u.old_beta,
                "new_alpha": u.new_alpha,
                "new_beta": u.new_beta,
            }
            for u in self.updates
        ]


# ============================================================================
# Gap Concept Schemas (Story 4.8 - Focused Practice)
# ============================================================================


class GapConcept(BaseModel):
    """A concept identified as a gap in user knowledge."""

    concept_id: UUID = Field(..., description="UUID of the gap concept")
    concept_name: str = Field(..., description="Name of the concept")
    mastery: float = Field(
        ..., ge=0.0, le=1.0, description="Current mastery probability (0-1)"
    )
    gap_severity: float = Field(
        ..., ge=0.0, le=1.0, description="Gap severity (0=mild, 1=severe)"
    )


class KAGapsResponse(BaseModel):
    """Response for knowledge area gaps endpoint."""

    knowledge_area_id: str = Field(..., description="Knowledge area ID")
    gap_count: int = Field(..., description="Number of gap concepts found")
    gaps: list[GapConcept] = Field(..., description="List of gap concepts")
