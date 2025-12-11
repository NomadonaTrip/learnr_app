"""
Pydantic schemas for ReadingChunk model.
Handles validation and serialization for reading chunk data.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ChunkBase(BaseModel):
    """Base schema with common reading chunk fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Chunk title")
    content: str = Field(..., min_length=1, description="Chunk content text")
    corpus_section: str = Field(
        ..., max_length=50, description="Reference to source section (e.g., '3.2.1')"
    )
    knowledge_area_id: str = Field(
        ..., max_length=50, description="Reference to course.knowledge_areas[].id"
    )
    concept_ids: List[UUID] = Field(
        default_factory=list, description="UUIDs of concepts this chunk is linked to"
    )
    estimated_read_time_minutes: int = Field(
        default=5, ge=1, description="Estimated reading time in minutes"
    )
    chunk_index: int = Field(
        default=0, ge=0, description="Order within section (0-indexed)"
    )


class ChunkCreate(ChunkBase):
    """Schema for creating a new reading chunk."""

    course_id: UUID = Field(..., description="UUID of the course this chunk belongs to")

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Ensure title is not empty after stripping whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("title cannot be empty or whitespace")
        return v

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Ensure content is not empty after stripping whitespace."""
        v = v.strip()
        if not v:
            raise ValueError("content cannot be empty or whitespace")
        return v


class ChunkUpdate(BaseModel):
    """Schema for updating an existing reading chunk."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    corpus_section: Optional[str] = Field(None, max_length=50)
    knowledge_area_id: Optional[str] = Field(None, max_length=50)
    concept_ids: Optional[List[UUID]] = None
    estimated_read_time_minutes: Optional[int] = Field(None, ge=1)
    chunk_index: Optional[int] = Field(None, ge=0)


class ChunkResponse(ChunkBase):
    """Schema for reading chunk response with all fields."""

    id: UUID
    course_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChunkExport(BaseModel):
    """Schema for CSV export to facilitate SME review."""

    id: UUID
    course_id: UUID
    title: str
    corpus_section: str
    knowledge_area_id: str
    concept_count: int = Field(..., description="Number of linked concepts")
    concept_names: str = Field(..., description="Comma-separated concept names")
    content_preview: str = Field(..., description="First 100 characters of content")
    estimated_read_time_minutes: int

    model_config = {"from_attributes": True}


class ChunkCountByKA(BaseModel):
    """Schema for chunk count grouped by knowledge area."""

    knowledge_area_id: str
    count: int


class ChunkValidationReport(BaseModel):
    """Schema for chunk validation statistics."""

    total_chunks: int
    chunks_per_ka: dict[str, int]
    chunks_without_concepts: int
    orphan_chunk_ids: List[UUID]
    average_concepts_per_chunk: float
    chunks_below_min_tokens: int
    chunks_above_max_tokens: int
    validation_passed: bool
    errors: List[str]


class ReadingChunkResponse(BaseModel):
    """Schema for reading chunk in API retrieval responses."""

    id: UUID
    course_id: UUID
    title: str
    content: str
    corpus_section: str
    knowledge_area_id: str
    concept_ids: List[UUID]
    concept_names: List[str] = Field(
        default_factory=list, description="Human-readable concept names"
    )
    estimated_read_time_minutes: int
    relevance_score: Optional[float] = Field(
        None, description="Relevance score for ranking (number of matching concepts)"
    )

    model_config = {"from_attributes": True}


class ReadingQueryParams(BaseModel):
    """Schema for reading retrieval query parameters."""

    concept_ids: List[UUID] = Field(..., description="Concepts to find reading for")
    knowledge_area_id: Optional[str] = Field(
        None, description="Filter by knowledge area"
    )
    limit: int = Field(5, ge=1, le=20, description="Maximum number of chunks to return")


class ReadingListResponse(BaseModel):
    """Schema for paginated reading chunk list response."""

    items: List[ReadingChunkResponse]
    total: int = Field(..., description="Total number of matching chunks")
    fallback_used: bool = Field(
        False, description="True if semantic search fallback was used"
    )
