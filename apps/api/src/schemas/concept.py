"""
Pydantic schemas for Concept model.
Handles validation and serialization for concept data.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ConceptBase(BaseModel):
    """Base schema with common concept fields."""

    name: str = Field(..., min_length=1, max_length=255, description="Concept name")
    description: Optional[str] = Field(None, description="1-2 sentence definition")
    corpus_section_ref: Optional[str] = Field(
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

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    corpus_section_ref: Optional[str] = Field(None, max_length=50)
    knowledge_area_id: Optional[str] = Field(None, max_length=50)
    difficulty_estimate: Optional[float] = Field(None, ge=0.0, le=1.0)
    prerequisite_depth: Optional[int] = Field(None, ge=0)


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
    description: Optional[str]
    corpus_section_ref: Optional[str]
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
