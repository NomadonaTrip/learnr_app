"""
Unit tests for DiagnosticSessionService.
Tests session management lifecycle including creation, resumption, and reset.
"""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.diagnostic_session_service import DiagnosticSessionService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_session_repo():
    """Create mock DiagnosticSessionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_belief_repo():
    """Create mock BeliefRepository."""
    return AsyncMock()


@pytest.fixture
def mock_question_repo():
    """Create mock QuestionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_diagnostic_service():
    """Create mock DiagnosticService."""
    return AsyncMock()


@pytest.fixture
def session_service(
    mock_session_repo, mock_belief_repo, mock_question_repo, mock_diagnostic_service
):
    """Create DiagnosticSessionService with mock dependencies."""
    return DiagnosticSessionService(
        session_repo=mock_session_repo,
        belief_repo=mock_belief_repo,
        question_repo=mock_question_repo,
        diagnostic_service=mock_diagnostic_service,
    )


def create_mock_session(
    session_id=None,
    user_id=None,
    enrollment_id=None,
    status="in_progress",
    current_index=0,
    question_ids=None,
    started_at=None,
    completed_at=None,
):
    """Helper to create mock DiagnosticSession."""
    session = MagicMock()
    session.id = session_id or uuid4()
    session.user_id = user_id or uuid4()
    session.enrollment_id = enrollment_id or uuid4()
    session.status = status
    session.current_index = current_index
    session.question_ids = question_ids or [str(uuid4()) for _ in range(15)]
    session.started_at = started_at or datetime.now(timezone.utc)
    session.completed_at = completed_at
    session.questions_total = len(session.question_ids)
    session.questions_remaining = max(0, len(session.question_ids) - current_index)
    return session


def create_mock_question(question_id=None):
    """Helper to create mock Question."""
    question = MagicMock()
    question.id = question_id or uuid4()
    question.question_text = f"Question {question.id}"
    question.options = {"A": "A", "B": "B", "C": "C", "D": "D"}
    question.knowledge_area_id = "ba-planning"
    question.difficulty = 0.5
    question.discrimination = 1.0
    question.question_concepts = []
    return question


# ============================================================================
# Session Creation Tests
# ============================================================================


class TestSessionCreation:
    """Test creating new diagnostic sessions."""

    @pytest.mark.asyncio
    async def test_creates_new_session_when_none_exists(
        self,
        session_service,
        mock_session_repo,
        mock_diagnostic_service,
    ):
        """Verify new session created when no active session exists."""
        user_id = uuid4()
        enrollment_id = uuid4()
        course_id = uuid4()

        # No existing session
        mock_session_repo.get_active_session.return_value = None

        # Mock question selection
        mock_questions = [create_mock_question() for _ in range(15)]
        mock_diagnostic_service.select_diagnostic_questions.return_value = (
            mock_questions,
            set(),
            100,
        )

        # Mock session creation
        new_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            question_ids=[str(q.id) for q in mock_questions],
        )
        mock_session_repo.create_session.return_value = new_session

        session, questions, is_resumed = await session_service.start_or_resume_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            course_id=course_id,
        )

        assert session == new_session
        assert questions == mock_questions
        assert is_resumed is False
        mock_session_repo.create_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_creates_session_with_correct_question_ids(
        self,
        session_service,
        mock_session_repo,
        mock_diagnostic_service,
    ):
        """Verify session stores question IDs from selection."""
        user_id = uuid4()
        enrollment_id = uuid4()
        course_id = uuid4()

        mock_session_repo.get_active_session.return_value = None

        # Create specific questions
        q1, q2, q3 = create_mock_question(), create_mock_question(), create_mock_question()
        mock_diagnostic_service.select_diagnostic_questions.return_value = (
            [q1, q2, q3],
            set(),
            10,
        )

        new_session = create_mock_session(
            question_ids=[str(q1.id), str(q2.id), str(q3.id)]
        )
        mock_session_repo.create_session.return_value = new_session

        await session_service.start_or_resume_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            course_id=course_id,
        )

        # Verify question IDs passed to create_session
        call_kwargs = mock_session_repo.create_session.call_args[1]
        assert str(q1.id) in call_kwargs["question_ids"]
        assert str(q2.id) in call_kwargs["question_ids"]
        assert str(q3.id) in call_kwargs["question_ids"]


# ============================================================================
# Session Resumption Tests
# ============================================================================


class TestSessionResumption:
    """Test resuming existing diagnostic sessions."""

    @pytest.mark.asyncio
    async def test_resumes_active_session(
        self,
        session_service,
        mock_session_repo,
        mock_question_repo,
    ):
        """Verify active session is resumed, not recreated."""
        user_id = uuid4()
        enrollment_id = uuid4()
        course_id = uuid4()

        # Existing active session at question 5
        existing_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            current_index=5,
            started_at=datetime.now(timezone.utc) - timedelta(minutes=10),  # Not expired
        )
        mock_session_repo.get_active_session.return_value = existing_session

        # Mock remaining questions
        remaining_ids = existing_session.question_ids[5:]
        remaining_questions = [create_mock_question(uuid4()) for _ in remaining_ids]
        mock_question_repo.get_questions_by_ids.return_value = remaining_questions

        session, questions, is_resumed = await session_service.start_or_resume_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            course_id=course_id,
        )

        assert session == existing_session
        assert is_resumed is True
        assert len(questions) == len(remaining_questions)
        mock_session_repo.create_session.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_remaining_questions_on_resume(
        self,
        session_service,
        mock_session_repo,
        mock_question_repo,
    ):
        """Verify only remaining questions returned on resume."""
        user_id = uuid4()
        enrollment_id = uuid4()
        course_id = uuid4()

        # Session at question 10 of 15
        question_ids = [str(uuid4()) for _ in range(15)]
        existing_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            current_index=10,
            question_ids=question_ids,
            started_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )
        mock_session_repo.get_active_session.return_value = existing_session

        # Mock 5 remaining questions
        remaining_questions = [create_mock_question() for _ in range(5)]
        mock_question_repo.get_questions_by_ids.return_value = remaining_questions

        session, questions, is_resumed = await session_service.start_or_resume_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            course_id=course_id,
        )

        assert len(questions) == 5
        # Verify get_questions_by_ids called with remaining IDs
        mock_question_repo.get_questions_by_ids.assert_called_once()


# ============================================================================
# Session Expiration Tests
# ============================================================================


class TestSessionExpiration:
    """Test session timeout and expiration handling."""

    @pytest.mark.asyncio
    async def test_expires_old_session_and_creates_new(
        self,
        session_service,
        mock_session_repo,
        mock_diagnostic_service,
    ):
        """Verify expired session is marked and new session created."""
        user_id = uuid4()
        enrollment_id = uuid4()
        course_id = uuid4()

        # Expired session (started 31 minutes ago)
        expired_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            started_at=datetime.now(timezone.utc) - timedelta(minutes=31),
        )
        mock_session_repo.get_active_session.return_value = expired_session

        # Mock new session creation
        mock_questions = [create_mock_question() for _ in range(15)]
        mock_diagnostic_service.select_diagnostic_questions.return_value = (
            mock_questions,
            set(),
            100,
        )

        new_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
        )
        mock_session_repo.create_session.return_value = new_session

        session, questions, is_resumed = await session_service.start_or_resume_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
            course_id=course_id,
        )

        # Old session should be marked expired
        mock_session_repo.mark_expired.assert_called_once_with(expired_session.id)

        # New session should be created
        mock_session_repo.create_session.assert_called_once()
        assert is_resumed is False

    def test_is_session_expired_within_timeout(self, session_service):
        """Verify session within timeout is not expired."""
        session = create_mock_session(
            started_at=datetime.now(timezone.utc) - timedelta(minutes=25)
        )
        assert session_service._is_session_expired(session) is False

    def test_is_session_expired_after_timeout(self, session_service):
        """Verify session past timeout is expired."""
        session = create_mock_session(
            started_at=datetime.now(timezone.utc) - timedelta(minutes=35)
        )
        assert session_service._is_session_expired(session) is True

    def test_is_session_expired_exactly_at_timeout(self, session_service):
        """Verify session at exactly 30 minutes is expired."""
        session = create_mock_session(
            started_at=datetime.now(timezone.utc) - timedelta(minutes=30, seconds=1)
        )
        assert session_service._is_session_expired(session) is True


# ============================================================================
# Answer Recording Tests
# ============================================================================


class TestAnswerRecording:
    """Test recording answers and advancing session progress."""

    @pytest.mark.asyncio
    async def test_records_answer_and_advances_progress(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify answer recording increments session progress."""
        user_id = uuid4()
        question_id = uuid4()
        session_id = uuid4()

        # Question at index 5 should be our question_id
        question_ids = [str(uuid4()) for _ in range(5)] + [str(question_id)] + [str(uuid4()) for _ in range(9)]
        existing_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            current_index=5,  # We're at position 5
            question_ids=question_ids,  # question_id is at position 5
        )
        mock_session_repo.get_session_by_id.return_value = existing_session

        updated_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            current_index=6,  # Advanced
        )
        mock_session_repo.increment_progress.return_value = updated_session

        session = await session_service.record_answer(
            session_id=session_id,
            question_id=question_id,
            user_id=user_id,
        )

        mock_session_repo.increment_progress.assert_called_once_with(session_id)
        assert session.current_index == 6

    @pytest.mark.asyncio
    async def test_marks_session_completed_on_last_answer(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify session marked completed after final answer."""
        user_id = uuid4()
        question_id = uuid4()
        session_id = uuid4()

        # Session at last question (index 14 of 15)
        existing_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            current_index=14,
            question_ids=[str(uuid4()) for _ in range(14)] + [str(question_id)],
        )
        mock_session_repo.get_session_by_id.return_value = existing_session

        # After increment, at position 15 (completed)
        incremented_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            current_index=15,
            question_ids=existing_session.question_ids,
        )
        mock_session_repo.increment_progress.return_value = incremented_session

        completed_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            current_index=15,
            status="completed",
            completed_at=datetime.now(timezone.utc),
        )
        mock_session_repo.mark_completed.return_value = completed_session

        session = await session_service.record_answer(
            session_id=session_id,
            question_id=question_id,
            user_id=user_id,
        )

        mock_session_repo.mark_completed.assert_called_once_with(session_id)
        assert session.status == "completed"

    @pytest.mark.asyncio
    async def test_rejects_answer_for_wrong_user(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify answer rejected if user doesn't own session."""
        session_id = uuid4()
        session_user_id = uuid4()
        other_user_id = uuid4()
        question_id = uuid4()

        existing_session = create_mock_session(
            session_id=session_id,
            user_id=session_user_id,  # Different user
        )
        mock_session_repo.get_session_by_id.return_value = existing_session

        with pytest.raises(ValueError, match="Unauthorized"):
            await session_service.record_answer(
                session_id=session_id,
                question_id=question_id,
                user_id=other_user_id,
            )

    @pytest.mark.asyncio
    async def test_rejects_answer_for_wrong_question(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify answer rejected if question doesn't match expected position."""
        user_id = uuid4()
        session_id = uuid4()
        expected_question_id = uuid4()
        wrong_question_id = uuid4()

        existing_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            current_index=5,
            question_ids=[str(uuid4()) for _ in range(5)] + [str(expected_question_id)] + [str(uuid4()) for _ in range(9)],
        )
        mock_session_repo.get_session_by_id.return_value = existing_session

        with pytest.raises(ValueError, match="does not match expected position"):
            await session_service.record_answer(
                session_id=session_id,
                question_id=wrong_question_id,
                user_id=user_id,
            )

    @pytest.mark.asyncio
    async def test_rejects_answer_for_non_active_session(
        self,
        session_service,
        mock_session_repo,
    ):
        """Verify answer rejected for completed/expired session."""
        user_id = uuid4()
        session_id = uuid4()
        question_id = uuid4()

        completed_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            status="completed",
            question_ids=[str(question_id)],
        )
        mock_session_repo.get_session_by_id.return_value = completed_session

        with pytest.raises(ValueError, match="completed"):
            await session_service.record_answer(
                session_id=session_id,
                question_id=question_id,
                user_id=user_id,
            )


# ============================================================================
# Reset Tests
# ============================================================================


class TestDiagnosticReset:
    """Test diagnostic reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_clears_active_session(
        self,
        session_service,
        mock_session_repo,
        mock_belief_repo,
    ):
        """Verify reset marks active session as reset."""
        user_id = uuid4()
        enrollment_id = uuid4()

        active_session = create_mock_session(
            user_id=user_id,
            enrollment_id=enrollment_id,
        )
        mock_session_repo.get_active_session.return_value = active_session
        mock_belief_repo.reset_beliefs_for_enrollment.return_value = 50

        result = await session_service.reset_diagnostic(
            user_id=user_id,
            enrollment_id=enrollment_id,
        )

        mock_session_repo.mark_reset.assert_called_once_with(active_session.id)
        assert result["session_cleared"] is True

    @pytest.mark.asyncio
    async def test_reset_resets_all_beliefs(
        self,
        session_service,
        mock_session_repo,
        mock_belief_repo,
    ):
        """Verify reset resets belief states to Beta(1,1)."""
        user_id = uuid4()
        enrollment_id = uuid4()

        mock_session_repo.get_active_session.return_value = None
        mock_belief_repo.reset_beliefs_for_enrollment.return_value = 100

        result = await session_service.reset_diagnostic(
            user_id=user_id,
            enrollment_id=enrollment_id,
        )

        mock_belief_repo.reset_beliefs_for_enrollment.assert_called_once_with(
            user_id=user_id,
            enrollment_id=enrollment_id,
            alpha=1.0,
            beta=1.0,
        )
        assert result["beliefs_reset_count"] == 100

    @pytest.mark.asyncio
    async def test_reset_without_active_session(
        self,
        session_service,
        mock_session_repo,
        mock_belief_repo,
    ):
        """Verify reset works when no active session exists."""
        user_id = uuid4()
        enrollment_id = uuid4()

        mock_session_repo.get_active_session.return_value = None
        mock_belief_repo.reset_beliefs_for_enrollment.return_value = 75

        result = await session_service.reset_diagnostic(
            user_id=user_id,
            enrollment_id=enrollment_id,
        )

        mock_session_repo.mark_reset.assert_not_called()
        assert result["session_cleared"] is False
        assert result["beliefs_reset_count"] == 75
