"""
Unit tests for QuizAnswerService.
Story 4.3: Answer Submission and Immediate Feedback

Tests:
1. Correct answer returns is_correct=True
2. Wrong answer returns is_correct=False
3. Response includes explanation
4. Time taken calculated correctly
5. Idempotent request returns same response
"""
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.exceptions import AlreadyAnsweredError, InvalidQuestionError, InvalidSessionError
from src.models.question import Question
from src.models.quiz_response import QuizResponse
from src.models.quiz_session import QuizSession
from src.services.quiz_answer_service import QuizAnswerService


@pytest.fixture
def mock_response_repo():
    """Mock ResponseRepository."""
    repo = AsyncMock()
    repo.get_by_request_id.return_value = None
    repo.check_already_answered.return_value = False
    return repo


@pytest.fixture
def mock_question_repo():
    """Mock QuestionRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_session_repo():
    """Mock QuizSessionRepository."""
    repo = AsyncMock()
    return repo


@pytest.fixture
def mock_belief_updater():
    """Mock BeliefUpdater."""
    updater = AsyncMock()
    updater.update_beliefs.return_value = []
    return updater


@pytest.fixture
def sample_question():
    """Create a sample question for testing."""
    question = MagicMock(spec=Question)
    question.id = uuid4()
    question.question_text = "What is stakeholder analysis?"
    question.options = {
        "A": "A method to identify stakeholders",
        "B": "A financial analysis technique",
        "C": "A project scheduling method",
        "D": "A risk assessment tool",
    }
    question.correct_answer = "A"
    question.explanation = "Stakeholder analysis is the process of identifying and analyzing project stakeholders."
    question.is_active = True
    question.guess_rate = 0.25
    question.slip_rate = 0.10
    question.question_concepts = []
    return question


@pytest.fixture
def sample_session():
    """Create a sample quiz session for testing."""
    session = MagicMock(spec=QuizSession)
    session.id = uuid4()
    session.user_id = uuid4()
    session.enrollment_id = uuid4()
    session.ended_at = None
    session.is_paused = False
    session.total_questions = 5
    session.correct_count = 3
    session.updated_at = datetime.now(UTC)
    return session


@pytest.fixture
def quiz_answer_service(mock_response_repo, mock_question_repo, mock_session_repo, mock_belief_updater):
    """Create QuizAnswerService with mocked dependencies."""
    return QuizAnswerService(
        response_repo=mock_response_repo,
        question_repo=mock_question_repo,
        session_repo=mock_session_repo,
        belief_updater=mock_belief_updater,
    )


class TestCorrectAnswerDetection:
    """Tests for answer correctness determination."""

    @pytest.mark.asyncio
    async def test_correct_answer_returns_is_correct_true(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that submitting the correct answer returns is_correct=True."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        # Mock response creation
        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = True
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        # Mock session update
        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 4
        mock_session_repo.increment_question_count.return_value = updated_session

        # Submit correct answer
        response, was_cached = await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="A",  # Correct answer
        )

        assert response.is_correct is True
        assert response.correct_answer == "A"
        assert was_cached is False

        # Verify create was called with is_correct=True
        mock_response_repo.create.assert_called_once()
        call_kwargs = mock_response_repo.create.call_args.kwargs
        assert call_kwargs["is_correct"] is True

    @pytest.mark.asyncio
    async def test_wrong_answer_returns_is_correct_false(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that submitting a wrong answer returns is_correct=False."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        # Mock response creation
        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = False
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        # Mock session update
        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 3  # No increment for wrong answer
        mock_session_repo.increment_question_count.return_value = updated_session

        # Submit wrong answer
        response, was_cached = await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="B",  # Wrong answer
        )

        assert response.is_correct is False
        assert response.correct_answer == "A"
        assert was_cached is False

        # Verify create was called with is_correct=False
        mock_response_repo.create.assert_called_once()
        call_kwargs = mock_response_repo.create.call_args.kwargs
        assert call_kwargs["is_correct"] is False


class TestResponseContent:
    """Tests for response content completeness."""

    @pytest.mark.asyncio
    async def test_response_includes_explanation(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that the response includes the question explanation."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = True
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 4
        mock_session_repo.increment_question_count.return_value = updated_session

        # Submit answer
        response, _ = await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="A",
        )

        # Verify explanation is included
        assert response.explanation == sample_question.explanation
        assert "stakeholder" in response.explanation.lower()

    @pytest.mark.asyncio
    async def test_response_includes_session_stats(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that response includes session statistics."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = True
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        # Updated session after answer
        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 4
        mock_session_repo.increment_question_count.return_value = updated_session

        # Submit answer
        response, _ = await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="A",
        )

        # Verify session stats
        assert response.session_stats is not None
        assert response.session_stats.questions_answered == 6
        assert response.session_stats.accuracy == pytest.approx(4 / 6, rel=0.01)


class TestTimeTakenCalculation:
    """Tests for time_taken_ms calculation."""

    @pytest.mark.asyncio
    async def test_time_taken_from_client_timestamp(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test time calculation from client-provided timestamp."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = True
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 4
        mock_session_repo.increment_question_count.return_value = updated_session

        # Client timestamp from 5 seconds ago
        client_timestamp = datetime.now(UTC) - timedelta(seconds=5)

        # Submit answer with client timestamp
        await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="A",
            client_timestamp=client_timestamp,
        )

        # Verify time_taken_ms was calculated and passed to create
        mock_response_repo.create.assert_called_once()
        call_kwargs = mock_response_repo.create.call_args.kwargs
        time_taken_ms = call_kwargs["time_taken_ms"]

        # Should be approximately 5000ms (5 seconds)
        assert time_taken_ms is not None
        assert time_taken_ms >= 4500  # Allow for some timing variance
        assert time_taken_ms <= 6000

    @pytest.mark.asyncio
    async def test_time_taken_none_without_timestamp(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that time_taken_ms is None when no timestamp provided."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = True
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 4
        mock_session_repo.increment_question_count.return_value = updated_session

        # Submit answer without timestamp
        await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="A",
        )

        # Verify time_taken_ms is None
        mock_response_repo.create.assert_called_once()
        call_kwargs = mock_response_repo.create.call_args.kwargs
        assert call_kwargs["time_taken_ms"] is None


class TestIdempotency:
    """Tests for idempotent request handling."""

    @pytest.mark.asyncio
    async def test_idempotent_request_returns_cached_response(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that duplicate request_id returns cached response."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id
        request_id = uuid4()

        # Create existing response (cached)
        existing_response = MagicMock(spec=QuizResponse)
        existing_response.id = uuid4()
        existing_response.question_id = question_id
        existing_response.is_correct = True
        existing_response.belief_updates = None

        # Mock: response already exists for this request_id
        mock_response_repo.get_by_request_id.return_value = existing_response
        mock_question_repo.get_question_by_id.return_value = sample_question
        mock_session_repo.get_session_by_id.return_value = sample_session

        # Submit answer with existing request_id
        response, was_cached = await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="A",
            request_id=request_id,
        )

        # Should return cached response
        assert was_cached is True
        assert response.is_correct is True

        # Verify no new response was created
        mock_response_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_new_request_id_creates_new_response(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that new request_id creates new response."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id
        request_id = uuid4()

        # Setup mocks - no existing response
        mock_response_repo.get_by_request_id.return_value = None
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = True
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 4
        mock_session_repo.increment_question_count.return_value = updated_session

        # Submit answer with new request_id
        response, was_cached = await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="A",
            request_id=request_id,
        )

        # Should create new response
        assert was_cached is False
        mock_response_repo.create.assert_called_once()

        # Verify request_id was passed
        call_kwargs = mock_response_repo.create.call_args.kwargs
        assert call_kwargs["request_id"] == request_id


class TestErrorHandling:
    """Tests for error conditions."""

    @pytest.mark.asyncio
    async def test_invalid_session_raises_error(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
    ):
        """Test that invalid session raises InvalidSessionError."""
        user_id = uuid4()
        session_id = uuid4()
        question_id = uuid4()

        # Mock: session not found
        mock_session_repo.get_session_by_id.return_value = None

        with pytest.raises(InvalidSessionError) as exc_info:
            await quiz_answer_service.submit_answer(
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                selected_answer="A",
            )

        assert "not found" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_invalid_question_raises_error(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_session,
    ):
        """Test that invalid question raises InvalidQuestionError."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = uuid4()

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = None  # Question not found

        with pytest.raises(InvalidQuestionError) as exc_info:
            await quiz_answer_service.submit_answer(
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                selected_answer="A",
            )

        assert "not found" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_already_answered_raises_error(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that answering same question twice raises AlreadyAnsweredError."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question
        mock_response_repo.check_already_answered.return_value = True  # Already answered

        with pytest.raises(AlreadyAnsweredError) as exc_info:
            await quiz_answer_service.submit_answer(
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                selected_answer="A",
            )

        assert "already answered" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_unauthorized_session_raises_error(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_session,
    ):
        """Test that accessing another user's session raises InvalidSessionError."""
        other_user_id = uuid4()  # Different user
        session_id = sample_session.id
        question_id = uuid4()

        # Setup mocks - session belongs to different user
        mock_session_repo.get_session_by_id.return_value = sample_session

        with pytest.raises(InvalidSessionError) as exc_info:
            await quiz_answer_service.submit_answer(
                user_id=other_user_id,
                session_id=session_id,
                question_id=question_id,
                selected_answer="A",
            )

        assert "unauthorized" in exc_info.value.message.lower()

    @pytest.mark.asyncio
    async def test_ended_session_raises_error(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_session,
    ):
        """Test that submitting to ended session raises InvalidSessionError."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = uuid4()

        # Mark session as ended
        sample_session.ended_at = datetime.now(UTC)
        mock_session_repo.get_session_by_id.return_value = sample_session

        with pytest.raises(InvalidSessionError) as exc_info:
            await quiz_answer_service.submit_answer(
                user_id=user_id,
                session_id=session_id,
                question_id=question_id,
                selected_answer="A",
            )

        assert "ended" in exc_info.value.message.lower()


class TestAnswerNormalization:
    """Tests for answer input normalization."""

    @pytest.mark.asyncio
    async def test_lowercase_answer_is_normalized(
        self,
        quiz_answer_service,
        mock_response_repo,
        mock_question_repo,
        mock_session_repo,
        sample_question,
        sample_session,
    ):
        """Test that lowercase answer is normalized to uppercase."""
        user_id = sample_session.user_id
        session_id = sample_session.id
        question_id = sample_question.id

        # Setup mocks
        mock_session_repo.get_session_by_id.return_value = sample_session
        mock_question_repo.get_question_by_id.return_value = sample_question

        created_response = MagicMock(spec=QuizResponse)
        created_response.id = uuid4()
        created_response.is_correct = True
        created_response.belief_updates = None
        mock_response_repo.create.return_value = created_response

        updated_session = MagicMock(spec=QuizSession)
        updated_session.total_questions = 6
        updated_session.correct_count = 4
        mock_session_repo.increment_question_count.return_value = updated_session

        # Submit lowercase answer
        response, _ = await quiz_answer_service.submit_answer(
            user_id=user_id,
            session_id=session_id,
            question_id=question_id,
            selected_answer="a",  # lowercase
        )

        # Should still be correct
        assert response.is_correct is True

        # Verify uppercase was stored
        mock_response_repo.create.assert_called_once()
        call_kwargs = mock_response_repo.create.call_args.kwargs
        assert call_kwargs["selected_answer"] == "A"
