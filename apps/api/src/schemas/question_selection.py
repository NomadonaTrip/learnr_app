"""
Pydantic schemas for question selection API.
Defines request/response models for the next-question endpoint.
Story 4.7: Added progress indicator fields.
"""
from uuid import UUID

from pydantic import BaseModel, Field


class QuestionSelectionRequest(BaseModel):
    """Request body for next question selection."""

    session_id: UUID = Field(..., description="Quiz session ID")
    strategy: str = Field(
        default="max_info_gain",
        description="Question selection strategy",
        pattern="^(max_info_gain|max_uncertainty|prerequisite_first|balanced)$",
    )


class SelectedQuestion(BaseModel):
    """
    Selected question for quiz display.

    Note: Does NOT include correct_answer or explanation.
    Those are revealed only after answer submission (Story 4.3).
    """

    question_id: UUID = Field(..., description="Question UUID")
    question_text: str = Field(..., description="The question text")
    options: dict[str, str] = Field(
        ...,
        description="Answer options keyed by letter (A, B, C, D)",
        examples=[{
            "A": "Interviews",
            "B": "Surveys",
            "C": "Workshops",
            "D": "Document Analysis"
        }],
    )
    knowledge_area_id: str = Field(..., description="Knowledge area ID")
    knowledge_area_name: str | None = Field(
        None, description="Human-readable knowledge area name"
    )
    difficulty: float = Field(
        ..., ge=-3.0, le=3.0, description="IRT difficulty b-parameter (-3.0 to +3.0)"
    )
    estimated_info_gain: float = Field(
        ..., description="Selection metric (info gain or entropy depending on strategy)"
    )
    concepts_tested: list[str] = Field(
        default_factory=list,
        description="Concept names tested by this question (for debug/analytics)",
    )


class QuestionSelectionResponse(BaseModel):
    """Response from next-question endpoint."""

    session_id: UUID = Field(..., description="Quiz session ID")
    question: SelectedQuestion = Field(..., description="Selected question details")
    questions_remaining: int = Field(
        ..., ge=0, description="Estimate of available questions remaining"
    )
    # Story 4.7: Progress indicator fields
    current_question_number: int = Field(
        ..., ge=1, description="Current question number (1-indexed, e.g., 8 of 12)"
    )
    question_target: int = Field(
        ..., ge=1, description="Target number of questions for this session (e.g., 12)"
    )
    progress_percentage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Session progress as fraction (0.0-1.0), e.g., 0.667 for 8/12",
    )


class NoQuestionsAvailableResponse(BaseModel):
    """Response when no questions are available for selection."""

    session_id: UUID = Field(..., description="Quiz session ID")
    message: str = Field(
        default="No questions available",
        description="Explanation of why no questions are available",
    )
    reason: str = Field(
        ...,
        description="Machine-readable reason code",
        examples=["exhausted", "knowledge_area_empty", "all_recent"],
    )
