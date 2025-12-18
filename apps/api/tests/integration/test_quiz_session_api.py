"""
Integration tests for quiz session API.
Tests the complete lifecycle: start -> pause -> resume -> end.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.user import User
from src.utils.auth import create_access_token, hash_password


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def quiz_test_course(db_session):
    """Create a course for quiz testing."""
    course = Course(
        slug=f"quiz-test-{uuid4().hex[:6]}",
        name="Quiz Test Course",
        description="Course for quiz session integration tests",
        knowledge_areas=[
            {"id": "ka1", "name": "Knowledge Area 1", "short_name": "KA1", "display_order": 1, "color": "#3B82F6"},
            {"id": "ka2", "name": "Knowledge Area 2", "short_name": "KA2", "display_order": 2, "color": "#10B981"},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def quiz_test_user(db_session):
    """Create a user for quiz testing."""
    user = User(
        email=f"quiztest_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def quiz_test_enrollment(db_session, quiz_test_user, quiz_test_course):
    """Create enrollment for testing."""
    enrollment = Enrollment(
        user_id=quiz_test_user.id,
        course_id=quiz_test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
def quiz_auth_headers(quiz_test_user):
    """Auth headers for the test user."""
    token = create_access_token(data={"sub": str(quiz_test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Session Start Tests
# ============================================================================


class TestQuizSessionStart:
    """Test starting quiz sessions."""

    @pytest.mark.asyncio
    async def test_start_quiz_session_creates_new_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify POST /quiz/session/start creates a new session."""
        response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert "session_id" in data
        assert data["session_type"] == "adaptive"
        assert data["question_strategy"] == "max_info_gain"
        assert data["is_resumed"] is False
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_start_quiz_session_returns_existing_active(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify starting when active session exists returns it."""
        # Start first session
        response1 = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        assert response1.status_code == 201
        session_id_1 = response1.json()["session_id"]

        # Start again - should return same session
        response2 = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        assert response2.status_code == 201
        data2 = response2.json()

        assert data2["session_id"] == session_id_1
        assert data2["is_resumed"] is True

    @pytest.mark.asyncio
    async def test_start_quiz_session_with_custom_config(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify custom session configuration is accepted."""
        response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
            json={
                "session_type": "focused",
                "question_strategy": "balanced",
                "knowledge_area_filter": "ka1",
            },
        )

        assert response.status_code == 201
        data = response.json()

        assert data["session_type"] == "focused"
        assert data["question_strategy"] == "balanced"

    @pytest.mark.asyncio
    async def test_start_quiz_session_requires_enrollment(
        self,
        client: AsyncClient,
        quiz_test_user,
    ):
        """Verify error when user has no enrollment."""
        # Create auth headers for user without enrollment
        token = create_access_token(data={"sub": str(quiz_test_user.id)})
        headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/v1/quiz/session/start",
            headers=headers,
        )

        assert response.status_code == 404


# ============================================================================
# Session Get Tests
# ============================================================================


class TestQuizSessionGet:
    """Test getting quiz session details."""

    @pytest.mark.asyncio
    async def test_get_quiz_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify GET /quiz/session/{id} returns session details."""
        # Create session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Get session
        response = await client.get(
            f"/v1/quiz/session/{session_id}",
            headers=quiz_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == session_id
        assert data["session_type"] == "adaptive"
        assert data["status"] == "active"
        assert data["total_questions"] == 0
        assert data["correct_count"] == 0
        assert data["accuracy"] == 0.0
        assert data["is_paused"] is False

    @pytest.mark.asyncio
    async def test_get_quiz_session_not_found(
        self,
        client: AsyncClient,
        quiz_auth_headers,
    ):
        """Verify 404 for non-existent session."""
        response = await client.get(
            f"/v1/quiz/session/{uuid4()}",
            headers=quiz_auth_headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_quiz_session_wrong_user(
        self,
        client: AsyncClient,
        db_session,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify 403 when accessing another user's session."""
        # Create session as original user
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Create another user
        other_user = User(
            email=f"other_{uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("testpass123"),
            is_admin=False,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_token = create_access_token(data={"sub": str(other_user.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        # Try to access with other user
        response = await client.get(
            f"/v1/quiz/session/{session_id}",
            headers=other_headers,
        )

        assert response.status_code == 403


# ============================================================================
# Session Pause/Resume Tests
# ============================================================================


class TestQuizSessionPauseResume:
    """Test pausing and resuming quiz sessions."""

    @pytest.mark.asyncio
    async def test_pause_quiz_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify POST /quiz/session/{id}/pause pauses session."""
        # Create session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Pause session
        response = await client.post(
            f"/v1/quiz/session/{session_id}/pause",
            headers=quiz_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == session_id
        assert data["is_paused"] is True
        assert data["status"] == "paused"

    @pytest.mark.asyncio
    async def test_pause_already_paused_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify error when pausing already paused session."""
        # Create and pause session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        await client.post(
            f"/v1/quiz/session/{session_id}/pause",
            headers=quiz_auth_headers,
        )

        # Try to pause again
        response = await client.post(
            f"/v1/quiz/session/{session_id}/pause",
            headers=quiz_auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_resume_quiz_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify POST /quiz/session/{id}/resume resumes session."""
        # Create and pause session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        await client.post(
            f"/v1/quiz/session/{session_id}/pause",
            headers=quiz_auth_headers,
        )

        # Resume session
        response = await client.post(
            f"/v1/quiz/session/{session_id}/resume",
            headers=quiz_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == session_id
        assert data["is_paused"] is False
        assert data["status"] == "active"

    @pytest.mark.asyncio
    async def test_resume_not_paused_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify error when resuming non-paused session."""
        # Create session (not paused)
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Try to resume
        response = await client.post(
            f"/v1/quiz/session/{session_id}/resume",
            headers=quiz_auth_headers,
        )

        assert response.status_code == 400


# ============================================================================
# Session End Tests
# ============================================================================


class TestQuizSessionEnd:
    """Test ending quiz sessions."""

    @pytest.mark.asyncio
    async def test_end_quiz_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify POST /quiz/session/{id}/end ends session."""
        # Create session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Get current version
        get_response = await client.get(
            f"/v1/quiz/session/{session_id}",
            headers=quiz_auth_headers,
        )
        version = get_response.json()["version"]

        # End session
        response = await client.post(
            f"/v1/quiz/session/{session_id}/end",
            headers=quiz_auth_headers,
            json={"expected_version": version},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == session_id
        assert data["ended_at"] is not None
        assert data["total_questions"] == 0
        assert data["correct_count"] == 0
        assert data["accuracy"] == 0.0

    @pytest.mark.asyncio
    async def test_end_quiz_session_version_conflict(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify 409 when version doesn't match."""
        # Create session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        # Try to end with wrong version
        response = await client.post(
            f"/v1/quiz/session/{session_id}/end",
            headers=quiz_auth_headers,
            json={"expected_version": 999},  # Wrong version
        )

        assert response.status_code == 409

    @pytest.mark.asyncio
    async def test_end_already_ended_session(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify error when ending already ended session."""
        # Create and end session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        session_id = start_response.json()["session_id"]

        get_response = await client.get(
            f"/v1/quiz/session/{session_id}",
            headers=quiz_auth_headers,
        )
        version = get_response.json()["version"]

        await client.post(
            f"/v1/quiz/session/{session_id}/end",
            headers=quiz_auth_headers,
            json={"expected_version": version},
        )

        # Try to end again
        response = await client.post(
            f"/v1/quiz/session/{session_id}/end",
            headers=quiz_auth_headers,
            json={"expected_version": version + 1},
        )

        assert response.status_code == 400


# ============================================================================
# Full Flow Tests
# ============================================================================


class TestQuizSessionFullFlow:
    """Test complete session lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_session_lifecycle(
        self,
        client: AsyncClient,
        quiz_test_enrollment,
        quiz_auth_headers,
    ):
        """Verify complete flow: start -> pause -> resume -> end."""
        # 1. Start session
        start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        assert start_response.status_code == 201
        session_id = start_response.json()["session_id"]

        # 2. Verify active status
        get_response = await client.get(
            f"/v1/quiz/session/{session_id}",
            headers=quiz_auth_headers,
        )
        assert get_response.json()["status"] == "active"

        # 3. Pause session
        pause_response = await client.post(
            f"/v1/quiz/session/{session_id}/pause",
            headers=quiz_auth_headers,
        )
        assert pause_response.status_code == 200
        assert pause_response.json()["status"] == "paused"

        # 4. Resume session
        resume_response = await client.post(
            f"/v1/quiz/session/{session_id}/resume",
            headers=quiz_auth_headers,
        )
        assert resume_response.status_code == 200
        assert resume_response.json()["status"] == "active"

        # 5. Get current version for ending
        get_response2 = await client.get(
            f"/v1/quiz/session/{session_id}",
            headers=quiz_auth_headers,
        )
        version = get_response2.json()["version"]

        # 6. End session
        end_response = await client.post(
            f"/v1/quiz/session/{session_id}/end",
            headers=quiz_auth_headers,
            json={"expected_version": version},
        )
        assert end_response.status_code == 200
        assert end_response.json()["ended_at"] is not None

        # 7. Starting new session should create new one (old one ended)
        new_start_response = await client.post(
            "/v1/quiz/session/start",
            headers=quiz_auth_headers,
        )
        assert new_start_response.status_code == 201
        assert new_start_response.json()["session_id"] != session_id
        assert new_start_response.json()["is_resumed"] is False
