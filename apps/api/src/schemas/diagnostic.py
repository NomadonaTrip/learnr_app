"""
Diagnostic Pydantic schemas for request/response validation.
Used for diagnostic assessment question selection API.
"""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

AnswerLetter = Literal["A", "B", "C", "D"]


class DiagnosticAnswerRequest(BaseModel):
    """Request body for submitting a diagnostic answer."""
    question_id: UUID = Field(..., description="UUID of the question being answered")
    selected_answer: AnswerLetter = Field(..., description="Selected answer letter (A/B/C/D)")


class DiagnosticAnswerResponse(BaseModel):
    """Response from submitting a diagnostic answer."""
    is_recorded: bool = Field(..., description="Whether the answer was successfully recorded")
    concepts_updated: list[str] = Field(
        default_factory=list,
        description="List of concept IDs updated by this answer"
    )
    diagnostic_progress: int = Field(..., description="Current progress (answers submitted)")
    diagnostic_total: int = Field(..., description="Total questions in diagnostic")


class DiagnosticQuestionResponse(BaseModel):
    """
    Schema for diagnostic question response.

    Excludes correct_answer and explanation to prevent cheating during diagnostic.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(..., description="Question UUID")
    question_text: str = Field(..., description="Question text")
    options: dict[str, str] = Field(
        ...,
        description="Answer options as {A: text, B: text, C: text, D: text}"
    )
    knowledge_area_id: str = Field(..., description="Knowledge area ID")
    difficulty: float = Field(..., ge=0.0, le=1.0, description="IRT difficulty (0.0-1.0)")
    discrimination: float = Field(..., ge=0.0, description="IRT discrimination parameter")


class DiagnosticQuestionsResponse(BaseModel):
    """
    Schema for diagnostic questions API response.

    Contains the selected questions and coverage statistics.
    """
    questions: list[DiagnosticQuestionResponse] = Field(
        ...,
        description="Selected diagnostic questions"
    )
    total: int = Field(..., description="Total number of questions selected")
    concepts_covered: int = Field(..., description="Number of unique concepts covered")
    coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Percentage of course concepts covered (0.0-1.0)"
    )
