"""
Pydantic schemas for Mastery Gate functionality.
Story 4.11: Prerequisite-Based Curriculum Navigation
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnforcementMode(str, Enum):
    """Enforcement mode for prerequisite gates."""
    SOFT = "soft"    # Deprioritize locked concepts (weight = 0.1)
    HARD = "hard"    # Exclude locked concepts entirely


class MasteryGateConfig(BaseModel):
    """Configuration for mastery gates."""
    prerequisite_mastery_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum P(mastery) required for prerequisites"
    )
    prerequisite_confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence required for prerequisites"
    )
    enforcement_mode: EnforcementMode = Field(
        default=EnforcementMode.SOFT,
        description="How to handle locked concepts: soft (deprioritize) or hard (exclude)"
    )
    min_responses_for_gate: int = Field(
        default=3,
        ge=0,
        description="Minimum responses before gate applies"
    )


class BlockingPrerequisite(BaseModel):
    """Information about a prerequisite blocking concept unlock."""
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID
    name: str
    current_mastery: float = Field(ge=0.0, le=1.0)
    current_confidence: float = Field(ge=0.0, le=1.0)
    required_mastery: float = Field(ge=0.0, le=1.0)
    required_confidence: float = Field(ge=0.0, le=1.0)
    responses_count: int = Field(ge=0)
    progress_to_unlock: float = Field(
        ge=0.0,
        le=1.0,
        description="Progress toward meeting threshold (0.0-1.0)"
    )


class GateCheckResult(BaseModel):
    """Result of checking prerequisite mastery for a concept."""
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID
    concept_name: str
    is_unlocked: bool
    blocking_prerequisites: list[BlockingPrerequisite] = Field(default_factory=list)
    closest_to_unlock: BlockingPrerequisite | None = None
    mastery_progress: float = Field(
        ge=0.0,
        le=1.0,
        description="Overall progress toward unlocking (0.0-1.0)"
    )
    estimated_questions_to_unlock: int = Field(
        ge=0,
        description="Estimated questions needed to unlock"
    )


class ConceptUnlockStatus(BaseModel):
    """Unlock status for a single concept."""
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID
    concept_name: str
    knowledge_area_id: str
    is_unlocked: bool
    has_prerequisites: bool
    prerequisite_count: int = Field(ge=0)
    mastered_prerequisite_count: int = Field(ge=0)
    mastery_progress: float = Field(ge=0.0, le=1.0)


class BulkUnlockStatusResponse(BaseModel):
    """Response for bulk unlock status query."""
    model_config = ConfigDict(from_attributes=True)

    knowledge_area_id: str | None = None
    total_concepts: int = Field(ge=0)
    unlocked_count: int = Field(ge=0)
    locked_count: int = Field(ge=0)
    no_prerequisites_count: int = Field(ge=0)
    concepts: list[ConceptUnlockStatus]


class ConceptUnlockEventResponse(BaseModel):
    """Response schema for concept unlock events."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    concept_id: UUID
    concept_name: str
    prerequisite_concept_id: UUID | None = None
    prerequisite_concept_name: str | None = None
    unlocked_at: datetime


class RecentUnlocksResponse(BaseModel):
    """Response for recently unlocked concepts."""
    model_config = ConfigDict(from_attributes=True)

    unlocks: list[ConceptUnlockEventResponse]
    total_unlocked: int = Field(ge=0)


class CoverageWithLockStatus(BaseModel):
    """Extended coverage summary with lock status counts."""
    model_config = ConfigDict(from_attributes=True)

    total_concepts: int = Field(ge=0)
    unlocked_concepts: int = Field(ge=0)
    locked_concepts: int = Field(ge=0)
    mastered: int = Field(ge=0)
    gaps: int = Field(ge=0)
    borderline: int = Field(ge=0)
    uncertain: int = Field(ge=0)
    coverage_percentage: float = Field(ge=0.0, le=1.0)
    unlock_percentage: float = Field(ge=0.0, le=1.0)


class OverrideAttemptResponse(BaseModel):
    """Response for override attempt on locked concept."""
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID
    concept_name: str
    was_locked: bool = Field(description="Whether concept was locked at time of attempt")
    override_allowed: bool = Field(
        default=True,
        description="Whether override is allowed (always True for now)"
    )
    blocking_prerequisites: list[BlockingPrerequisite] = Field(default_factory=list)
    mastery_progress: float = Field(ge=0.0, le=1.0)
    message: str = Field(description="User-friendly message about the attempt")
