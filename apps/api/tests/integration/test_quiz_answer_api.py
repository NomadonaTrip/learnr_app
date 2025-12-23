"""
Integration tests for quiz answer submission API.
Story 4.3: Answer Submission and Immediate Feedback

Tests:
1. Submit answer success (200)
2. Submit answer unauthorized (401)
3. Submit answer invalid session (404)
4. Submit answer invalid question (404)
5. Submit answer already answered (409)
6. Submit answer invalid format (400)
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.question import Question
from src.models.quiz_session import QuizSession
from src.models.user import User
from src.utils.auth import create_access_token, hash_password

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def answer_test_course(db_session):
    """Create a course for answer testing."""
    course = Course(
        slug=f"answer-test-{uuid4().hex[:6]}",
        name="Answer Test Course",
        description="Course for answer submission integration tests",
        knowledge_areas=[
            {
                "id": "ka1",
                "name": "Knowledge Area 1",
                "short_name": "KA1",
                "display_order": 1,
                "color": "#3B82F6",
            },
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def answer_test_user(db_session):
    """Create a user for answer testing."""
    user = User(
        email=f"answertest_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def answer_test_enrollment(db_session, answer_test_user, answer_test_course):
    """Create enrollment for testing."""
    enrollment = Enrollment(
        user_id=answer_test_user.id,
        course_id=answer_test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def answer_test_question(db_session, answer_test_course):
    """Create a test question."""
    question = Question(
        course_id=answer_test_course.id,
        question_text="What is the primary purpose of stakeholder analysis?",
        options={
            "A": "To identify and understand project stakeholders",
            "B": "To calculate project costs",
            "C": "To schedule project tasks",
            "D": "To design system architecture",
        },
        correct_answer="A",
        explanation="Stakeholder analysis is a technique used to identify and understand the individuals and groups who have an interest in the project.",
        knowledge_area_id="ka1",
        difficulty=0.5,
        source="test",
        is_active=True,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)
    return question


@pytest.fixture
async def answer_test_session(
    db_session, answer_test_user, answer_test_enrollment
):
    """Create a test quiz session."""
    session = QuizSession(
        user_id=answer_test_user.id,
        enrollment_id=answer_test_enrollment.id,
        session_type="adaptive",
        question_strategy="max_info_gain",
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
def answer_auth_headers(answer_test_user):
    """Auth headers for the test user."""
    token = create_access_token(data={"sub": str(answer_test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Success Tests
# ============================================================================


class TestSubmitAnswerSuccess:
    """Test successful answer submission scenarios."""

    @pytest.mark.asyncio
    async def test_submit_correct_answer_returns_200(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with correct answer returns 200."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_correct"] is True
        assert data["correct_answer"] == "A"
        assert "explanation" in data
        assert "stakeholder" in data["explanation"].lower()
        assert "concepts_updated" in data
        assert "session_stats" in data

    @pytest.mark.asyncio
    async def test_submit_wrong_answer_returns_200(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with wrong answer returns 200 with correct feedback."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "B",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_correct"] is False
        assert data["correct_answer"] == "A"
        assert "explanation" in data

    @pytest.mark.asyncio
    async def test_submit_answer_includes_session_stats(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify response includes session statistics."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 200
        data = response.json()

        stats = data["session_stats"]
        assert "questions_answered" in stats
        assert "accuracy" in stats
        assert stats["questions_answered"] >= 1

    @pytest.mark.asyncio
    async def test_submit_answer_lowercase_normalized(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify lowercase answer is normalized to uppercase."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "a",  # lowercase
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True

    @pytest.mark.asyncio
    async def test_submit_answer_with_request_id_idempotent(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify same request_id returns same response (idempotency)."""
        request_id = str(uuid4())

        # First submission
        response1 = await client.post(
            "/v1/quiz/answer",
            headers={**answer_auth_headers, "X-Request-ID": request_id},
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )
        assert response1.status_code == 200

        # Second submission with same request_id
        response2 = await client.post(
            "/v1/quiz/answer",
            headers={**answer_auth_headers, "X-Request-ID": request_id},
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )
        assert response2.status_code == 200

        # Both should return same result
        assert response1.json()["is_correct"] == response2.json()["is_correct"]


# ============================================================================
# Authentication Tests
# ============================================================================


class TestSubmitAnswerAuthentication:
    """Test authentication requirements."""

    @pytest.mark.asyncio
    async def test_submit_answer_without_auth_returns_401(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
    ):
        """Verify POST /quiz/answer without auth returns 401."""
        response = await client.post(
            "/v1/quiz/answer",
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_submit_answer_with_invalid_token_returns_401(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
    ):
        """Verify POST /quiz/answer with invalid token returns 401."""
        response = await client.post(
            "/v1/quiz/answer",
            headers={"Authorization": "Bearer invalid_token"},
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 401


# ============================================================================
# Invalid Session Tests
# ============================================================================


class TestSubmitAnswerInvalidSession:
    """Test invalid session handling."""

    @pytest.mark.asyncio
    async def test_submit_answer_nonexistent_session_returns_404(
        self,
        client: AsyncClient,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with nonexistent session returns 404."""
        fake_session_id = str(uuid4())

        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": fake_session_id,
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "INVALID_SESSION"

    @pytest.mark.asyncio
    async def test_submit_answer_other_users_session_returns_404(
        self,
        client: AsyncClient,
        db_session,
        answer_test_session,
        answer_test_question,
    ):
        """Verify POST /quiz/answer to another user's session returns 404."""
        # Create a different user
        other_user = User(
            email=f"other_{uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("testpass123"),
            is_admin=False,
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        # Auth as different user
        other_token = create_access_token(data={"sub": str(other_user.id)})
        other_headers = {"Authorization": f"Bearer {other_token}"}

        response = await client.post(
            "/v1/quiz/answer",
            headers=other_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "INVALID_SESSION"


# ============================================================================
# Invalid Question Tests
# ============================================================================


class TestSubmitAnswerInvalidQuestion:
    """Test invalid question handling."""

    @pytest.mark.asyncio
    async def test_submit_answer_nonexistent_question_returns_404(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with nonexistent question returns 404."""
        fake_question_id = str(uuid4())

        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": fake_question_id,
                "selected_answer": "A",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "INVALID_QUESTION"

    @pytest.mark.asyncio
    async def test_submit_answer_inactive_question_returns_404(
        self,
        client: AsyncClient,
        db_session,
        answer_test_session,
        answer_test_course,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with inactive question returns 404."""
        # Create inactive question
        inactive_question = Question(
            course_id=answer_test_course.id,
            question_text="Inactive question",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka1",
            difficulty=0.5,
            source="test",
            is_active=False,  # Inactive
        )
        db_session.add(inactive_question)
        await db_session.commit()
        await db_session.refresh(inactive_question)

        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(inactive_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "INVALID_QUESTION"


# ============================================================================
# Already Answered Tests
# ============================================================================


class TestSubmitAnswerAlreadyAnswered:
    """Test duplicate answer handling."""

    @pytest.mark.asyncio
    async def test_submit_answer_twice_returns_409(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer twice for same question returns 409."""
        # First submission
        response1 = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )
        assert response1.status_code == 200

        # Second submission (without request_id) should fail
        response2 = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "B",  # Even different answer
            },
        )

        assert response2.status_code == 409
        data = response2.json()
        assert "detail" in data
        assert data["detail"]["error"]["code"] == "ALREADY_ANSWERED"


# ============================================================================
# Invalid Format Tests
# ============================================================================


class TestSubmitAnswerInvalidFormat:
    """Test invalid answer format handling."""

    @pytest.mark.asyncio
    async def test_submit_answer_invalid_option_returns_422(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with invalid option returns 422."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "E",  # Invalid option
            },
        )

        # Pydantic validation returns 422 Unprocessable Entity
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_answer_empty_option_returns_422(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with empty option returns 422."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "question_id": str(answer_test_question.id),
                "selected_answer": "",  # Empty
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_answer_missing_session_id_returns_422(
        self,
        client: AsyncClient,
        answer_test_question,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer without session_id returns 422."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "question_id": str(answer_test_question.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_answer_missing_question_id_returns_422(
        self,
        client: AsyncClient,
        answer_test_session,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer without question_id returns 422."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": str(answer_test_session.id),
                "selected_answer": "A",
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_answer_invalid_uuid_format_returns_422(
        self,
        client: AsyncClient,
        answer_auth_headers,
    ):
        """Verify POST /quiz/answer with invalid UUID returns 422."""
        response = await client.post(
            "/v1/quiz/answer",
            headers=answer_auth_headers,
            json={
                "session_id": "not-a-uuid",
                "question_id": "also-not-a-uuid",
                "selected_answer": "A",
            },
        )

        assert response.status_code == 422
