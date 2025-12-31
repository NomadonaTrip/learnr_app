"""
Unit tests for quiz API routes.
Tests quiz session endpoints with dependency injection mocks.
"""
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from fastapi import FastAPI, status
from httpx import ASGITransport, AsyncClient

from src.db.session import get_db
from src.dependencies import get_active_enrollment, get_current_user, get_quiz_session_service
from src.routes.quiz import router

# ============================================================================
# Test Fixtures
# ============================================================================


def create_test_app_with_mocks(
    mock_user=None,
    mock_enrollment=None,
    mock_session_service=None,
    mock_db_session=None,
):
    """Create test app with dependency overrides."""
    app = FastAPI()
    app.include_router(router, prefix="/v1")

    if mock_user:
        async def override_user():
            return mock_user
        app.dependency_overrides[get_current_user] = override_user

    if mock_enrollment:
        async def override_enrollment():
            return mock_enrollment
        app.dependency_overrides[get_active_enrollment] = override_enrollment

    if mock_session_service:
        async def override_service():
            return mock_session_service
        app.dependency_overrides[get_quiz_session_service] = override_service

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


def create_mock_enrollment(enrollment_id=None, user_id=None, course_id=None):
    """Create a mock enrollment."""
    enrollment = MagicMock()
    enrollment.id = enrollment_id or uuid4()
    enrollment.user_id = user_id or uuid4()
    enrollment.course_id = course_id or uuid4()
    enrollment.status = "active"
    return enrollment


def create_mock_quiz_session(
    session_id=None,
    user_id=None,
    enrollment_id=None,
    session_type="adaptive",
    question_strategy="max_info_gain",
    knowledge_area_filter=None,
    question_target=10,
    is_paused=False,
    ended_at=None,
    total_questions=0,
    correct_count=0,
    version=1,
):
    """Create a mock quiz session."""
    session = MagicMock()
    session.id = session_id or uuid4()
    session.user_id = user_id or uuid4()
    session.enrollment_id = enrollment_id or uuid4()
    session.session_type = session_type
    session.question_strategy = question_strategy
    session.knowledge_area_filter = knowledge_area_filter
    session.question_target = question_target
    session.started_at = datetime.now(UTC)
    session.ended_at = ended_at
    session.total_questions = total_questions
    session.correct_count = correct_count
    session.is_paused = is_paused
    session.version = version
    session.updated_at = datetime.now(UTC)

    # Derive status
    if ended_at:
        session.status = "completed"
    elif is_paused:
        session.status = "paused"
    else:
        session.status = "active"

    # Accuracy
    if total_questions > 0:
        session.accuracy = (correct_count / total_questions) * 100.0
    else:
        session.accuracy = 0.0

    return session


# ============================================================================
# Start Session Tests
# ============================================================================


class TestStartSession:
    """Test POST /quiz/session/start endpoint."""

    @pytest.mark.asyncio
    async def test_start_session_creates_new_session(self):
        """Verify endpoint creates new session when none exists."""
        user = create_mock_user()
        enrollment = create_mock_enrollment(user_id=user.id)
        new_session = create_mock_quiz_session(user_id=user.id, enrollment_id=enrollment.id)

        mock_service = AsyncMock()
        mock_service.start_session.return_value = (new_session, False)

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_enrollment=enrollment,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/quiz/session/start")

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["is_resumed"] is False
            assert data["session_type"] == "adaptive"
            assert data["question_strategy"] == "max_info_gain"

    @pytest.mark.asyncio
    async def test_start_session_returns_existing_session(self):
        """Verify endpoint returns existing session when one exists."""
        user = create_mock_user()
        enrollment = create_mock_enrollment(user_id=user.id)
        existing_session = create_mock_quiz_session(
            user_id=user.id,
            enrollment_id=enrollment.id,
            total_questions=5,
            correct_count=3,
        )

        mock_service = AsyncMock()
        mock_service.start_session.return_value = (existing_session, True)

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_enrollment=enrollment,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/quiz/session/start")

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["is_resumed"] is True

    @pytest.mark.asyncio
    async def test_start_session_with_custom_config(self):
        """Verify endpoint accepts custom session configuration."""
        user = create_mock_user()
        enrollment = create_mock_enrollment(user_id=user.id)
        new_session = create_mock_quiz_session(
            user_id=user.id,
            enrollment_id=enrollment.id,
            session_type="focused",
            question_strategy="balanced",
            knowledge_area_filter="ba-planning",
        )

        mock_service = AsyncMock()
        mock_service.start_session.return_value = (new_session, False)

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_enrollment=enrollment,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/quiz/session/start",
                json={
                    "session_type": "focused",
                    "question_strategy": "balanced",
                    "knowledge_area_filter": "ba-planning",
                },
            )

            assert response.status_code == status.HTTP_201_CREATED


# ============================================================================
# Get Session Tests
# ============================================================================


class TestGetSession:
    """Test GET /quiz/session/{id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_session_returns_session(self):
        """Verify endpoint returns session details."""
        user = create_mock_user()
        session_id = uuid4()
        session = create_mock_quiz_session(
            session_id=session_id,
            user_id=user.id,
            total_questions=10,
            correct_count=7,
        )

        mock_service = AsyncMock()
        mock_service.get_session.return_value = session

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/session/{session_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_questions"] == 10
            assert data["correct_count"] == 7
            assert data["accuracy"] == 70.0

    @pytest.mark.asyncio
    async def test_get_session_not_found(self):
        """Verify endpoint returns 404 for non-existent session."""
        user = create_mock_user()

        mock_service = AsyncMock()
        mock_service.get_session.side_effect = ValueError("Session not found")

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/session/{uuid4()}")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_get_session_unauthorized(self):
        """Verify endpoint returns 403 for wrong user."""
        user = create_mock_user()

        mock_service = AsyncMock()
        mock_service.get_session.side_effect = ValueError("Unauthorized: session belongs to different user")

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/session/{uuid4()}")

            assert response.status_code == status.HTTP_403_FORBIDDEN


# ============================================================================
# Pause Session Tests
# ============================================================================


class TestPauseSession:
    """Test POST /quiz/session/{id}/pause endpoint."""

    @pytest.mark.asyncio
    async def test_pause_session_success(self):
        """Verify endpoint pauses active session."""
        user = create_mock_user()
        session_id = uuid4()
        paused_session = create_mock_quiz_session(
            session_id=session_id,
            user_id=user.id,
            is_paused=True,
        )

        mock_service = AsyncMock()
        mock_service.pause_session.return_value = paused_session

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/session/{session_id}/pause")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_paused"] is True
            assert data["status"] == "paused"

    @pytest.mark.asyncio
    async def test_pause_already_paused_session(self):
        """Verify endpoint returns 400 for already paused session."""
        user = create_mock_user()

        mock_service = AsyncMock()
        mock_service.pause_session.side_effect = ValueError("Session is already paused")

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/session/{uuid4()}/pause")

            assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Resume Session Tests
# ============================================================================


class TestResumeSession:
    """Test POST /quiz/session/{id}/resume endpoint."""

    @pytest.mark.asyncio
    async def test_resume_session_success(self):
        """Verify endpoint resumes paused session."""
        user = create_mock_user()
        session_id = uuid4()
        resumed_session = create_mock_quiz_session(
            session_id=session_id,
            user_id=user.id,
            is_paused=False,
            total_questions=5,
            correct_count=3,
        )

        mock_service = AsyncMock()
        mock_service.resume_session.return_value = resumed_session

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/session/{session_id}/resume")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["is_paused"] is False
            assert data["status"] == "active"
            assert data["total_questions"] == 5

    @pytest.mark.asyncio
    async def test_resume_not_paused_session(self):
        """Verify endpoint returns 400 for non-paused session."""
        user = create_mock_user()

        mock_service = AsyncMock()
        mock_service.resume_session.side_effect = ValueError("Session is not paused")

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(f"/v1/quiz/session/{uuid4()}/resume")

            assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# End Session Tests
# ============================================================================


class TestEndSession:
    """Test POST /quiz/session/{id}/end endpoint."""

    @pytest.mark.asyncio
    async def test_end_session_success(self):
        """Verify endpoint ends session with correct version."""
        user = create_mock_user()
        session_id = uuid4()
        ended_session = create_mock_quiz_session(
            session_id=session_id,
            user_id=user.id,
            ended_at=datetime.now(UTC),
            total_questions=20,
            correct_count=15,
            version=2,
        )

        mock_service = AsyncMock()
        mock_service.end_session.return_value = ended_session

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/session/{session_id}/end",
                json={"expected_version": 1},
            )

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total_questions"] == 20
            assert data["correct_count"] == 15
            assert data["accuracy"] == 75.0

    @pytest.mark.asyncio
    async def test_end_session_version_conflict(self):
        """Verify endpoint returns 409 for version mismatch."""
        user = create_mock_user()

        mock_service = AsyncMock()
        mock_service.end_session.side_effect = ValueError(
            "Version conflict: expected 1, actual 3"
        )

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/session/{uuid4()}/end",
                json={"expected_version": 1},
            )

            assert response.status_code == status.HTTP_409_CONFLICT

    @pytest.mark.asyncio
    async def test_end_session_already_ended(self):
        """Verify endpoint returns 400 for already ended session."""
        user = create_mock_user()

        mock_service = AsyncMock()
        mock_service.end_session.side_effect = ValueError("Session is already ended")

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/session/{uuid4()}/end",
                json={"expected_version": 1},
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST


# ============================================================================
# Schema Validation Tests
# ============================================================================


class TestSchemaValidation:
    """Test request/response schema validation."""

    @pytest.mark.asyncio
    async def test_end_session_requires_version(self):
        """Verify end endpoint requires expected_version."""
        user = create_mock_user()

        mock_service = AsyncMock()
        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                f"/v1/quiz/session/{uuid4()}/end",
                json={},  # Missing expected_version
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_start_session_validates_session_type(self):
        """Verify start endpoint validates session type enum."""
        user = create_mock_user()
        enrollment = create_mock_enrollment(user_id=user.id)

        mock_service = AsyncMock()
        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_enrollment=enrollment,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/quiz/session/start",
                json={"session_type": "invalid_type"},
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_start_session_validates_question_strategy(self):
        """Verify start endpoint validates question strategy enum."""
        user = create_mock_user()
        enrollment = create_mock_enrollment(user_id=user.id)

        mock_service = AsyncMock()
        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_enrollment=enrollment,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/v1/quiz/session/start",
                json={"question_strategy": "invalid_strategy"},
            )

            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


# ============================================================================
# Question Target Tests (Story 4.1 Tasks 18-23)
# ============================================================================


class TestQuestionTarget:
    """Test question_target field in quiz session responses."""

    @pytest.mark.asyncio
    async def test_start_session_returns_question_target(self):
        """Verify start endpoint returns question_target in response."""
        user = create_mock_user()
        enrollment = create_mock_enrollment(user_id=user.id)
        new_session = create_mock_quiz_session(
            user_id=user.id,
            enrollment_id=enrollment.id,
            question_target=10,
        )

        mock_service = AsyncMock()
        mock_service.start_session.return_value = (new_session, False)

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_enrollment=enrollment,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/quiz/session/start")

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert "question_target" in data
            assert data["question_target"] == 10

    @pytest.mark.asyncio
    async def test_get_session_returns_question_target(self):
        """Verify get session endpoint returns question_target."""
        user = create_mock_user()
        session_id = uuid4()
        session = create_mock_quiz_session(
            session_id=session_id,
            user_id=user.id,
            question_target=10,
        )

        mock_service = AsyncMock()
        mock_service.get_session.return_value = session

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_session_service=mock_service,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get(f"/v1/quiz/session/{session_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert "question_target" in data
            assert data["question_target"] == 10

    @pytest.mark.asyncio
    async def test_question_target_default_is_10(self):
        """Verify default question_target is 10 for habit-forming consistency."""
        user = create_mock_user()
        enrollment = create_mock_enrollment(user_id=user.id)
        # Use default question_target (should be 10)
        new_session = create_mock_quiz_session(
            user_id=user.id,
            enrollment_id=enrollment.id,
        )

        mock_service = AsyncMock()
        mock_service.start_session.return_value = (new_session, False)

        mock_db = AsyncMock()

        app = create_test_app_with_mocks(
            mock_user=user,
            mock_enrollment=enrollment,
            mock_session_service=mock_service,
            mock_db_session=mock_db,
        )

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post("/v1/quiz/session/start")

            assert response.status_code == status.HTTP_201_CREATED
            data = response.json()
            assert data["question_target"] == 10
