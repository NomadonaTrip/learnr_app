"""
Quiz Session Pydantic schemas for request/response validation.
Used for adaptive quiz session management API.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class QuizSessionType(str, Enum):
    """Types of quiz sessions."""

    DIAGNOSTIC = "diagnostic"
    ADAPTIVE = "adaptive"
    FOCUSED = "focused"  # Generic focused (existing, kept for backward compatibility)
    FOCUSED_KA = "focused_ka"  # Focused on knowledge area
    FOCUSED_CONCEPT = "focused_concept"  # Focused on specific concepts
    REVIEW = "review"


class QuestionStrategy(str, Enum):
    """Question selection strategies for adaptive sessions."""

    MAX_INFO_GAIN = "max_info_gain"
    MAX_UNCERTAINTY = "max_uncertainty"
    PREREQUISITE_FIRST = "prerequisite_first"
    BALANCED = "balanced"


class QuizSessionStatus(str, Enum):
    """Derived status values for quiz sessions."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    EXPIRED = "expired"


class QuizSessionCreate(BaseModel):
    """Request schema for creating/starting a quiz session."""

    session_type: QuizSessionType = Field(
        default=QuizSessionType.ADAPTIVE,
        description="Type of quiz session"
    )
    question_strategy: QuestionStrategy = Field(
        default=QuestionStrategy.MAX_INFO_GAIN,
        description="Strategy for question selection"
    )
    knowledge_area_filter: str | None = Field(
        default=None,
        description="Optional knowledge area to focus on (for focused/focused_ka sessions)"
    )
    target_concept_ids: list[UUID] | None = Field(
        default=None,
        description="Target concept IDs for focused_concept sessions"
    )

    @model_validator(mode="after")
    def validate_focused_targets(self) -> "QuizSessionCreate":
        """Validate that focused session types have required target fields."""
        if self.session_type == QuizSessionType.FOCUSED_KA:
            if not self.knowledge_area_filter:
                raise ValueError("knowledge_area_filter required for focused_ka sessions")
        if self.session_type == QuizSessionType.FOCUSED_CONCEPT:
            if not self.target_concept_ids or len(self.target_concept_ids) == 0:
                raise ValueError("target_concept_ids required for focused_concept sessions")
        return self


class QuizSessionResponse(BaseModel):
    """Response schema for quiz session details."""

    id: UUID = Field(..., description="Session UUID")
    user_id: UUID = Field(..., description="User UUID")
    enrollment_id: UUID = Field(..., description="Enrollment UUID")
    session_type: QuizSessionType = Field(..., description="Type of quiz session")
    question_strategy: QuestionStrategy = Field(..., description="Question selection strategy")
    knowledge_area_filter: str | None = Field(None, description="Knowledge area filter if set")
    question_target: int = Field(..., description="Target number of questions for this session, configurable default 10")
    status: QuizSessionStatus = Field(..., description="Current session status (derived)")
    started_at: datetime = Field(..., description="Session start timestamp")
    ended_at: datetime | None = Field(None, description="Session end timestamp")
    total_questions: int = Field(..., description="Total questions answered")
    correct_count: int = Field(..., description="Number of correct answers")
    accuracy: float = Field(..., description="Session accuracy percentage (0-100)")
    is_paused: bool = Field(..., description="Whether session is currently paused")
    version: int = Field(..., description="Optimistic lock version")


class QuizSessionStartResponse(BaseModel):
    """Response schema for starting a quiz session."""

    session_id: UUID = Field(..., description="Created/resumed session UUID")
    session_type: QuizSessionType = Field(..., description="Type of quiz session")
    question_strategy: QuestionStrategy = Field(..., description="Question selection strategy")
    question_target: int = Field(..., description="Target number of questions for this session, configurable default 10")
    started_at: datetime = Field(..., description="Session start timestamp")
    is_resumed: bool = Field(..., description="Whether an existing session was resumed")
    status: QuizSessionStatus = Field(..., description="Current session status")
    version: int = Field(..., description="Session version for optimistic locking")
    # first_question will be populated by Story 4.2 (placeholder for now)
    first_question: dict | None = Field(None, description="First question (populated in Story 4.2)")
    # Story 4.8: Focus context for focused sessions
    focus_target_type: str | None = Field(
        None, description="Type of focus: 'ka' for knowledge area, 'concept' for concepts"
    )
    focus_target_id: str | None = Field(
        None, description="Focus target ID (knowledge_area_id or comma-separated concept IDs)"
    )


class FocusedKASessionCreate(BaseModel):
    """Request schema for starting a knowledge area focused session."""

    knowledge_area_id: str = Field(..., description="Knowledge area ID to focus on")
    question_strategy: QuestionStrategy = Field(
        default=QuestionStrategy.MAX_INFO_GAIN,
        description="Strategy for question selection"
    )


class FocusedConceptSessionCreate(BaseModel):
    """Request schema for starting a concept focused session."""

    concept_ids: list[UUID] = Field(
        ...,
        min_length=1,
        description="Concept IDs to focus on (1 or more)"
    )
    question_strategy: QuestionStrategy = Field(
        default=QuestionStrategy.MAX_INFO_GAIN,
        description="Strategy for question selection"
    )


class QuizSessionEndRequest(BaseModel):
    """Request schema for ending a quiz session."""

    expected_version: int = Field(
        ...,
        description="Expected session version for optimistic locking"
    )


class TargetProgress(BaseModel):
    """Progress metrics for focused session target (KA or concepts)."""

    focus_type: str = Field(..., description="Type of focus: 'ka' or 'concept'")
    target_name: str = Field(..., description="Name of target KA or concept(s)")
    questions_in_focus_count: int = Field(
        ..., description="Number of questions that tested target focus"
    )
    session_improvement: float = Field(
        ..., description="Mastery improvement during session (delta)"
    )
    current_mastery: float = Field(
        ..., ge=0.0, le=1.0, description="Current average mastery for target (0-1)"
    )


class QuizSessionEndResponse(BaseModel):
    """Response schema for ending a quiz session."""

    session_id: UUID = Field(..., description="Ended session UUID")
    ended_at: datetime = Field(..., description="Session end timestamp")
    total_questions: int = Field(..., description="Total questions answered in session")
    correct_count: int = Field(..., description="Number of correct answers")
    accuracy: float = Field(..., description="Final session accuracy percentage (0-100)")
    # Story 4.8: Focused session target progress
    target_progress: TargetProgress | None = Field(
        None, description="Progress metrics for focused session target (if applicable)"
    )


class QuizSessionPauseResponse(BaseModel):
    """Response schema for pausing a quiz session."""

    session_id: UUID = Field(..., description="Paused session UUID")
    status: QuizSessionStatus = Field(..., description="New session status (paused)")
    is_paused: bool = Field(default=True, description="Pause confirmation")
    version: int = Field(..., description="Updated session version for optimistic locking")
    message: str = Field(default="Session paused successfully", description="Status message")


class QuizSessionResumeResponse(BaseModel):
    """Response schema for resuming a quiz session."""

    session_id: UUID = Field(..., description="Resumed session UUID")
    status: QuizSessionStatus = Field(..., description="New session status (active)")
    is_paused: bool = Field(default=False, description="Pause status confirmation")
    total_questions: int = Field(..., description="Questions answered so far")
    correct_count: int = Field(..., description="Correct answers so far")
    version: int = Field(..., description="Updated session version for optimistic locking")
    message: str = Field(default="Session resumed successfully", description="Status message")
