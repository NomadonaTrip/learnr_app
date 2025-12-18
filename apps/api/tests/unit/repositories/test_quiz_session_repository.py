"""
Unit tests for QuizSessionRepository.
Tests database operations for quiz session management.
"""
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.user import User
from src.repositories.quiz_session_repository import QuizSessionRepository
from src.utils.auth import hash_password


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_course(db_session: AsyncSession):
    """Create a test course."""
    course = Course(
        slug=f"test-course-{uuid4().hex[:8]}",
        name="Test Course",
        description="A test course for repository tests",
        knowledge_areas=[
            {"id": "ka1", "name": "KA 1", "short_name": "KA1", "display_order": 1, "color": "#000"},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_user_for_quiz(db_session: AsyncSession):
    """Create a test user for quiz session tests."""
    user = User(
        email=f"quizuser_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_enrollment(db_session: AsyncSession, test_user_for_quiz, test_course):
    """Create a test enrollment."""
    enrollment = Enrollment(
        user_id=test_user_for_quiz.id,
        course_id=test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
def quiz_session_repo(db_session: AsyncSession):
    """Create QuizSessionRepository with test database."""
    return QuizSessionRepository(db_session)


# ============================================================================
# Session Creation Tests
# ============================================================================


class TestCreateSession:
    """Test session creation functionality."""

    @pytest.mark.asyncio
    async def test_create_session_success(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify session can be created with all required fields."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
            session_type="adaptive",
            question_strategy="max_info_gain",
        )

        assert session.id is not None
        assert session.user_id == test_user_for_quiz.id
        assert session.enrollment_id == test_enrollment.id
        assert session.session_type == "adaptive"
        assert session.question_strategy == "max_info_gain"
        assert session.knowledge_area_filter is None
        assert session.total_questions == 0
        assert session.correct_count == 0
        assert session.is_paused is False
        assert session.version == 1
        assert session.started_at is not None
        assert session.ended_at is None

    @pytest.mark.asyncio
    async def test_create_focused_session_with_filter(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify focused session with knowledge area filter."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
            session_type="focused",
            question_strategy="balanced",
            knowledge_area_filter="ba-planning",
        )

        assert session.session_type == "focused"
        assert session.question_strategy == "balanced"
        assert session.knowledge_area_filter == "ba-planning"


# ============================================================================
# Session Retrieval Tests
# ============================================================================


class TestGetActiveSession:
    """Test active session retrieval."""

    @pytest.mark.asyncio
    async def test_get_active_session_returns_session(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify active session can be retrieved."""
        created_session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        retrieved = await quiz_session_repo.get_active_session(
            user_id=test_user_for_quiz.id,
        )

        assert retrieved is not None
        assert retrieved.id == created_session.id

    @pytest.mark.asyncio
    async def test_get_active_session_returns_none_when_no_session(
        self, quiz_session_repo, test_user_for_quiz
    ):
        """Verify None returned when no active session exists."""
        retrieved = await quiz_session_repo.get_active_session(
            user_id=test_user_for_quiz.id,
        )

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_active_session_ignores_ended_sessions(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify ended sessions are not returned as active."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )
        await quiz_session_repo.mark_ended(session.id)

        retrieved = await quiz_session_repo.get_active_session(
            user_id=test_user_for_quiz.id,
        )

        assert retrieved is None


class TestGetSessionById:
    """Test session retrieval by ID."""

    @pytest.mark.asyncio
    async def test_get_session_by_id_returns_session(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify session can be retrieved by ID."""
        created_session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        retrieved = await quiz_session_repo.get_session_by_id(created_session.id)

        assert retrieved is not None
        assert retrieved.id == created_session.id

    @pytest.mark.asyncio
    async def test_get_session_by_id_returns_none_for_invalid_id(
        self, quiz_session_repo
    ):
        """Verify None returned for non-existent session ID."""
        retrieved = await quiz_session_repo.get_session_by_id(uuid4())

        assert retrieved is None


# ============================================================================
# Question Count Update Tests
# ============================================================================


class TestIncrementQuestionCount:
    """Test question count increment functionality."""

    @pytest.mark.asyncio
    async def test_increment_question_count_correct(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify increment with correct answer."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )
        assert session.total_questions == 0
        assert session.correct_count == 0

        updated = await quiz_session_repo.increment_question_count(
            session.id, is_correct=True
        )

        assert updated.total_questions == 1
        assert updated.correct_count == 1

    @pytest.mark.asyncio
    async def test_increment_question_count_incorrect(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify increment with incorrect answer."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        updated = await quiz_session_repo.increment_question_count(
            session.id, is_correct=False
        )

        assert updated.total_questions == 1
        assert updated.correct_count == 0

    @pytest.mark.asyncio
    async def test_increment_question_count_multiple_times(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify multiple increments work correctly."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        # Simulate 5 correct and 3 incorrect answers
        for _ in range(5):
            await quiz_session_repo.increment_question_count(session.id, is_correct=True)
        for _ in range(3):
            await quiz_session_repo.increment_question_count(session.id, is_correct=False)

        updated = await quiz_session_repo.get_session_by_id(session.id)
        assert updated.total_questions == 8
        assert updated.correct_count == 5

    @pytest.mark.asyncio
    async def test_increment_question_count_raises_for_invalid_session(
        self, quiz_session_repo
    ):
        """Verify error raised for non-existent session."""
        with pytest.raises(ValueError, match="not found"):
            await quiz_session_repo.increment_question_count(uuid4(), is_correct=True)


# ============================================================================
# Pause/Resume Tests
# ============================================================================


class TestMarkPaused:
    """Test marking session as paused."""

    @pytest.mark.asyncio
    async def test_mark_paused_sets_flag(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify mark_paused sets is_paused to True."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )
        assert session.is_paused is False

        updated = await quiz_session_repo.mark_paused(session.id)

        assert updated.is_paused is True

    @pytest.mark.asyncio
    async def test_mark_paused_raises_for_invalid_session(
        self, quiz_session_repo
    ):
        """Verify error raised for non-existent session."""
        with pytest.raises(ValueError, match="not found"):
            await quiz_session_repo.mark_paused(uuid4())


class TestMarkResumed:
    """Test marking session as resumed."""

    @pytest.mark.asyncio
    async def test_mark_resumed_clears_flag(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify mark_resumed sets is_paused to False."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )
        await quiz_session_repo.mark_paused(session.id)

        updated = await quiz_session_repo.mark_resumed(session.id)

        assert updated.is_paused is False

    @pytest.mark.asyncio
    async def test_mark_resumed_raises_for_invalid_session(
        self, quiz_session_repo
    ):
        """Verify error raised for non-existent session."""
        with pytest.raises(ValueError, match="not found"):
            await quiz_session_repo.mark_resumed(uuid4())


# ============================================================================
# End Session Tests
# ============================================================================


class TestMarkEnded:
    """Test marking session as ended."""

    @pytest.mark.asyncio
    async def test_mark_ended_sets_ended_at(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify mark_ended sets ended_at timestamp."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )
        assert session.ended_at is None

        updated = await quiz_session_repo.mark_ended(session.id)

        assert updated.ended_at is not None

    @pytest.mark.asyncio
    async def test_mark_ended_raises_for_invalid_session(
        self, quiz_session_repo
    ):
        """Verify error raised for non-existent session."""
        with pytest.raises(ValueError, match="not found"):
            await quiz_session_repo.mark_ended(uuid4())


# ============================================================================
# Batch Expiration Tests
# ============================================================================


class TestExpireStaleSessions:
    """Test batch session expiration."""

    @pytest.mark.asyncio
    async def test_expire_stale_sessions_expires_old_sessions(
        self, quiz_session_repo, db_session, test_user_for_quiz, test_enrollment
    ):
        """Verify old sessions are expired in batch."""
        # Create a session
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        # Manually update updated_at to be old (3 hours ago)
        from sqlalchemy import update
        from src.models.quiz_session import QuizSession

        await db_session.execute(
            update(QuizSession)
            .where(QuizSession.id == session.id)
            .values(updated_at=datetime.now(timezone.utc) - timedelta(hours=3))
        )
        await db_session.flush()

        # Expire stale sessions (2 hour timeout)
        expired_count = await quiz_session_repo.expire_stale_sessions(timeout_hours=2)

        assert expired_count == 1

        # Verify session ended_at is set
        updated = await quiz_session_repo.get_session_by_id(session.id)
        assert updated.ended_at is not None

    @pytest.mark.asyncio
    async def test_expire_stale_sessions_does_not_expire_recent_sessions(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify recent sessions are not expired."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        expired_count = await quiz_session_repo.expire_stale_sessions(timeout_hours=2)

        assert expired_count == 0

        updated = await quiz_session_repo.get_session_by_id(session.id)
        assert updated.ended_at is None

    @pytest.mark.asyncio
    async def test_expire_stale_sessions_ignores_already_ended(
        self, quiz_session_repo, db_session, test_user_for_quiz, test_enrollment
    ):
        """Verify already ended sessions are not expired again."""
        # Create and end a session
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )
        await quiz_session_repo.mark_ended(session.id)

        # Make it old
        from sqlalchemy import update
        from src.models.quiz_session import QuizSession

        await db_session.execute(
            update(QuizSession)
            .where(QuizSession.id == session.id)
            .values(updated_at=datetime.now(timezone.utc) - timedelta(hours=5))
        )
        await db_session.flush()

        # Try to expire
        expired_count = await quiz_session_repo.expire_stale_sessions(timeout_hours=2)

        # Should not expire already-ended session
        assert expired_count == 0


class TestGetStaleSessions:
    """Test retrieving stale sessions."""

    @pytest.mark.asyncio
    async def test_get_stale_sessions_returns_old_sessions(
        self, quiz_session_repo, db_session, test_user_for_quiz, test_enrollment
    ):
        """Verify stale sessions are returned."""
        session = await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        # Make it old
        from sqlalchemy import update
        from src.models.quiz_session import QuizSession

        await db_session.execute(
            update(QuizSession)
            .where(QuizSession.id == session.id)
            .values(updated_at=datetime.now(timezone.utc) - timedelta(hours=3))
        )
        await db_session.flush()

        stale = await quiz_session_repo.get_stale_sessions(timeout_hours=2)

        assert len(stale) == 1
        assert stale[0].id == session.id

    @pytest.mark.asyncio
    async def test_get_stale_sessions_returns_empty_for_recent(
        self, quiz_session_repo, test_user_for_quiz, test_enrollment
    ):
        """Verify no sessions returned when all are recent."""
        await quiz_session_repo.create_session(
            user_id=test_user_for_quiz.id,
            enrollment_id=test_enrollment.id,
        )

        stale = await quiz_session_repo.get_stale_sessions(timeout_hours=2)

        assert len(stale) == 0
