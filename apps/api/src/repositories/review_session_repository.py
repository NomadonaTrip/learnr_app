"""
ReviewSessionRepository for database operations on ReviewSession and ReviewResponse models.
Implements repository pattern for review session data access.

Story 4.9: Post-Session Review Mode
"""
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.question import Question
from src.models.quiz_response import QuizResponse
from src.models.review_response import ReviewResponse
from src.models.review_session import ReviewSession

logger = structlog.get_logger(__name__)


class ReviewSessionRepository:
    """Repository for ReviewSession and ReviewResponse database operations."""

    def __init__(self, db: AsyncSession):
        """
        Initialize review session repository.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    async def create(
        self,
        user_id: UUID,
        original_session_id: UUID,
        question_ids: list[UUID],
    ) -> ReviewSession:
        """
        Create a new review session.

        Args:
            user_id: User UUID
            original_session_id: Original quiz session UUID
            question_ids: List of question UUIDs to review (incorrect questions)

        Returns:
            Created ReviewSession
        """
        review_session = ReviewSession(
            user_id=user_id,
            original_session_id=original_session_id,
            question_ids=[str(qid) for qid in question_ids],
            total_to_review=len(question_ids),
        )
        self.db.add(review_session)
        await self.db.flush()
        await self.db.refresh(review_session)

        logger.info(
            "review_session_created",
            review_session_id=str(review_session.id),
            user_id=str(user_id),
            original_session_id=str(original_session_id),
            questions_to_review=len(question_ids),
        )

        return review_session

    async def get_by_id(
        self,
        review_session_id: UUID,
        user_id: UUID | None = None,
    ) -> ReviewSession | None:
        """
        Get a review session by ID, optionally filtered by user.

        Args:
            review_session_id: ReviewSession UUID
            user_id: Optional user UUID for ownership validation

        Returns:
            ReviewSession if found, None otherwise
        """
        query = select(ReviewSession).where(ReviewSession.id == review_session_id)

        if user_id is not None:
            query = query.where(ReviewSession.user_id == user_id)

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_id_for_update(
        self,
        review_session_id: UUID,
    ) -> ReviewSession | None:
        """
        Get a review session by ID with row lock for concurrent access safety.

        Args:
            review_session_id: ReviewSession UUID

        Returns:
            ReviewSession if found, None otherwise
        """
        result = await self.db.execute(
            select(ReviewSession)
            .where(ReviewSession.id == review_session_id)
            .with_for_update()
        )
        return result.scalar_one_or_none()

    async def get_pending_for_session(
        self,
        original_session_id: UUID,
    ) -> ReviewSession | None:
        """
        Get a pending review session for a quiz session.

        Args:
            original_session_id: Original quiz session UUID

        Returns:
            ReviewSession if pending review exists, None otherwise
        """
        result = await self.db.execute(
            select(ReviewSession)
            .where(ReviewSession.original_session_id == original_session_id)
            .where(ReviewSession.status.in_(["pending", "in_progress"]))
        )
        return result.scalar_one_or_none()

    async def update_progress(
        self,
        review_session_id: UUID,
        reviewed: int,
        reinforced: int,
        still_incorrect: int,
    ) -> ReviewSession:
        """
        Update review session progress counters.

        Args:
            review_session_id: ReviewSession UUID
            reviewed: Total reviewed count
            reinforced: Reinforced count (incorrect→correct)
            still_incorrect: Still incorrect count

        Returns:
            Updated ReviewSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_by_id_for_update(review_session_id)
        if not session:
            raise ValueError(f"Review session {review_session_id} not found")

        session.reviewed_count = reviewed
        session.reinforced_count = reinforced
        session.still_incorrect_count = still_incorrect

        await self.db.flush()
        await self.db.refresh(session)

        logger.debug(
            "review_session_progress_updated",
            review_session_id=str(review_session_id),
            reviewed_count=reviewed,
            reinforced_count=reinforced,
            still_incorrect_count=still_incorrect,
        )

        return session

    async def mark_started(
        self,
        review_session_id: UUID,
    ) -> ReviewSession:
        """
        Mark a review session as started.

        Args:
            review_session_id: ReviewSession UUID

        Returns:
            Updated ReviewSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_by_id_for_update(review_session_id)
        if not session:
            raise ValueError(f"Review session {review_session_id} not found")

        session.status = "in_progress"
        session.started_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(session)

        logger.info(
            "review_session_started",
            review_session_id=str(review_session_id),
            user_id=str(session.user_id),
        )

        return session

    async def mark_skipped(
        self,
        review_session_id: UUID,
    ) -> ReviewSession:
        """
        Mark a review session as skipped.

        Args:
            review_session_id: ReviewSession UUID

        Returns:
            Updated ReviewSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_by_id_for_update(review_session_id)
        if not session:
            raise ValueError(f"Review session {review_session_id} not found")

        session.status = "skipped"
        session.completed_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(session)

        logger.info(
            "review_session_skipped",
            review_session_id=str(review_session_id),
            user_id=str(session.user_id),
            questions_skipped=session.total_to_review,
        )

        return session

    async def mark_completed(
        self,
        review_session_id: UUID,
    ) -> ReviewSession:
        """
        Mark a review session as completed.

        Args:
            review_session_id: ReviewSession UUID

        Returns:
            Updated ReviewSession

        Raises:
            ValueError: If session not found
        """
        session = await self.get_by_id_for_update(review_session_id)
        if not session:
            raise ValueError(f"Review session {review_session_id} not found")

        session.status = "completed"
        session.completed_at = datetime.now(UTC)

        await self.db.flush()
        await self.db.refresh(session)

        logger.info(
            "review_session_completed",
            review_session_id=str(review_session_id),
            user_id=str(session.user_id),
            total_reviewed=session.reviewed_count,
            reinforced_count=session.reinforced_count,
            reinforcement_rate=session.reinforcement_rate,
        )

        return session

    async def create_review_response(
        self,
        review_session_id: UUID,
        user_id: UUID,
        question_id: UUID,
        original_response_id: UUID,
        selected_answer: str,
        is_correct: bool,
        was_reinforced: bool,
        belief_updates: list[dict[str, Any]] | None = None,
    ) -> ReviewResponse:
        """
        Create a new review response record.

        Args:
            review_session_id: ReviewSession UUID
            user_id: User UUID
            question_id: Question UUID being answered
            original_response_id: Original quiz response UUID
            selected_answer: Selected answer option (A, B, C, or D)
            is_correct: Whether the answer was correct
            was_reinforced: Whether this was a reinforcement (incorrect→correct)
            belief_updates: Optional belief update snapshot (JSON)

        Returns:
            Created ReviewResponse instance
        """
        try:
            response = ReviewResponse(
                review_session_id=review_session_id,
                user_id=user_id,
                question_id=question_id,
                original_response_id=original_response_id,
                selected_answer=selected_answer.upper(),
                is_correct=is_correct,
                was_reinforced=was_reinforced,
                belief_updates=belief_updates,
            )
            self.db.add(response)
            await self.db.flush()
            await self.db.refresh(response)

            logger.info(
                "review_response_created",
                review_response_id=str(response.id),
                review_session_id=str(review_session_id),
                question_id=str(question_id),
                is_correct=is_correct,
                was_reinforced=was_reinforced,
            )

            return response
        except SQLAlchemyError as e:
            logger.error(f"Failed to create review response: {str(e)}")
            raise

    async def get_review_responses(
        self,
        review_session_id: UUID,
    ) -> list[ReviewResponse]:
        """
        Get all review responses for a review session.

        Args:
            review_session_id: ReviewSession UUID

        Returns:
            List of ReviewResponse instances
        """
        result = await self.db.execute(
            select(ReviewResponse)
            .where(ReviewResponse.review_session_id == review_session_id)
            .order_by(ReviewResponse.created_at)
        )
        return list(result.scalars().all())

    async def check_question_already_reviewed(
        self,
        review_session_id: UUID,
        question_id: UUID,
    ) -> bool:
        """
        Check if a question has already been answered in a review session.

        Args:
            review_session_id: ReviewSession UUID
            question_id: Question UUID

        Returns:
            True if question already reviewed, False otherwise
        """
        result = await self.db.execute(
            select(ReviewResponse.id)
            .where(ReviewResponse.review_session_id == review_session_id)
            .where(ReviewResponse.question_id == question_id)
            .limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_incorrect_responses_for_session(
        self,
        session_id: UUID,
    ) -> list[QuizResponse]:
        """
        Get all incorrect responses from a quiz session.

        Used to determine which questions need review.

        Args:
            session_id: Quiz session UUID

        Returns:
            List of incorrect QuizResponse instances
        """
        result = await self.db.execute(
            select(QuizResponse)
            .where(QuizResponse.session_id == session_id)
            .where(QuizResponse.is_correct == False)  # noqa: E712
            .order_by(QuizResponse.created_at)
        )
        return list(result.scalars().all())

    async def get_question_with_options(
        self,
        question_id: UUID,
    ) -> Question | None:
        """
        Get a question by ID with all options.

        Args:
            question_id: Question UUID

        Returns:
            Question if found, None otherwise
        """
        result = await self.db.execute(
            select(Question)
            .where(Question.id == question_id)
            .options(selectinload(Question.question_concepts))
        )
        return result.scalar_one_or_none()

    async def get_questions_with_concepts_batch(
        self,
        question_ids: list[UUID],
    ) -> list[Question]:
        """
        Batch load questions with their concepts eagerly loaded.

        Optimized query to avoid N+1 when fetching multiple questions
        with their associated concepts.

        Args:
            question_ids: List of Question UUIDs

        Returns:
            List of Question instances with concepts loaded
        """
        from src.models.concept import Concept
        from src.models.question_concept import QuestionConcept

        if not question_ids:
            return []

        result = await self.db.execute(
            select(Question)
            .where(Question.id.in_(question_ids))
            .options(
                selectinload(Question.question_concepts).selectinload(
                    QuestionConcept.concept
                )
            )
        )
        return list(result.scalars().all())

    async def get_original_response_for_question(
        self,
        session_id: UUID,
        question_id: UUID,
    ) -> QuizResponse | None:
        """
        Get the original quiz response for a question in a session.

        Args:
            session_id: Quiz session UUID
            question_id: Question UUID

        Returns:
            QuizResponse if found, None otherwise
        """
        result = await self.db.execute(
            select(QuizResponse)
            .where(QuizResponse.session_id == session_id)
            .where(QuizResponse.question_id == question_id)
        )
        return result.scalar_one_or_none()
