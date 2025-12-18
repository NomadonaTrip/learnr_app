"""
Quiz Answer Submission Pydantic schemas for request/response validation.
Story 4.3: Answer Submission and Immediate Feedback
"""
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class AnswerSubmission(BaseModel):
    """Request schema for submitting an answer to a quiz question."""

    session_id: UUID = Field(..., description="Quiz session UUID")
    question_id: UUID = Field(..., description="Question UUID being answered")
    selected_answer: str = Field(
        ...,
        description="Selected answer option (A, B, C, or D)",
        min_length=1,
        max_length=1,
    )

    @field_validator("selected_answer")
    @classmethod
    def validate_answer(cls, v: str) -> str:
        """Validate that selected_answer is A, B, C, or D."""
        v = v.upper()
        if v not in ("A", "B", "C", "D"):
            raise ValueError("selected_answer must be A, B, C, or D")
        return v


class ConceptUpdate(BaseModel):
    """Schema for concept mastery updates after an answer."""

    concept_id: UUID = Field(..., description="Concept UUID")
    name: str = Field(..., description="Concept name")
    new_mastery: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="New mastery level (0.0-1.0)"
    )


class SessionStats(BaseModel):
    """Schema for session statistics in answer response."""

    questions_answered: int = Field(..., ge=0, description="Total questions answered in session")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Session accuracy (0.0-1.0)"
    )
    total_info_gain: float = Field(
        default=0.0,
        ge=0.0,
        description="Total information gain from session"
    )
    coverage_progress: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Progress through concept coverage (0.0-1.0)"
    )


class AnswerResponse(BaseModel):
    """Response schema after submitting an answer."""

    is_correct: bool = Field(..., description="Whether the answer was correct")
    correct_answer: str = Field(
        ...,
        description="The correct answer option (A, B, C, or D)"
    )
    explanation: str = Field(..., description="Explanation of the correct answer")
    concepts_updated: list[ConceptUpdate] = Field(
        default_factory=list,
        description="List of concepts with updated mastery levels"
    )
    session_stats: SessionStats = Field(
        ...,
        description="Current session statistics"
    )


class CachedAnswerResponse(BaseModel):
    """
    Extended response for cached/idempotent responses.
    Includes all AnswerResponse fields plus caching metadata.
    """

    is_correct: bool = Field(..., description="Whether the answer was correct")
    correct_answer: str = Field(
        ...,
        description="The correct answer option (A, B, C, or D)"
    )
    explanation: str = Field(..., description="Explanation of the correct answer")
    concepts_updated: list[ConceptUpdate] = Field(
        default_factory=list,
        description="List of concepts with updated mastery levels"
    )
    session_stats: SessionStats = Field(
        ...,
        description="Current session statistics"
    )
    cached: bool = Field(
        default=False,
        description="Whether this response was served from cache"
    )
