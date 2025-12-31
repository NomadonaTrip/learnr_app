"""
Pydantic schemas for Reading operations.
Story 5.6: Silent Badge Updates in Navigation
Story 5.7: Reading Library Page with Queue Display
Story 5.8: Reading Item Detail View and Engagement Tracking
"""
from datetime import datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class ReadingStatsResponse(BaseModel):
    """
    Response schema for reading queue statistics.
    Used by the reading badge to display unread counts.
    """
    unread_count: int = Field(
        ge=0,
        description="Count of unread items in the reading queue"
    )
    high_priority_count: int = Field(
        ge=0,
        description="Count of high-priority unread items in the queue"
    )


class ReadingQueueSortBy(str, Enum):
    """Sort options for reading queue list."""
    PRIORITY = "priority"
    DATE = "date"
    RELEVANCE = "relevance"


class ReadingQueueFilterStatus(str, Enum):
    """Filter status options for reading queue list."""
    UNREAD = "unread"
    READING = "reading"
    COMPLETED = "completed"
    DISMISSED = "dismissed"
    ALL = "all"


class ReadingQueueFilterPriority(str, Enum):
    """Filter priority options for reading queue list."""
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class ReadingQueueItemResponse(BaseModel):
    """
    Response schema for a single reading queue item.
    Story 5.7: Reading Library Page with Queue Display
    """
    model_config = ConfigDict(from_attributes=True)

    queue_id: UUID = Field(description="Reading queue item ID")
    chunk_id: UUID = Field(description="Reading chunk ID")
    title: str = Field(description="BABOK section title")
    preview: str = Field(description="First 100 characters of content")
    babok_section: str = Field(description="BABOK section reference (e.g., '3.2.1')")
    ka_name: str = Field(description="Knowledge Area name")
    ka_id: str = Field(description="Knowledge Area ID")
    relevance_score: float | None = Field(
        default=None,
        description="Semantic relevance score (0-1)"
    )
    priority: str = Field(description="Priority level: High, Medium, Low")
    status: str = Field(description="Queue item status")
    word_count: int = Field(ge=0, description="Word count of the reading chunk")
    estimated_read_minutes: int = Field(
        ge=1,
        description="Estimated read time in minutes (word_count / 200)"
    )
    question_preview: str | None = Field(
        default=None,
        description="Preview of the triggering question text"
    )
    was_incorrect: bool = Field(
        default=True,
        description="Whether the item was triggered by an incorrect answer"
    )
    added_at: datetime = Field(description="When the item was added to the queue")


class PaginationMeta(BaseModel):
    """Pagination metadata for list responses."""
    page: int = Field(ge=1, description="Current page number")
    per_page: int = Field(ge=1, le=100, description="Items per page")
    total_items: int = Field(ge=0, description="Total number of items")
    total_pages: int = Field(ge=0, description="Total number of pages")


class ReadingQueueListResponse(BaseModel):
    """
    Paginated response for reading queue list.
    Story 5.7: Reading Library Page with Queue Display
    """
    items: list[ReadingQueueItemResponse] = Field(
        description="List of reading queue items"
    )
    pagination: PaginationMeta = Field(
        description="Pagination metadata"
    )


class ReadingQueueStatusUpdate(BaseModel):
    """Request schema for updating queue item status."""
    status: str = Field(
        description="New status: reading, completed, or dismissed"
    )


class QuestionContextResponse(BaseModel):
    """
    Nested schema for question context in reading detail.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    question_id: UUID | None = Field(
        default=None,
        description="ID of the triggering question"
    )
    question_preview: str | None = Field(
        default=None,
        description="Preview of the triggering question (first 80 chars)"
    )
    was_incorrect: bool = Field(
        default=True,
        description="Whether the item was triggered by an incorrect answer"
    )


class ReadingQueueDetailResponse(BaseModel):
    """
    Response schema for a single reading queue item with full content.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    model_config = ConfigDict(from_attributes=True)

    queue_id: UUID = Field(description="Reading queue item ID")
    chunk_id: UUID = Field(description="Reading chunk ID")
    title: str = Field(description="BABOK section title")
    text_content: str = Field(description="Full reading content (markdown)")
    babok_section: str = Field(description="BABOK section reference (e.g., '3.2.1')")
    ka_name: str = Field(description="Knowledge Area name")
    priority: str = Field(description="Priority level: High, Medium, Low")
    status: str = Field(description="Queue item status")
    word_count: int = Field(ge=0, description="Word count of the reading chunk")
    estimated_read_minutes: int = Field(
        ge=1,
        description="Estimated read time in minutes (word_count / 200)"
    )
    times_opened: int = Field(
        ge=0,
        description="Number of times this item has been opened"
    )
    total_reading_time_seconds: int = Field(
        ge=0,
        description="Total cumulative reading time in seconds"
    )
    first_opened_at: datetime | None = Field(
        default=None,
        description="When this item was first opened"
    )
    question_context: QuestionContextResponse = Field(
        description="Context about the triggering question"
    )
    added_at: datetime = Field(description="When the item was added to the queue")


class EngagementUpdateRequest(BaseModel):
    """
    Request schema for updating engagement metrics.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    time_spent_seconds: int = Field(
        ge=0,
        le=1800,  # Max 30 minutes per session
        description="Time spent reading in seconds (max 1800 = 30 min)"
    )


class EngagementUpdateResponse(BaseModel):
    """
    Response schema for engagement update.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    queue_id: UUID = Field(description="Reading queue item ID")
    total_reading_time_seconds: int = Field(
        ge=0,
        description="Updated total reading time in seconds"
    )
    times_opened: int = Field(
        ge=0,
        description="Total times opened"
    )


class StatusUpdateRequest(BaseModel):
    """
    Request schema for updating queue item status.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    status: Literal["completed", "dismissed"] = Field(
        description="New status: 'completed' or 'dismissed'"
    )


class StatusUpdateResponse(BaseModel):
    """
    Response schema for status update.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    queue_id: UUID = Field(description="Reading queue item ID")
    status: str = Field(description="Updated status")
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when marked as completed"
    )
    dismissed_at: datetime | None = Field(
        default=None,
        description="Timestamp when dismissed"
    )


class BatchDismissRequest(BaseModel):
    """
    Request schema for batch dismiss operation.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    queue_ids: list[UUID] = Field(
        min_length=1,
        max_length=100,
        description="List of queue item IDs to dismiss (max 100)"
    )

    @field_validator("queue_ids")
    @classmethod
    def validate_queue_ids(cls, v: list[UUID]) -> list[UUID]:
        """Ensure no duplicate IDs."""
        if len(v) != len(set(v)):
            raise ValueError("Duplicate queue IDs are not allowed")
        return v


class BatchDismissResponse(BaseModel):
    """
    Response schema for batch dismiss operation.
    Story 5.8: Reading Item Detail View and Engagement Tracking
    """
    dismissed_count: int = Field(
        ge=0,
        description="Number of items actually dismissed"
    )
    remaining_unread_count: int = Field(
        ge=0,
        description="Remaining unread items after dismiss"
    )
