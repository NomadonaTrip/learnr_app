"""
Integration tests for diagnostic session flow.
Tests the complete lifecycle: start -> answer -> complete -> results.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.models.concept import Concept
from src.models.course import Course
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.models.user import User
from src.utils.auth import create_access_token, hash_password

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def session_test_course(db_session):
    """Create a course for session testing."""
    course = Course(
        slug=f"session-test-{uuid4().hex[:6]}",
        name="Session Test Course",
        description="Course for session integration tests",
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
async def session_test_concepts(db_session, session_test_course):
    """Create concepts for testing."""
    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=session_test_course.id,
            name=f"Test Concept {i+1}",
            description=f"Description for concept {i+1}",
            knowledge_area_id="ka1" if i < 3 else "ka2",
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        )
        db_session.add(concept)
        concepts.append(concept)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
async def session_test_questions(db_session, session_test_course, session_test_concepts):
    """Create questions for testing."""
    questions = []
    for i in range(15):
        question = Question(
            course_id=session_test_course.id,
            question_text=f"Test Question {i+1}?",
            options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            correct_answer="A",
            explanation=f"Explanation for question {i+1}",
            knowledge_area_id="ka1" if i < 10 else "ka2",
            difficulty=0.5,
            discrimination=1.0,
            slip_rate=0.1,
            guess_rate=0.25,
            is_active=True,
        )
        db_session.add(question)
        questions.append(question)
    await db_session.commit()

    # Add concept mappings
    for i, question in enumerate(questions):
        await db_session.refresh(question)
        concept = session_test_concepts[i % len(session_test_concepts)]
        mapping = QuestionConcept(
            question_id=question.id,
            concept_id=concept.id,
            relevance=1.0,
        )
        db_session.add(mapping)
    await db_session.commit()

    return questions


@pytest.fixture
async def session_test_user(db_session):
    """Create a user for session testing."""
    user = User(
        email=f"sessiontest_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def session_auth_headers(session_test_user):
    """Auth headers for the test user."""
    token = create_access_token(data={"sub": str(session_test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Session Start Tests
# ============================================================================


class TestDiagnosticSessionStart:
    """Test starting diagnostic sessions."""

    @pytest.mark.asyncio
    async def test_start_diagnostic_creates_session(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Verify GET /diagnostic/questions creates a new session."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have session info
        assert "session_id" in data
        assert data["session_status"] == "in_progress"
        assert data["current_index"] == 0
        assert data["is_resumed"] is False
        assert len(data["questions"]) > 0

    @pytest.mark.asyncio
    async def test_resume_diagnostic_session(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Verify GET /diagnostic/questions resumes existing session."""
        # Start session
        response1 = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        assert response1.status_code == 200
        data1 = response1.json()
        session_id = data1["session_id"]

        # Get questions again - should resume
        response2 = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        assert response2.status_code == 200
        data2 = response2.json()

        # Same session should be returned
        assert data2["session_id"] == session_id
        assert data2["is_resumed"] is True


# ============================================================================
# Answer Submission Tests
# ============================================================================


class TestDiagnosticAnswerSubmission:
    """Test submitting diagnostic answers."""

    @pytest.mark.asyncio
    async def test_submit_answer_advances_progress(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Verify answer submission advances session progress."""
        # Start session
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        data = response.json()
        session_id = data["session_id"]
        first_question = data["questions"][0]

        # Submit answer
        answer_response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "session_id": session_id,
                "question_id": first_question["id"],
                "selected_answer": "A",
            },
            headers=session_auth_headers,
        )

        assert answer_response.status_code == 200
        answer_data = answer_response.json()

        assert answer_data["is_recorded"] is True
        assert answer_data["diagnostic_progress"] == 1
        assert answer_data["session_status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_submit_answer_requires_valid_session(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_auth_headers,
    ):
        """Verify answer submission fails with invalid session."""
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "session_id": str(uuid4()),  # Non-existent session
                "question_id": str(session_test_questions[0].id),
                "selected_answer": "A",
            },
            headers=session_auth_headers,
        )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_submit_answer_validates_question_order(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Verify answer submission validates question matches expected position."""
        # Start session
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        data = response.json()
        session_id = data["session_id"]

        # Try to answer second question before first
        second_question = data["questions"][1]
        answer_response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "session_id": session_id,
                "question_id": second_question["id"],
                "selected_answer": "A",
            },
            headers=session_auth_headers,
        )

        assert answer_response.status_code == 400
        assert "does not match expected position" in answer_response.json()["detail"]["error"]["message"]


# ============================================================================
# Session Reset Tests
# ============================================================================


class TestDiagnosticReset:
    """Test diagnostic reset functionality."""

    @pytest.mark.asyncio
    async def test_reset_requires_confirmation(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Verify reset requires exact confirmation string."""
        # Start session first
        await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )

        # Try reset with wrong confirmation
        response = await client.post(
            f"/v1/diagnostic/reset?course_id={session_test_course.id}",
            json={"confirmation": "wrong"},
            headers=session_auth_headers,
        )

        assert response.status_code == 400
        assert "CONFIRMATION_REQUIRED" in response.json()["detail"]["error"]["code"]

    @pytest.mark.asyncio
    async def test_reset_clears_session(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Verify reset clears active session."""
        # Start session
        start_response = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        assert start_response.status_code == 200

        # Reset
        reset_response = await client.post(
            f"/v1/diagnostic/reset?course_id={session_test_course.id}",
            json={"confirmation": "RESET DIAGNOSTIC"},
            headers=session_auth_headers,
        )

        assert reset_response.status_code == 200
        reset_data = reset_response.json()

        assert reset_data["session_cleared"] is True
        assert reset_data["can_retake"] is True

    @pytest.mark.asyncio
    async def test_after_reset_new_session_created(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Verify new session created after reset."""
        # Start first session
        response1 = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        session_id_1 = response1.json()["session_id"]

        # Reset
        await client.post(
            f"/v1/diagnostic/reset?course_id={session_test_course.id}",
            json={"confirmation": "RESET DIAGNOSTIC"},
            headers=session_auth_headers,
        )

        # Start new session
        response2 = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        session_id_2 = response2.json()["session_id"]

        assert session_id_2 != session_id_1
        assert response2.json()["is_resumed"] is False


# ============================================================================
# Full Flow Integration Test
# ============================================================================


class TestFullDiagnosticFlow:
    """Test complete diagnostic flow from start to completion."""

    @pytest.mark.asyncio
    async def test_complete_diagnostic_flow(
        self,
        client: AsyncClient,
        session_test_course,
        session_test_questions,
        session_test_concepts,
        session_auth_headers,
    ):
        """Test the complete flow: start -> answer all -> complete -> results."""
        # 1. Start diagnostic session
        start_response = await client.get(
            f"/v1/diagnostic/questions?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )
        assert start_response.status_code == 200
        data = start_response.json()

        session_id = data["session_id"]
        questions = data["questions"]
        total = data["total"]

        assert data["session_status"] == "in_progress"

        # 2. Answer all questions
        for i, question in enumerate(questions):
            answer_response = await client.post(
                "/v1/diagnostic/answer",
                json={
                    "session_id": session_id,
                    "question_id": question["id"],
                    "selected_answer": "A",  # Always correct for this test
                },
                headers=session_auth_headers,
            )

            assert answer_response.status_code == 200
            answer_data = answer_response.json()

            assert answer_data["diagnostic_progress"] == i + 1

            # Last answer should complete the session
            if i == len(questions) - 1:
                assert answer_data["session_status"] == "completed"
            else:
                assert answer_data["session_status"] == "in_progress"

        # 3. Get results
        results_response = await client.get(
            f"/v1/diagnostic/results?course_id={session_test_course.id}",
            headers=session_auth_headers,
        )

        assert results_response.status_code == 200
        results_data = results_response.json()

        # Results should include session info
        assert results_data["session_status"] == "completed"
        assert results_data["score"]["questions_answered"] == total
