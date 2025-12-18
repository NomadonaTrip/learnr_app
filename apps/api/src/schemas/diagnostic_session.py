"""
Diagnostic Session Pydantic schemas for request/response validation.
Used for diagnostic session management API.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class DiagnosticSessionStatus(str, Enum):
    """Status values for diagnostic sessions."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    EXPIRED = "expired"
    RESET = "reset"


class DiagnosticSessionCreate(BaseModel):
    """Schema for creating a diagnostic session (internal use)."""

    enrollment_id: UUID = Field(..., description="Enrollment UUID")
    question_ids: list[UUID] = Field(..., description="List of question UUIDs in order")


class DiagnosticSessionResponse(BaseModel):
    """Response schema for diagnostic session status."""

    id: UUID = Field(..., description="Session UUID")
    user_id: UUID = Field(..., description="User UUID")
    enrollment_id: UUID = Field(..., description="Enrollment UUID")
    current_index: int = Field(..., description="Current question index (0-based)")
    status: DiagnosticSessionStatus = Field(..., description="Session status")
    started_at: datetime = Field(..., description="Session start timestamp")
    completed_at: datetime | None = Field(None, description="Session completion timestamp")
    questions_total: int = Field(..., description="Total number of questions")
    questions_remaining: int = Field(..., description="Number of questions remaining")


class DiagnosticResetRequest(BaseModel):
    """Request body for resetting diagnostic session."""

    confirmation: str = Field(
        ...,
        description="Must be 'RESET DIAGNOSTIC' to confirm reset"
    )


class DiagnosticResetResponse(BaseModel):
    """Response from resetting diagnostic session."""

    message: str = Field(..., description="Confirmation message")
    session_cleared: bool = Field(..., description="Whether an active session was cleared")
    beliefs_reset_count: int = Field(..., description="Number of belief states reset")
    can_retake: bool = Field(default=True, description="Whether user can retake diagnostic")
