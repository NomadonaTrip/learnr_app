"""
Review Session Pydantic schemas for request/response validation.
Story 4.9: Post-Session Review Mode
"""
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReviewAvailableResponse(BaseModel):
    """Response for checking if review is available for a session."""

    available: bool = Field(
        ...,
        description="Whether review is available (has incorrect answers)"
    )
    incorrect_count: int = Field(
        ...,
        ge=0,
        description="Number of incorrect answers to review"
    )
    question_ids: list[str] = Field(
        default_factory=list,
        description="List of question UUIDs to review"
    )


class ReviewSessionResponse(BaseModel):
    """Response schema for review session details."""

    id: str = Field(..., description="Review session UUID")
    original_session_id: str = Field(..., description="Original quiz session UUID")
    status: str = Field(..., description="Session status: pending, in_progress, completed, skipped")
    total_to_review: int = Field(..., ge=0, description="Total questions to review")
    reviewed_count: int = Field(..., ge=0, description="Questions reviewed so far")
    reinforced_count: int = Field(..., ge=0, description="Questions reinforced (incorrect→correct)")
    still_incorrect_count: int = Field(..., ge=0, description="Questions still incorrect")
    started_at: datetime | None = Field(None, description="When review started")
    created_at: datetime = Field(..., description="When review session was created")


class ReviewQuestionResponse(BaseModel):
    """Response schema for a review question (without correct answer)."""

    question_id: str = Field(..., description="Question UUID")
    question_text: str = Field(..., description="The question text")
    options: dict[str, str] = Field(
        ...,
        description="Answer options map: {'A': '...', 'B': '...', 'C': '...', 'D': '...'}"
    )
    review_number: int = Field(..., ge=1, description="Current review number (1-indexed)")
    total_to_review: int = Field(..., ge=1, description="Total questions to review")


class ReviewAnswerSubmission(BaseModel):
    """Request schema for submitting a review answer."""

    question_id: str = Field(..., description="Question UUID being answered")
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
    """Schema for concept update in review answer response."""

    concept_id: str = Field(..., description="Concept UUID")
    name: str = Field(..., description="Concept name")
    new_mastery: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="New mastery level (0.0-1.0)"
    )


class ReviewAnswerResponse(BaseModel):
    """Response schema after submitting a review answer."""

    is_correct: bool = Field(..., description="Whether the answer was correct")
    was_reinforced: bool = Field(
        ...,
        description="Whether this was a reinforcement (incorrect→correct)"
    )
    correct_answer: str = Field(..., description="The correct answer option (A, B, C, or D)")
    explanation: str = Field(..., description="Explanation of the correct answer")
    concepts_updated: list[dict[str, Any]] = Field(
        default_factory=list,
        description="List of concepts with updated mastery levels"
    )
    feedback_message: str = Field(
        ...,
        description="Feedback message: 'Great improvement!' or 'Still needs practice...'"
    )
    reading_link: str | None = Field(
        None,
        description="Link to reading material for this concept"
    )


class StillIncorrectConcept(BaseModel):
    """Schema for concepts that were still incorrect after review."""

    concept_id: str = Field(..., description="Concept UUID")
    name: str = Field(..., description="Concept name")
    reading_link: str = Field(
        ...,
        description="Link to reading library filtered by this concept"
    )


class ReviewSummaryResponse(BaseModel):
    """Response schema for review session summary."""

    total_reviewed: int = Field(..., ge=0, description="Total questions reviewed")
    reinforced_count: int = Field(..., ge=0, description="Questions reinforced (incorrect→correct)")
    still_incorrect_count: int = Field(..., ge=0, description="Questions still incorrect")
    reinforcement_rate: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Reinforcement rate (0.0-1.0)"
    )
    still_incorrect_concepts: list[StillIncorrectConcept] = Field(
        default_factory=list,
        description="Concepts that were still incorrect, with study links"
    )


class ReviewSkipResponse(BaseModel):
    """Response schema for skipping a review session."""

    message: str = Field(..., description="Confirmation message")
    session_id: str = Field(..., description="Review session UUID")
    questions_skipped: int = Field(..., ge=0, description="Number of questions skipped")
