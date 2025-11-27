"""
Question repository for data access operations.
Follows the repository pattern for question-related database operations.
"""
import logging
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.question import Question

logger = logging.getLogger(__name__)


class QuestionRepository:
    """Repository for question data access operations."""

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
            question_data: Dictionary with question fields

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

    async def bulk_create_questions(self, questions: list[dict]) -> int:
        """
        Bulk insert questions with transaction support and duplicate handling.

        Tries bulk insert first for performance. If duplicates are detected,
        falls back to inserting one-by-one, skipping duplicates.

        Args:
            questions: List of question dictionaries

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
        except IntegrityError as e:
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
                    logger.debug(f"Skipped duplicate: {question_data.get('question_text', '')[:50]}...")

            await self.db.commit()
            logger.info(f"Inserted {inserted_count} questions, skipped {skipped_count} duplicates")
            return inserted_count
        except SQLAlchemyError as e:
            logger.error(f"Bulk insert failed: {str(e)}")
            await self.db.rollback()
            raise

    async def get_question_by_id(self, question_id: UUID) -> Question | None:
        """
        Retrieve question by ID.

        Args:
            question_id: UUID of the question

        Returns:
            Question instance or None if not found
        """
        result = await self.db.execute(
            select(Question).where(Question.id == question_id)
        )
        return result.scalar_one_or_none()

    async def get_questions_by_ka(self, ka: str) -> list[Question]:
        """
        Retrieve all questions for a specific knowledge area.

        Args:
            ka: Knowledge area name

        Returns:
            List of Question instances
        """
        result = await self.db.execute(select(Question).where(Question.ka == ka))
        return list(result.scalars().all())

    async def get_question_count_by_ka(self) -> dict[str, int]:
        """
        Get question count grouped by knowledge area.

        Returns:
            Dictionary mapping KA name to count
        """
        result = await self.db.execute(
            select(Question.ka, func.count(Question.id)).group_by(Question.ka)
        )
        return {ka: count for ka, count in result.all()}

    async def get_question_count_by_difficulty(self) -> dict[str, int]:
        """
        Get question count grouped by difficulty.

        Returns:
            Dictionary mapping difficulty to count
        """
        result = await self.db.execute(
            select(Question.difficulty, func.count(Question.id)).group_by(
                Question.difficulty
            )
        )
        return {difficulty: count for difficulty, count in result.all()}
