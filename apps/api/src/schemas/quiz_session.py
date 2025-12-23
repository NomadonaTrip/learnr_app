"""
Quiz Session Pydantic schemas for request/response validation.
Used for adaptive quiz session management API.
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


class QuizSessionType(str, Enum):
    """Types of quiz sessions."""

    DIAGNOSTIC = "diagnostic"
    ADAPTIVE = "adaptive"
    FOCUSED = "focused"
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
        description="Optional knowledge area to focus on (for focused sessions)"
    )


class QuizSessionResponse(BaseModel):
    """Response schema for quiz session details."""

    id: UUID = Field(..., description="Session UUID")
    user_id: UUID = Field(..., description="User UUID")
    enrollment_id: UUID = Field(..., description="Enrollment UUID")
    session_type: QuizSessionType = Field(..., description="Type of quiz session")
    question_strategy: QuestionStrategy = Field(..., description="Question selection strategy")
    knowledge_area_filter: str | None = Field(None, description="Knowledge area filter if set")
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
    started_at: datetime = Field(..., description="Session start timestamp")
    is_resumed: bool = Field(..., description="Whether an existing session was resumed")
    status: QuizSessionStatus = Field(..., description="Current session status")
    version: int = Field(..., description="Session version for optimistic locking")
    # first_question will be populated by Story 4.2 (placeholder for now)
    first_question: dict | None = Field(None, description="First question (populated in Story 4.2)")


class QuizSessionEndRequest(BaseModel):
    """Request schema for ending a quiz session."""

    expected_version: int = Field(
        ...,
        description="Expected session version for optimistic locking"
    )


class QuizSessionEndResponse(BaseModel):
    """Response schema for ending a quiz session."""

    session_id: UUID = Field(..., description="Ended session UUID")
    ended_at: datetime = Field(..., description="Session end timestamp")
    total_questions: int = Field(..., description="Total questions answered in session")
    correct_count: int = Field(..., description="Number of correct answers")
    accuracy: float = Field(..., description="Final session accuracy percentage (0-100)")


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
