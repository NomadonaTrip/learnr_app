"""
Pydantic schemas for Coverage Progress Tracking (Story 4.5).
Handles validation and serialization for coverage analysis data.
"""
from uuid import UUID

from pydantic import BaseModel, Field

from .belief_state import BeliefStatus


class ConceptStatus(BaseModel):
    """Individual concept coverage status."""

    concept_id: UUID = Field(..., description="UUID of the concept")
    concept_name: str = Field(..., description="Name of the concept")
    knowledge_area_id: str = Field(..., description="Knowledge area ID")
    status: BeliefStatus = Field(..., description="Classification status")
    probability: float = Field(
        ...,
        ge=0,
        le=1,
        description="Mean mastery probability (alpha / (alpha + beta))"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence level ((alpha + beta) / (alpha + beta + 2))"
    )
    is_locked: bool = Field(
        default=False,
        description="Whether concept is locked due to unmastered prerequisites"
    )


class KnowledgeAreaCoverage(BaseModel):
    """Coverage breakdown for a single knowledge area."""

    ka_id: str = Field(..., description="Knowledge area ID")
    ka_name: str = Field(..., description="Knowledge area display name")
    total_concepts: int = Field(..., ge=0, description="Total concepts in this KA")
    mastered_count: int = Field(..., ge=0, description="Concepts with mastered status")
    gap_count: int = Field(..., ge=0, description="Concepts with gap status")
    borderline_count: int = Field(..., ge=0, description="Concepts with borderline status")
    uncertain_count: int = Field(..., ge=0, description="Concepts with uncertain status")
    locked_count: int = Field(
        default=0,
        ge=0,
        description="Concepts locked due to unmastered prerequisites"
    )
    unlocked_count: int = Field(
        default=0,
        ge=0,
        description="Concepts unlocked (prerequisites mastered or no prerequisites)"
    )
    readiness_score: float = Field(
        ...,
        ge=0,
        le=1,
        description="KA readiness: mastered_count / total_concepts"
    )


class CoverageSummary(BaseModel):
    """Summary of coverage metrics."""

    total_concepts: int = Field(..., ge=0, description="Total concepts in corpus")
    mastered: int = Field(..., ge=0, description="Count of mastered concepts")
    gaps: int = Field(..., ge=0, description="Count of gap concepts")
    borderline: int = Field(..., ge=0, description="Count of borderline concepts")
    uncertain: int = Field(..., ge=0, description="Count of uncertain concepts")
    locked_concepts: int = Field(
        default=0,
        ge=0,
        description="Count of concepts locked due to unmastered prerequisites"
    )
    unlocked_concepts: int = Field(
        default=0,
        ge=0,
        description="Count of unlocked concepts (prerequisites mastered)"
    )
    coverage_percentage: float = Field(
        ...,
        ge=0,
        le=1,
        description="Mastery coverage: mastered / total_concepts"
    )
    confidence_percentage: float = Field(
        ...,
        ge=0,
        le=1,
        description="Classification coverage: (mastered + gaps + borderline) / total_concepts"
    )
    estimated_questions_remaining: int = Field(
        ...,
        ge=0,
        description="Estimated questions needed to resolve uncertain concepts"
    )


class CoverageReport(CoverageSummary):
    """Full coverage report with knowledge area breakdown."""

    by_knowledge_area: list[KnowledgeAreaCoverage] = Field(
        default_factory=list,
        description="Coverage breakdown by knowledge area"
    )


class CoverageDetailReport(CoverageReport):
    """Detailed coverage report with concept lists (for debugging/analytics)."""

    mastered_concepts: list[ConceptStatus] = Field(
        default_factory=list,
        description="List of mastered concepts"
    )
    gap_concepts: list[ConceptStatus] = Field(
        default_factory=list,
        description="List of gap concepts"
    )
    borderline_concepts: list[ConceptStatus] = Field(
        default_factory=list,
        description="List of borderline concepts"
    )
    uncertain_concepts: list[ConceptStatus] = Field(
        default_factory=list,
        description="List of uncertain concepts"
    )


class GapConcept(BaseModel):
    """Single gap concept for prioritized practice."""

    concept_id: UUID = Field(..., description="UUID of the concept")
    concept_name: str = Field(..., description="Name of the concept")
    knowledge_area_id: str = Field(..., description="Knowledge area ID")
    probability: float = Field(
        ...,
        ge=0,
        le=1,
        description="Mean mastery probability (lower = worse gap)"
    )
    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence level"
    )


class GapConceptList(BaseModel):
    """List of gap concepts for focused practice mode."""

    total_gaps: int = Field(..., ge=0, description="Total number of gap concepts")
    gaps: list[GapConcept] = Field(
        default_factory=list,
        description="Gap concepts sorted by probability ascending (worst first)"
    )
