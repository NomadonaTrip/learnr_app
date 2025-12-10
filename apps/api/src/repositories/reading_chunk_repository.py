"""
ReadingChunk repository for database operations on ReadingChunk model.
Implements repository pattern for data access with multi-course support.
"""
from typing import Dict, List, Optional
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.reading_chunk import ReadingChunk
from src.schemas.reading_chunk import ChunkCreate


class ReadingChunkRepository:
    """Repository for ReadingChunk database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_chunk(self, chunk: ChunkCreate) -> ReadingChunk:
        """
        Create a new reading chunk.

        Args:
            chunk: ChunkCreate schema with chunk data

        Returns:
            Created ReadingChunk model
        """
        db_chunk = ReadingChunk(
            course_id=chunk.course_id,
            title=chunk.title,
            content=chunk.content,
            corpus_section=chunk.corpus_section,
            knowledge_area_id=chunk.knowledge_area_id,
            concept_ids=chunk.concept_ids,
            estimated_read_time_minutes=chunk.estimated_read_time_minutes,
            chunk_index=chunk.chunk_index,
        )
        self.session.add(db_chunk)
        await self.session.flush()
        await self.session.refresh(db_chunk)
        return db_chunk

    async def bulk_create(self, chunks: List[ChunkCreate]) -> int:
        """
        Bulk create reading chunks for efficiency.

        Args:
            chunks: List of ChunkCreate schemas

        Returns:
            Number of chunks created
        """
        db_chunks = [
            ReadingChunk(
                course_id=c.course_id,
                title=c.title,
                content=c.content,
                corpus_section=c.corpus_section,
                knowledge_area_id=c.knowledge_area_id,
                concept_ids=c.concept_ids,
                estimated_read_time_minutes=c.estimated_read_time_minutes,
                chunk_index=c.chunk_index,
            )
            for c in chunks
        ]
        self.session.add_all(db_chunks)
        await self.session.flush()
        return len(db_chunks)

    async def get_by_id(self, chunk_id: UUID) -> Optional[ReadingChunk]:
        """
        Get a reading chunk by its UUID.

        Args:
            chunk_id: ReadingChunk UUID

        Returns:
            ReadingChunk model if found, None otherwise
        """
        result = await self.session.execute(
            select(ReadingChunk).where(ReadingChunk.id == chunk_id)
        )
        return result.scalar_one_or_none()

    async def get_all_chunks(self, course_id: UUID) -> List[ReadingChunk]:
        """
        Get all reading chunks for a course.

        Args:
            course_id: Course UUID to filter by

        Returns:
            List of ReadingChunk models for the course
        """
        result = await self.session.execute(
            select(ReadingChunk)
            .where(ReadingChunk.course_id == course_id)
            .order_by(ReadingChunk.corpus_section, ReadingChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def get_chunks_by_concept(
        self, concept_id: UUID, course_id: UUID
    ) -> List[ReadingChunk]:
        """
        Get reading chunks linked to a specific concept.
        Uses GIN index for efficient array containment queries.

        Args:
            concept_id: Concept UUID to search for
            course_id: Course UUID to filter by

        Returns:
            List of ReadingChunk models containing the concept_id
        """
        result = await self.session.execute(
            select(ReadingChunk)
            .where(ReadingChunk.course_id == course_id)
            .where(ReadingChunk.concept_ids.contains([concept_id]))
            .order_by(ReadingChunk.corpus_section, ReadingChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def get_chunks_by_section(
        self, section_ref: str, course_id: UUID
    ) -> List[ReadingChunk]:
        """
        Get reading chunks for a specific corpus section.

        Args:
            section_ref: Corpus section reference (e.g., "3.2.1")
            course_id: Course UUID to filter by

        Returns:
            List of ReadingChunk models for the section
        """
        result = await self.session.execute(
            select(ReadingChunk)
            .where(ReadingChunk.course_id == course_id)
            .where(ReadingChunk.corpus_section == section_ref)
            .order_by(ReadingChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def get_chunks_by_knowledge_area(
        self, knowledge_area_id: str, course_id: UUID
    ) -> List[ReadingChunk]:
        """
        Get reading chunks for a specific knowledge area.

        Args:
            knowledge_area_id: Knowledge area ID (from course.knowledge_areas[].id)
            course_id: Course UUID to filter by

        Returns:
            List of ReadingChunk models for the knowledge area
        """
        result = await self.session.execute(
            select(ReadingChunk)
            .where(ReadingChunk.course_id == course_id)
            .where(ReadingChunk.knowledge_area_id == knowledge_area_id)
            .order_by(ReadingChunk.corpus_section, ReadingChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def get_chunk_count(self, course_id: UUID) -> int:
        """
        Get total chunk count for a course.

        Args:
            course_id: Course UUID

        Returns:
            Total count of reading chunks
        """
        result = await self.session.execute(
            select(func.count(ReadingChunk.id))
            .where(ReadingChunk.course_id == course_id)
        )
        return result.scalar_one()

    async def get_chunk_count_by_ka(self, course_id: UUID) -> Dict[str, int]:
        """
        Get chunk count grouped by knowledge area for a course.

        Args:
            course_id: Course UUID

        Returns:
            Dictionary mapping knowledge_area_id to count
        """
        result = await self.session.execute(
            select(
                ReadingChunk.knowledge_area_id,
                func.count(ReadingChunk.id)
            )
            .where(ReadingChunk.course_id == course_id)
            .group_by(ReadingChunk.knowledge_area_id)
        )
        return {row[0]: row[1] for row in result.all()}

    async def get_chunks_without_concepts(
        self, course_id: UUID
    ) -> List[ReadingChunk]:
        """
        Get chunks with empty concept_ids array (orphan chunks).
        Used for validation reporting.

        Args:
            course_id: Course UUID

        Returns:
            List of ReadingChunk models with no concepts
        """
        result = await self.session.execute(
            select(ReadingChunk)
            .where(ReadingChunk.course_id == course_id)
            .where(func.array_length(ReadingChunk.concept_ids, 1).is_(None))
            .order_by(ReadingChunk.corpus_section, ReadingChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def delete_all_for_course(self, course_id: UUID) -> int:
        """
        Delete all reading chunks for a course.
        Useful for re-parsing scenarios.

        Args:
            course_id: Course UUID

        Returns:
            Number of chunks deleted
        """
        from sqlalchemy import delete

        result = await self.session.execute(
            delete(ReadingChunk).where(ReadingChunk.course_id == course_id)
        )
        return result.rowcount
