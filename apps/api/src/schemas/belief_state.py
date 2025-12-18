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
