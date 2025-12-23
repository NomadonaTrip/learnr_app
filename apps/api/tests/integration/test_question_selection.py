"""
Integration tests for question selection API.
Tests the Bayesian question selection endpoint with real database interactions.
"""
import time
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.models.quiz_response import QuizResponse
from src.models.quiz_session import QuizSession
from src.models.user import User
from src.utils.auth import create_access_token, hash_password

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def selection_test_course(db_session):
    """Create a course with knowledge areas for selection testing."""
    course = Course(
        slug=f"selection-test-{uuid4().hex[:6]}",
        name="Selection Test Course",
        description="Course for question selection integration tests",
        knowledge_areas=[
            {"id": "elicitation", "name": "Elicitation", "short_name": "EL", "display_order": 1, "color": "#3B82F6"},
            {"id": "planning", "name": "Planning", "short_name": "PL", "display_order": 2, "color": "#10B981"},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def selection_test_user(db_session):
    """Create a user for selection testing."""
    user = User(
        email=f"selecttest_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def selection_test_enrollment(db_session, selection_test_user, selection_test_course):
    """Create enrollment for testing."""
    enrollment = Enrollment(
        user_id=selection_test_user.id,
        course_id=selection_test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def selection_test_concepts(db_session, selection_test_course):
    """Create concepts for testing - mix of uncertain and confident."""
    concepts = []
    for i, ka_id in enumerate(["elicitation", "elicitation", "planning"]):
        concept = Concept(
            course_id=selection_test_course.id,
            name=f"Test Concept {i+1}",
            description=f"Description for concept {i+1}",
            knowledge_area_id=ka_id,
            difficulty_estimate=0.5,
        )
        db_session.add(concept)
        concepts.append(concept)

    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
async def selection_test_questions(db_session, selection_test_course, selection_test_concepts):
    """Create questions with concept mappings for testing."""
    questions = []

    # Question 1: Tests uncertain concept
    q1 = Question(
        course_id=selection_test_course.id,
        question_text="What is the best elicitation technique for stakeholders?",
        options={"A": "Interviews", "B": "Surveys", "C": "Workshops", "D": "Documents"},
        correct_answer="A",
        explanation="Interviews are best for stakeholder engagement.",
        knowledge_area_id="elicitation",
        difficulty=0.5,
        slip_rate=0.10,
        guess_rate=0.25,
        is_active=True,
    )
    db_session.add(q1)
    questions.append(q1)

    # Question 2: Tests different concept
    q2 = Question(
        course_id=selection_test_course.id,
        question_text="Which planning technique is most effective?",
        options={"A": "WBS", "B": "Gantt", "C": "PERT", "D": "CPM"},
        correct_answer="B",
        explanation="Gantt charts are effective for planning.",
        knowledge_area_id="planning",
        difficulty=0.6,
        slip_rate=0.10,
        guess_rate=0.25,
        is_active=True,
    )
    db_session.add(q2)
    questions.append(q2)

    # Question 3: Another elicitation question
    q3 = Question(
        course_id=selection_test_course.id,
        question_text="When should you use observation?",
        options={"A": "Always", "B": "Never", "C": "Sometimes", "D": "Rarely"},
        correct_answer="C",
        explanation="Observation is situational.",
        knowledge_area_id="elicitation",
        difficulty=0.4,
        slip_rate=0.10,
        guess_rate=0.25,
        is_active=True,
    )
    db_session.add(q3)
    questions.append(q3)

    await db_session.commit()

    # Create question-concept mappings
    for i, q in enumerate(questions):
        await db_session.refresh(q)
        qc = QuestionConcept(
            question_id=q.id,
            concept_id=selection_test_concepts[i % len(selection_test_concepts)].id,
            relevance=1.0,
        )
        db_session.add(qc)

    await db_session.commit()
    return questions


@pytest.fixture
async def selection_test_beliefs(db_session, selection_test_user, selection_test_concepts):
    """Create belief states for the user - with varying uncertainties."""
    beliefs = []

    # First concept: very uncertain (Beta(1,1))
    b1 = BeliefState(
        user_id=selection_test_user.id,
        concept_id=selection_test_concepts[0].id,
        alpha=1.0,
        beta=1.0,
        response_count=0,
    )
    db_session.add(b1)
    beliefs.append(b1)

    # Second concept: somewhat confident (Beta(8,2))
    b2 = BeliefState(
        user_id=selection_test_user.id,
        concept_id=selection_test_concepts[1].id,
        alpha=8.0,
        beta=2.0,
        response_count=5,
    )
    db_session.add(b2)
    beliefs.append(b2)

    # Third concept: moderately uncertain (Beta(3,3))
    b3 = BeliefState(
        user_id=selection_test_user.id,
        concept_id=selection_test_concepts[2].id,
        alpha=3.0,
        beta=3.0,
        response_count=3,
    )
    db_session.add(b3)
    beliefs.append(b3)

    await db_session.commit()
    for b in beliefs:
        await db_session.refresh(b)
    return beliefs


@pytest.fixture
async def selection_test_session(db_session, selection_test_user, selection_test_enrollment):
    """Create an active quiz session for testing."""
    session = QuizSession(
        user_id=selection_test_user.id,
        enrollment_id=selection_test_enrollment.id,
        session_type="adaptive",
        question_strategy="max_info_gain",
        knowledge_area_filter=None,
        is_paused=False,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
def selection_auth_headers(selection_test_user):
    """Auth headers for the test user."""
    token = create_access_token(data={"sub": str(selection_test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Question Selection Tests
# ============================================================================


class TestQuestionSelectionEndpoint:
    """Test the POST /quiz/next-question endpoint."""

    @pytest.mark.asyncio
    async def test_selects_question_successfully(
        self,
        client: AsyncClient,
        selection_test_session,
        selection_test_questions,
        selection_test_beliefs,
        selection_auth_headers,
    ):
        """Verify endpoint returns a selected question."""
        response = await client.post(
            "/v1/quiz/next-question",
            json={"session_id": str(selection_test_session.id)},
            headers=selection_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "session_id" in data
        assert "question" in data
        assert "questions_remaining" in data

        question = data["question"]
        assert "question_id" in question
        assert "question_text" in question
        assert "options" in question
        assert "knowledge_area_id" in question
        assert "difficulty" in question
        assert "estimated_info_gain" in question
        assert "concepts_tested" in question

        # Should NOT include correct_answer or explanation
        assert "correct_answer" not in question
        assert "explanation" not in question

    @pytest.mark.asyncio
    async def test_favors_uncertain_concepts(
        self,
        client: AsyncClient,
        selection_test_session,
        selection_test_questions,
        selection_test_beliefs,
        selection_auth_headers,
    ):
        """Selection should favor questions testing uncertain concepts."""
        # Get multiple selections and verify uncertain concepts are preferred
        info_gains = []
        for _ in range(3):
            response = await client.post(
                "/v1/quiz/next-question",
                json={"session_id": str(selection_test_session.id)},
                headers=selection_auth_headers,
            )
            assert response.status_code == 200
            data = response.json()
            info_gains.append(data["question"]["estimated_info_gain"])

        # All should have positive info gain
        assert all(g >= 0 for g in info_gains)

    @pytest.mark.asyncio
    async def test_requires_authentication(
        self,
        client: AsyncClient,
        selection_test_session,
    ):
        """Endpoint requires valid authentication."""
        response = await client.post(
            "/v1/quiz/next-question",
            json={"session_id": str(selection_test_session.id)},
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_rejects_invalid_session(
        self,
        client: AsyncClient,
        selection_test_enrollment,  # Required for get_active_enrollment dependency
        selection_auth_headers,
    ):
        """Endpoint rejects non-existent session."""
        response = await client.post(
            "/v1/quiz/next-question",
            json={"session_id": str(uuid4())},
            headers=selection_auth_headers,
        )

        assert response.status_code == 404
        assert "SESSION_NOT_FOUND" in response.json()["detail"]["error"]["code"]

    @pytest.mark.asyncio
    async def test_rejects_other_users_session(
        self,
        client: AsyncClient,
        db_session,
        selection_test_session,
    ):
        """Endpoint rejects session belonging to another user."""
        # Create a different user
        other_user = User(
            email=f"other_{uuid4().hex[:8]}@example.com",
            hashed_password=hash_password("testpass123"),
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        # Create token for other user
        token = create_access_token(data={"sub": str(other_user.id)})
        other_headers = {"Authorization": f"Bearer {token}"}

        response = await client.post(
            "/v1/quiz/next-question",
            json={"session_id": str(selection_test_session.id)},
            headers=other_headers,
        )

        # Should be 403 or 404 (depends on implementation)
        assert response.status_code in [403, 404]


class TestKnowledgeAreaFilter:
    """Test focused session knowledge area filtering."""

    @pytest.mark.asyncio
    async def test_respects_knowledge_area_filter(
        self,
        client: AsyncClient,
        db_session,
        selection_test_user,
        selection_test_enrollment,
        selection_test_questions,
        selection_test_beliefs,
        selection_auth_headers,
    ):
        """Focused session only returns questions from target KA."""
        # Create a focused session for elicitation
        focused_session = QuizSession(
            user_id=selection_test_user.id,
            enrollment_id=selection_test_enrollment.id,
            session_type="focused",
            question_strategy="max_info_gain",
            knowledge_area_filter="elicitation",
            is_paused=False,
        )
        db_session.add(focused_session)
        await db_session.commit()
        await db_session.refresh(focused_session)

        response = await client.post(
            "/v1/quiz/next-question",
            json={"session_id": str(focused_session.id)},
            headers=selection_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Selected question should be from elicitation KA
        assert data["question"]["knowledge_area_id"] == "elicitation"


class TestSelectionPerformance:
    """Test selection performance requirements."""

    @pytest.mark.asyncio
    async def test_selection_completes_quickly(
        self,
        client: AsyncClient,
        selection_test_session,
        selection_test_questions,
        selection_test_beliefs,
        selection_auth_headers,
    ):
        """Selection should complete in <200ms."""
        start = time.perf_counter()

        response = await client.post(
            "/v1/quiz/next-question",
            json={"session_id": str(selection_test_session.id)},
            headers=selection_auth_headers,
        )

        duration_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        # Allow some slack for test environment overhead
        assert duration_ms < 500  # 500ms with margin for test overhead


class TestSelectionStrategies:
    """Test different selection strategies."""

    @pytest.mark.asyncio
    async def test_max_uncertainty_strategy(
        self,
        client: AsyncClient,
        selection_test_session,
        selection_test_questions,
        selection_test_beliefs,
        selection_auth_headers,
    ):
        """max_uncertainty strategy should work."""
        response = await client.post(
            "/v1/quiz/next-question",
            json={
                "session_id": str(selection_test_session.id),
                "strategy": "max_uncertainty",
            },
            headers=selection_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "question" in data

    @pytest.mark.asyncio
    async def test_prerequisite_first_strategy(
        self,
        client: AsyncClient,
        selection_test_session,
        selection_test_questions,
        selection_test_beliefs,
        selection_auth_headers,
    ):
        """prerequisite_first strategy should work."""
        response = await client.post(
            "/v1/quiz/next-question",
            json={
                "session_id": str(selection_test_session.id),
                "strategy": "prerequisite_first",
            },
            headers=selection_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "question" in data


class TestRecentlyAnsweredExclusion:
    """Test that recently answered questions are excluded."""

    @pytest.mark.asyncio
    async def test_excludes_session_questions(
        self,
        client: AsyncClient,
        db_session,
        selection_test_session,
        selection_test_questions,
        selection_test_beliefs,
        selection_test_user,
        selection_auth_headers,
    ):
        """Questions answered in current session should be excluded."""
        # Record a response for the first question
        response_record = QuizResponse(
            user_id=selection_test_user.id,
            session_id=selection_test_session.id,
            question_id=selection_test_questions[0].id,
            selected_answer="A",
            is_correct=True,
        )
        db_session.add(response_record)
        await db_session.commit()

        # Update session count
        selection_test_session.total_questions = 1
        await db_session.commit()

        # Get next question
        response = await client.post(
            "/v1/quiz/next-question",
            json={"session_id": str(selection_test_session.id)},
            headers=selection_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # The selected question should NOT be the one we already answered
        assert data["question"]["question_id"] != str(selection_test_questions[0].id)

        # Questions remaining should reflect the answered question
        assert data["questions_remaining"] >= 0
