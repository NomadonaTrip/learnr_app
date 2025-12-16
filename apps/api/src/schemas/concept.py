"""
Pydantic schemas for Concept model.
Handles validation and serialization for concept data.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ConceptBase(BaseModel):
    """Base schema with common concept fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Concept name")
    description: str | None = Field(None, description="1-2 sentence definition")
    corpus_section_ref: str | None = Field(
        None, max_length=50, description="Reference to source material section (e.g., '3.2.1')"
    )
    knowledge_area_id: str = Field(
        ..., max_length=50, description="Reference to course.knowledge_areas[].id"
    )
    difficulty_estimate: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Estimated difficulty (0.0 = foundational, 1.0 = advanced)",
    )
    prerequisite_depth: int = Field(
        default=0, ge=0, description="Distance from root concepts (0 = foundational)"
    )


class ConceptCreate(ConceptBase):
    """Schema for creating a new concept."""

    course_id: UUID = Field(..., description="UUID of the course this concept belongs to")

    @field_validator("difficulty_estimate")
    @classmethod
    def validate_difficulty(cls, v: float) -> float:
        """Ensure difficulty is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("difficulty_estimate must be between 0.0 and 1.0")
        return round(v, 2)  # Round to 2 decimal places


class ConceptUpdate(BaseModel):
    """Schema for updating an existing concept."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    corpus_section_ref: str | None = Field(None, max_length=50)
    knowledge_area_id: str | None = Field(None, max_length=50)
    difficulty_estimate: float | None = Field(None, ge=0.0, le=1.0)
    prerequisite_depth: int | None = Field(None, ge=0)


class ConceptResponse(ConceptBase):
    """Schema for concept response with all fields."""

    id: UUID
    course_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConceptExport(BaseModel):
    """Schema for CSV export to facilitate SME review."""

    id: UUID
    course_id: UUID
    name: str
    description: str | None
    corpus_section_ref: str | None
    knowledge_area_id: str
    difficulty_estimate: float
    prerequisite_depth: int

    model_config = {"from_attributes": True}


class ConceptCountByKA(BaseModel):
    """Schema for concept count grouped by knowledge area."""

    knowledge_area_id: str
    count: int


class ConceptSummary(BaseModel):
    """Schema for extraction summary statistics."""

    total_count: int
    counts_by_ka: dict[str, int]
    section_coverage_percent: float
    sections_without_concepts: list[str]


# ===== API Endpoint Schemas (Story 2.10) =====


class ConceptListParams(BaseModel):
    """Query parameters for listing concepts."""

    knowledge_area_id: str | None = Field(None, description="Filter by knowledge area")
    search: str | None = Field(None, description="Search by concept name")
    limit: int = Field(50, ge=1, le=200, description="Number of results to return")
    offset: int = Field(0, ge=0, description="Number of results to skip")


class PaginatedConceptResponse(BaseModel):
    """Paginated response for concept list."""

    items: list[ConceptResponse]
    total: int = Field(..., description="Total number of concepts matching filters")
    limit: int
    offset: int
    has_more: bool = Field(..., description="Whether there are more results")


class ConceptPrerequisitesResponse(BaseModel):
    """Response for concept prerequisites API endpoint (Story 2.10)."""

    concept_id: UUID
    prerequisites: list[ConceptResponse]
    depth: int = Field(..., description="Maximum depth in prerequisite chain")


class QuestionSummary(BaseModel):
    """Summary information for a question."""

    id: UUID
    question_text: str = Field(..., description="Truncated question text (first 100 chars)")
    difficulty: float = Field(..., ge=0.0, le=1.0)

    model_config = {"from_attributes": True}


class ConceptQuestionsResponse(BaseModel):
    """Response for concept questions endpoint."""

    concept_id: UUID
    question_count: int = Field(..., description="Total number of questions for this concept")
    sample_questions: list[QuestionSummary]


class ConceptStatsResponse(BaseModel):
    """Response for concept statistics endpoint."""

    course_id: UUID
    total_concepts: int
    by_knowledge_area: dict[str, int] = Field(..., description="Keyed by knowledge_area_id")
    by_depth: dict[int, int] = Field(..., description="Concepts grouped by prerequisite_depth")
    average_prerequisites_per_concept: float
    concepts_with_questions: int
    concepts_without_questions: int
