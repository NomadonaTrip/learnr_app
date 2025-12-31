"""
Unit tests for QuizAnswerService auto-completion.
Story 4.7: Fixed-Length Session Auto-Completion
"""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.services.quiz_answer_service import QuizAnswerService


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_response_repo():
    """Create mock ResponseRepository."""
    return AsyncMock()


@pytest.fixture
def mock_question_repo():
    """Create mock QuestionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_session_repo():
    """Create mock QuizSessionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_user_repo():
    """Create mock UserRepository."""
    return AsyncMock()


@pytest.fixture
def mock_belief_updater():
    """Create mock BeliefUpdater."""
    return AsyncMock()


@pytest.fixture
def answer_service(
    mock_response_repo,
    mock_question_repo,
    mock_session_repo,
    mock_user_repo,
    mock_belief_updater,
):
    """Create QuizAnswerService with mock dependencies."""
    return QuizAnswerService(
        response_repo=mock_response_repo,
        question_repo=mock_question_repo,
        session_repo=mock_session_repo,
        user_repo=mock_user_repo,
        belief_updater=mock_belief_updater,
    )


def create_mock_session(
    session_id=None,
    user_id=None,
    total_questions=0,
    correct_count=0,
    question_target=12,
    started_at=None,
    ended_at=None,
    updated_at=None,
    version=1,
):
    """Helper to create mock QuizSession."""
    session = MagicMock()
    session.id = session_id or uuid4()
    session.user_id = user_id or uuid4()
    session.total_questions = total_questions
    session.correct_count = correct_count
    session.question_target = question_target
    session.started_at = started_at or datetime.now(UTC)
    session.ended_at = ended_at
    session.updated_at = updated_at or datetime.now(UTC)
    session.version = version
    session.status = "active" if not ended_at else "completed"
    return session


def create_mock_question(question_id=None, is_active=True):
    """Helper to create mock Question."""
    question = MagicMock()
    question.id = question_id or uuid4()
    question.correct_answer = "B"
    question.explanation = "Test explanation"
    question.question_concepts = []
    question.is_active = is_active
    return question


def create_mock_response(
    is_correct=True,
    belief_updates=None,
):
    """Helper to create mock QuizResponse."""
    response = MagicMock()
    response.is_correct = is_correct
    response.belief_updates = belief_updates or []
    return response


def create_mock_user(
    user_id=None,
    quizzes_completed=0,
    total_questions_answered=0,
    total_time_spent_seconds=0,
):
    """Helper to create mock User."""
    user = MagicMock()
    user.id = user_id or uuid4()
    user.quizzes_completed = quizzes_completed
    user.total_questions_answered = total_questions_answered
    user.total_time_spent_seconds = total_time_spent_seconds
    return user


# ============================================================================
# Auto-Completion Tests (Story 4.7)
# ============================================================================


class TestAutoCompletion:
    """Test session auto-completion when reaching question target."""

    @pytest.mark.asyncio
    async def test_session_auto_completes_at_target(
        self,
        answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        mock_user_repo,
        mock_belief_updater,
    ):
        """Verify session auto-completes when questions_answered == question_target."""
        user_id = uuid4()
        session_id = uuid4()
        question_id = uuid4()

        # Session at 11 questions (one before target of 12)
        session_before = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=11,
            correct_count=8,
            question_target=12,
        )

        # Session after increment (12 questions - target reached)
        session_after = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=12,
            correct_count=9,
            question_target=12,
        )

        # Session after mark_ended
        ended_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=12,
            correct_count=9,
            question_target=12,
            ended_at=datetime.now(UTC),
        )

        mock_session_repo.get_session_by_id.return_value = session_before
        mock_session_repo.increment_question_count.return_value = session_after
        mock_session_repo.mark_ended.return_value = ended_session

        # Mock question
        question = create_mock_question(question_id=question_id)
        mock_question_repo.get_question_by_id.return_value = question

        # Mock response repo (no existing response)
        mock_response_repo.check_already_answered.return_value = False
        mock_response_repo.get_by_request_id.return_value = None
        mock_response_repo.get_by_session_id.return_value = []

        # Mock response creation
        response = create_mock_response(is_correct=True)
        mock_response_repo.create.return_value = response

        # Mock user
        user = create_mock_user(user_id=user_id, quizzes_completed=4)
        user.quizzes_completed = 5  # After increment
        mock_user_repo.increment_quiz_stats.return_value = user

        # Mock belief updater
        mock_belief_updater.update_beliefs.return_value = []

        # Submit answer
        result, was_cached = await answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="B",
        )

        # Verify session was marked as ended
        mock_session_repo.mark_ended.assert_called_once_with(session_id)

        # Verify user stats were updated
        mock_user_repo.increment_quiz_stats.assert_called_once()

        # Verify response includes session_completed and summary
        assert result.session_completed is True
        assert result.session_summary is not None
        assert result.session_summary.questions_answered == 12
        assert result.session_summary.question_target == 12
        assert result.session_summary.quizzes_completed_total == 5

    @pytest.mark.asyncio
    async def test_session_not_completed_before_target(
        self,
        answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        mock_user_repo,
        mock_belief_updater,
    ):
        """Verify session is NOT completed when below target."""
        user_id = uuid4()
        session_id = uuid4()
        question_id = uuid4()

        # Session at 5 questions (well below target of 12)
        session_before = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=5,
            correct_count=3,
            question_target=12,
        )

        # Session after increment (6 questions - still below target)
        session_after = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=6,
            correct_count=4,
            question_target=12,
        )

        mock_session_repo.get_session_by_id.return_value = session_before
        mock_session_repo.increment_question_count.return_value = session_after

        # Mock question
        question = create_mock_question(question_id=question_id)
        mock_question_repo.get_question_by_id.return_value = question

        # Mock response repo
        mock_response_repo.check_already_answered.return_value = False
        mock_response_repo.get_by_request_id.return_value = None

        # Mock response creation
        response = create_mock_response(is_correct=True)
        mock_response_repo.create.return_value = response

        # Mock belief updater
        mock_belief_updater.update_beliefs.return_value = []

        # Submit answer
        result, was_cached = await answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="B",
        )

        # Verify session was NOT marked as ended
        mock_session_repo.mark_ended.assert_not_called()

        # Verify user stats were NOT updated
        mock_user_repo.increment_quiz_stats.assert_not_called()

        # Verify response has session_completed = False
        assert result.session_completed is False
        assert result.session_summary is None


class TestSessionSummary:
    """Test session summary response fields."""

    @pytest.mark.asyncio
    async def test_session_summary_accuracy_calculation(
        self,
        answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        mock_user_repo,
        mock_belief_updater,
    ):
        """Verify accuracy is calculated correctly in session summary."""
        user_id = uuid4()
        session_id = uuid4()
        question_id = uuid4()

        # Session will complete with 9/12 correct = 75% accuracy
        session_before = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=11,
            correct_count=8,
            question_target=12,
        )

        session_after = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=12,
            correct_count=9,  # 9/12 = 75%
            question_target=12,
        )

        ended_session = create_mock_session(
            session_id=session_id,
            user_id=user_id,
            total_questions=12,
            correct_count=9,
            question_target=12,
            ended_at=datetime.now(UTC),
        )

        mock_session_repo.get_session_by_id.return_value = session_before
        mock_session_repo.increment_question_count.return_value = session_after
        mock_session_repo.mark_ended.return_value = ended_session

        question = create_mock_question(question_id=question_id)
        mock_question_repo.get_question_by_id.return_value = question

        mock_response_repo.check_already_answered.return_value = False
        mock_response_repo.get_by_request_id.return_value = None
        mock_response_repo.get_by_session_id.return_value = []

        response = create_mock_response(is_correct=True)
        mock_response_repo.create.return_value = response

        user = create_mock_user(user_id=user_id, quizzes_completed=5)
        mock_user_repo.increment_quiz_stats.return_value = user

        mock_belief_updater.update_beliefs.return_value = []

        result, _ = await answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="B",
        )

        # Verify accuracy: 9/12 * 100 = 75.0
        assert result.session_summary.accuracy == 75.0
        assert result.session_summary.correct_count == 9
        assert result.session_summary.questions_answered == 12


class TestConceptsStrengthened:
    """Test concepts_strengthened count in session summary."""

    @pytest.mark.asyncio
    async def test_counts_unique_concepts(
        self,
        answer_service,
    ):
        """Verify unique concepts are counted correctly."""
        # Create mock responses with belief_updates
        response1 = MagicMock()
        response1.belief_updates = [
            {"concept_id": "concept-1"},
            {"concept_id": "concept-2"},
        ]

        response2 = MagicMock()
        response2.belief_updates = [
            {"concept_id": "concept-1"},  # Duplicate
            {"concept_id": "concept-3"},
        ]

        response3 = MagicMock()
        response3.belief_updates = None  # No updates

        # Mock get_by_session_id
        answer_service.response_repo.get_by_session_id = AsyncMock(
            return_value=[response1, response2, response3]
        )

        count = await answer_service._count_session_concepts_strengthened(uuid4())

        # Should count 3 unique concepts
        assert count == 3
