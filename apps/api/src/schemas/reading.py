"""
Pydantic schemas for Reading operations.
Story 5.6: Silent Badge Updates in Navigation
"""
from pydantic import BaseModel, Field


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
