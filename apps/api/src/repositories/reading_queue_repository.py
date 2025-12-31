"""
ReadingQueue repository for database operations.
Story 5.5: Background Reading Queue Population
Story 5.7: Reading Library Page with Queue Display
Story 5.8: Reading Item Detail View and Engagement Tracking
Implements repository pattern for reading queue data access with upsert logic.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import case, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.question import Question
from src.models.reading_chunk import ReadingChunk
from src.models.reading_queue import ReadingQueue
from src.schemas.reading import (
    ReadingQueueFilterPriority,
    ReadingQueueFilterStatus,
    ReadingQueueSortBy,
)
from src.schemas.reading_queue import ReadingPriority, ReadingQueueCreate


@dataclass
class QueueItemWithDetails:
    """Data class for queue item with joined chunk and question details."""
    queue: ReadingQueue
    chunk: ReadingChunk
    question: Question | None


class ReadingQueueRepository:
    """Repository for ReadingQueue database operations."""

    # Priority order for comparison (lower = higher priority)
    PRIORITY_ORDER = {
        ReadingPriority.HIGH: 0,
        ReadingPriority.MEDIUM: 1,
        ReadingPriority.LOW: 2,
        "High": 0,
        "Medium": 1,
        "Low": 2,
    }

    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_to_queue(self, queue_item: ReadingQueueCreate) -> ReadingQueue:
        """
        Add a reading item to the queue with upsert logic.

        If the chunk already exists in the user's queue, updates priority
        only if the new priority is higher.

        Args:
            queue_item: ReadingQueueCreate schema with item data

        Returns:
            Created or updated ReadingQueue model
        """
        # Prepare insert statement with conflict handling
        stmt = insert(ReadingQueue).values(
            user_id=queue_item.user_id,
            enrollment_id=queue_item.enrollment_id,
            chunk_id=queue_item.chunk_id,
            triggered_by_question_id=queue_item.triggered_by_question_id,
            triggered_by_concept_id=queue_item.triggered_by_concept_id,
            priority=queue_item.priority.value if isinstance(queue_item.priority, ReadingPriority) else queue_item.priority,
            status="unread",  # Explicitly set status since raw insert doesn't use Python defaults
        )

        # On conflict (enrollment_id, chunk_id), update priority only if new is higher
        # Use CASE expression to compare priorities
        stmt = stmt.on_conflict_do_update(
            constraint="uq_reading_queue_enrollment_chunk",
            set_={
                "priority": stmt.excluded.priority,
                "triggered_by_question_id": stmt.excluded.triggered_by_question_id,
                "triggered_by_concept_id": stmt.excluded.triggered_by_concept_id,
            },
            where=(
                # Only update if new priority is higher (lower number)
                # High=0, Medium=1, Low=2
                # Update when: (old is Medium and new is High) OR (old is Low and new is not Low)
                (ReadingQueue.priority == "Low") |
                ((ReadingQueue.priority == "Medium") & (stmt.excluded.priority == "High"))
            ),
        )

        await self.session.execute(stmt)
        await self.session.flush()

        # Fetch and return the record
        return await self.get_queue_item(queue_item.enrollment_id, queue_item.chunk_id)

    async def get_queue_item(
        self, enrollment_id: UUID, chunk_id: UUID
    ) -> ReadingQueue | None:
        """
        Get a queue item by enrollment and chunk IDs.

        Args:
            enrollment_id: Enrollment UUID
            chunk_id: Chunk UUID

        Returns:
            ReadingQueue model if found, None otherwise
        """
        result = await self.session.execute(
            select(ReadingQueue)
            .where(ReadingQueue.enrollment_id == enrollment_id)
            .where(ReadingQueue.chunk_id == chunk_id)
        )
        return result.scalar_one_or_none()

    async def update_priority_if_higher(
        self,
        enrollment_id: UUID,
        chunk_id: UUID,
        new_priority: ReadingPriority,
    ) -> bool:
        """
        Update priority only if the new priority is higher.

        Args:
            enrollment_id: Enrollment UUID
            chunk_id: Chunk UUID
            new_priority: New priority to set

        Returns:
            True if updated, False if not found or priority not higher
        """
        existing = await self.get_queue_item(enrollment_id, chunk_id)
        if not existing:
            return False

        new_order = self.PRIORITY_ORDER.get(new_priority, 1)
        existing_order = self.PRIORITY_ORDER.get(existing.priority, 1)

        if new_order < existing_order:
            existing.priority = new_priority.value if isinstance(new_priority, ReadingPriority) else new_priority
            await self.session.flush()
            return True

        return False

    async def get_user_queue(
        self,
        enrollment_id: UUID,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ReadingQueue]:
        """
        Get reading queue items for an enrollment.

        Args:
            enrollment_id: Enrollment UUID
            status: Optional filter by status
            limit: Maximum items to return

        Returns:
            List of ReadingQueue models ordered by priority and added_at
        """
        query = (
            select(ReadingQueue)
            .where(ReadingQueue.enrollment_id == enrollment_id)
        )

        if status:
            query = query.where(ReadingQueue.status == status)

        # Order by priority (High first) then by added_at
        # Use CASE expression since alphabetical order is wrong (High < Low < Medium)
        priority_order = case(
            (ReadingQueue.priority == "High", 0),
            (ReadingQueue.priority == "Medium", 1),
            else_=2  # Low
        )
        query = query.order_by(
            priority_order,
            ReadingQueue.added_at.desc()
        ).limit(limit)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_unread_count(self, enrollment_id: UUID) -> int:
        """
        Get count of unread items in the queue.

        Args:
            enrollment_id: Enrollment UUID

        Returns:
            Count of unread items
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(func.count(ReadingQueue.id))
            .where(ReadingQueue.enrollment_id == enrollment_id)
            .where(ReadingQueue.status == "unread")
        )
        return result.scalar_one()

    async def get_unread_stats(self, enrollment_id: UUID) -> dict[str, int]:
        """
        Get aggregated stats for unread items in the queue.
        Story 5.6: Silent Badge Updates in Navigation

        Uses a single query with conditional counts for performance.
        Leverages the idx_reading_queue_enrollment_status index.

        Args:
            enrollment_id: Enrollment UUID

        Returns:
            Dictionary with unread_count and high_priority_count
        """
        from sqlalchemy import func

        result = await self.session.execute(
            select(
                func.count(ReadingQueue.id).label("unread_count"),
                func.count(ReadingQueue.id).filter(
                    ReadingQueue.priority == "High"
                ).label("high_priority_count"),
            )
            .where(ReadingQueue.enrollment_id == enrollment_id)
            .where(ReadingQueue.status == "unread")
        )
        row = result.one()
        return {
            "unread_count": row.unread_count or 0,
            "high_priority_count": row.high_priority_count or 0,
        }

    async def bulk_add_to_queue(
        self, items: list[ReadingQueueCreate]
    ) -> int:
        """
        Bulk add reading items to the queue with upsert logic.

        Args:
            items: List of ReadingQueueCreate schemas

        Returns:
            Number of items added/updated
        """
        if not items:
            return 0

        added_count = 0
        for item in items:
            await self.add_to_queue(item)
            added_count += 1

        return added_count

    async def get_queue_items(
        self,
        enrollment_id: UUID,
        status: ReadingQueueFilterStatus = ReadingQueueFilterStatus.UNREAD,
        ka_id: str | None = None,
        priority: ReadingQueueFilterPriority | None = None,
        sort_by: ReadingQueueSortBy = ReadingQueueSortBy.PRIORITY,
        page: int = 1,
        per_page: int = 20,
    ) -> tuple[list[QueueItemWithDetails], int]:
        """
        Get paginated reading queue items with full details.
        Story 5.7: Reading Library Page with Queue Display

        Args:
            enrollment_id: Enrollment UUID to filter by
            status: Filter by status (unread, reading, completed, dismissed, all)
            ka_id: Optional filter by Knowledge Area ID
            priority: Optional filter by priority (High, Medium, Low)
            sort_by: Sort order (priority, date, relevance)
            page: Page number (1-indexed)
            per_page: Items per page (max 100)

        Returns:
            Tuple of (list of QueueItemWithDetails, total count)
        """
        # Clamp per_page to max 100
        per_page = min(per_page, 100)

        # Build base query with joins
        query = (
            select(ReadingQueue)
            .options(
                joinedload(ReadingQueue.chunk),
                joinedload(ReadingQueue.triggered_by_question),
            )
            .where(ReadingQueue.enrollment_id == enrollment_id)
        )

        # Apply status filter
        if status != ReadingQueueFilterStatus.ALL:
            query = query.where(ReadingQueue.status == status.value)

        # Apply KA filter (joins with chunk for knowledge_area_id)
        if ka_id:
            query = query.join(ReadingQueue.chunk).where(
                ReadingChunk.knowledge_area_id == ka_id
            )

        # Apply priority filter
        if priority:
            query = query.where(ReadingQueue.priority == priority.value)

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.session.execute(count_query)
        total_count = total_result.scalar_one()

        # Apply sorting
        if sort_by == ReadingQueueSortBy.PRIORITY:
            # Custom priority order: High (0) > Medium (1) > Low (2)
            priority_order = case(
                (ReadingQueue.priority == "High", 0),
                (ReadingQueue.priority == "Medium", 1),
                else_=2  # Low
            )
            query = query.order_by(priority_order, ReadingQueue.added_at.desc())
        elif sort_by == ReadingQueueSortBy.DATE:
            query = query.order_by(ReadingQueue.added_at.desc())
        elif sort_by == ReadingQueueSortBy.RELEVANCE:
            # Sort by priority as proxy for relevance (High = most relevant)
            priority_order = case(
                (ReadingQueue.priority == "High", 0),
                (ReadingQueue.priority == "Medium", 1),
                else_=2
            )
            query = query.order_by(priority_order, ReadingQueue.added_at.desc())

        # Apply pagination
        offset = (page - 1) * per_page
        query = query.offset(offset).limit(per_page)

        # Execute query
        result = await self.session.execute(query)
        queue_items = result.unique().scalars().all()

        # Build response with details
        items_with_details = [
            QueueItemWithDetails(
                queue=item,
                chunk=item.chunk,
                question=item.triggered_by_question,
            )
            for item in queue_items
        ]

        return items_with_details, total_count

    async def get_queue_item_by_id(
        self,
        queue_id: UUID,
    ) -> QueueItemWithDetails | None:
        """
        Get a single queue item by ID with full details.
        Story 5.8: Reading Detail Page

        Args:
            queue_id: ReadingQueue UUID

        Returns:
            QueueItemWithDetails if found, None otherwise
        """
        query = (
            select(ReadingQueue)
            .options(
                joinedload(ReadingQueue.chunk),
                joinedload(ReadingQueue.triggered_by_question),
            )
            .where(ReadingQueue.id == queue_id)
        )

        result = await self.session.execute(query)
        queue_item = result.unique().scalar_one_or_none()

        if not queue_item:
            return None

        return QueueItemWithDetails(
            queue=queue_item,
            chunk=queue_item.chunk,
            question=queue_item.triggered_by_question,
        )

    async def get_queue_item_detail(
        self,
        enrollment_id: UUID,
        queue_id: UUID,
    ) -> QueueItemWithDetails | None:
        """
        Get a single queue item by ID with enrollment authorization check.
        Story 5.8: Reading Item Detail View and Engagement Tracking

        Args:
            enrollment_id: Enrollment UUID for authorization
            queue_id: ReadingQueue UUID

        Returns:
            QueueItemWithDetails if found and authorized, None otherwise
        """
        query = (
            select(ReadingQueue)
            .options(
                joinedload(ReadingQueue.chunk),
                joinedload(ReadingQueue.triggered_by_question),
            )
            .where(ReadingQueue.id == queue_id)
            .where(ReadingQueue.enrollment_id == enrollment_id)
        )

        result = await self.session.execute(query)
        queue_item = result.unique().scalar_one_or_none()

        if not queue_item:
            return None

        return QueueItemWithDetails(
            queue=queue_item,
            chunk=queue_item.chunk,
            question=queue_item.triggered_by_question,
        )

    async def increment_times_opened(
        self,
        queue_id: UUID,
        enrollment_id: UUID,
    ) -> ReadingQueue | None:
        """
        Increment times_opened counter and set first_opened_at if first view.
        Story 5.8: Reading Item Detail View and Engagement Tracking

        Args:
            queue_id: ReadingQueue UUID
            enrollment_id: Enrollment UUID for authorization

        Returns:
            Updated ReadingQueue if found and authorized, None otherwise
        """
        # First, fetch the item to check authorization
        result = await self.session.execute(
            select(ReadingQueue)
            .where(ReadingQueue.id == queue_id)
            .where(ReadingQueue.enrollment_id == enrollment_id)
        )
        queue_item = result.scalar_one_or_none()

        if not queue_item:
            return None

        # Increment times_opened
        queue_item.times_opened += 1

        # Set first_opened_at if this is the first view
        if queue_item.first_opened_at is None:
            queue_item.first_opened_at = datetime.now(timezone.utc)

        await self.session.flush()
        return queue_item

    async def update_engagement(
        self,
        queue_id: UUID,
        enrollment_id: UUID,
        time_spent_seconds: int,
    ) -> ReadingQueue | None:
        """
        Update reading engagement by adding time to total_reading_time_seconds.
        Story 5.8: Reading Item Detail View and Engagement Tracking

        Args:
            queue_id: ReadingQueue UUID
            enrollment_id: Enrollment UUID for authorization
            time_spent_seconds: Time spent in this session (seconds)

        Returns:
            Updated ReadingQueue if found and authorized, None otherwise
        """
        # Fetch the item with authorization check
        result = await self.session.execute(
            select(ReadingQueue)
            .where(ReadingQueue.id == queue_id)
            .where(ReadingQueue.enrollment_id == enrollment_id)
        )
        queue_item = result.scalar_one_or_none()

        if not queue_item:
            return None

        # Add time to total (capped at 30 min per session)
        capped_time = min(time_spent_seconds, 1800)
        queue_item.total_reading_time_seconds += capped_time

        await self.session.flush()
        return queue_item

    async def update_status(
        self,
        queue_id: UUID,
        enrollment_id: UUID,
        status: str,
    ) -> ReadingQueue | None:
        """
        Update queue item status with appropriate timestamp.
        Story 5.8: Reading Item Detail View and Engagement Tracking

        Args:
            queue_id: ReadingQueue UUID
            enrollment_id: Enrollment UUID for authorization
            status: New status ('completed' or 'dismissed')

        Returns:
            Updated ReadingQueue if found and authorized, None otherwise
        """
        # Fetch the item with authorization check
        result = await self.session.execute(
            select(ReadingQueue)
            .where(ReadingQueue.id == queue_id)
            .where(ReadingQueue.enrollment_id == enrollment_id)
        )
        queue_item = result.scalar_one_or_none()

        if not queue_item:
            return None

        now = datetime.now(timezone.utc)

        # Update status and appropriate timestamp
        queue_item.status = status
        if status == "completed":
            queue_item.completed_at = now
        elif status == "dismissed":
            queue_item.dismissed_at = now

        await self.session.flush()
        return queue_item

    async def batch_dismiss(
        self,
        enrollment_id: UUID,
        queue_ids: list[UUID],
    ) -> int:
        """
        Batch dismiss multiple queue items.
        Story 5.8: Reading Item Detail View and Engagement Tracking

        Only dismisses items that belong to the enrollment (authorization).
        Silently skips invalid or non-existent IDs.

        Args:
            enrollment_id: Enrollment UUID for authorization
            queue_ids: List of queue IDs to dismiss

        Returns:
            Number of items actually dismissed
        """
        if not queue_ids:
            return 0

        now = datetime.now(timezone.utc)

        # Update only items belonging to this enrollment
        result = await self.session.execute(
            update(ReadingQueue)
            .where(ReadingQueue.id.in_(queue_ids))
            .where(ReadingQueue.enrollment_id == enrollment_id)
            .where(ReadingQueue.status != "dismissed")  # Skip already dismissed
            .values(
                status="dismissed",
                dismissed_at=now,
            )
        )

        await self.session.flush()
        return result.rowcount

    async def get_remaining_unread_count(
        self,
        enrollment_id: UUID,
    ) -> int:
        """
        Get count of remaining unread items in the queue.
        Story 5.8: Reading Item Detail View and Engagement Tracking

        Args:
            enrollment_id: Enrollment UUID

        Returns:
            Count of unread items
        """
        result = await self.session.execute(
            select(func.count(ReadingQueue.id))
            .where(ReadingQueue.enrollment_id == enrollment_id)
            .where(ReadingQueue.status == "unread")
        )
        return result.scalar_one()
