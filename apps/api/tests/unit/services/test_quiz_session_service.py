"""
Unit tests for QuizSessionService.
Tests session management lifecycle including creation, pause/resume, and termination.
"""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.schemas.quiz_session import QuestionStrategy, QuizSessionCreate, QuizSessionType
from src.services.quiz_session_service import QuizSessionService

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session_repo():
    """Create mock QuizSessionRepository."""
    return AsyncMock()


@pytest.fixture
def session_service(mock_session_repo):
    """Create QuizSessionService with mock dependencies."""
    return QuizSessionService(session_repo=mock_session_repo)


def create_mock_session(
    session_id=None,
    user_id=None,
    enrollment_id=None,
    session_type="adaptive",
    question_strategy="max_info_gain",
    knowledge_area_filter=None,
    question_target=10,
    started_at=None,
    ended_at=None,
    total_questions=0,
    correct_count=0,
    is_paused=False,
    version=1,
    updated_at=None,
):
    """Helper to create mock QuizSession."""
    session = MagicMock()
    session.id = session_id or uuid4()
    session.user_id = user_id or uuid4()
    session.enrollment_id = enrollment_id or uuid4()
    session.session_type = session_type
    session.question_strategy = question_strategy
    session.knowledge_area_filter = knowledge_area_filter
    session.question_target = question_target
    session.started_at = started_at or datetime.now(UTC)
    session.ended_at = ended_at
    session.total_questions = total_questions
    session.correct_count = correct_count
    session.is_paused = is_paused
    session.version = version
    session.updated_at = updated_at or datetime.now(UTC)

    # Compute status property
    if ended_at:
        session.status = "completed"
    elif is_paused:
        session.status = "paused"
    else:
        session.status = "active"

    # Compute accuracy property
    if total_questions > 0:
        session.accuracy = (correct_count / total_questions) * 100.0
    else:
        session.accuracy = 0.0

    return session


# ============================================================================
# Session Start Tests
# ============================================================================


class TestSessionStart:
    """Test starting quiz sessions."""

    @pytest.mark.asyncio
    async def test_creates_new_session_when_none_exists(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify new session created when no active session exists."""
        user_id = uuid4()
        enrollment_id = uuid4()

        # No existing session
        mock_session_repo.get_active_session.return_value = None

        # Mock session creation
        new_session = create_mock_session(user_id=user_id, enrollment_id=enrollment_id)
        mock_session_repo.create_session.return_value = new_session

        session_data = QuizSessionCreate()
        session, is_resumed = await session_service.start_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_data=session_data,
        )

        assert session == new_session
        assert is_resumed is False
        mock_session_repo.create_session.assert_called_once_with(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_type="adaptive",
            question_strategy="max_info_gain",
            knowledge_area_filter=None,
            target_concept_ids=None,
        )

    @pytest.mark.asyncio
    async def test_returns_existing_active_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify active session is returned, not recreated."""
        user_id = uuid4()
        enrollment_id = uuid4()

        # Existing active session
        existing_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            updated_at=datetime.now(UTC) - timedelta(minutes=30),
        )
        mock_session_repo.get_active_session.return_value = existing_session

        session_data = QuizSessionCreate()
        session, is_resumed = await session_service.start_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_data=session_data,
        )

        assert session == existing_session
        assert is_resumed is True
        mock_session_repo.create_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_ends_expired_session_creates_new(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify expired session is ended and new session created."""
        user_id = uuid4()
        enrollment_id = uuid4()

        # Expired session (3 hours old)
        expired_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            updated_at=datetime.now(UTC) - timedelta(hours=3),
        )
        mock_session_repo.get_active_session.return_value = expired_session

        # New session
        new_session = create_mock_session(user_id=user_id, enrollment_id=enrollment_id)
        mock_session_repo.create_session.return_value = new_session

        session_data = QuizSessionCreate()
        session, is_resumed = await session_service.start_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_data=session_data,
        )

        # Old session should be ended
        mock_session_repo.mark_ended.assert_called_once_with(expired_session.id)

        # New session should be created
        assert session == new_session
        assert is_resumed is False

    @pytest.mark.asyncio
    async def test_creates_focused_session_with_filter(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify focused session with knowledge area filter."""
        user_id = uuid4()
        enrollment_id = uuid4()

        mock_session_repo.get_active_session.return_value = None

        new_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_type="focused",
            knowledge_area_filter="ba-planning",
        )
        mock_session_repo.create_session.return_value = new_session

        session_data = QuizSessionCreate(
            session_type=QuizSessionType.FOCUSED,
            question_strategy=QuestionStrategy.BALANCED,
            knowledge_area_filter="ba-planning",
        )
        session, is_resumed = await session_service.start_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_data=session_data,
        )

        mock_session_repo.create_session.assert_called_once_with(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_type="focused",
            question_strategy="balanced",
            knowledge_area_filter="ba-planning",
            target_concept_ids=None,
        )

    @pytest.mark.asyncio
    async def test_creates_focused_ka_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Story 4.8: Verify focused_ka session creation."""
        user_id = uuid4()
        enrollment_id = uuid4()

        mock_session_repo.get_active_session.return_value = None

        new_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_type="focused_ka",
            knowledge_area_filter="ka-requirements",
        )
        mock_session_repo.create_session.return_value = new_session

        session_data = QuizSessionCreate(
            session_type=QuizSessionType.FOCUSED_KA,
            knowledge_area_filter="ka-requirements",
        )
        session, is_resumed = await session_service.start_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_data=session_data,
        )

        assert session == new_session
        assert is_resumed is False
        assert mock_session_repo.create_session.called

    @pytest.mark.asyncio
    async def test_creates_focused_concept_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Story 4.8: Verify focused_concept session creation with target concepts."""
        user_id = uuid4()
        enrollment_id = uuid4()
        concept_id_1 = uuid4()
        concept_id_2 = uuid4()

        mock_session_repo.get_active_session.return_value = None

        new_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_type="focused_concept",
        )
        # Add target_concept_ids attribute
        new_session.target_concept_ids = [str(concept_id_1), str(concept_id_2)]
        mock_session_repo.create_session.return_value = new_session

        session_data = QuizSessionCreate(
            session_type=QuizSessionType.FOCUSED_CONCEPT,
            target_concept_ids=[concept_id_1, concept_id_2],
        )
        session, is_resumed = await session_service.start_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            session_data=session_data,
        )

        assert session == new_session
        assert is_resumed is False
        assert mock_session_repo.create_session.called


# ============================================================================
# Session Get Tests
# ============================================================================


class TestSessionGet:
    """Test getting session details."""

    @pytest.mark.asyncio
    async def test_get_session_returns_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify get_session returns session for owner."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(session_id=session_id, user_id=user_id)
        mock_session_repo.get_session_by_id.return_value = session

        result = await session_service.get_session(session_id, user_id)

        assert result == session
        mock_session_repo.get_session_by_id.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_get_session_not_found(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify get_session raises for non-existent session."""
        mock_session_repo.get_session_by_id.return_value = None

        with pytest.raises(ValueError, match="not found"):
            await session_service.get_session(uuid4(), uuid4())

    @pytest.mark.asyncio
    async def test_get_session_wrong_user(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify get_session raises for wrong user."""
        session_user = uuid4()
        other_user = uuid4()
        session_id = uuid4()

        session = create_mock_session(session_id=session_id, user_id=session_user)
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="Unauthorized"):
            await session_service.get_session(session_id, other_user)


# ============================================================================
# Session Pause Tests
# ============================================================================


class TestSessionPause:
    """Test pausing quiz sessions."""

    @pytest.mark.asyncio
    async def test_pause_session_success(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify session can be paused."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(session_id=session_id, user_id=user_id)
        mock_session_repo.get_session_by_id.return_value = session

        paused_session = create_mock_session(
            session_id=session_id, user_id=user_id, is_paused=True
        )
        mock_session_repo.mark_paused.return_value = paused_session

        result = await session_service.pause_session(session_id, user_id)

        assert result.is_paused is True
        mock_session_repo.mark_paused.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_pause_already_paused_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify cannot pause already paused session."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(session_id=session_id, user_id=user_id, is_paused=True)
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="already paused"):
            await session_service.pause_session(session_id, user_id)

    @pytest.mark.asyncio
    async def test_pause_ended_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify cannot pause ended session."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            ended_at=datetime.now(UTC),
        )
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="Cannot pause ended session"):
            await session_service.pause_session(session_id, user_id)

    @pytest.mark.asyncio
    async def test_pause_expired_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify cannot pause expired session."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            updated_at=datetime.now(UTC) - timedelta(hours=3),
        )
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="expired"):
            await session_service.pause_session(session_id, user_id)


# ============================================================================
# Session Resume Tests
# ============================================================================


class TestSessionResume:
    """Test resuming paused quiz sessions."""

    @pytest.mark.asyncio
    async def test_resume_session_success(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify paused session can be resumed."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(session_id=session_id, user_id=user_id, is_paused=True)
        mock_session_repo.get_session_by_id.return_value = session

        resumed_session = create_mock_session(
            session_id=session_id, user_id=user_id, is_paused=False
        )
        mock_session_repo.mark_resumed.return_value = resumed_session

        result = await session_service.resume_session(session_id, user_id)

        assert result.is_paused is False
        mock_session_repo.mark_resumed.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_resume_not_paused_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify cannot resume non-paused session."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(session_id=session_id, user_id=user_id, is_paused=False)
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="not paused"):
            await session_service.resume_session(session_id, user_id)

    @pytest.mark.asyncio
    async def test_resume_ended_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify cannot resume ended session."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            is_paused=True,
            ended_at=datetime.now(UTC),
        )
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="Cannot resume ended session"):
            await session_service.resume_session(session_id, user_id)


# ============================================================================
# Session End Tests
# ============================================================================


class TestSessionEnd:
    """Test ending quiz sessions."""

    @pytest.mark.asyncio
    async def test_end_session_success(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify session can be ended with correct version."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            version=3,
            total_questions=10,
            correct_count=7,
        )
        mock_session_repo.get_session_by_id.return_value = session

        ended_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            version=4,
            ended_at=datetime.now(UTC),
            total_questions=10,
            correct_count=7,
        )
        mock_session_repo.mark_ended.return_value = ended_session

        result = await session_service.end_session(session_id, user_id, expected_version=3)

        assert result.ended_at is not None
        mock_session_repo.mark_ended.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_end_session_version_mismatch(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify end fails with version mismatch (optimistic locking)."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            version=5,  # Current version is 5
        )
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="Version conflict"):
            await session_service.end_session(session_id, user_id, expected_version=3)

    @pytest.mark.asyncio
    async def test_end_already_ended_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify cannot end already ended session."""
        user_id = uuid4()
        session_id = uuid4()

        session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            version=1,
            ended_at=datetime.now(UTC),
        )
        mock_session_repo.get_session_by_id.return_value = session

        with pytest.raises(ValueError, match="already ended"):
            await session_service.end_session(session_id, user_id, expected_version=1)


# ============================================================================
# Status Derivation Tests
# ============================================================================


class TestDeriveStatus:
    """Test derive_status utility method."""

    def test_derive_status_active(self, session_service):
        """Verify active status for ongoing session."""
        session = create_mock_session()
        assert session_service.derive_status(session) == "active"

    def test_derive_status_paused(self, session_service):
        """Verify paused status."""
        session = create_mock_session(is_paused=True)
        assert session_service.derive_status(session) == "paused"

    def test_derive_status_completed(self, session_service):
        """Verify completed status."""
        session = create_mock_session(ended_at=datetime.now(UTC))
        assert session_service.derive_status(session) == "completed"

    def test_derive_status_expired(self, session_service):
        """Verify expired status for session past timeout."""
        session = create_mock_session(
            updated_at=datetime.now(UTC) - timedelta(hours=3)
        )
        assert session_service.derive_status(session) == "expired"


# ============================================================================
# Expiration Check Tests
# ============================================================================


class TestExpirationCheck:
    """Test session expiration checking."""

    def test_session_not_expired_within_timeout(self, session_service):
        """Verify session within timeout is not expired."""
        session = create_mock_session(
            updated_at=datetime.now(UTC) - timedelta(hours=1)
        )
        assert session_service._is_session_expired(session) is False

    def test_session_expired_after_timeout(self, session_service):
        """Verify session past 2 hours is expired."""
        session = create_mock_session(
            updated_at=datetime.now(UTC) - timedelta(hours=2, minutes=1)
        )
        assert session_service._is_session_expired(session) is True

    def test_session_expired_exactly_at_timeout(self, session_service):
        """Verify session at exactly 2 hours boundary."""
        session = create_mock_session(
            updated_at=datetime.now(UTC) - timedelta(hours=2, seconds=1)
        )
        assert session_service._is_session_expired(session) is True

    def test_session_just_before_timeout(self, session_service):
        """Verify session just before 2 hours is not expired."""
        session = create_mock_session(
            updated_at=datetime.now(UTC) - timedelta(hours=1, minutes=59)
        )
        assert session_service._is_session_expired(session) is False
