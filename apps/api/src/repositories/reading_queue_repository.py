"""
ReadingQueue repository for database operations.
Story 5.5: Background Reading Queue Population
Implements repository pattern for reading queue data access with upsert logic.
"""
from uuid import UUID

from sqlalchemy import case, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.reading_queue import ReadingQueue
from src.schemas.reading_queue import ReadingPriority, ReadingQueueCreate


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
