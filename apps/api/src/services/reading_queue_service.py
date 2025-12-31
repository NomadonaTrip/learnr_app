"""
ReadingQueueService for background population of reading materials.
Story 5.5: Background Reading Queue Population

This service handles:
- Building semantic search queries from question concepts
- Searching Qdrant for relevant reading chunks
- Calculating priority based on competency and correctness
- Adding reading materials to the user's queue
"""
from uuid import UUID

import structlog
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.models.concept import Concept
from src.models.enrollment import Enrollment
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.repositories.qdrant_repository import QdrantRepository
from src.repositories.reading_queue_repository import ReadingQueueRepository
from src.schemas.reading_queue import ReadingPriority, ReadingQueueCreate
from src.services.embedding_service import EmbeddingService

logger = structlog.get_logger(__name__)


class ReadingQueueService:
    """
    Service for populating the reading queue based on quiz answers.

    Automatically adds relevant reading materials when users answer questions,
    with priority based on correctness and competency level.
    """

    def __init__(self, session: AsyncSession):
        """
        Initialize the service with database session.

        Args:
            session: Async SQLAlchemy session
        """
        self.session = session
        self.reading_queue_repo = ReadingQueueRepository(session)
        self.qdrant_repo = QdrantRepository()

    async def populate_reading_queue(
        self,
        user_id: UUID,
        enrollment_id: UUID,
        question_id: UUID,
        session_id: UUID,  # For logging only
        is_correct: bool,
        difficulty: float,
    ) -> int:
        """
        Populate reading queue after a quiz answer submission.

        This is the main entry point called by the Celery background task.

        Args:
            user_id: User UUID
            enrollment_id: Enrollment UUID
            question_id: Question UUID that was answered
            session_id: Quiz session UUID (for logging/debugging)
            is_correct: Whether the answer was correct
            difficulty: IRT b-parameter difficulty of the question

        Returns:
            Number of reading chunks added to the queue
        """
        # Get question with concepts
        question = await self._get_question_with_concepts(question_id)
        if not question:
            logger.warning(
                "reading_queue_question_not_found",
                question_id=str(question_id),
            )
            return 0

        # Get enrollment for course_id
        enrollment = await self._get_enrollment(enrollment_id)
        if not enrollment:
            logger.warning(
                "reading_queue_enrollment_not_found",
                enrollment_id=str(enrollment_id),
            )
            return 0

        # Determine if we should add reading materials
        chunks_to_add = self._determine_chunks_to_add(is_correct, difficulty)
        if chunks_to_add == 0:
            logger.debug(
                "reading_queue_skip",
                user_id=str(user_id),
                question_id=str(question_id),
                is_correct=is_correct,
                difficulty=difficulty,
                reason="correct_on_easy_medium",
            )
            return 0

        # Calculate priority based on KA competency
        ka_competency = await self._get_ka_competency(
            user_id, question.knowledge_area_id
        )
        priority = self._calculate_reading_priority(
            ka_competency, is_correct, difficulty
        )

        # Build semantic search query from concepts
        query_text = self._build_search_query(question)
        if not query_text:
            logger.warning(
                "reading_queue_no_query_text",
                question_id=str(question_id),
            )
            return 0

        # Search for relevant reading chunks
        try:
            chunk_results = await self._search_reading_chunks(
                query_text=query_text,
                course_id=enrollment.course_id,
                knowledge_area_id=question.knowledge_area_id,
                limit=chunks_to_add,
            )
        except Exception as e:
            logger.error(
                "reading_queue_search_failed",
                question_id=str(question_id),
                error=str(e),
            )
            return 0

        if not chunk_results:
            logger.debug(
                "reading_queue_no_chunks_found",
                question_id=str(question_id),
                query_text=query_text[:100],
                course_id=str(enrollment.course_id),
                knowledge_area_id=question.knowledge_area_id,
            )
            return 0

        # Get primary concept for triggered_by_concept_id
        primary_concept_id = self._get_primary_concept_id(question)

        # Add chunks to queue
        added_count = 0
        for result in chunk_results:
            try:
                chunk_id = UUID(result["id"])
                queue_item = ReadingQueueCreate(
                    user_id=user_id,
                    enrollment_id=enrollment_id,
                    chunk_id=chunk_id,
                    triggered_by_question_id=question_id,
                    triggered_by_concept_id=primary_concept_id,
                    priority=priority,
                )
                await self.reading_queue_repo.add_to_queue(queue_item)
                added_count += 1
            except Exception as e:
                logger.warning(
                    "reading_queue_add_failed",
                    chunk_id=result.get("id"),
                    error=str(e),
                )

        # Commit the reading queue items to ensure they're persisted
        # This is necessary because the reading queue population happens
        # after the main quiz answer logic, and we want to ensure items
        # are saved even if there's an issue with the outer transaction
        await self.session.commit()

        logger.info(
            "reading_queue_populated",
            user_id=str(user_id),
            session_id=str(session_id),
            question_id=str(question_id),
            is_correct=is_correct,
            difficulty=difficulty,
            priority=priority.value,
            chunks_added=added_count,
            ka_competency=round(ka_competency, 3),
        )

        return added_count

    def _determine_chunks_to_add(self, is_correct: bool, difficulty: float) -> int:
        """
        Determine how many chunks to add based on answer correctness and difficulty.

        Per AC 2-4:
        - Incorrect answers: 2-3 high-priority chunks
        - Correct on Hard: 1 medium-priority chunk (if enabled)
        - Correct on Easy/Medium: Skip (0 chunks)

        Args:
            is_correct: Whether the answer was correct
            difficulty: IRT b-parameter difficulty

        Returns:
            Number of chunks to add to queue
        """
        if not is_correct:
            # Incorrect answer: add 2-3 chunks
            return settings.READING_CHUNKS_INCORRECT

        # Correct answer - check if hard question
        is_hard = difficulty >= settings.READING_HARD_DIFFICULTY_THRESHOLD

        if is_hard and settings.READING_HARD_CORRECT_ENABLED:
            return settings.READING_CHUNKS_HARD_CORRECT

        # Correct on Easy/Medium: skip
        return 0

    def _calculate_reading_priority(
        self,
        ka_competency: float,
        is_correct: bool,
        difficulty: float,
    ) -> ReadingPriority:
        """
        Calculate reading priority based on competency and correctness.

        Per AC 7:
        - High: competency < 0.6 AND incorrect
        - Medium: 0.6 <= competency < 0.8 OR (correct AND hard)
        - Low: competency >= 0.8 AND correct

        Args:
            ka_competency: Average mastery in the knowledge area (0.0-1.0)
            is_correct: Whether the answer was correct
            difficulty: IRT b-parameter difficulty

        Returns:
            ReadingPriority enum value
        """
        is_hard = difficulty >= settings.READING_HARD_DIFFICULTY_THRESHOLD

        if not is_correct and ka_competency < settings.READING_PRIORITY_HIGH_THRESHOLD:
            return ReadingPriority.HIGH

        if (
            settings.READING_PRIORITY_HIGH_THRESHOLD <= ka_competency < settings.READING_PRIORITY_LOW_THRESHOLD
            or (is_correct and is_hard)
        ):
            return ReadingPriority.MEDIUM

        if ka_competency >= settings.READING_PRIORITY_LOW_THRESHOLD and is_correct:
            return ReadingPriority.LOW

        # Default to Medium for edge cases
        return ReadingPriority.MEDIUM

    async def _get_ka_competency(
        self,
        user_id: UUID,
        knowledge_area_id: str,
    ) -> float:
        """
        Calculate average mastery across all concepts in a Knowledge Area.

        Per Dev Notes:
        SELECT AVG(alpha / (alpha + beta))
        FROM belief_states bs
        JOIN concepts c ON bs.concept_id = c.id
        WHERE bs.user_id = :user_id AND c.knowledge_area_id = :ka_id

        Args:
            user_id: User UUID
            knowledge_area_id: Knowledge area ID

        Returns:
            Average mastery (0.0-1.0), defaults to 0.5 if no data
        """
        query = text("""
            SELECT AVG(bs.alpha / (bs.alpha + bs.beta)) as avg_mastery
            FROM belief_states bs
            JOIN concepts c ON bs.concept_id = c.id
            WHERE bs.user_id = :user_id
              AND c.knowledge_area_id = :ka_id
        """)
        result = await self.session.execute(
            query, {"user_id": str(user_id), "ka_id": knowledge_area_id}
        )
        row = result.fetchone()

        if row and row.avg_mastery is not None:
            return float(row.avg_mastery)

        # Default to 50% if no data (uninformative prior)
        return 0.5

    def _build_search_query(self, question: Question) -> str:
        """
        Build semantic search query from question concepts.

        Per AC 5:
        - Primary: Concept names from question_concepts
        - Secondary: Question text if concepts insufficient

        Args:
            question: Question model with loaded concepts

        Returns:
            Search query text
        """
        # Get concept names from question_concepts relationship
        concept_names = []
        if question.question_concepts:
            for qc in question.question_concepts:
                if qc.concept and qc.concept.name:
                    concept_names.append(qc.concept.name)

        if concept_names:
            return " ".join(concept_names)

        # Fallback to question text
        return question.question_text[:500]  # Limit length

    def _get_primary_concept_id(self, question: Question) -> UUID | None:
        """
        Get the primary concept ID from the question.

        Uses the concept with highest relevance score, or first if tied.

        Args:
            question: Question model

        Returns:
            Primary concept UUID or None
        """
        if not question.question_concepts:
            return None

        # Sort by relevance and get first
        sorted_concepts = sorted(
            question.question_concepts,
            key=lambda qc: qc.relevance,
            reverse=True,
        )

        if sorted_concepts and sorted_concepts[0].concept:
            return sorted_concepts[0].concept.id

        return None

    async def _search_reading_chunks(
        self,
        query_text: str,
        course_id: UUID,
        knowledge_area_id: str,
        limit: int,
    ) -> list[dict]:
        """
        Search Qdrant for relevant reading chunks.

        Generates embedding for query text and searches the reading_chunks
        collection with KA filtering.

        Args:
            query_text: Search query (concept names or question text)
            course_id: Course UUID for filtering
            knowledge_area_id: Knowledge area ID for filtering
            limit: Maximum results to return

        Returns:
            List of search results with id, score, payload
        """
        # Generate embedding for query
        async with EmbeddingService() as embedding_service:
            query_vector = await embedding_service.generate_embedding(query_text)

        # Search Qdrant
        results = await self.qdrant_repo.search_chunks(
            query_vector=query_vector,
            course_id=course_id,
            knowledge_area_id=knowledge_area_id,
            limit=limit,
        )

        return results

    async def _get_question_with_concepts(
        self, question_id: UUID
    ) -> Question | None:
        """
        Get question with loaded question_concepts relationship.

        Args:
            question_id: Question UUID

        Returns:
            Question model with concepts, or None if not found
        """
        from sqlalchemy.orm import selectinload

        result = await self.session.execute(
            select(Question)
            .options(
                selectinload(Question.question_concepts).selectinload(
                    QuestionConcept.concept
                )
            )
            .where(Question.id == question_id)
        )
        return result.scalar_one_or_none()

    async def _get_enrollment(self, enrollment_id: UUID) -> Enrollment | None:
        """
        Get enrollment by ID.

        Args:
            enrollment_id: Enrollment UUID

        Returns:
            Enrollment model or None
        """
        result = await self.session.execute(
            select(Enrollment).where(Enrollment.id == enrollment_id)
        )
        return result.scalar_one_or_none()


# Standalone function for Celery task
async def populate_reading_queue_async(
    user_id: str,
    enrollment_id: str,
    question_id: str,
    session_id: str,
    is_correct: bool,
    difficulty: float,
) -> dict:
    """
    Async function to populate reading queue, used by Celery task.

    Creates a fresh database engine for each task to avoid event loop issues
    in Celery fork workers.

    Args:
        user_id: User UUID string
        enrollment_id: Enrollment UUID string
        question_id: Question UUID string
        session_id: Quiz session UUID string
        is_correct: Whether the answer was correct
        difficulty: IRT b-parameter difficulty

    Returns:
        Dict with chunks_added and priority
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

    from src.config import settings

    # Create fresh engine for this task (avoids event loop issues in Celery fork workers)
    task_engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        pool_size=1,
        max_overflow=0,
        pool_pre_ping=True,
    )
    TaskSession = async_sessionmaker(
        task_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    try:
        async with TaskSession() as session:
            try:
                service = ReadingQueueService(session)
                chunks_added = await service.populate_reading_queue(
                    user_id=UUID(user_id),
                    enrollment_id=UUID(enrollment_id),
                    question_id=UUID(question_id),
                    session_id=UUID(session_id),
                    is_correct=is_correct,
                    difficulty=difficulty,
                )
                await session.commit()

                return {
                    "chunks_added": chunks_added,
                    "status": "success",
                }
            except Exception as e:
                await session.rollback()
                logger.error(
                    "reading_queue_task_failed",
                    user_id=user_id,
                    question_id=question_id,
                    error=str(e),
                )
                raise
    finally:
        # Clean up engine to avoid connection leaks
        await task_engine.dispose()
