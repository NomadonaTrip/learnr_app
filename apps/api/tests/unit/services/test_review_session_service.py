"""
Unit tests for ReviewSessionService.
Story 4.9: Post-Session Review Mode
"""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.services.review_session_service import (
    ReviewSessionService,
    REINFORCEMENT_MULTIPLIER,
    STILL_INCORRECT_MULTIPLIER,
)


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_review_repo():
    """Create mock ReviewSessionRepository."""
    return AsyncMock()


@pytest.fixture
def mock_belief_repo():
    """Create mock BeliefRepository."""
    return AsyncMock()


@pytest.fixture
def mock_concept_repo():
    """Create mock ConceptRepository."""
    return AsyncMock()


@pytest.fixture
def mock_belief_updater():
    """Create mock BeliefUpdater."""
    return AsyncMock()


@pytest.fixture
def review_service(
    mock_review_repo,
    mock_belief_repo,
    mock_concept_repo,
    mock_belief_updater,
):
    """Create ReviewSessionService with mock dependencies."""
    return ReviewSessionService(
        review_repo=mock_review_repo,
        belief_repo=mock_belief_repo,
        concept_repo=mock_concept_repo,
        belief_updater=mock_belief_updater,
    )


def create_mock_quiz_response(
    question_id=None,
    is_correct=False,
):
    """Helper to create mock QuizResponse."""
    response = MagicMock()
    response.id = uuid4()
    response.question_id = question_id or uuid4()
    response.is_correct = is_correct
    return response


def create_mock_review_session(
    session_id=None,
    user_id=None,
    original_session_id=None,
    total_to_review=3,
    reviewed_count=0,
    reinforced_count=0,
    still_incorrect_count=0,
    status="pending",
):
    """Helper to create mock ReviewSession."""
    session = MagicMock()
    session.id = session_id or uuid4()
    session.user_id = user_id or uuid4()
    session.original_session_id = original_session_id or uuid4()
    session.total_to_review = total_to_review
    session.reviewed_count = reviewed_count
    session.reinforced_count = reinforced_count
    session.still_incorrect_count = still_incorrect_count
    session.status = status
    session.question_ids = [str(uuid4()) for _ in range(total_to_review)]
    session.started_at = None
    session.created_at = "2025-01-01T00:00:00Z"
    session.reinforcement_rate = reinforced_count / reviewed_count if reviewed_count > 0 else 0
    return session


def create_mock_question(
    question_id=None,
    correct_answer="B",
    explanation="Test explanation",
):
    """Helper to create mock Question."""
    question = MagicMock()
    question.id = question_id or uuid4()
    question.question_text = "Test question?"
    question.options = {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}
    question.correct_answer = correct_answer
    question.explanation = explanation
    question.slip_rate = 0.1
    question.guess_rate = 0.25
    question.question_concepts = []
    return question


def create_mock_belief(
    concept_id=None,
    alpha=5.0,
    beta=5.0,
):
    """Helper to create mock BeliefState."""
    belief = MagicMock()
    belief.concept_id = concept_id or uuid4()
    belief.alpha = alpha
    belief.beta = beta
    belief.response_count = 10
    belief.concept = MagicMock()
    belief.concept.name = "Test Concept"
    return belief


# ============================================================================
# Test Check Review Available
# ============================================================================


class TestCheckReviewAvailable:
    """Test checking review availability."""

    @pytest.mark.asyncio
    async def test_returns_available_when_incorrect_answers_exist(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify returns available=True when there are incorrect answers."""
        session_id = uuid4()
        incorrect_responses = [
            create_mock_quiz_response(),
            create_mock_quiz_response(),
        ]
        mock_review_repo.get_incorrect_responses_for_session.return_value = incorrect_responses

        result = await review_service.check_review_available(session_id)

        assert result.available is True
        assert result.incorrect_count == 2
        assert len(result.question_ids) == 2
        mock_review_repo.get_incorrect_responses_for_session.assert_called_once_with(session_id)

    @pytest.mark.asyncio
    async def test_returns_not_available_when_no_incorrect_answers(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify returns available=False when no incorrect answers."""
        session_id = uuid4()
        mock_review_repo.get_incorrect_responses_for_session.return_value = []

        result = await review_service.check_review_available(session_id)

        assert result.available is False
        assert result.incorrect_count == 0
        assert len(result.question_ids) == 0


# ============================================================================
# Test Start Review
# ============================================================================


class TestStartReview:
    """Test starting a review session."""

    @pytest.mark.asyncio
    async def test_creates_new_review_session(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify a new review session is created."""
        user_id = uuid4()
        session_id = uuid4()
        question_ids = [uuid4(), uuid4()]
        incorrect_responses = [
            create_mock_quiz_response(question_id=question_ids[0]),
            create_mock_quiz_response(question_id=question_ids[1]),
        ]
        mock_review_repo.get_pending_for_session.return_value = None
        mock_review_repo.get_incorrect_responses_for_session.return_value = incorrect_responses

        review_session = create_mock_review_session(
            user_id=user_id,
            original_session_id=session_id,
            total_to_review=2,
        )
        mock_review_repo.create.return_value = review_session
        mock_review_repo.mark_started.return_value = review_session

        result = await review_service.start_review(user_id, session_id)

        assert result.id == str(review_session.id)
        assert result.total_to_review == 2
        mock_review_repo.create.assert_called_once()
        mock_review_repo.mark_started.assert_called_once()

    @pytest.mark.asyncio
    async def test_resumes_existing_review_session(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify existing review session is resumed."""
        user_id = uuid4()
        session_id = uuid4()
        existing_review = create_mock_review_session(
            user_id=user_id,
            original_session_id=session_id,
            status="in_progress",
            reviewed_count=1,
        )
        mock_review_repo.get_pending_for_session.return_value = existing_review

        result = await review_service.start_review(user_id, session_id)

        assert result.id == str(existing_review.id)
        mock_review_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_raises_error_when_no_incorrect_answers(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify ValueError raised when no incorrect answers."""
        user_id = uuid4()
        session_id = uuid4()
        mock_review_repo.get_pending_for_session.return_value = None
        mock_review_repo.get_incorrect_responses_for_session.return_value = []

        with pytest.raises(ValueError, match="No incorrect answers"):
            await review_service.start_review(user_id, session_id)


# ============================================================================
# Test Get Next Review Question
# ============================================================================


class TestGetNextReviewQuestion:
    """Test getting the next review question."""

    @pytest.mark.asyncio
    async def test_returns_next_unreviewed_question(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify next unreviewed question is returned."""
        user_id = uuid4()
        review_session_id = uuid4()
        question_id = uuid4()

        review_session = create_mock_review_session(
            session_id=review_session_id,
            user_id=user_id,
            total_to_review=2,
            reviewed_count=1,
            status="in_progress",
        )
        review_session.question_ids = [str(uuid4()), str(question_id)]
        mock_review_repo.get_by_id.return_value = review_session
        mock_review_repo.get_review_responses.return_value = []

        question = create_mock_question(question_id=question_id)
        mock_review_repo.get_question_with_options.return_value = question

        result = await review_service.get_next_review_question(review_session_id, user_id)

        assert result is not None
        assert result.question_text == "Test question?"
        assert result.review_number == 1
        assert result.total_to_review == 2

    @pytest.mark.asyncio
    async def test_returns_none_when_all_reviewed(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify None returned when all questions reviewed."""
        user_id = uuid4()
        review_session_id = uuid4()
        question_id = uuid4()

        review_session = create_mock_review_session(
            session_id=review_session_id,
            user_id=user_id,
            total_to_review=1,
            reviewed_count=1,
            status="in_progress",
        )
        review_session.question_ids = [str(question_id)]
        mock_review_repo.get_by_id.return_value = review_session

        # Mock that the question was already reviewed
        reviewed_response = MagicMock()
        reviewed_response.question_id = question_id
        mock_review_repo.get_review_responses.return_value = [reviewed_response]
        mock_review_repo.mark_completed.return_value = review_session

        result = await review_service.get_next_review_question(review_session_id, user_id)

        assert result is None
        mock_review_repo.mark_completed.assert_called_once()


# ============================================================================
# Test Submit Review Answer
# ============================================================================


class TestSubmitReviewAnswer:
    """Test submitting a review answer."""

    @pytest.mark.asyncio
    async def test_correct_answer_is_reinforced(
        self,
        review_service,
        mock_review_repo,
        mock_belief_repo,
    ):
        """Verify correct answer marks was_reinforced=True."""
        user_id = uuid4()
        review_session_id = uuid4()
        question_id = uuid4()
        original_response_id = uuid4()

        review_session = create_mock_review_session(
            session_id=review_session_id,
            user_id=user_id,
            total_to_review=2,
            reviewed_count=0,
            status="in_progress",
        )
        mock_review_repo.get_by_id.return_value = review_session
        mock_review_repo.check_question_already_reviewed.return_value = False

        question = create_mock_question(question_id=question_id, correct_answer="B")
        mock_review_repo.get_question_with_options.return_value = question

        original_response = MagicMock()
        original_response.id = original_response_id
        mock_review_repo.get_original_response_for_question.return_value = original_response

        mock_belief_repo.get_beliefs_for_concepts.return_value = {}
        mock_review_repo.create_review_response.return_value = MagicMock()
        mock_review_repo.update_progress.return_value = review_session

        result = await review_service.submit_review_answer(
            review_session_id=review_session_id,
            user_id=user_id,
            question_id=question_id,
            selected_answer="B",
        )

        assert result.is_correct is True
        assert result.was_reinforced is True
        assert "improvement" in result.feedback_message.lower() or "correct" in result.feedback_message.lower()

    @pytest.mark.asyncio
    async def test_incorrect_answer_not_reinforced(
        self,
        review_service,
        mock_review_repo,
        mock_belief_repo,
    ):
        """Verify incorrect answer has was_reinforced=False."""
        user_id = uuid4()
        review_session_id = uuid4()
        question_id = uuid4()
        original_response_id = uuid4()

        review_session = create_mock_review_session(
            session_id=review_session_id,
            user_id=user_id,
            total_to_review=2,
            reviewed_count=0,
            status="in_progress",
        )
        mock_review_repo.get_by_id.return_value = review_session
        mock_review_repo.check_question_already_reviewed.return_value = False

        question = create_mock_question(question_id=question_id, correct_answer="B")
        mock_review_repo.get_question_with_options.return_value = question

        original_response = MagicMock()
        original_response.id = original_response_id
        mock_review_repo.get_original_response_for_question.return_value = original_response

        mock_belief_repo.get_beliefs_for_concepts.return_value = {}
        mock_review_repo.create_review_response.return_value = MagicMock()
        mock_review_repo.update_progress.return_value = review_session

        result = await review_service.submit_review_answer(
            review_session_id=review_session_id,
            user_id=user_id,
            question_id=question_id,
            selected_answer="A",  # Wrong answer
        )

        assert result.is_correct is False
        assert result.was_reinforced is False
        assert "practice" in result.feedback_message.lower() or "incorrect" in result.feedback_message.lower()


# ============================================================================
# Test Skip Review
# ============================================================================


class TestSkipReview:
    """Test skipping a review session."""

    @pytest.mark.asyncio
    async def test_marks_session_as_skipped(
        self,
        review_service,
        mock_review_repo,
    ):
        """Verify session is marked as skipped."""
        user_id = uuid4()
        review_session_id = uuid4()

        review_session = create_mock_review_session(
            session_id=review_session_id,
            user_id=user_id,
            total_to_review=3,
        )
        mock_review_repo.get_by_id.return_value = review_session
        mock_review_repo.mark_skipped.return_value = review_session

        result = await review_service.skip_review(review_session_id, user_id)

        assert result.questions_skipped == 3
        mock_review_repo.mark_skipped.assert_called_once()


# ============================================================================
# Test Get Review Summary
# ============================================================================


class TestGetReviewSummary:
    """Test getting review summary."""

    @pytest.mark.asyncio
    async def test_returns_correct_summary(
        self,
        review_service,
        mock_review_repo,
        mock_concept_repo,
    ):
        """Verify correct summary is returned."""
        user_id = uuid4()
        review_session_id = uuid4()

        review_session = create_mock_review_session(
            session_id=review_session_id,
            user_id=user_id,
            total_to_review=4,
            reviewed_count=4,
            reinforced_count=3,
            still_incorrect_count=1,
            status="completed",
        )
        mock_review_repo.get_by_id.return_value = review_session
        mock_review_repo.get_review_responses.return_value = []

        result = await review_service.get_review_summary(review_session_id, user_id)

        assert result.total_reviewed == 4
        assert result.reinforced_count == 3
        assert result.still_incorrect_count == 1
        assert result.reinforcement_rate == 0.75  # 3/4


# ============================================================================
# Test Reinforcement Multipliers
# ============================================================================


class TestReinforcementMultipliers:
    """Test belief update reinforcement multipliers."""

    def test_reinforcement_multiplier_is_greater_than_one(self):
        """Verify reinforcement multiplier provides stronger positive update."""
        assert REINFORCEMENT_MULTIPLIER > 1.0
        assert REINFORCEMENT_MULTIPLIER == 1.5

    def test_still_incorrect_multiplier_is_less_than_one(self):
        """Verify still-incorrect multiplier provides weaker negative update."""
        assert STILL_INCORRECT_MULTIPLIER < 1.0
        assert STILL_INCORRECT_MULTIPLIER == 0.5
