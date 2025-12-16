"""
Pydantic schemas for Enrollment API responses.
"""
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EnrollmentBase(BaseModel):
    """Base schema for enrollment data."""
    exam_date: date | None = Field(None, description="Target exam date")
    target_score: int | None = Field(None, ge=0, le=100, description="Target score percentage")
    daily_study_time: int | None = Field(None, ge=0, description="Daily study time in minutes")


class EnrollmentCreate(EnrollmentBase):
    """Schema for creating a new enrollment."""
    course_id: UUID = Field(..., description="Course UUID to enroll in")


class EnrollmentResponse(EnrollmentBase):
    """Full enrollment response."""
    id: UUID = Field(..., description="Enrollment UUID")
    user_id: UUID = Field(..., description="User UUID")
    course_id: UUID = Field(..., description="Course UUID")
    enrolled_at: datetime = Field(..., description="Enrollment timestamp")
    last_activity_at: datetime | None = Field(None, description="Last activity timestamp")
    status: str = Field(..., description="Enrollment status (active, paused, completed, archived)")
    completion_percentage: float = Field(..., ge=0, le=100, description="Course completion percentage")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")

    model_config = {"from_attributes": True}


class EnrollmentWithCourse(EnrollmentResponse):
    """Enrollment response including course details."""
    course_slug: str = Field(..., description="Course slug")
    course_name: str = Field(..., description="Course name")
