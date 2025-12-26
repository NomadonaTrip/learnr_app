"""
Pydantic schemas for Reading Queue operations.
Story 5.5: Background Reading Queue Population
"""
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ReadingPriority(str, Enum):
    """Priority levels for reading queue items."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ReadingQueueStatus(str, Enum):
    """Status of a reading queue item."""
    UNREAD = "unread"
    READING = "reading"
    COMPLETED = "completed"
    DISMISSED = "dismissed"


class ReadingQueueCreate(BaseModel):
    """Schema for creating a reading queue item."""
    user_id: UUID
    enrollment_id: UUID
    chunk_id: UUID
    triggered_by_question_id: UUID | None = None
    triggered_by_concept_id: UUID | None = None
    priority: ReadingPriority = ReadingPriority.MEDIUM


class ReadingQueueTaskPayload(BaseModel):
    """Payload for the Celery background task."""
    user_id: str
    enrollment_id: str
    question_id: str
    session_id: str  # For logging/debugging context only
    is_correct: bool
    difficulty: float = Field(ge=-3.0, le=3.0)  # IRT b-parameter scale


class ReadingQueueResponse(BaseModel):
    """Response schema for a reading queue item."""
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID
    enrollment_id: UUID
    chunk_id: UUID
    triggered_by_question_id: UUID | None
    triggered_by_concept_id: UUID | None
    priority: ReadingPriority
    status: ReadingQueueStatus
    added_at: datetime
    times_opened: int
    total_reading_time_seconds: int
    completed_at: datetime | None


class ReadingQueueWithChunk(ReadingQueueResponse):
    """Reading queue item with chunk details included."""
    chunk_title: str
    chunk_content: str
    corpus_section: str
    knowledge_area_id: str
    estimated_read_time_minutes: int


class ReadingQueueTaskResult(BaseModel):
    """Result returned by the Celery background task."""
    chunks_added: int
    priority: str | None = None
    duration_ms: int
    skipped_reason: str | None = None
