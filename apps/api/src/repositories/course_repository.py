"""
Course repository for database operations on Course model.
Implements repository pattern for data access.
"""
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.course import Course


class CourseRepository:
    """Repository for Course database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all_active(self) -> List[Course]:
        """
        Get all active courses.

        Returns:
            List of active Course models
        """
        result = await self.session.execute(
            select(Course)
            .where(Course.is_active == True)
            .order_by(Course.name)
        )
        return list(result.scalars().all())

    async def get_by_slug(self, slug: str) -> Optional[Course]:
        """
        Get a course by its slug.

        Args:
            slug: Course slug (URL-friendly identifier)

        Returns:
            Course model if found, None otherwise
        """
        result = await self.session.execute(
            select(Course).where(Course.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, course_id: UUID) -> Optional[Course]:
        """
        Get a course by its UUID.

        Args:
            course_id: Course UUID

        Returns:
            Course model if found, None otherwise
        """
        result = await self.session.execute(
            select(Course).where(Course.id == course_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_slug(self, slug: str) -> Optional[Course]:
        """
        Get an active course by its slug.

        Args:
            slug: Course slug (URL-friendly identifier)

        Returns:
            Active Course model if found, None otherwise
        """
        result = await self.session.execute(
            select(Course)
            .where(Course.slug == slug)
            .where(Course.is_active == True)
        )
        return result.scalar_one_or_none()
