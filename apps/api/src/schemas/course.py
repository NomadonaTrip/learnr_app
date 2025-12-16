"""
Pydantic schemas for Course API responses.
"""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeArea(BaseModel):
    """Schema for knowledge area within a course."""
    id: str = Field(..., description="Knowledge area identifier (e.g., 'ba-planning')")
    name: str = Field(..., description="Full name of the knowledge area")
    short_name: str = Field(..., description="Short display name")
    display_order: int = Field(..., description="Order for display purposes")
    color: str = Field(..., description="Hex color code for UI (e.g., '#3B82F6')")


class CourseBase(BaseModel):
    """Base schema for course data."""
    slug: str = Field(..., description="URL-friendly identifier")
    name: str = Field(..., description="Course display name")
    description: str | None = Field(None, description="Course description")
    corpus_name: str | None = Field(None, description="Reference corpus name (e.g., 'BABOK v3')")


class CourseResponse(CourseBase):
    """Full course response with all details."""
    id: UUID = Field(..., description="Course UUID")
    knowledge_areas: list[KnowledgeArea] = Field(..., description="List of knowledge areas")
    default_diagnostic_count: int = Field(..., description="Default number of diagnostic questions")
    mastery_threshold: float = Field(..., description="Threshold for mastery (0.0-1.0)")
    gap_threshold: float = Field(..., description="Threshold for knowledge gap (0.0-1.0)")
    confidence_threshold: float = Field(..., description="Threshold for confidence (0.0-1.0)")
    icon_url: str | None = Field(None, description="URL to course icon")
    color_hex: str | None = Field(None, description="Hex color for course branding")
    is_active: bool = Field(..., description="Whether course is active")
    is_public: bool = Field(..., description="Whether course is publicly visible")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class CourseListItem(BaseModel):
    """Abbreviated course data for list responses."""
    id: UUID = Field(..., description="Course UUID")
    slug: str = Field(..., description="URL-friendly identifier")
    name: str = Field(..., description="Course display name")
    description: str | None = Field(None, description="Course description")
    corpus_name: str | None = Field(None, description="Reference corpus name")
    icon_url: str | None = Field(None, description="URL to course icon")
    color_hex: str | None = Field(None, description="Hex color for course branding")
    knowledge_area_count: int = Field(..., description="Number of knowledge areas")

    model_config = {"from_attributes": True}


class CourseListResponse(BaseModel):
    """Response for listing courses."""
    data: list[CourseListItem] = Field(..., description="List of courses")
    meta: dict = Field(default_factory=dict, description="Response metadata")


class CourseDetailResponse(BaseModel):
    """Response for single course details."""
    data: CourseResponse = Field(..., description="Course details")
    meta: dict = Field(default_factory=dict, description="Response metadata")
