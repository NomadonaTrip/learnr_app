"""
Integration tests for Belief API endpoints.
Tests the /v1/beliefs/* endpoints.
"""
import asyncio
from unittest.mock import patch, AsyncMock
from uuid import uuid4

import pytest

from src.exceptions import BeliefInitializationError
from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.user import User
from src.utils.auth import create_access_token, hash_password


@pytest.fixture
async def test_course_api(db_session, sample_course_data):
    """Create a test course for API tests."""
    course = Course(
        slug="belief-api-test",
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
async def test_user_api(db_session):
    """Create a test user for API tests."""
    user = User(
        email="belief_api_test@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_concepts_api(db_session, test_course_api):
    """Create test concepts for API tests."""
    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=test_course_api.id,
            name=f"API Test Concept {i}",
            knowledge_area_id="ba-planning",
            corpus_section_ref=f"3.{i}.1",
        )
        db_session.add(concept)
        concepts.append(concept)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
def api_auth_headers(test_user_api):
    """Generate authentication headers for API tests."""
    token = create_access_token(data={"sub": str(test_user_api.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_get_belief_stats_not_initialized(
    client, test_user_api, test_course_api, test_concepts_api, api_auth_headers
):
    """Test GET /v1/beliefs/stats when not initialized."""
    response = await client.get(
        f"/v1/beliefs/stats?course_id={test_course_api.id}",
        headers=api_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["initialized"] is False
    assert data["total_concepts"] == 5
    assert data["belief_count"] == 0
    assert data["coverage_percentage"] == 0.0
    assert data["created_at"] is None


@pytest.mark.asyncio
async def test_get_belief_stats_requires_auth(client, test_course_api):
    """Test GET /v1/beliefs/stats requires authentication."""
    response = await client.get(
        f"/v1/beliefs/stats?course_id={test_course_api.id}"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_belief_stats_requires_course_id(client, api_auth_headers):
    """Test GET /v1/beliefs/stats requires course_id parameter."""
    response = await client.get(
        "/v1/beliefs/stats",
        headers=api_auth_headers
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_initialize_beliefs_endpoint(
    client, test_user_api, test_course_api, test_concepts_api, api_auth_headers
):
    """Test POST /v1/beliefs/initialize."""
    response = await client.post(
        f"/v1/beliefs/initialize?course_id={test_course_api.id}",
        headers=api_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["already_initialized"] is False
    assert data["belief_count"] == 5
    assert data["duration_ms"] >= 0
    assert "Initialized 5 belief states" in data["message"]


@pytest.mark.asyncio
async def test_initialize_beliefs_idempotent(
    client, test_user_api, test_course_api, test_concepts_api, api_auth_headers
):
    """Test that POST /v1/beliefs/initialize is idempotent."""
    # First call
    response1 = await client.post(
        f"/v1/beliefs/initialize?course_id={test_course_api.id}",
        headers=api_auth_headers
    )
    assert response1.status_code == 200
    data1 = response1.json()
    assert data1["already_initialized"] is False
    assert data1["belief_count"] == 5

    # Second call (should be idempotent)
    response2 = await client.post(
        f"/v1/beliefs/initialize?course_id={test_course_api.id}",
        headers=api_auth_headers
    )
    assert response2.status_code == 200
    data2 = response2.json()
    assert data2["already_initialized"] is True
    assert data2["belief_count"] == 5  # Same count, not doubled


@pytest.mark.asyncio
async def test_initialize_beliefs_requires_auth(client, test_course_api):
    """Test POST /v1/beliefs/initialize requires authentication."""
    response = await client.post(
        f"/v1/beliefs/initialize?course_id={test_course_api.id}"
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_belief_summary(
    client, db_session, test_user_api, test_course_api, test_concepts_api, api_auth_headers
):
    """Test GET /v1/beliefs/summary."""
    # First initialize some beliefs with different statuses
    # Mastered
    db_session.add(BeliefState(
        user_id=test_user_api.id,
        concept_id=test_concepts_api[0].id,
        alpha=20.0,
        beta=2.0
    ))
    # Gap
    db_session.add(BeliefState(
        user_id=test_user_api.id,
        concept_id=test_concepts_api[1].id,
        alpha=2.0,
        beta=20.0
    ))
    # Uncertain
    db_session.add(BeliefState(
        user_id=test_user_api.id,
        concept_id=test_concepts_api[2].id,
        alpha=1.0,
        beta=1.0
    ))
    await db_session.commit()

    response = await client.get(
        "/v1/beliefs/summary",
        headers=api_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 3
    assert data["mastered"] == 1
    assert data["gap"] == 1
    assert data["uncertain"] == 1
    assert "average_mean" in data


@pytest.mark.asyncio
async def test_get_belief_summary_empty(
    client, test_user_api, api_auth_headers
):
    """Test GET /v1/beliefs/summary when no beliefs exist."""
    response = await client.get(
        "/v1/beliefs/summary",
        headers=api_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total"] == 0
    assert data["average_mean"] == 0.0


@pytest.mark.asyncio
async def test_get_belief_stats_after_initialization(
    client, test_user_api, test_course_api, test_concepts_api, api_auth_headers
):
    """Test GET /v1/beliefs/stats after initialization."""
    # Initialize first
    init_response = await client.post(
        f"/v1/beliefs/initialize?course_id={test_course_api.id}",
        headers=api_auth_headers
    )
    assert init_response.status_code == 200

    # Check stats
    response = await client.get(
        f"/v1/beliefs/stats?course_id={test_course_api.id}",
        headers=api_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["initialized"] is True
    assert data["total_concepts"] == 5
    assert data["belief_count"] == 5
    assert data["coverage_percentage"] == 100.0
    assert data["created_at"] is not None


@pytest.mark.asyncio
async def test_initialize_empty_course(
    client, db_session, test_user_api, api_auth_headers, sample_course_data
):
    """Test initializing beliefs for a course with no concepts."""
    # Create empty course
    empty_course = Course(
        slug="empty-api-course",
        name="Empty Course",
        description="No concepts",
        corpus_name="Empty",
        knowledge_areas=[],
        is_active=True
    )
    db_session.add(empty_course)
    await db_session.commit()
    await db_session.refresh(empty_course)

    response = await client.post(
        f"/v1/beliefs/initialize?course_id={empty_course.id}",
        headers=api_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    assert data["success"] is True
    assert data["belief_count"] == 0
    assert "No concepts found" in data["message"]


@pytest.mark.asyncio
async def test_concurrent_initialization_race_condition(
    client, db_session, test_course_api, test_concepts_api, sample_course_data
):
    """
    Test that concurrent initialization requests are handled correctly.

    Verifies that race conditions don't cause:
    - Duplicate beliefs (ON CONFLICT DO NOTHING handles this)
    - Incorrect counts
    - Errors from concurrent access

    This tests the idempotency under concurrent load per Story 3.4 Task 13.
    """
    # Create a dedicated user for this test
    user = User(
        email="concurrent_test@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    token = create_access_token(data={"sub": str(user.id)})
    headers = {"Authorization": f"Bearer {token}"}

    # Launch 5 concurrent initialization requests
    async def init_request():
        return await client.post(
            f"/v1/beliefs/initialize?course_id={test_course_api.id}",
            headers=headers
        )

    # Execute all requests concurrently
    responses = await asyncio.gather(*[init_request() for _ in range(5)])

    # All requests should succeed
    for response in responses:
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        # Either created or already_initialized
        assert data["belief_count"] == 5

    # Exactly one should have already_initialized=False (the first to complete)
    # The rest should have already_initialized=True
    not_initialized_count = sum(
        1 for r in responses if not r.json()["already_initialized"]
    )
    already_initialized_count = sum(
        1 for r in responses if r.json()["already_initialized"]
    )

    # At least one created, rest found existing
    assert not_initialized_count >= 1
    assert not_initialized_count + already_initialized_count == 5

    # Verify final state: exactly 5 beliefs exist (no duplicates)
    stats_response = await client.get(
        f"/v1/beliefs/stats?course_id={test_course_api.id}",
        headers=headers
    )
    assert stats_response.status_code == 200
    stats = stats_response.json()
    assert stats["belief_count"] == 5
    assert stats["coverage_percentage"] == 100.0


@pytest.mark.asyncio
async def test_initialize_beliefs_error_handling(
    client, test_user_api, test_course_api, api_auth_headers
):
    """Test that BeliefInitializationError returns proper 500 response."""
    # Patch the service to raise BeliefInitializationError
    with patch(
        'src.routes.beliefs.BeliefInitializationService.initialize_beliefs_for_user',
        new_callable=AsyncMock
    ) as mock_init:
        mock_init.side_effect = BeliefInitializationError("Database connection failed")

        response = await client.post(
            f"/v1/beliefs/initialize?course_id={test_course_api.id}",
            headers=api_auth_headers
        )

    assert response.status_code == 500
    data = response.json()
    assert data["detail"]["error"]["code"] == "BELIEF_INITIALIZATION_FAILED"
    assert "Database connection failed" in data["detail"]["error"]["message"]


@pytest.mark.asyncio
async def test_belief_state_repr(db_session, test_user_api, test_concepts_api):
    """Test BeliefState __repr__ method."""
    belief = BeliefState(
        user_id=test_user_api.id,
        concept_id=test_concepts_api[0].id,
        alpha=2.5,
        beta=1.5
    )
    db_session.add(belief)
    await db_session.commit()
    await db_session.refresh(belief)

    repr_str = repr(belief)

    assert "BeliefState" in repr_str
    assert str(belief.user_id) in repr_str
    assert str(belief.concept_id) in repr_str
    assert "alpha=2.5" in repr_str
    assert "beta=1.5" in repr_str


@pytest.mark.asyncio
async def test_get_belief_summary_returns_user_id(
    client, db_session, test_user_api, test_concepts_api, api_auth_headers
):
    """Test GET /v1/beliefs/summary includes user_id in response."""
    # Add a belief to ensure we get non-empty response
    db_session.add(BeliefState(
        user_id=test_user_api.id,
        concept_id=test_concepts_api[0].id,
        alpha=1.0,
        beta=1.0
    ))
    await db_session.commit()

    response = await client.get(
        "/v1/beliefs/summary",
        headers=api_auth_headers
    )

    assert response.status_code == 200
    data = response.json()

    # Verify user_id is in response (covers line 129 return statement)
    assert "user_id" in data
    assert data["user_id"] == str(test_user_api.id)
    assert data["total"] == 1
