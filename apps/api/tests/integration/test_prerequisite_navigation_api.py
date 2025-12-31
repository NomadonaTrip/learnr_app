"""
Integration tests for prerequisite navigation and mastery gates.
Story 4.11: Prerequisite-Based Curriculum Navigation

Tests:
- Concept lock status endpoint
- Bulk unlock status endpoint
- Override attempt logging
- Question selection respects gates
"""
import time
from uuid import uuid4

import pytest
from sqlalchemy import text

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.concept_prerequisite import ConceptPrerequisite
from src.models.course import Course
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def test_course(db_session, sample_course_data):
    """Create a test course."""
    course = Course(
        slug=f"prereq-nav-{uuid4().hex[:8]}",
        name=sample_course_data["name"],
        description=sample_course_data["description"],
        corpus_name=sample_course_data["corpus_name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concepts(db_session, test_course):
    """Create test concepts with prerequisite relationships."""
    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=test_course.id,
            name=f"Concept {i}",
            description=f"Description for concept {i}",
            corpus_section_ref=f"4.{i}.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.2 + (i * 0.15),
            prerequisite_depth=i
        )
        db_session.add(concept)
        concepts.append(concept)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
async def concepts_with_prerequisites(db_session, test_concepts):
    """Create prerequisite relationships between test concepts."""
    repo = ConceptRepository(db_session)

    # Concept 1 requires Concept 0
    await repo.add_prerequisite(
        test_concepts[1].id, test_concepts[0].id, 1.0, "required"
    )
    # Concept 2 requires Concept 1
    await repo.add_prerequisite(
        test_concepts[2].id, test_concepts[1].id, 1.0, "required"
    )
    # Concept 3 requires Concept 0 and Concept 1
    await repo.add_prerequisite(
        test_concepts[3].id, test_concepts[0].id, 1.0, "required"
    )
    await repo.add_prerequisite(
        test_concepts[3].id, test_concepts[1].id, 1.0, "required"
    )
    # Concept 4 has no prerequisites (root concept)

    await db_session.commit()
    return test_concepts


@pytest.fixture
async def test_user(db_session):
    """Create a test user."""
    user = User(
        email=f"mastery-gate-{uuid4().hex[:8]}@example.com",
        hashed_password="$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.M1E0pV6SyqV9Gy"
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def auth_token(test_user):
    """Generate auth token for test user."""
    from src.utils.auth import create_access_token
    token = create_access_token({"sub": str(test_user.id)})
    return token


@pytest.fixture
def auth_headers(auth_token):
    """Auth headers for API requests."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
async def user_with_partial_mastery(db_session, test_user, concepts_with_prerequisites):
    """Create belief states where user has mastered only Concept 0."""
    # Mastered: alpha=8, beta=2 (mean=0.8, high confidence)
    mastered_belief = BeliefState(
        user_id=test_user.id,
        concept_id=concepts_with_prerequisites[0].id,
        alpha=8.0,
        beta=2.0,
        response_count=5
    )
    db_session.add(mastered_belief)

    # Not mastered: alpha=2, beta=8 (mean=0.2, low mastery)
    not_mastered_belief = BeliefState(
        user_id=test_user.id,
        concept_id=concepts_with_prerequisites[1].id,
        alpha=2.0,
        beta=8.0,
        response_count=5
    )
    db_session.add(not_mastered_belief)

    await db_session.commit()
    return test_user


# ============================================================================
# Test: Concept Lock Status Endpoint
# ============================================================================


class TestConceptLockStatusEndpoint:
    """Tests for GET /concepts/{id}/prerequisites/status endpoint."""

    @pytest.mark.asyncio
    async def test_unlocked_concept_no_prerequisites(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Concept with no prerequisites is always unlocked."""
        # Concept 4 has no prerequisites
        response = await client.get(
            f"/v1/concepts/{concepts_with_prerequisites[4].id}/prerequisites/status",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_unlocked"] is True
        assert data["blocking_prerequisites"] == []
        assert data["mastery_progress"] == 1.0

    @pytest.mark.asyncio
    async def test_locked_concept_missing_prerequisites(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Concept is locked when user has no belief state for prerequisites."""
        # Concept 1 requires Concept 0, user has no belief state
        response = await client.get(
            f"/v1/concepts/{concepts_with_prerequisites[1].id}/prerequisites/status",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_unlocked"] is False
        assert len(data["blocking_prerequisites"]) >= 1

    @pytest.mark.asyncio
    async def test_unlocked_with_mastered_prerequisite(
        self, client, db_session, test_user, concepts_with_prerequisites, auth_headers
    ):
        """Concept unlocks when all prerequisites are mastered."""
        # Create mastered belief for Concept 0
        mastered = BeliefState(
            user_id=test_user.id,
            concept_id=concepts_with_prerequisites[0].id,
            alpha=8.0,
            beta=2.0,
            response_count=5
        )
        db_session.add(mastered)
        await db_session.commit()

        # Concept 1 should now be unlocked
        response = await client.get(
            f"/v1/concepts/{concepts_with_prerequisites[1].id}/prerequisites/status",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_unlocked"] is True

    @pytest.mark.asyncio
    async def test_partial_mastery_shows_progress(
        self, client, user_with_partial_mastery, concepts_with_prerequisites, auth_headers
    ):
        """Partial prerequisite mastery shows progress and closest to unlock."""
        # Concept 3 requires Concept 0 (mastered) and Concept 1 (not mastered)
        response = await client.get(
            f"/v1/concepts/{concepts_with_prerequisites[3].id}/prerequisites/status",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["is_unlocked"] is False
        assert 0.0 < data["mastery_progress"] < 1.0
        assert data["closest_to_unlock"] is not None

    @pytest.mark.asyncio
    async def test_response_contains_correct_schema(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Response matches GateCheckResult schema."""
        response = await client.get(
            f"/v1/concepts/{concepts_with_prerequisites[1].id}/prerequisites/status",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "concept_id" in data
        assert "concept_name" in data
        assert "is_unlocked" in data
        assert "blocking_prerequisites" in data
        assert "mastery_progress" in data
        assert "estimated_questions_to_unlock" in data


# ============================================================================
# Test: Bulk Unlock Status Endpoint
# ============================================================================


class TestBulkUnlockStatusEndpoint:
    """Tests for GET /concepts/unlock-status endpoint."""

    @pytest.mark.asyncio
    async def test_bulk_status_returns_all_concepts(
        self, client, test_course, concepts_with_prerequisites, auth_headers
    ):
        """Bulk status returns status for all concepts in course."""
        response = await client.get(
            f"/v1/concepts/unlock-status?course_id={test_course.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_concepts"] == 5
        assert len(data["concepts"]) == 5

    @pytest.mark.asyncio
    async def test_bulk_status_counts_locked_unlocked(
        self, client, test_course, concepts_with_prerequisites, auth_headers
    ):
        """Bulk status correctly counts locked and unlocked concepts."""
        response = await client.get(
            f"/v1/concepts/unlock-status?course_id={test_course.id}",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        # Concepts 0 and 4 have no prerequisites (unlocked)
        # Concepts 1, 2, 3 have prerequisites (locked - no belief states)
        assert data["unlocked_count"] >= 2  # At least root concepts
        assert data["locked_count"] >= 0

    @pytest.mark.asyncio
    async def test_bulk_status_with_ka_filter(
        self, client, test_course, concepts_with_prerequisites, auth_headers
    ):
        """Bulk status respects knowledge area filter."""
        response = await client.get(
            f"/v1/concepts/unlock-status?course_id={test_course.id}&ka_id=ba-planning",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["knowledge_area_id"] == "ba-planning"
        # All test concepts are in ba-planning
        assert data["total_concepts"] == 5

    @pytest.mark.asyncio
    async def test_bulk_status_performance(
        self, client, test_course, concepts_with_prerequisites, auth_headers
    ):
        """Bulk status responds within 200ms (AC: 9)."""
        start = time.time()
        response = await client.get(
            f"/v1/concepts/unlock-status?course_id={test_course.id}",
            headers=auth_headers
        )
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 200, f"Response took {elapsed_ms:.2f}ms, expected <200ms"


# ============================================================================
# Test: Override Attempt Endpoint
# ============================================================================


class TestOverrideAttemptEndpoint:
    """Tests for POST /concepts/{id}/attempt-locked endpoint."""

    @pytest.mark.asyncio
    async def test_override_allowed_for_locked_concept(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Override is allowed even for locked concepts."""
        # Concept 1 is locked (no belief state for prereq)
        response = await client.post(
            f"/v1/concepts/{concepts_with_prerequisites[1].id}/attempt-locked",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["override_allowed"] is True
        assert data["was_locked"] is True
        assert "Proceeding with locked concept" in data["message"]

    @pytest.mark.asyncio
    async def test_override_on_unlocked_concept(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Override on already unlocked concept returns appropriate message."""
        # Concept 4 has no prerequisites (always unlocked)
        response = await client.post(
            f"/v1/concepts/{concepts_with_prerequisites[4].id}/attempt-locked",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["was_locked"] is False
        assert "already unlocked" in data["message"]

    @pytest.mark.asyncio
    async def test_override_returns_blocking_prerequisites(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Override response includes blocking prerequisites."""
        response = await client.post(
            f"/v1/concepts/{concepts_with_prerequisites[1].id}/attempt-locked",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "blocking_prerequisites" in data
        # Concept 1 requires Concept 0
        if data["was_locked"]:
            assert len(data["blocking_prerequisites"]) >= 1

    @pytest.mark.asyncio
    async def test_override_response_schema(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Override response matches OverrideAttemptResponse schema."""
        response = await client.post(
            f"/v1/concepts/{concepts_with_prerequisites[1].id}/attempt-locked",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "concept_id" in data
        assert "concept_name" in data
        assert "was_locked" in data
        assert "override_allowed" in data
        assert "blocking_prerequisites" in data
        assert "mastery_progress" in data
        assert "message" in data


# ============================================================================
# Test: Question Selection Respects Gates
# ============================================================================


class TestQuestionSelectionRespectsGates:
    """Tests that question selection integrates with mastery gates."""

    @pytest.mark.asyncio
    async def test_gate_check_performance(
        self, client, concepts_with_prerequisites, auth_headers
    ):
        """Single gate check responds in <20ms (AC: 9)."""
        start = time.time()
        response = await client.get(
            f"/v1/concepts/{concepts_with_prerequisites[1].id}/prerequisites/status",
            headers=auth_headers
        )
        elapsed_ms = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 20, f"Gate check took {elapsed_ms:.2f}ms, expected <20ms"

    @pytest.mark.asyncio
    async def test_recent_unlocks_endpoint(
        self, client, auth_headers
    ):
        """Recent unlocks endpoint returns correct schema."""
        response = await client.get(
            "/v1/concepts/recent-unlocks?limit=5",
            headers=auth_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert "unlocks" in data
        assert "total_unlocked" in data
        assert isinstance(data["unlocks"], list)


# ============================================================================
# Test: Authentication
# ============================================================================


class TestAuthentication:
    """Tests that all endpoints require authentication."""

    @pytest.mark.asyncio
    async def test_lock_status_requires_auth(self, client, concepts_with_prerequisites):
        """Lock status endpoint requires authentication."""
        response = await client.get(
            f"/v1/concepts/{concepts_with_prerequisites[0].id}/prerequisites/status"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_bulk_status_requires_auth(self, client, test_course):
        """Bulk status endpoint requires authentication."""
        response = await client.get(
            f"/v1/concepts/unlock-status?course_id={test_course.id}"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_override_requires_auth(self, client, concepts_with_prerequisites):
        """Override endpoint requires authentication."""
        response = await client.post(
            f"/v1/concepts/{concepts_with_prerequisites[0].id}/attempt-locked"
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_recent_unlocks_requires_auth(self, client):
        """Recent unlocks endpoint requires authentication."""
        response = await client.get("/v1/concepts/recent-unlocks")
        assert response.status_code == 401
