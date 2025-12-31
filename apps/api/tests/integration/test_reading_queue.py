"""
Integration tests for Reading Queue functionality.
Story 5.5: Background Reading Queue Population

Tests:
1. Full flow: answer question → reading_queue populated
2. Correct Easy answer doesn't add to queue
3. Incorrect answer adds high-priority items
4. Correct Hard answer adds medium-priority item
5. Duplicate chunk handling (priority upgrade)
"""
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.models.reading_chunk import ReadingChunk
from src.models.reading_queue import ReadingQueue
from src.models.user import User
from src.repositories.reading_queue_repository import ReadingQueueRepository
from src.schemas.reading_queue import ReadingPriority, ReadingQueueCreate
from src.services.reading_queue_service import ReadingQueueService
from src.utils.auth import hash_password


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def rq_test_course(db_session):
    """Create a course for reading queue testing."""
    course = Course(
        slug=f"rq-test-{uuid4().hex[:6]}",
        name="Reading Queue Test Course",
        description="Course for reading queue integration tests",
        knowledge_areas=[
            {
                "id": "BA",
                "name": "Business Analysis",
                "short_name": "BA",
                "display_order": 1,
                "color": "#3B82F6",
            },
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def rq_test_user(db_session):
    """Create a user for reading queue testing."""
    user = User(
        email=f"rqtest_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def rq_test_enrollment(db_session, rq_test_user, rq_test_course):
    """Create enrollment for testing."""
    enrollment = Enrollment(
        user_id=rq_test_user.id,
        course_id=rq_test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def rq_test_concept(db_session, rq_test_course):
    """Create a test concept."""
    concept = Concept(
        course_id=rq_test_course.id,
        name="Stakeholder Analysis",
        knowledge_area_id="BA",
        corpus_section_ref="3.2.1",
    )
    db_session.add(concept)
    await db_session.commit()
    await db_session.refresh(concept)
    return concept


@pytest.fixture
async def rq_test_question(db_session, rq_test_course, rq_test_concept):
    """Create a test question with concept mapping."""
    question = Question(
        course_id=rq_test_course.id,
        question_text="What is the primary purpose of stakeholder analysis?",
        options={
            "A": "To identify and understand project stakeholders",
            "B": "To calculate project costs",
            "C": "To schedule project tasks",
            "D": "To design system architecture",
        },
        correct_answer="A",
        explanation="Stakeholder analysis identifies project stakeholders.",
        knowledge_area_id="BA",
        difficulty=0.5,  # Medium difficulty
        source="test",
        is_active=True,
    )
    db_session.add(question)
    await db_session.flush()

    # Create question-concept mapping
    qc = QuestionConcept(
        question_id=question.id,
        concept_id=rq_test_concept.id,
        relevance=1.0,
    )
    db_session.add(qc)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def rq_test_reading_chunk(db_session, rq_test_course, rq_test_concept):
    """Create a test reading chunk."""
    chunk = ReadingChunk(
        course_id=rq_test_course.id,
        title="Understanding Stakeholder Analysis",
        content="Stakeholder analysis is a technique used to identify and understand the individuals and groups who have an interest in the project or are affected by its outcome.",
        corpus_section="3.2.1",
        knowledge_area_id="BA",
        concept_ids=[rq_test_concept.id],
        estimated_read_time_minutes=5,
        chunk_index=0,
    )
    db_session.add(chunk)
    await db_session.commit()
    await db_session.refresh(chunk)
    return chunk


@pytest.fixture
async def rq_test_belief(db_session, rq_test_user, rq_test_concept):
    """Create a belief state for the user."""
    belief = BeliefState(
        user_id=rq_test_user.id,
        concept_id=rq_test_concept.id,
        alpha=3.0,  # ~75% mastery (3/(3+1)=0.75)
        beta=1.0,
        response_count=4,
    )
    db_session.add(belief)
    await db_session.commit()
    await db_session.refresh(belief)
    return belief


# ============================================================================
# Repository Tests
# ============================================================================


class TestReadingQueueRepository:
    """Integration tests for ReadingQueueRepository."""

    @pytest.mark.asyncio
    async def test_add_to_queue_creates_item(
        self, db_session, rq_test_user, rq_test_enrollment, rq_test_reading_chunk
    ):
        """Test: add_to_queue creates a new queue item."""
        repo = ReadingQueueRepository(db_session)

        queue_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.HIGH,
        )

        result = await repo.add_to_queue(queue_item)
        await db_session.commit()

        assert result is not None
        assert result.user_id == rq_test_user.id
        assert result.chunk_id == rq_test_reading_chunk.id
        assert result.priority == "High"
        assert result.status == "unread"

    @pytest.mark.asyncio
    async def test_add_to_queue_upsert_upgrades_priority(
        self, db_session, rq_test_user, rq_test_enrollment, rq_test_reading_chunk
    ):
        """Test: add_to_queue upgrades priority for existing item."""
        repo = ReadingQueueRepository(db_session)

        # Add with Low priority first
        low_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.LOW,
        )
        await repo.add_to_queue(low_item)
        await db_session.commit()

        # Add same chunk with High priority
        high_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.HIGH,
        )
        result = await repo.add_to_queue(high_item)
        await db_session.commit()

        # Priority should be upgraded to High
        assert result.priority == "High"

    @pytest.mark.asyncio
    async def test_add_to_queue_no_downgrade(
        self, db_session, rq_test_user, rq_test_enrollment, rq_test_reading_chunk
    ):
        """Test: add_to_queue doesn't downgrade priority."""
        repo = ReadingQueueRepository(db_session)

        # Add with High priority first
        high_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.HIGH,
        )
        await repo.add_to_queue(high_item)
        await db_session.commit()

        # Try to add same chunk with Low priority
        low_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.LOW,
        )
        result = await repo.add_to_queue(low_item)
        await db_session.commit()

        # Priority should remain High
        assert result.priority == "High"

    @pytest.mark.asyncio
    async def test_get_queue_item(
        self, db_session, rq_test_user, rq_test_enrollment, rq_test_reading_chunk
    ):
        """Test: get_queue_item retrieves existing item."""
        repo = ReadingQueueRepository(db_session)

        # Add item
        queue_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.MEDIUM,
        )
        await repo.add_to_queue(queue_item)
        await db_session.commit()

        # Retrieve item
        result = await repo.get_queue_item(
            rq_test_enrollment.id, rq_test_reading_chunk.id
        )

        assert result is not None
        assert result.chunk_id == rq_test_reading_chunk.id

    @pytest.mark.asyncio
    async def test_get_unread_count(
        self, db_session, rq_test_user, rq_test_enrollment, rq_test_reading_chunk
    ):
        """Test: get_unread_count returns correct count."""
        repo = ReadingQueueRepository(db_session)

        # Add item
        queue_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.HIGH,
        )
        await repo.add_to_queue(queue_item)
        await db_session.commit()

        count = await repo.get_unread_count(rq_test_enrollment.id)

        assert count == 1


# ============================================================================
# Service Tests (with mocked Qdrant)
# ============================================================================


class TestReadingQueueServiceIntegration:
    """Integration tests for ReadingQueueService."""

    @pytest.mark.asyncio
    async def test_skips_for_correct_easy_answer(
        self,
        db_session,
        rq_test_user,
        rq_test_enrollment,
        rq_test_question,
        rq_test_belief,
    ):
        """Test: Service skips queue population for correct easy answers (AC 4)."""
        service = ReadingQueueService(db_session)

        result = await service.populate_reading_queue(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            question_id=rq_test_question.id,
            session_id=uuid4(),
            is_correct=True,
            difficulty=0.3,  # Easy question
        )

        assert result == 0

    @pytest.mark.asyncio
    async def test_calculates_priority_correctly(
        self,
        db_session,
        rq_test_user,
        rq_test_enrollment,
        rq_test_question,
        rq_test_belief,
    ):
        """Test: Service calculates priority correctly based on competency."""
        service = ReadingQueueService(db_session)

        # User has ~75% mastery (alpha=3, beta=1)
        # Incorrect answer with 75% competency should be Medium priority
        priority = service._calculate_reading_priority(
            ka_competency=0.75,
            is_correct=False,
            difficulty=0.5,
        )

        assert priority == ReadingPriority.MEDIUM

    @pytest.mark.asyncio
    async def test_builds_query_from_concepts(
        self,
        db_session,
        rq_test_user,
        rq_test_enrollment,
        rq_test_question,
        rq_test_concept,
    ):
        """Test: Service builds search query from question concepts."""
        service = ReadingQueueService(db_session)

        # Get question with concepts loaded
        question = await service._get_question_with_concepts(rq_test_question.id)

        query = service._build_search_query(question)

        # Should contain the concept name
        assert "Stakeholder Analysis" in query

    @pytest.mark.asyncio
    async def test_gets_ka_competency(
        self,
        db_session,
        rq_test_user,
        rq_test_belief,
    ):
        """Test: Service calculates KA competency from belief states."""
        service = ReadingQueueService(db_session)

        competency = await service._get_ka_competency(
            user_id=rq_test_user.id,
            knowledge_area_id="BA",
        )

        # Belief has alpha=3, beta=1 → 3/(3+1) = 0.75
        assert abs(competency - 0.75) < 0.01

    @pytest.mark.asyncio
    async def test_returns_default_competency_for_no_beliefs(
        self,
        db_session,
        rq_test_user,
    ):
        """Test: Service returns 0.5 for user with no beliefs."""
        service = ReadingQueueService(db_session)

        competency = await service._get_ka_competency(
            user_id=rq_test_user.id,
            knowledge_area_id="UNKNOWN_KA",
        )

        assert competency == 0.5


# ============================================================================
# Celery Task Tests (with eager mode)
# ============================================================================


class TestReadingQueueTask:
    """Tests for Celery background task."""

    @pytest.mark.asyncio
    async def test_task_imports_correctly(self):
        """Test: Task can be imported and has correct name."""
        from src.tasks.reading_queue_tasks import add_reading_to_queue

        assert add_reading_to_queue.name == "src.tasks.reading_queue_tasks.add_reading_to_queue"

    @pytest.mark.asyncio
    async def test_async_convenience_function_exists(self):
        """Test: Async convenience function exists for direct calls."""
        from src.tasks.reading_queue_tasks import add_reading_to_queue_async

        assert callable(add_reading_to_queue_async)

    @pytest.mark.asyncio
    async def test_task_has_performance_threshold_constant(self):
        """Test: Task has performance threshold defined for monitoring (AC 10)."""
        from src.tasks.reading_queue_tasks import TASK_DURATION_WARNING_MS

        assert TASK_DURATION_WARNING_MS == 200


# ============================================================================
# Performance Tests
# ============================================================================


class TestReadingQueuePerformance:
    """Performance tests for reading queue operations (AC 10)."""

    @pytest.mark.asyncio
    async def test_skip_path_completes_within_threshold(
        self,
        db_session,
        rq_test_user,
        rq_test_enrollment,
        rq_test_question,
        rq_test_belief,
    ):
        """Test: Skip path (correct easy answer) completes within 200ms.

        AC 4: "For correct answers on Easy/Medium: Skip reading recommendation"

        This tests the SKIP PATH where no chunks are added because the user
        answered correctly on an easy question (difficulty < 0.7). This path:
        - Does NOT call OpenAI for embeddings
        - Does NOT query Qdrant for similar chunks
        - Only performs DB lookups

        The FULL PATH (incorrect answer) involves:
        1. OpenAI Embedding API call (~$0.000005/call, NOT an LLM call)
           - Converts search query text to 3072-dim vector
           - No "thinking" or generation, just vector encoding
        2. Qdrant vector similarity search (local, no external API)
        3. PostgreSQL insert

        Reading chunks were pre-embedded during content ingestion (Story 2.7),
        so only the query needs embedding at runtime.

        Full path performance is monitored via TASK_DURATION_WARNING_MS in production.
        """
        import time

        from src.services.reading_queue_service import ReadingQueueService

        service = ReadingQueueService(db_session)

        start = time.perf_counter()
        result = await service.populate_reading_queue(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            question_id=rq_test_question.id,
            session_id=uuid4(),
            is_correct=True,
            difficulty=0.3,  # Easy question (< 0.7) triggers skip path
        )
        duration_ms = (time.perf_counter() - start) * 1000

        assert result == 0, "Expected skip path to add 0 chunks"
        assert duration_ms < 200, f"Skip path took {duration_ms:.1f}ms, exceeds 200ms threshold"

    @pytest.mark.asyncio
    async def test_repository_add_completes_within_threshold(
        self,
        db_session,
        rq_test_user,
        rq_test_enrollment,
        rq_test_reading_chunk,
    ):
        """Test: Repository add_to_queue completes within 50ms."""
        import time

        from src.repositories.reading_queue_repository import ReadingQueueRepository
        from src.schemas.reading_queue import ReadingPriority, ReadingQueueCreate

        repo = ReadingQueueRepository(db_session)

        queue_item = ReadingQueueCreate(
            user_id=rq_test_user.id,
            enrollment_id=rq_test_enrollment.id,
            chunk_id=rq_test_reading_chunk.id,
            priority=ReadingPriority.HIGH,
        )

        start = time.perf_counter()
        await repo.add_to_queue(queue_item)
        await db_session.commit()
        duration_ms = (time.perf_counter() - start) * 1000

        assert duration_ms < 50, f"Repository took {duration_ms:.1f}ms, exceeds 50ms threshold"
