"""
Unit tests for review API routes.
Tests review session endpoints with dependency injection mocks.

Story 4.9: Post-Session Review Mode
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.db.session import get_db
from src.dependencies import get_current_user
from src.routes.review import get_review_session_service, router
from src.schemas.review import (
    ReviewAnswerResponse,
    ReviewAvailableResponse,
    ReviewQuestionResponse,
    ReviewSessionResponse,
    ReviewSkipResponse,
    ReviewSummaryResponse,
)

# ============================================================================
# Test Fixtures
# ============================================================================


def create_test_app_with_mocks(
    mock_user=None,
    mock_review_service=None,
    mock_db_session=None,
):
    """Create test app with dependency overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/v1")

    if mock_user:
        async def override_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_user

    if mock_review_service:
        async def override_service():
            return mock_review_service
        app.dependency_overrides[get_review_session_service] = override_service

    if mock_db_session:
        async def override_db():
            yield mock_db_session
        app.dependency_overrides[get_db] = override_db

    return app


def create_mock_user(user_id=None):
    """Create a mock user."""
    user = MagicMock()
    user.id = user_id or uuid4()
    return user


def create_mock_review_available_response(
    available=True,
    incorrect_count=3,
    question_ids=None,
):
    """Create a mock ReviewAvailableResponse."""
    return ReviewAvailableResponse(
        available=available,
        incorrect_count=incorrect_count,
        question_ids=question_ids or [str(uuid4()) for _ in range(incorrect_count)],
    )


def create_mock_review_session_response(
    session_id=None,
    original_session_id=None,
    status="in_progress",
    total_to_review=3,
    reviewed_count=0,
    reinforced_count=0,
    still_incorrect_count=0,
):
    """Create a mock ReviewSessionResponse."""
    return ReviewSessionResponse(
        id=str(session_id or uuid4()),
        original_session_id=str(original_session_id or uuid4()),
        status=status,
        total_to_review=total_to_review,
        reviewed_count=reviewed_count,
        reinforced_count=reinforced_count,
        still_incorrect_count=still_incorrect_count,
        started_at=datetime.now(UTC) if status == "in_progress" else None,
        created_at=datetime.now(UTC),
    )


def create_mock_review_question_response(
    question_id=None,
    review_number=1,
    total_to_review=3,
):
    """Create a mock ReviewQuestionResponse."""
    return ReviewQuestionResponse(
        question_id=str(question_id or uuid4()),
        question_text="What is the primary benefit of adaptive quiz sessions?",
        options={
            "A": "Fixed question order",
            "B": "Personalized learning paths",
            "C": "Shorter sessions",
            "D": "Random selection",
        },
        review_number=review_number,
        total_to_review=total_to_review,
    )


def create_mock_review_answer_response(
    is_correct=True,
    was_reinforced=True,
):
    """Create a mock ReviewAnswerResponse."""
    return ReviewAnswerResponse(
        is_correct=is_correct,
        was_reinforced=was_reinforced,
        correct_answer="B",
        explanation="Personalized learning paths adapt to student knowledge.",
        concepts_updated=[
            {"concept_id": str(uuid4()), "name": "Adaptive Learning", "new_mastery": 0.75}
        ],
        feedback_message="Great improvement! You've reinforced this concept." if was_reinforced else "Still needs practice. Review the material and try again.",
        reading_link=None if is_correct else "/reading?concept=adaptive-learning",
    )


def create_mock_review_skip_response(
    session_id=None,
    questions_skipped=3,
):
    """Create a mock ReviewSkipResponse."""
    return ReviewSkipResponse(
        message="Review session skipped. You can return to it later.",
        session_id=str(session_id or uuid4()),
        questions_skipped=questions_skipped,
    )


def create_mock_review_summary_response(
    total_reviewed=4,
    reinforced_count=3,
    still_incorrect_count=1,
):
    """Create a mock ReviewSummaryResponse."""
    return ReviewSummaryResponse(
        total_reviewed=total_reviewed,
        reinforced_count=reinforced_count,
        still_incorrect_count=still_incorrect_count,
        reinforcement_rate=reinforced_count / total_reviewed if total_reviewed > 0 else 0.0,
        still_incorrect_concepts=[
            {
                "concept_id": str(uuid4()),
                "name": "Test Concept",
                "reading_link": "/reading?concept=test-concept",
            }
        ] if still_incorrect_count > 0 else [],
    )


# ============================================================================
# Check Review Available Tests
# ============================================================================


class TestCheckReviewAvailable:
    """Test GET /quiz/session/{session_id}/review-available endpoint."""

    @pytest.mark.asyncio
    async def test_review_available_when_incorrect_answers_exist(self):
        """Verify endpoint returns available=True with incorrect answers."""
        user = create_mock_user()
        session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.check_review_available.return_value = create_mock_review_available_response(
            available=True,
            incorrect_count=3,
        )

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/session/{session_id}/review-available")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["available"] is True
            assert data["incorrect_count"] == 3
            assert len(data["question_ids"]) == 3

    @pytest.mark.asyncio
    async def test_review_not_available_when_all_correct(self):
        """Verify endpoint returns available=False when no incorrect answers."""
        user = create_mock_user()
        session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.check_review_available.return_value = create_mock_review_available_response(
            available=False,
            incorrect_count=0,
            question_ids=[],
        )

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/session/{session_id}/review-available")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["available"] is False
            assert data["incorrect_count"] == 0
            assert len(data["question_ids"]) == 0


# ============================================================================
# Start Review Tests
# ============================================================================


class TestStartReview:
    """Test POST /quiz/session/{session_id}/review/start endpoint."""

    @pytest.mark.asyncio
    async def test_start_review_creates_new_session(self):
        """Verify endpoint creates new review session."""
        user = create_mock_user()
        session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.start_review.return_value = create_mock_review_session_response(
            original_session_id=session_id,
            status="in_progress",
            total_to_review=3,
        )

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/session/{session_id}/review/start")

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["original_session_id"] == str(session_id)
            assert data["total_to_review"] == 3
            assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_start_review_returns_400_when_no_incorrect(self):
        """Verify endpoint returns 400 when no incorrect answers to review."""
        user = create_mock_user()
        session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.start_review.side_effect = ValueError("No incorrect answers to review")

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/session/{session_id}/review/start")

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert data["detail"]["error"]["code"] == "NO_INCORRECT_ANSWERS"


# ============================================================================
# Get Next Review Question Tests
# ============================================================================


class TestGetNextReviewQuestion:
    """Test GET /quiz/review/{review_session_id}/next-question endpoint."""

    @pytest.mark.asyncio
    async def test_returns_next_question(self):
        """Verify endpoint returns next question to review."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.get_next_review_question.return_value = create_mock_review_question_response(
            review_number=1,
            total_to_review=3,
        )

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/review/{review_session_id}/next-question")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "question_text" in data
            assert data["review_number"] == 1
            assert data["total_to_review"] == 3
            assert "options" in data
            assert len(data["options"]) == 4

    @pytest.mark.asyncio
    async def test_returns_null_when_all_reviewed(self):
        """Verify endpoint returns null when all questions reviewed."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.get_next_review_question.return_value = None

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/review/{review_session_id}/next-question")

            assert response.status_code == status.HTTP_200_OK
            assert response.json() is None

    @pytest.mark.asyncio
    async def test_returns_404_when_session_not_found(self):
        """Verify endpoint returns 404 for non-existent review session."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.get_next_review_question.side_effect = ValueError("Review session not found")

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/review/{review_session_id}/next-question")

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["detail"]["error"]["code"] == "REVIEW_SESSION_NOT_FOUND"


# ============================================================================
# Submit Review Answer Tests
# ============================================================================


class TestSubmitReviewAnswer:
    """Test POST /quiz/review/{review_session_id}/answer endpoint."""

    @pytest.mark.asyncio
    async def test_correct_answer_returns_reinforced(self):
        """Verify correct answer is marked as reinforced."""
        user = create_mock_user()
        review_session_id = uuid4()
        question_id = uuid4()

        mock_service = AsyncMock()
        mock_service.submit_review_answer.return_value = create_mock_review_answer_response(
            is_correct=True,
            was_reinforced=True,
        )

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/review/{review_session_id}/answer",
                json={
                    "question_id": str(question_id),
                    "selected_answer": "B",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_correct"] is True
            assert data["was_reinforced"] is True
            assert data["correct_answer"] == "B"
            assert "explanation" in data
            assert "Great improvement" in data["feedback_message"]

    @pytest.mark.asyncio
    async def test_incorrect_answer_returns_still_incorrect(self):
        """Verify incorrect answer shows still needs practice."""
        user = create_mock_user()
        review_session_id = uuid4()
        question_id = uuid4()

        mock_service = AsyncMock()
        mock_service.submit_review_answer.return_value = create_mock_review_answer_response(
            is_correct=False,
            was_reinforced=False,
        )

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/review/{review_session_id}/answer",
                json={
                    "question_id": str(question_id),
                    "selected_answer": "A",
                },
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_correct"] is False
            assert data["was_reinforced"] is False
            assert "practice" in data["feedback_message"].lower()
            assert data["reading_link"] is not None

    @pytest.mark.asyncio
    async def test_returns_409_when_already_reviewed(self):
        """Verify endpoint returns 409 when question already reviewed."""
        user = create_mock_user()
        review_session_id = uuid4()
        question_id = uuid4()

        mock_service = AsyncMock()
        mock_service.submit_review_answer.side_effect = ValueError("Question already reviewed")

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/review/{review_session_id}/answer",
                json={
                    "question_id": str(question_id),
                    "selected_answer": "B",
                },
            )

            assert response.status_code == status.HTTP_409_CONFLICT
            data = response.json()
            assert data["detail"]["error"]["code"] == "ALREADY_REVIEWED"

    @pytest.mark.asyncio
    async def test_validates_answer_format(self):
        """Verify endpoint validates answer format (A, B, C, D only)."""
        user = create_mock_user()
        review_session_id = uuid4()
        question_id = uuid4()

        mock_service = AsyncMock()
        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/review/{review_session_id}/answer",
                json={
                    "question_id": str(question_id),
                    "selected_answer": "E",  # Invalid answer
                },
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Skip Review Tests
# ============================================================================


class TestSkipReview:
    """Test POST /quiz/review/{review_session_id}/skip endpoint."""

    @pytest.mark.asyncio
    async def test_skip_review_success(self):
        """Verify endpoint successfully skips review session."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.skip_review.return_value = create_mock_review_skip_response(
            session_id=review_session_id,
            questions_skipped=3,
        )

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/review/{review_session_id}/skip")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["session_id"] == str(review_session_id)
            assert data["questions_skipped"] == 3
            assert "skipped" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_skip_returns_404_when_not_found(self):
        """Verify endpoint returns 404 for non-existent session."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.skip_review.side_effect = ValueError("Review session not found")

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/review/{review_session_id}/skip")

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["detail"]["error"]["code"] == "REVIEW_SESSION_NOT_FOUND"


# ============================================================================
# Get Review Summary Tests
# ============================================================================


class TestGetReviewSummary:
    """Test GET /quiz/review/{review_session_id}/summary endpoint."""

    @pytest.mark.asyncio
    async def test_returns_correct_summary(self):
        """Verify endpoint returns correct review summary."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.get_review_summary.return_value = create_mock_review_summary_response(
            total_reviewed=4,
            reinforced_count=3,
            still_incorrect_count=1,
        )

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/review/{review_session_id}/summary")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_reviewed"] == 4
            assert data["reinforced_count"] == 3
            assert data["still_incorrect_count"] == 1
            assert data["reinforcement_rate"] == 0.75
            assert len(data["still_incorrect_concepts"]) == 1

    @pytest.mark.asyncio
    async def test_perfect_review_has_no_incorrect_concepts(self):
        """Verify perfect review shows 100% reinforcement with no incorrect concepts."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.get_review_summary.return_value = create_mock_review_summary_response(
            total_reviewed=4,
            reinforced_count=4,
            still_incorrect_count=0,
        )

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/review/{review_session_id}/summary")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["reinforcement_rate"] == 1.0
            assert len(data["still_incorrect_concepts"]) == 0

    @pytest.mark.asyncio
    async def test_returns_404_when_not_found(self):
        """Verify endpoint returns 404 for non-existent review session."""
        user = create_mock_user()
        review_session_id = uuid4()

        mock_service = AsyncMock()
        mock_service.get_review_summary.side_effect = ValueError("Review session not found")

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_review_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/review/{review_session_id}/summary")

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert data["detail"]["error"]["code"] == "REVIEW_SESSION_NOT_FOUND"
