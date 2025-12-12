"""
Pydantic schemas for ConceptPrerequisite model.
Handles validation and serialization for prerequisite relationship data.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class RelationshipType(str, Enum):
    """Enum for prerequisite relationship types."""
    REQUIRED = "required"
    HELPFUL = "helpful"
    RELATED = "related"


class PrerequisiteBase(BaseModel):
    """Base schema with common prerequisite fields."""

    strength: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="How strongly required (0.0 = weak, 1.0 = must know first)"
    )
    relationship_type: RelationshipType = Field(
        default=RelationshipType.REQUIRED,
        description="Type of prerequisite relationship"
    )


class PrerequisiteCreate(PrerequisiteBase):
    """Schema for creating a new prerequisite relationship."""

    concept_id: UUID = Field(..., description="UUID of the concept that has this prerequisite")
    prerequisite_concept_id: UUID = Field(..., description="UUID of the prerequisite concept")

    @field_validator("strength")
    @classmethod
    def validate_strength(cls, v: float) -> float:
        """Ensure strength is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("strength must be between 0.0 and 1.0")
        return round(v, 2)

    @field_validator("prerequisite_concept_id")
    @classmethod
    def validate_no_self_loop(cls, v: UUID, info) -> UUID:
        """Ensure concept is not a prerequisite of itself."""
        if "concept_id" in info.data and info.data["concept_id"] == v:
            raise ValueError("A concept cannot be a prerequisite of itself")
        return v


class PrerequisiteResponse(PrerequisiteBase):
    """Schema for prerequisite response with all fields."""

    concept_id: UUID
    prerequisite_concept_id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class PrerequisiteWithConcept(BaseModel):
    """Schema for prerequisite with concept details."""

    concept_id: UUID
    concept_name: str
    knowledge_area_id: str
    difficulty_estimate: float
    prerequisite_depth: int
    strength: float
    relationship_type: RelationshipType

    model_config = {"from_attributes": True}


class PrerequisiteChainItem(BaseModel):
    """Single item in a prerequisite chain."""

    concept_id: UUID
    concept_name: str
    knowledge_area_id: str
    depth: int = Field(..., description="Distance from target concept (0 = direct prerequisite)")
    strength: float
    relationship_type: RelationshipType


class PrerequisiteChainResponse(BaseModel):
    """Schema for full prerequisite chain response."""

    target_concept_id: UUID
    target_concept_name: str
    chain: list[PrerequisiteChainItem]
    total_depth: int = Field(..., description="Maximum depth in the chain")


class PrerequisiteBulkCreate(BaseModel):
    """Schema for bulk creating prerequisites."""

    prerequisites: list[PrerequisiteCreate]


class PrerequisiteBulkResult(BaseModel):
    """Schema for bulk create result."""

    created_count: int
    skipped_count: int = Field(
        default=0,
        description="Count of prerequisites skipped (duplicates or invalid)"
    )
    errors: list[str] = Field(
        default_factory=list,
        description="Error messages for failed inserts"
    )


class RootConceptResponse(BaseModel):
    """Schema for concepts with no prerequisites (foundational)."""

    id: UUID
    name: str
    knowledge_area_id: str
    difficulty_estimate: float
    dependent_count: int = Field(..., description="Number of concepts that depend on this one")

    model_config = {"from_attributes": True}
