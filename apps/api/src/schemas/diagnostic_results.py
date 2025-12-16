"""
Diagnostic Results Pydantic schemas for response validation.
Used for diagnostic results API after completing diagnostic assessment.
"""
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class KnowledgeAreaResult(BaseModel):
    """Per-knowledge area statistics for diagnostic results."""
    model_config = ConfigDict(from_attributes=True)

    ka: str = Field(..., description="Full name of the knowledge area")
    ka_id: str = Field(..., description="Knowledge area slug identifier")
    concepts: int = Field(..., ge=0, description="Total concepts in this KA")
    touched: int = Field(..., ge=0, description="Concepts with response_count > 0")
    estimated_mastery: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Average mean value for touched concepts (0.0-1.0)"
    )


class ConceptGap(BaseModel):
    """Identified gap concept with low mastery probability."""
    model_config = ConfigDict(from_attributes=True)

    concept_id: UUID = Field(..., description="Concept UUID")
    name: str = Field(..., description="Concept name")
    mastery_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Mean mastery probability (0.0-1.0)"
    )
    knowledge_area: str = Field(..., description="Knowledge area name for display")


class Recommendations(BaseModel):
    """Actionable recommendations based on diagnostic results."""
    primary_focus: str = Field(..., description="KA name to focus on")
    estimated_questions_to_coverage: int = Field(
        ...,
        ge=0,
        description="Estimated questions to reach good coverage"
    )
    message: str = Field(..., description="Contextual encouragement message")


ConfidenceLevel = Literal["initial", "developing", "established"]


class DiagnosticScore(BaseModel):
    """Diagnostic test score summary."""
    model_config = ConfigDict(from_attributes=True)

    questions_answered: int = Field(..., ge=0, description="Number of questions answered")
    questions_correct: int = Field(..., ge=0, description="Number of correct answers")
    questions_incorrect: int = Field(..., ge=0, description="Number of incorrect answers")
    score_percentage: float = Field(
        ...,
        ge=0.0,
        le=100.0,
        description="Score as percentage (0-100)"
    )


class DiagnosticResultsResponse(BaseModel):
    """
    Complete diagnostic results response after assessment completion.

    Provides comprehensive view of user's knowledge profile including:
    - Diagnostic score (correct/incorrect counts)
    - Overall coverage statistics
    - Per-knowledge area breakdown
    - Top identified gaps
    - Personalized recommendations
    """
    model_config = ConfigDict(from_attributes=True)

    # Diagnostic score
    score: DiagnosticScore = Field(..., description="Diagnostic test score summary")

    total_concepts: int = Field(..., ge=0, description="Total concepts in course")
    concepts_touched: int = Field(
        ...,
        ge=0,
        description="Concepts with at least one response"
    )
    coverage_percentage: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Ratio of touched/total concepts"
    )
    estimated_mastered: int = Field(
        ...,
        ge=0,
        description="Concepts with mean >= 0.8 and confidence >= 0.7"
    )
    estimated_gaps: int = Field(
        ...,
        ge=0,
        description="Concepts with mean < 0.5 and confidence >= 0.7"
    )
    uncertain: int = Field(
        ...,
        ge=0,
        description="Concepts with confidence < 0.7"
    )
    confidence_level: ConfidenceLevel = Field(
        ...,
        description="Overall profile confidence: initial (<30%), developing (30-70%), established (>70%)"
    )
    by_knowledge_area: list[KnowledgeAreaResult] = Field(
        ...,
        description="Statistics per knowledge area"
    )
    top_gaps: list[ConceptGap] = Field(
        ...,
        description="Top 10 concepts with lowest mastery probability"
    )
    recommendations: Recommendations = Field(
        ...,
        description="Personalized recommendations for next steps"
    )


class DiagnosticFeedbackRequest(BaseModel):
    """Request body for submitting diagnostic feedback survey."""
    rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="User's accuracy rating 1-5"
    )
    comment: str | None = Field(
        None,
        max_length=500,
        description="Optional feedback comment"
    )


class DiagnosticFeedbackResponse(BaseModel):
    """Response from submitting diagnostic feedback."""
    success: bool = Field(..., description="Whether feedback was recorded")
    message: str = Field(..., description="Confirmation message")
