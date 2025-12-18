"""
Integration tests for diagnostic results API.
Tests the full flow of getting results after completing diagnostic.
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.user import User


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
async def test_course(db_session: AsyncSession) -> Course:
    """Create a test course with knowledge areas."""
    course = Course(
        id=uuid4(),
        slug="test-course",
        name="Test Course",
        description="A test course",
        knowledge_areas=[
            {"id": "ka-1", "name": "Knowledge Area 1", "short_name": "KA1", "display_order": 1, "color": "#FF0000"},
            {"id": "ka-2", "name": "Knowledge Area 2", "short_name": "KA2", "display_order": 2, "color": "#00FF00"},
        ],
        default_diagnostic_count=12,
        mastery_threshold=0.8,
        gap_threshold=0.5,
        confidence_threshold=0.7,
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
    concepts = [
        Concept(
            id=uuid4(),
            course_id=test_course.id,
            name=f"Concept {i}",
            knowledge_area_id="ka-1" if i < 3 else "ka-2",
            difficulty_estimate=0.5,
        )
        for i in range(6)
    ]
    db_session.add_all(concepts)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
async def test_enrollment(
    db_session: AsyncSession,
    test_user: User,
    test_course: Course,
) -> Enrollment:
    """Create test enrollment."""
    enrollment = Enrollment(
        id=uuid4(),
        user_id=test_user.id,
        course_id=test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def test_beliefs(
    db_session: AsyncSession,
    test_user: User,
    test_concepts: list[Concept],
) -> list[BeliefState]:
    """Create test belief states with varied mastery levels."""
    beliefs = []

    # Mastered concept
    beliefs.append(BeliefState(
        id=uuid4(),
        user_id=test_user.id,
        concept_id=test_concepts[0].id,
        alpha=10.0,
        beta=2.0,  # mean=0.833
        response_count=5,
    ))

    # Gap concept
    beliefs.append(BeliefState(
        id=uuid4(),
        user_id=test_user.id,
        concept_id=test_concepts[1].id,
        alpha=2.0,
        beta=10.0,  # mean=0.167
        response_count=5,
    ))

    # Borderline concept
    beliefs.append(BeliefState(
        id=uuid4(),
        user_id=test_user.id,
        concept_id=test_concepts[2].id,
        alpha=6.0,
        beta=4.0,  # mean=0.6
        response_count=3,
    ))

    # Uncertain concepts
    for i in range(3, 6):
        beliefs.append(BeliefState(
            id=uuid4(),
            user_id=test_user.id,
            concept_id=test_concepts[i].id,
            alpha=1.0,
            beta=1.0,  # mean=0.5, low confidence
            response_count=0,
        ))

    db_session.add_all(beliefs)
    await db_session.commit()
    for b in beliefs:
        await db_session.refresh(b)
    return beliefs


# ============================================================================
# GET /diagnostic/results Tests
# ============================================================================

class TestGetDiagnosticResults:
    """Integration tests for GET /diagnostic/results endpoint."""

    @pytest.mark.asyncio
    async def test_returns_complete_results(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_enrollment: Enrollment,
        test_beliefs: list[BeliefState],
        test_course: Course,
    ):
        """Verify endpoint returns complete results structure."""
        response = await async_client.get(
            f"/v1/diagnostic/results?course_id={test_course.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify basic counts
        assert data["total_concepts"] == 6
        assert data["concepts_touched"] == 3  # Only ones with response_count > 0
        assert data["coverage_percentage"] == 0.5

        # Verify classification
        assert data["estimated_mastered"] == 1
        assert data["estimated_gaps"] == 1
        assert data["uncertain"] >= 1  # At least borderline counts

        # Verify confidence level
        assert data["confidence_level"] in ["initial", "developing", "established"]

        # Verify KA breakdown structure
        assert len(data["by_knowledge_area"]) == 2
        ka1 = next(ka for ka in data["by_knowledge_area"] if ka["ka_id"] == "ka-1")
        assert ka1["concepts"] == 3
        assert ka1["ka"] == "Knowledge Area 1"

        # Verify top gaps
        assert len(data["top_gaps"]) >= 1
        assert data["top_gaps"][0]["mastery_probability"] < 0.5

        # Verify recommendations
        assert "primary_focus" in data["recommendations"]
        assert "message" in data["recommendations"]
        assert data["recommendations"]["estimated_questions_to_coverage"] >= 0

    @pytest.mark.asyncio
    async def test_returns_404_without_enrollment(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """Verify endpoint returns 404 if user has no enrollment."""
        response = await async_client.get(
            f"/v1/diagnostic/results?course_id={test_course.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "NO_ENROLLMENT" in response.json()["detail"]["error"]["code"]

    @pytest.mark.asyncio
    async def test_returns_404_without_beliefs(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_enrollment: Enrollment,
        test_course: Course,
    ):
        """Verify endpoint returns 404 if user has no belief states."""
        response = await async_client.get(
            f"/v1/diagnostic/results?course_id={test_course.id}",
            headers=auth_headers,
        )

        assert response.status_code == 404
        assert "NO_DIAGNOSTIC" in response.json()["detail"]["error"]["code"]

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(
        self,
        async_client: AsyncClient,
        test_course: Course,
    ):
        """Verify endpoint returns 401 for unauthenticated request."""
        response = await async_client.get(
            f"/v1/diagnostic/results?course_id={test_course.id}",
        )

        assert response.status_code == 401


# ============================================================================
# POST /diagnostic/feedback Tests
# ============================================================================

class TestSubmitDiagnosticFeedback:
    """Integration tests for POST /diagnostic/feedback endpoint."""

    @pytest.mark.asyncio
    async def test_accepts_valid_feedback(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """Verify endpoint accepts valid feedback."""
        response = await async_client.post(
            f"/v1/diagnostic/feedback?course_id={test_course.id}",
            headers=auth_headers,
            json={"rating": 4, "comment": "The results feel accurate!"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "Thank you" in data["message"]

    @pytest.mark.asyncio
    async def test_accepts_feedback_without_comment(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """Verify endpoint accepts feedback without optional comment."""
        response = await async_client.post(
            f"/v1/diagnostic/feedback?course_id={test_course.id}",
            headers=auth_headers,
            json={"rating": 3},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    @pytest.mark.asyncio
    async def test_rejects_invalid_rating(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
    ):
        """Verify endpoint rejects invalid rating values."""
        # Rating too low
        response = await async_client.post(
            f"/v1/diagnostic/feedback?course_id={test_course.id}",
            headers=auth_headers,
            json={"rating": 0},
        )
        assert response.status_code == 422

        # Rating too high
        response = await async_client.post(
            f"/v1/diagnostic/feedback?course_id={test_course.id}",
            headers=auth_headers,
            json={"rating": 6},
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_returns_401_without_auth(
        self,
        async_client: AsyncClient,
        test_course: Course,
    ):
        """Verify endpoint returns 401 for unauthenticated request."""
        response = await async_client.post(
            f"/v1/diagnostic/feedback?course_id={test_course.id}",
            json={"rating": 4},
        )

        assert response.status_code == 401


# ============================================================================
# Full Flow Tests
# ============================================================================

class TestDiagnosticResultsFlow:
    """Integration tests for the complete diagnostic results flow."""

    @pytest.mark.asyncio
    async def test_complete_diagnostic_to_results_flow(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_enrollment: Enrollment,
        test_beliefs: list[BeliefState],
        test_course: Course,
    ):
        """Test complete flow from diagnostic completion to viewing results."""
        # Step 1: Get diagnostic results
        results_response = await async_client.get(
            f"/v1/diagnostic/results?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert results_response.status_code == 200
        results = results_response.json()

        # Verify results contain expected data
        assert results["total_concepts"] > 0
        assert results["recommendations"]["message"] is not None

        # Step 2: Submit feedback
        feedback_response = await async_client.post(
            f"/v1/diagnostic/feedback?course_id={test_course.id}",
            headers=auth_headers,
            json={
                "rating": 4,
                "comment": "The diagnostic accurately identified my weak areas.",
            },
        )
        assert feedback_response.status_code == 200
        assert feedback_response.json()["success"] is True

        # Step 3: Verify results can be fetched again (idempotent)
        second_results = await async_client.get(
            f"/v1/diagnostic/results?course_id={test_course.id}",
            headers=auth_headers,
        )
        assert second_results.status_code == 200
        # Results should be consistent
        assert second_results.json()["total_concepts"] == results["total_concepts"]
