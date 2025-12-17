"""
Unit tests for DiagnosticSessionRepository.
Tests database operations for diagnostic session management.
"""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.user import User
from src.repositories.diagnostic_session_repository import DiagnosticSessionRepository
from src.utils.auth import hash_password


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_course(db_session: AsyncSession):
    """Create a test course."""
    course = Course(
        slug="test-course",
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
async def test_user_for_session(db_session: AsyncSession):
    """Create a test user for session tests."""
    user = User(
        email=f"sessionuser_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_enrollment(db_session: AsyncSession, test_user_for_session, test_course):
    """Create a test enrollment."""
    enrollment = Enrollment(
        user_id=test_user_for_session.id,
        course_id=test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
def session_repo(db_session: AsyncSession):
    """Create DiagnosticSessionRepository with test database."""
    return DiagnosticSessionRepository(db_session)


# ============================================================================
# Session Creation Tests
# ============================================================================


class TestCreateSession:
    """Test session creation functionality."""

    @pytest.mark.asyncio
    async def test_create_session_success(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify session can be created with all required fields."""
        question_ids = [str(uuid4()) for _ in range(15)]

        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=question_ids,
        )

        assert session.id is not None
        assert session.user_id == test_user_for_session.id
        assert session.enrollment_id == test_enrollment.id
        assert session.question_ids == question_ids
        assert session.current_index == 0
        assert session.status == "in_progress"
        assert session.started_at is not None

    @pytest.mark.asyncio
    async def test_create_session_initializes_index_to_zero(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify new session starts at index 0."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        assert session.current_index == 0


# ============================================================================
# Session Retrieval Tests
# ============================================================================


class TestGetActiveSession:
    """Test active session retrieval."""

    @pytest.mark.asyncio
    async def test_get_active_session_returns_session(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify active session can be retrieved."""
        created_session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        retrieved = await session_repo.get_active_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
        )

        assert retrieved is not None
        assert retrieved.id == created_session.id

    @pytest.mark.asyncio
    async def test_get_active_session_returns_none_when_no_session(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify None returned when no active session exists."""
        retrieved = await session_repo.get_active_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
        )

        assert retrieved is None

    @pytest.mark.asyncio
    async def test_get_active_session_ignores_completed_sessions(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify completed sessions are not returned as active."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )
        await session_repo.mark_completed(session.id)

        retrieved = await session_repo.get_active_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
        )

        assert retrieved is None


class TestGetSessionById:
    """Test session retrieval by ID."""

    @pytest.mark.asyncio
    async def test_get_session_by_id_returns_session(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify session can be retrieved by ID."""
        created_session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        retrieved = await session_repo.get_session_by_id(created_session.id)

        assert retrieved is not None
        assert retrieved.id == created_session.id

    @pytest.mark.asyncio
    async def test_get_session_by_id_returns_none_for_invalid_id(
        self, session_repo
    ):
        """Verify None returned for non-existent session ID."""
        retrieved = await session_repo.get_session_by_id(uuid4())

        assert retrieved is None


# ============================================================================
# Progress Update Tests
# ============================================================================


class TestIncrementProgress:
    """Test progress increment functionality."""

    @pytest.mark.asyncio
    async def test_increment_progress_increases_index(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify increment_progress increases current_index."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4()) for _ in range(5)],
        )
        assert session.current_index == 0

        updated = await session_repo.increment_progress(session.id)

        assert updated.current_index == 1

    @pytest.mark.asyncio
    async def test_increment_progress_multiple_times(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify multiple increments work correctly."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4()) for _ in range(10)],
        )

        for expected_index in range(1, 6):
            updated = await session_repo.increment_progress(session.id)
            assert updated.current_index == expected_index

    @pytest.mark.asyncio
    async def test_increment_progress_raises_for_invalid_session(
        self, session_repo
    ):
        """Verify error raised for non-existent session."""
        with pytest.raises(ValueError, match="not found"):
            await session_repo.increment_progress(uuid4())


# ============================================================================
# Status Update Tests
# ============================================================================


class TestMarkCompleted:
    """Test marking session as completed."""

    @pytest.mark.asyncio
    async def test_mark_completed_changes_status(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify mark_completed sets status to 'completed'."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        updated = await session_repo.mark_completed(session.id)

        assert updated.status == "completed"
        assert updated.completed_at is not None


class TestMarkExpired:
    """Test marking session as expired."""

    @pytest.mark.asyncio
    async def test_mark_expired_changes_status(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify mark_expired sets status to 'expired'."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        updated = await session_repo.mark_expired(session.id)

        assert updated.status == "expired"


class TestMarkReset:
    """Test marking session as reset."""

    @pytest.mark.asyncio
    async def test_mark_reset_changes_status(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify mark_reset sets status to 'reset'."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        updated = await session_repo.mark_reset(session.id)

        assert updated.status == "reset"


# ============================================================================
# Batch Expiration Tests
# ============================================================================


class TestExpireStaleSessions:
    """Test batch session expiration."""

    @pytest.mark.asyncio
    async def test_expire_stale_sessions_expires_old_sessions(
        self, session_repo, db_session, test_user_for_session, test_enrollment
    ):
        """Verify old sessions are expired in batch."""
        # Create a session with old started_at
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        # Manually update started_at to be old
        from sqlalchemy import update
        from src.models.diagnostic_session import DiagnosticSession

        await db_session.execute(
            update(DiagnosticSession)
            .where(DiagnosticSession.id == session.id)
            .values(started_at=datetime.utcnow() - timedelta(minutes=35))
        )
        await db_session.flush()

        # Expire stale sessions
        expired_count = await session_repo.expire_stale_sessions(timeout_minutes=30)

        assert expired_count == 1

        # Verify session status changed
        updated = await session_repo.get_session_by_id(session.id)
        assert updated.status == "expired"

    @pytest.mark.asyncio
    async def test_expire_stale_sessions_does_not_expire_recent_sessions(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify recent sessions are not expired."""
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        expired_count = await session_repo.expire_stale_sessions(timeout_minutes=30)

        assert expired_count == 0

        updated = await session_repo.get_session_by_id(session.id)
        assert updated.status == "in_progress"


# ============================================================================
# Completed Session Retrieval Tests
# ============================================================================


class TestGetCompletedSession:
    """Test completed session retrieval."""

    @pytest.mark.asyncio
    async def test_get_completed_session_returns_most_recent(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify most recent completed session is returned."""
        # Create and complete a session
        session = await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )
        await session_repo.mark_completed(session.id)

        retrieved = await session_repo.get_completed_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
        )

        assert retrieved is not None
        assert retrieved.id == session.id
        assert retrieved.status == "completed"

    @pytest.mark.asyncio
    async def test_get_completed_session_returns_none_when_none_completed(
        self, session_repo, test_user_for_session, test_enrollment
    ):
        """Verify None returned when no completed sessions exist."""
        # Create session but don't complete it
        await session_repo.create_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
            question_ids=[str(uuid4())],
        )

        retrieved = await session_repo.get_completed_session(
            user_id=test_user_for_session.id,
            enrollment_id=test_enrollment.id,
        )

        assert retrieved is None
