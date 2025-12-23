"""
Integration tests for Coverage API endpoints (Story 4.5).
Tests coverage progress tracking endpoints with real database.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.user import User
from src.utils.auth import create_access_token, hash_password


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_course(db_session: AsyncSession) -> Course:
    """Create a test course with knowledge areas."""
    course = Course(
        slug="test-course",
        name="Test Course",
        description="A test course",
        knowledge_areas=[
            {"id": "ka-1", "name": "Knowledge Area 1", "short_name": "KA1", "display_order": 1},
            {"id": "ka-2", "name": "Knowledge Area 2", "short_name": "KA2", "display_order": 2},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_user_with_beliefs(db_session: AsyncSession, test_course: Course) -> tuple[User, list[Concept]]:
    """Create a test user with enrolled course, concepts, and belief states."""
    # Create user
    user = User(
        email="coverage_test@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Create enrollment
    enrollment = Enrollment(
        user_id=user.id,
        course_id=test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()

    # Create concepts across knowledge areas
    concepts = []
    for i in range(10):
        ka_id = "ka-1" if i < 6 else "ka-2"
        concept = Concept(
            name=f"Concept {i+1}",
            course_id=test_course.id,
            knowledge_area_id=ka_id,
            description=f"Description for concept {i+1}",
        )
        db_session.add(concept)
        concepts.append(concept)

    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)

    # Create belief states with various statuses
    # Mastered: alpha=9, beta=1 → mean=0.9, conf=0.83
    # Gap: alpha=1, beta=9 → mean=0.1, conf=0.83
    # Borderline: alpha=6, beta=4 → mean=0.6, conf=0.83
    # Uncertain: alpha=1, beta=1 → mean=0.5, conf=0.5
    belief_configs = [
        (9.0, 1.0),  # mastered
        (9.0, 1.0),  # mastered
        (9.0, 1.0),  # mastered
        (1.0, 9.0),  # gap
        (1.0, 9.0),  # gap
        (6.0, 4.0),  # borderline
        (1.0, 1.0),  # uncertain
        (1.0, 1.0),  # uncertain
        (1.0, 1.0),  # uncertain
        (1.0, 1.0),  # uncertain
    ]

    for i, (alpha, beta) in enumerate(belief_configs):
        belief = BeliefState(
            user_id=user.id,
            concept_id=concepts[i].id,
            alpha=alpha,
            beta=beta,
            response_count=int(alpha + beta - 2),  # Simulate some responses
        )
        db_session.add(belief)

    await db_session.commit()

    return user, concepts


@pytest.fixture
def auth_headers_for_coverage_user(test_user_with_beliefs):
    """Generate auth headers for the coverage test user."""
    user, _ = test_user_with_beliefs
    token = create_access_token(data={"sub": str(user.id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# GET /v1/coverage Tests
# ============================================================================


class TestGetCoverage:
    """Tests for GET /v1/coverage endpoint."""

    @pytest.mark.asyncio
    async def test_get_coverage_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_beliefs,
        test_course: Course,
        auth_headers_for_coverage_user,
    ):
        """Test successful coverage retrieval."""
        user, concepts = test_user_with_beliefs

        response = await client.get(
            f"/v1/coverage?course_id={test_course.id}",
            headers=auth_headers_for_coverage_user,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify structure
        assert "total_concepts" in data
        assert "mastered" in data
        assert "gaps" in data
        assert "borderline" in data
        assert "uncertain" in data
        assert "coverage_percentage" in data
        assert "confidence_percentage" in data
        assert "estimated_questions_remaining" in data
        assert "by_knowledge_area" in data

        # Verify counts (based on fixture: 3 mastered, 2 gaps, 1 borderline, 4 uncertain)
        assert data["total_concepts"] == 10
        assert data["mastered"] == 3
        assert data["gaps"] == 2
        assert data["borderline"] == 1
        assert data["uncertain"] == 4

        # Verify percentages
        assert data["coverage_percentage"] == 0.3  # 3/10
        assert data["confidence_percentage"] == 0.6  # (3+2+1)/10

    @pytest.mark.asyncio
    async def test_get_coverage_requires_auth(
        self,
        client: AsyncClient,
        test_course: Course,
    ):
        """Test coverage endpoint requires authentication."""
        response = await client.get(
            f"/v1/coverage?course_id={test_course.id}",
        )

        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_coverage_ka_breakdown(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_beliefs,
        test_course: Course,
        auth_headers_for_coverage_user,
    ):
        """Test coverage includes knowledge area breakdown."""
        response = await client.get(
            f"/v1/coverage?course_id={test_course.id}",
            headers=auth_headers_for_coverage_user,
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 2 KAs
        assert len(data["by_knowledge_area"]) == 2

        # Find KA-1 (first 6 concepts: 3 mastered, 2 gap, 1 borderline)
        ka1 = next((ka for ka in data["by_knowledge_area"] if ka["ka_id"] == "ka-1"), None)
        assert ka1 is not None
        assert ka1["total_concepts"] == 6
        assert ka1["mastered_count"] == 3
        assert ka1["gap_count"] == 2
        assert ka1["borderline_count"] == 1
        assert ka1["readiness_score"] == 0.5  # 3/6

        # Find KA-2 (last 4 concepts: all uncertain)
        ka2 = next((ka for ka in data["by_knowledge_area"] if ka["ka_id"] == "ka-2"), None)
        assert ka2 is not None
        assert ka2["total_concepts"] == 4
        assert ka2["uncertain_count"] == 4
        assert ka2["readiness_score"] == 0.0


# ============================================================================
# GET /v1/coverage/details Tests
# ============================================================================


class TestGetCoverageDetails:
    """Tests for GET /v1/coverage/details endpoint."""

    @pytest.mark.asyncio
    async def test_get_coverage_details_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_beliefs,
        test_course: Course,
        auth_headers_for_coverage_user,
    ):
        """Test detailed coverage retrieval includes concept lists."""
        response = await client.get(
            f"/v1/coverage/details?course_id={test_course.id}",
            headers=auth_headers_for_coverage_user,
        )

        assert response.status_code == 200
        data = response.json()

        # Should include concept lists
        assert "mastered_concepts" in data
        assert "gap_concepts" in data
        assert "borderline_concepts" in data
        assert "uncertain_concepts" in data

        # Verify counts match lists
        assert len(data["mastered_concepts"]) == data["mastered"]
        assert len(data["gap_concepts"]) == data["gaps"]
        assert len(data["borderline_concepts"]) == data["borderline"]
        assert len(data["uncertain_concepts"]) == data["uncertain"]

    @pytest.mark.asyncio
    async def test_concept_status_fields(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_beliefs,
        test_course: Course,
        auth_headers_for_coverage_user,
    ):
        """Test concept status objects have required fields."""
        response = await client.get(
            f"/v1/coverage/details?course_id={test_course.id}",
            headers=auth_headers_for_coverage_user,
        )

        assert response.status_code == 200
        data = response.json()

        # Check a mastered concept
        if data["mastered_concepts"]:
            concept = data["mastered_concepts"][0]
            assert "concept_id" in concept
            assert "concept_name" in concept
            assert "knowledge_area_id" in concept
            assert "status" in concept
            assert "probability" in concept
            assert "confidence" in concept
            assert concept["status"] == "mastered"


# ============================================================================
# GET /v1/coverage/gaps Tests
# ============================================================================


class TestGetGapConcepts:
    """Tests for GET /v1/coverage/gaps endpoint."""

    @pytest.mark.asyncio
    async def test_get_gaps_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_beliefs,
        test_course: Course,
        auth_headers_for_coverage_user,
    ):
        """Test gap concepts retrieval."""
        response = await client.get(
            f"/v1/coverage/gaps?course_id={test_course.id}",
            headers=auth_headers_for_coverage_user,
        )

        assert response.status_code == 200
        data = response.json()

        assert "total_gaps" in data
        assert "gaps" in data
        assert data["total_gaps"] == 2  # Based on fixture
        assert len(data["gaps"]) == 2

    @pytest.mark.asyncio
    async def test_gaps_sorted_by_probability(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_beliefs,
        test_course: Course,
        auth_headers_for_coverage_user,
    ):
        """Test gaps are sorted by probability ascending (worst first)."""
        response = await client.get(
            f"/v1/coverage/gaps?course_id={test_course.id}",
            headers=auth_headers_for_coverage_user,
        )

        assert response.status_code == 200
        data = response.json()

        if len(data["gaps"]) > 1:
            # Verify sorted ascending
            for i in range(len(data["gaps"]) - 1):
                assert data["gaps"][i]["probability"] <= data["gaps"][i + 1]["probability"]

    @pytest.mark.asyncio
    async def test_gaps_respects_limit(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_with_beliefs,
        test_course: Course,
        auth_headers_for_coverage_user,
    ):
        """Test gap limit parameter works."""
        response = await client.get(
            f"/v1/coverage/gaps?course_id={test_course.id}&limit=1",
            headers=auth_headers_for_coverage_user,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_gaps"] == 1
        assert len(data["gaps"]) == 1

    @pytest.mark.asyncio
    async def test_gaps_requires_auth(
        self,
        client: AsyncClient,
        test_course: Course,
    ):
        """Test gaps endpoint requires authentication."""
        response = await client.get(
            f"/v1/coverage/gaps?course_id={test_course.id}",
        )

        assert response.status_code == 401


# ============================================================================
# No Beliefs Edge Case
# ============================================================================


class TestNoBeliefsEdgeCase:
    """Test coverage endpoints when user has no beliefs."""

    @pytest.fixture
    async def test_user_no_beliefs(
        self, db_session: AsyncSession, test_course: Course
    ) -> User:
        """Create a user with enrollment but no beliefs."""
        user = User(
            email="no_beliefs@example.com",
            hashed_password=hash_password("testpass123"),
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)

        enrollment = Enrollment(
            user_id=user.id,
            course_id=test_course.id,
            status="active",
        )
        db_session.add(enrollment)
        await db_session.commit()

        return user

    @pytest.fixture
    def auth_headers_no_beliefs(self, test_user_no_beliefs):
        """Auth headers for no-beliefs user."""
        token = create_access_token(data={"sub": str(test_user_no_beliefs.id)})
        return {"Authorization": f"Bearer {token}"}

    @pytest.mark.asyncio
    async def test_coverage_empty_when_no_beliefs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_no_beliefs,
        test_course: Course,
        auth_headers_no_beliefs,
    ):
        """Test coverage returns zeros when user has no beliefs."""
        response = await client.get(
            f"/v1/coverage?course_id={test_course.id}",
            headers=auth_headers_no_beliefs,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_concepts"] == 0
        assert data["mastered"] == 0
        assert data["gaps"] == 0
        assert data["borderline"] == 0
        assert data["uncertain"] == 0
        assert data["coverage_percentage"] == 0.0
        assert data["confidence_percentage"] == 0.0

    @pytest.mark.asyncio
    async def test_gaps_empty_when_no_beliefs(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        test_user_no_beliefs,
        test_course: Course,
        auth_headers_no_beliefs,
    ):
        """Test gaps returns empty list when user has no beliefs."""
        response = await client.get(
            f"/v1/coverage/gaps?course_id={test_course.id}",
            headers=auth_headers_no_beliefs,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_gaps"] == 0
        assert data["gaps"] == []
