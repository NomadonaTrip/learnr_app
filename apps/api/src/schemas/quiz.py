"""
Quiz Answer Submission Pydantic schemas for request/response validation.
Story 4.3: Answer Submission and Immediate Feedback
Story 4.7: Fixed-Length Session Auto-Completion
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


class ConceptMasteryUpdate(BaseModel):
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
    session_version: int = Field(
        ...,
        ge=1,
        description="Current session version for optimistic locking"
    )


class SessionSummaryResponse(BaseModel):
    """
    Session summary returned when quiz auto-completes.
    Story 4.7: Fixed-Length Session Auto-Completion
    """

    questions_answered: int = Field(..., ge=0, description="Total questions answered (e.g., 12)")
    question_target: int = Field(..., ge=1, description="Target questions for session (e.g., 12)")
    correct_count: int = Field(..., ge=0, description="Number of correct answers")
    accuracy: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Session accuracy as percentage (0.0-100.0)"
    )
    concepts_strengthened: int = Field(
        ...,
        ge=0,
        description="Count of concepts with belief updates during session"
    )
    quizzes_completed_total: int = Field(
        ...,
        ge=0,
        description="User's lifetime total of completed quizzes"
    )
    session_duration_seconds: int = Field(
        ...,
        ge=0,
        description="Duration of the session in seconds"
    )


class AnswerResponse(BaseModel):
    """Response schema after submitting an answer."""

    is_correct: bool = Field(..., description="Whether the answer was correct")
    correct_answer: str = Field(
        ...,
        description="The correct answer option (A, B, C, or D)"
    )
    explanation: str = Field(..., description="Explanation of the correct answer")
    concepts_updated: list[ConceptMasteryUpdate] = Field(
        default_factory=list,
        description="List of concepts with updated mastery levels"
    )
    session_stats: SessionStats = Field(
        ...,
        description="Current session statistics"
    )
    # Story 4.7: Auto-completion fields
    session_completed: bool = Field(
        default=False,
        description="Whether session auto-completed (questions_answered == question_target)"
    )
    session_summary: SessionSummaryResponse | None = Field(
        default=None,
        description="Session summary when session_completed is True"
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
    concepts_updated: list[ConceptMasteryUpdate] = Field(
        default_factory=list,
        description="List of concepts with updated mastery levels"
    )
    session_stats: SessionStats = Field(
        ...,
        description="Current session statistics"
    )
    # Story 4.7: Auto-completion fields
    session_completed: bool = Field(
        default=False,
        description="Whether session auto-completed (questions_answered == question_target)"
    )
    session_summary: SessionSummaryResponse | None = Field(
        default=None,
        description="Session summary when session_completed is True"
    )
    cached: bool = Field(
        default=False,
        description="Whether this response was served from cache"
    )
