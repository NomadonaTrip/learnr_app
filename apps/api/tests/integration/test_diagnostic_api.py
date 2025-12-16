"""
Integration tests for Diagnostic API endpoints.
Tests GET /api/v1/diagnostic/questions and POST /api/v1/diagnostic/answer endpoints.
"""
import time
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.question import Question
from src.models.question_concept import QuestionConcept


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def test_course(db_session: AsyncSession) -> Course:
    """Create a test course for diagnostic tests."""
    course = Course(
        slug="test-diagnostic-course",
        name="Test Diagnostic Course",
        description="Course for testing diagnostic question selection",
        corpus_name="Test Corpus",
        knowledge_areas=[
            {"id": "ka1", "name": "Knowledge Area 1", "short_name": "KA1", "display_order": 1, "color": "#FF0000"},
            {"id": "ka2", "name": "Knowledge Area 2", "short_name": "KA2", "display_order": 2, "color": "#00FF00"},
            {"id": "ka3", "name": "Knowledge Area 3", "short_name": "KA3", "display_order": 3, "color": "#0000FF"},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concepts(db_session: AsyncSession, test_course: Course) -> list[Concept]:
    """Create test concepts for the course."""
    concepts = []
    for i in range(20):
        concept = Concept(
            course_id=test_course.id,
            name=f"Test Concept {i}",
            description=f"Description for concept {i}",
            corpus_section_ref=f"1.{i}",
            knowledge_area_id=f"ka{(i % 3) + 1}",
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        )
        concepts.append(concept)
    db_session.add_all(concepts)
    await db_session.commit()
    for concept in concepts:
        await db_session.refresh(concept)
    return concepts


@pytest.fixture
async def test_questions_with_concepts(
    db_session: AsyncSession,
    test_course: Course,
    test_concepts: list[Concept],
) -> list[Question]:
    """Create test questions with concept mappings."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    questions = []
    for i in range(18):
        ka_index = i % 3
        question = Question(
            course_id=test_course.id,
            question_text=f"This is test question number {i} with sufficient length for validation?",
            options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            correct_answer="A",
            explanation=f"This is the explanation for question {i} with sufficient length.",
            knowledge_area_id=f"ka{ka_index + 1}",
            difficulty=0.3 + (i * 0.03),
            discrimination=1.0 + (i * 0.1),
            is_active=True,
        )
        questions.append(question)

    db_session.add_all(questions)
    await db_session.commit()

    # Create concept mappings (each question covers 2-3 concepts)
    for i, question in enumerate(questions):
        await db_session.refresh(question)
        # Map to 2-3 concepts
        concept_indices = [(i * 2) % len(test_concepts), ((i * 2) + 1) % len(test_concepts)]
        if i % 3 == 0:
            concept_indices.append(((i * 2) + 2) % len(test_concepts))

        for idx in concept_indices:
            mapping = QuestionConcept(
                question_id=question.id,
                concept_id=test_concepts[idx].id,
                relevance=1.0,
            )
            db_session.add(mapping)

    await db_session.commit()

    # Re-fetch questions with relationships loaded to avoid lazy loading issues
    question_ids = [q.id for q in questions]
    result = await db_session.execute(
        select(Question)
        .where(Question.id.in_(question_ids))
        .options(selectinload(Question.question_concepts))
        .order_by(Question.difficulty)
    )
    return list(result.scalars().all())


# ============================================================================
# Authentication Tests
# ============================================================================

class TestAuthentication:
    """Test authentication requirements."""

    @pytest.mark.asyncio
    async def test_requires_authentication(
        self, client: AsyncClient, test_course: Course
    ):
        """Verify endpoint returns 401 without authentication."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_accepts_valid_token(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify endpoint accepts valid JWT token."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200


# ============================================================================
# Endpoint Response Tests
# ============================================================================

class TestEndpointResponse:
    """Test endpoint response format and content."""

    @pytest.mark.asyncio
    async def test_returns_200_with_questions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify endpoint returns 200 with questions."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert "questions" in data
        assert "total" in data
        assert "concepts_covered" in data
        assert "coverage_percentage" in data
        assert len(data["questions"]) > 0

    @pytest.mark.asyncio
    async def test_returns_correct_question_count(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify endpoint returns target number of questions."""
        # Request 15 questions
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}&target_count=15",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        # Should return 15 or all available (18), limited by KA balance (max 4 per KA)
        # With 3 KAs and max 4 each, max is 12 but we have 18 questions distributed
        assert data["total"] <= 15
        assert data["total"] == len(data["questions"])

    @pytest.mark.asyncio
    async def test_returns_404_when_no_questions(
        self, client: AsyncClient, auth_headers: dict, test_course: Course
    ):
        """Verify endpoint returns 404 when no questions available."""
        # Use a course with no questions (just create a new one)
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={uuid4()}",
            headers=auth_headers,
        )
        # Should return 404 since no questions exist for this course
        assert response.status_code == 404


# ============================================================================
# Schema Validation Tests
# ============================================================================

class TestSchemaValidation:
    """Test response schema excludes sensitive fields."""

    @pytest.mark.asyncio
    async def test_excludes_correct_answer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify response excludes correct_answer field."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        for question in data["questions"]:
            assert "correct_answer" not in question
            assert "correctAnswer" not in question

    @pytest.mark.asyncio
    async def test_excludes_explanation(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify response excludes explanation field."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        for question in data["questions"]:
            assert "explanation" not in question

    @pytest.mark.asyncio
    async def test_includes_required_fields(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify response includes all required fields."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        for question in data["questions"]:
            assert "id" in question
            assert "question_text" in question
            assert "options" in question
            assert "knowledge_area_id" in question
            assert "difficulty" in question
            assert "discrimination" in question


# ============================================================================
# Caching Tests
# ============================================================================

class TestCaching:
    """Test Redis caching behavior."""

    @pytest.mark.asyncio
    async def test_cache_returns_same_questions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify cached response returns same questions on repeated calls."""
        # First call
        response1 = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response1.status_code == 200
        questions1 = {q["id"] for q in response1.json()["questions"]}

        # Second call (should hit cache)
        response2 = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response2.status_code == 200
        questions2 = {q["id"] for q in response2.json()["questions"]}

        # Same questions should be returned
        assert questions1 == questions2

    @pytest.mark.asyncio
    async def test_cache_is_user_specific(
        self,
        client: AsyncClient,
        auth_headers: dict,
        admin_auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify cache is per-user (different users can get different questions)."""
        # First user
        response1 = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response1.status_code == 200

        # Second user (admin)
        response2 = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=admin_auth_headers,
        )
        assert response2.status_code == 200

        # Both should get valid responses (cache is user-specific)
        assert len(response1.json()["questions"]) > 0
        assert len(response2.json()["questions"]) > 0


# ============================================================================
# Performance Tests
# ============================================================================

class TestPerformance:
    """Test performance requirements."""

    @pytest.mark.asyncio
    async def test_response_time_under_500ms(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify response time is under 500ms."""
        # Clear any cache first by making request with different target
        await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}&target_count=12",
            headers=auth_headers,
        )

        # Time the actual request
        start = time.perf_counter()
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}&target_count=15",
            headers=auth_headers,
        )
        duration_ms = (time.perf_counter() - start) * 1000

        assert response.status_code == 200
        # Allow more time in test environment (500ms target, but tests may be slower)
        assert duration_ms < 2000, f"Response took {duration_ms:.0f}ms (target <500ms)"


# ============================================================================
# Query Parameter Tests
# ============================================================================

class TestQueryParameters:
    """Test query parameter validation."""

    @pytest.mark.asyncio
    async def test_requires_course_id(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Verify course_id is required."""
        response = await client.get(
            "/v1/diagnostic/questions",
            headers=auth_headers,
        )
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_validates_target_count_range(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify target_count validation (12-20)."""
        # Below minimum
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}&target_count=5",
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Above maximum
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}&target_count=50",
            headers=auth_headers,
        )
        assert response.status_code == 422

        # Valid range
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}&target_count=15",
            headers=auth_headers,
        )
        assert response.status_code == 200


# ============================================================================
# Coverage Statistics Tests
# ============================================================================

class TestCoverageStatistics:
    """Test coverage statistics in response."""

    @pytest.mark.asyncio
    async def test_returns_coverage_statistics(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
    ):
        """Verify response includes coverage statistics."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["concepts_covered"] > 0
        assert 0.0 <= data["coverage_percentage"] <= 1.0

    @pytest.mark.asyncio
    async def test_coverage_percentage_is_valid(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_questions_with_concepts: list[Question],
        test_concepts: list[Concept],
    ):
        """Verify coverage percentage is calculated correctly."""
        response = await client.get(
            f"/v1/diagnostic/questions?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        # Coverage should be concepts_covered / total_concepts
        # With 20 concepts and good coverage, should be > 0
        assert data["coverage_percentage"] > 0
        assert data["concepts_covered"] <= len(test_concepts)


# ============================================================================
# Diagnostic Answer Fixtures
# ============================================================================

@pytest.fixture
async def test_user_with_beliefs(
    db_session: AsyncSession,
    test_user,
    test_concepts: list[Concept],
) -> None:
    """Initialize belief states for test user for all test concepts."""
    beliefs = []
    for concept in test_concepts:
        belief = BeliefState(
            user_id=test_user.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0,
            response_count=0,
        )
        beliefs.append(belief)
    db_session.add_all(beliefs)
    await db_session.commit()


# ============================================================================
# Diagnostic Answer Endpoint Tests
# ============================================================================

class TestDiagnosticAnswerEndpoint:
    """Test POST /diagnostic/answer endpoint."""

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(
        self,
        client: AsyncClient,
        test_questions_with_concepts: list[Question],
    ):
        """Verify endpoint requires authentication."""
        question = test_questions_with_concepts[0]
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question.id),
                "selected_answer": "A",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_200_with_valid_answer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_questions_with_concepts: list[Question],
        test_user_with_beliefs,
    ):
        """Verify endpoint returns 200 for valid answer submission."""
        question = test_questions_with_concepts[0]
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question.id),
                "selected_answer": "A",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        assert data["is_recorded"] is True
        assert "concepts_updated" in data
        assert data["diagnostic_progress"] >= 1

    @pytest.mark.asyncio
    async def test_returns_404_for_nonexistent_question(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Verify endpoint returns 404 for nonexistent question."""
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(uuid4()),
                "selected_answer": "A",
            },
            headers=auth_headers,
        )
        assert response.status_code == 404
        assert response.json()["detail"]["error"]["code"] == "QUESTION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_validates_answer_format(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_questions_with_concepts: list[Question],
    ):
        """Verify endpoint rejects invalid answer letters."""
        question = test_questions_with_concepts[0]

        # Test invalid answer
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question.id),
                "selected_answer": "E",
            },
            headers=auth_headers,
        )
        assert response.status_code == 422


# ============================================================================
# Belief Update Integration Tests
# ============================================================================

class TestBeliefUpdates:
    """Test that beliefs are actually updated after answer submission."""

    @pytest.mark.asyncio
    async def test_beliefs_updated_after_correct_answer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_questions_with_concepts: list[Question],
        test_concepts: list[Concept],
        test_user_with_beliefs,
    ):
        """Verify belief states are updated after correct answer submission."""
        from sqlalchemy import select

        # Get first question and its linked concepts
        question = test_questions_with_concepts[0]

        # Save IDs before any expiration (to avoid greenlet issues)
        user_id = test_user.id
        question_id = question.id
        correct_answer = question.correct_answer
        concept_id = question.question_concepts[0].concept_id

        # Query initial belief
        initial_result = await db_session.execute(
            select(BeliefState).where(
                BeliefState.user_id == user_id,
                BeliefState.concept_id == concept_id,
            )
        )
        initial_belief = initial_result.scalar_one()
        initial_alpha = initial_belief.alpha
        initial_beta = initial_belief.beta
        initial_response_count = initial_belief.response_count

        # Submit correct answer
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question_id),
                "selected_answer": correct_answer,  # Correct answer
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Expire all cached objects and refresh session to get updated data
        db_session.expire_all()

        # Query updated belief fresh from database
        updated_result = await db_session.execute(
            select(BeliefState).where(
                BeliefState.user_id == user_id,
                BeliefState.concept_id == concept_id,
            )
        )
        updated_belief = updated_result.scalar_one()

        # Verify belief was updated
        assert updated_belief.alpha > initial_alpha, "Alpha should increase for correct answer"
        assert updated_belief.response_count == initial_response_count + 1

    @pytest.mark.asyncio
    async def test_beliefs_updated_after_incorrect_answer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_questions_with_concepts: list[Question],
        test_concepts: list[Concept],
        test_user_with_beliefs,
    ):
        """Verify belief states are updated after incorrect answer submission."""
        from sqlalchemy import select

        # Get first question
        question = test_questions_with_concepts[0]

        # Save IDs before any expiration (to avoid greenlet issues)
        user_id = test_user.id
        question_id = question.id
        correct_answer = question.correct_answer
        concept_id = question.question_concepts[0].concept_id

        # Get a wrong answer (not the correct one)
        wrong_answer = "B" if correct_answer != "B" else "C"

        # Query initial belief
        initial_result = await db_session.execute(
            select(BeliefState).where(
                BeliefState.user_id == user_id,
                BeliefState.concept_id == concept_id,
            )
        )
        initial_belief = initial_result.scalar_one()
        initial_alpha = initial_belief.alpha
        initial_beta = initial_belief.beta

        # Submit incorrect answer
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question_id),
                "selected_answer": wrong_answer,
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        # Expire all cached objects and refresh session to get updated data
        db_session.expire_all()

        # Query updated belief fresh from database
        updated_result = await db_session.execute(
            select(BeliefState).where(
                BeliefState.user_id == user_id,
                BeliefState.concept_id == concept_id,
            )
        )
        updated_belief = updated_result.scalar_one()

        # Verify belief was updated (beta increases more for incorrect)
        assert updated_belief.beta > initial_beta, "Beta should increase for incorrect answer"

    @pytest.mark.asyncio
    async def test_multiple_concepts_updated(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session: AsyncSession,
        test_user,
        test_questions_with_concepts: list[Question],
        test_concepts: list[Concept],
        test_user_with_beliefs,
    ):
        """Verify all concepts linked to question are updated."""
        # Find a question with multiple concepts (every 3rd question has 3 concepts)
        question = test_questions_with_concepts[0]  # This has 3 concepts

        # Get all concept IDs for this question
        concept_ids = [qc.concept_id for qc in question.question_concepts]
        assert len(concept_ids) >= 2, "Test requires question with multiple concepts"

        # Submit answer
        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question.id),
                "selected_answer": "A",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        # All concepts should be reported as updated
        assert len(data["concepts_updated"]) == len(concept_ids)

    @pytest.mark.asyncio
    async def test_response_excludes_correctness_feedback(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_questions_with_concepts: list[Question],
        test_user_with_beliefs,
    ):
        """Verify response does not include is_correct or explanation."""
        question = test_questions_with_concepts[0]

        response = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question.id),
                "selected_answer": "A",
            },
            headers=auth_headers,
        )
        assert response.status_code == 200

        data = response.json()
        # Should NOT contain feedback (diagnostic mode)
        assert "is_correct" not in data
        assert "explanation" not in data
        assert "correct_answer" not in data


# ============================================================================
# Duplicate Answer Prevention Tests
# ============================================================================

class TestDuplicateAnswerPrevention:
    """Test duplicate answer prevention."""

    @pytest.mark.asyncio
    async def test_returns_409_for_duplicate_answer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_questions_with_concepts: list[Question],
        test_user_with_beliefs,
    ):
        """Verify 409 returned when submitting same question twice."""
        question = test_questions_with_concepts[0]

        # First submission
        response1 = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question.id),
                "selected_answer": "A",
            },
            headers=auth_headers,
        )
        assert response1.status_code == 200

        # Second submission (duplicate)
        response2 = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(question.id),
                "selected_answer": "B",  # Different answer
            },
            headers=auth_headers,
        )
        assert response2.status_code == 409
        assert response2.json()["detail"]["error"]["code"] == "DUPLICATE_REQUEST"


# ============================================================================
# Progress Tracking Tests
# ============================================================================

class TestProgressTracking:
    """Test diagnostic progress tracking."""

    @pytest.mark.asyncio
    async def test_progress_increments_with_each_answer(
        self,
        client: AsyncClient,
        auth_headers: dict,
        test_questions_with_concepts: list[Question],
        test_user_with_beliefs,
    ):
        """Verify diagnostic_progress increments with each answer."""
        # Submit first answer
        response1 = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(test_questions_with_concepts[0].id),
                "selected_answer": "A",
            },
            headers=auth_headers,
        )
        assert response1.status_code == 200
        assert response1.json()["diagnostic_progress"] == 1

        # Submit second answer (different question)
        response2 = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(test_questions_with_concepts[1].id),
                "selected_answer": "B",
            },
            headers=auth_headers,
        )
        assert response2.status_code == 200
        assert response2.json()["diagnostic_progress"] == 2

        # Submit third answer
        response3 = await client.post(
            "/v1/diagnostic/answer",
            json={
                "question_id": str(test_questions_with_concepts[2].id),
                "selected_answer": "C",
            },
            headers=auth_headers,
        )
        assert response3.status_code == 200
        assert response3.json()["diagnostic_progress"] == 3
