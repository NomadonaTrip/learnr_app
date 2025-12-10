"""
Question repository for data access operations.
Follows the repository pattern for question-related database operations.
Supports multi-course architecture.
"""
import logging
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models.question import Question
from ..models.question_concept import QuestionConcept

logger = logging.getLogger(__name__)


class QuestionRepository:
    """Repository for question data access operations with multi-course support."""

    def __init__(self, db: AsyncSession):
        """
        Initialize question repository.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def create_question(self, question_data: dict) -> Question:
        """
        Create a single question.

        Args:
            question_data: Dictionary with question fields (must include course_id)

        Returns:
            Created Question instance

        Raises:
            SQLAlchemyError: If database operation fails
        """
        try:
            question = Question(**question_data)
            self.db.add(question)
            await self.db.commit()
            await self.db.refresh(question)
            logger.info(f"Created question: {question.id}")
            return question
        except SQLAlchemyError as e:
            logger.error(f"Failed to create question: {str(e)}")
            await self.db.rollback()
            raise

    async def bulk_create_questions(self, questions: List[dict]) -> int:
        """
        Bulk insert questions with transaction support and duplicate handling.

        Tries bulk insert first for performance. If duplicates are detected,
        falls back to inserting one-by-one, skipping duplicates.

        Args:
            questions: List of question dictionaries (must include course_id)

        Returns:
            Number of questions successfully inserted (excludes duplicates)

        Raises:
            SQLAlchemyError: If transaction fails (non-duplicate errors)
        """
        try:
            # Try bulk insert first (fastest path when no duplicates)
            async with self.db.begin():
                question_objects = [Question(**q) for q in questions]
                self.db.add_all(question_objects)
                await self.db.flush()
                count = len(question_objects)
                logger.info(f"Bulk inserted {count} questions")
                return count
        except IntegrityError:
            # Duplicate detected - fall back to one-by-one insert
            await self.db.rollback()
            logger.warning("Duplicate questions detected, inserting individually...")

            inserted_count = 0
            skipped_count = 0

            for question_data in questions:
                try:
                    async with self.db.begin_nested():  # Savepoint for each question
                        question = Question(**question_data)
                        self.db.add(question)
                        await self.db.flush()
                        inserted_count += 1
                except IntegrityError:
                    # Duplicate question - skip it
                    await self.db.rollback()
                    skipped_count += 1
                    q_text = question_data.get('question_text', '')[:50]
                    logger.debug(f"Skipped duplicate: {q_text}...")

            await self.db.commit()
            logger.info(f"Inserted {inserted_count} questions, skipped {skipped_count} duplicates")
            return inserted_count
        except SQLAlchemyError as e:
            logger.error(f"Bulk insert failed: {str(e)}")
            await self.db.rollback()
            raise

    async def get_question_by_id(
        self,
        question_id: UUID,
        course_id: Optional[UUID] = None
    ) -> Optional[Question]:
        """
        Retrieve question by ID, optionally scoped to a course.

        Args:
            question_id: UUID of the question
            course_id: Optional course_id to scope the query

        Returns:
            Question instance or None if not found
        """
        query = select(Question).where(Question.id == question_id)
        if course_id:
            query = query.where(Question.course_id == course_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_questions_by_course(
        self,
        course_id: UUID,
        knowledge_area_id: Optional[str] = None,
        is_active: Optional[bool] = True,
        limit: int = 100,
        offset: int = 0
    ) -> Tuple[List[Question], int]:
        """
        Retrieve questions for a specific course with optional filters.

        Args:
            course_id: Course UUID to filter by
            knowledge_area_id: Optional KA filter
            is_active: Filter by active status (default True)
            limit: Maximum results to return
            offset: Results to skip

        Returns:
            Tuple of (questions list, total count)
        """
        # Build base query
        query = select(Question).where(Question.course_id == course_id)

        if knowledge_area_id:
            query = query.where(Question.knowledge_area_id == knowledge_area_id)

        if is_active is not None:
            query = query.where(Question.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query) or 0

        # Apply pagination
        query = query.offset(offset).limit(limit)

        result = await self.db.execute(query)
        questions = list(result.scalars().all())

        return questions, total

    async def get_questions_by_ka(
        self,
        course_id: UUID,
        knowledge_area_id: str
    ) -> List[Question]:
        """
        Retrieve all questions for a specific knowledge area within a course.

        Args:
            course_id: Course UUID
            knowledge_area_id: Knowledge area ID

        Returns:
            List of Question instances
        """
        result = await self.db.execute(
            select(Question)
            .where(Question.course_id == course_id)
            .where(Question.knowledge_area_id == knowledge_area_id)
            .where(Question.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_all_questions(self, course_id: UUID) -> List[Question]:
        """
        Retrieve all questions for a course.

        Args:
            course_id: Course UUID

        Returns:
            List of Question instances
        """
        result = await self.db.execute(
            select(Question)
            .where(Question.course_id == course_id)
            .where(Question.is_active.is_(True))
        )
        return list(result.scalars().all())

    async def get_questions_with_concepts(self, course_id: UUID) -> List[Question]:
        """
        Retrieve all questions with their concept mappings eagerly loaded.

        Args:
            course_id: Course UUID

        Returns:
            List of Question instances with concepts loaded
        """
        result = await self.db.execute(
            select(Question)
            .where(Question.course_id == course_id)
            .where(Question.is_active.is_(True))
            .options(selectinload(Question.question_concepts))
        )
        return list(result.scalars().all())

    async def get_questions_by_concept(
        self,
        concept_id: UUID,
        course_id: Optional[UUID] = None
    ) -> List[Question]:
        """
        Retrieve all questions mapped to a specific concept.

        Args:
            concept_id: Concept UUID
            course_id: Optional course_id filter for safety

        Returns:
            List of Question instances
        """
        query = (
            select(Question)
            .join(QuestionConcept, Question.id == QuestionConcept.question_id)
            .where(QuestionConcept.concept_id == concept_id)
            .where(Question.is_active.is_(True))
        )
        if course_id:
            query = query.where(Question.course_id == course_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_question_count(self, course_id: UUID) -> int:
        """
        Get total question count for a course.

        Args:
            course_id: Course UUID

        Returns:
            Total question count
        """
        result = await self.db.scalar(
            select(func.count(Question.id))
            .where(Question.course_id == course_id)
            .where(Question.is_active.is_(True))
        )
        return result or 0

    async def get_question_count_by_ka(self, course_id: UUID) -> dict[str, int]:
        """
        Get question count grouped by knowledge area for a course.

        Args:
            course_id: Course UUID

        Returns:
            Dictionary mapping knowledge_area_id to count
        """
        result = await self.db.execute(
            select(Question.knowledge_area_id, func.count(Question.id))
            .where(Question.course_id == course_id)
            .where(Question.is_active.is_(True))
            .group_by(Question.knowledge_area_id)
        )
        return {ka: count for ka, count in result.all()}

    async def get_question_count_by_difficulty(self, course_id: UUID) -> dict[str, int]:
        """
        Get question count grouped by difficulty ranges for a course.

        Args:
            course_id: Course UUID

        Returns:
            Dictionary mapping difficulty range to count
        """
        # Get all questions and bucket by difficulty
        result = await self.db.execute(
            select(Question.difficulty)
            .where(Question.course_id == course_id)
            .where(Question.is_active.is_(True))
        )
        difficulties = [d for (d,) in result.all()]

        counts = {"Easy": 0, "Medium": 0, "Hard": 0}
        for d in difficulties:
            if d <= 0.4:
                counts["Easy"] += 1
            elif d <= 0.7:
                counts["Medium"] += 1
            else:
                counts["Hard"] += 1

        return counts

    # =====================================
    # Concept Mapping Methods
    # =====================================

    async def add_concept_mapping(
        self,
        question_id: UUID,
        concept_id: UUID,
        relevance: float = 1.0
    ) -> QuestionConcept:
        """
        Add a single question-concept mapping.

        Args:
            question_id: Question UUID
            concept_id: Concept UUID
            relevance: Relevance score (0.0-1.0)

        Returns:
            Created QuestionConcept instance
        """
        mapping = QuestionConcept(
            question_id=question_id,
            concept_id=concept_id,
            relevance=relevance
        )
        self.db.add(mapping)
        await self.db.commit()
        await self.db.refresh(mapping)
        return mapping

    async def bulk_add_concept_mappings(
        self,
        mappings: List[dict]
    ) -> int:
        """
        Bulk insert question-concept mappings.

        Args:
            mappings: List of dicts with question_id, concept_id, relevance

        Returns:
            Number of mappings inserted
        """
        try:
            mapping_objects = [QuestionConcept(**m) for m in mappings]
            self.db.add_all(mapping_objects)
            await self.db.commit()
            logger.info(f"Bulk inserted {len(mapping_objects)} concept mappings")
            return len(mapping_objects)
        except SQLAlchemyError as e:
            logger.error(f"Failed to bulk insert concept mappings: {str(e)}")
            await self.db.rollback()
            raise

    async def get_concept_mappings_for_question(
        self,
        question_id: UUID
    ) -> List[QuestionConcept]:
        """
        Get all concept mappings for a question.

        Args:
            question_id: Question UUID

        Returns:
            List of QuestionConcept instances
        """
        result = await self.db.execute(
            select(QuestionConcept)
            .where(QuestionConcept.question_id == question_id)
        )
        return list(result.scalars().all())

    async def get_questions_without_concepts(self, course_id: UUID) -> List[Question]:
        """
        Get questions that don't have any concept mappings.

        Args:
            course_id: Course UUID

        Returns:
            List of unmapped Question instances
        """
        # Subquery to find question_ids that have mappings
        mapped_subquery = (
            select(QuestionConcept.question_id)
            .distinct()
            .scalar_subquery()
        )

        result = await self.db.execute(
            select(Question)
            .where(Question.course_id == course_id)
            .where(Question.is_active.is_(True))
            .where(~Question.id.in_(mapped_subquery))
        )
        return list(result.scalars().all())

    async def delete_concept_mappings_for_question(self, question_id: UUID) -> int:
        """
        Delete all concept mappings for a question.

        Args:
            question_id: Question UUID

        Returns:
            Number of mappings deleted
        """
        from sqlalchemy import delete

        result = await self.db.execute(
            delete(QuestionConcept)
            .where(QuestionConcept.question_id == question_id)
        )
        await self.db.commit()
        return result.rowcount

    # =====================================
    # Rollback Support
    # =====================================

    async def delete_questions_by_ids(self, question_ids: List[UUID]) -> int:
        """
        Delete questions by list of IDs (used for rollback).

        Args:
            question_ids: List of question UUIDs to delete

        Returns:
            Number of questions deleted
        """
        from sqlalchemy import delete

        if not question_ids:
            return 0

        result = await self.db.execute(
            delete(Question)
            .where(Question.id.in_(question_ids))
        )
        await self.db.commit()
        logger.info(f"Deleted {result.rowcount} questions")
        return result.rowcount

    async def deactivate_questions_by_ids(self, question_ids: List[UUID]) -> int:
        """
        Soft-delete questions by setting is_active=False.

        Args:
            question_ids: List of question UUIDs to deactivate

        Returns:
            Number of questions deactivated
        """
        from sqlalchemy import update

        if not question_ids:
            return 0

        result = await self.db.execute(
            update(Question)
            .where(Question.id.in_(question_ids))
            .values(is_active=False)
        )
        await self.db.commit()
        logger.info(f"Deactivated {result.rowcount} questions")
        return result.rowcount
