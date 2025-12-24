"""
Integration tests for registration with onboarding data.
Story 3.4.1: Familiarity-Based Belief Prior Integration.

Tests the full registration flow with onboarding data and verifies
that belief states are initialized with correct alpha/beta values.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.belief_state import BeliefState
from src.models.course import Course
from src.models.concept import Concept
from src.models.user import User


@pytest.fixture
async def cbap_course(db_session: AsyncSession) -> Course:
    """Get or create the CBAP course for testing."""
    result = await db_session.execute(
        select(Course).where(Course.slug == "cbap")
    )
    course = result.scalar_one_or_none()
    if not course:
        course = Course(
            slug="cbap",
            name="CBAP Certification Prep",
            description="Test course",
            corpus_name="BABOK v3",
            knowledge_areas=[{"id": "ba-planning", "name": "BA Planning"}],
            is_active=True
        )
        db_session.add(course)
        await db_session.commit()
        await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concepts(db_session: AsyncSession, cbap_course: Course) -> list[Concept]:
    """Create test concepts for the CBAP course."""
    # Check if concepts already exist
    result = await db_session.execute(
        select(func.count(Concept.id)).where(Concept.course_id == cbap_course.id)
    )
    existing_count = result.scalar_one()
    if existing_count > 0:
        result = await db_session.execute(
            select(Concept).where(Concept.course_id == cbap_course.id)
        )
        return list(result.scalars().all())

    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=cbap_course.id,
            name=f"Test Concept {i}",
            knowledge_area_id="ba-planning",
            corpus_section_ref=f"test.{i}.1",
        )
        db_session.add(concept)
        concepts.append(concept)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.mark.asyncio
async def test_register_with_onboarding_data_sets_correct_priors(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cbap_course: Course,
    test_concepts: list[Concept]
):
    """Test that registration with onboarding_data sets correct belief priors."""
    # Register with onboarding data (familiarity=basics, prior=0.3)
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "onboarding_test_1@example.com",
            "password": "TestPass123",
            "onboarding_data": {
                "course": "cbap",
                "motivation": "certification",
                "familiarity": "basics",
                "initial_belief_prior": 0.3
            }
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert "user" in data
    assert "token" in data

    user_id = data["user"]["id"]

    # Verify belief states have correct alpha/beta
    result = await db_session.execute(
        select(BeliefState).where(BeliefState.user_id == user_id)
    )
    beliefs = list(result.scalars().all())

    assert len(beliefs) > 0, "Should have created belief states"

    for belief in beliefs:
        assert belief.alpha == pytest.approx(3.0), f"alpha should be 3.0, got {belief.alpha}"
        assert belief.beta == pytest.approx(7.0), f"beta should be 7.0, got {belief.beta}"


@pytest.mark.asyncio
async def test_register_with_expert_familiarity(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cbap_course: Course,
    test_concepts: list[Concept]
):
    """Test registration with expert familiarity (prior=0.7)."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "expert_test@example.com",
            "password": "TestPass123",
            "onboarding_data": {
                "course": "cbap",
                "motivation": "review",
                "familiarity": "expert",
                "initial_belief_prior": 0.7
            }
        }
    )

    assert response.status_code == 201
    user_id = response.json()["user"]["id"]

    # Verify beliefs have alpha=7, beta=3
    result = await db_session.execute(
        select(BeliefState).where(BeliefState.user_id == user_id)
    )
    beliefs = list(result.scalars().all())

    for belief in beliefs:
        assert belief.alpha == pytest.approx(7.0)
        assert belief.beta == pytest.approx(3.0)


@pytest.mark.asyncio
async def test_register_without_onboarding_uses_default(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cbap_course: Course,
    test_concepts: list[Concept]
):
    """Test registration without onboarding_data uses default Beta(1,1)."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "legacy_test@example.com",
            "password": "TestPass123"
            # No onboarding_data
        }
    )

    assert response.status_code == 201
    user_id = response.json()["user"]["id"]

    # Verify beliefs have default alpha=1, beta=1
    result = await db_session.execute(
        select(BeliefState).where(BeliefState.user_id == user_id)
    )
    beliefs = list(result.scalars().all())

    for belief in beliefs:
        assert belief.alpha == pytest.approx(1.0), f"Default alpha should be 1.0, got {belief.alpha}"
        assert belief.beta == pytest.approx(1.0), f"Default beta should be 1.0, got {belief.beta}"


@pytest.mark.asyncio
async def test_register_with_invalid_course_fallback(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cbap_course: Course,
    test_concepts: list[Concept]
):
    """Test registration with unknown course slug falls back to default course."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "unknown_course_test@example.com",
            "password": "TestPass123",
            "onboarding_data": {
                "course": "nonexistent-course",
                "motivation": "learning",
                "familiarity": "intermediate",
                "initial_belief_prior": 0.5
            }
        }
    )

    # Should succeed with fallback to default course
    assert response.status_code == 201
    user_id = response.json()["user"]["id"]

    # Verify beliefs were still created with the specified prior
    result = await db_session.execute(
        select(BeliefState).where(BeliefState.user_id == user_id)
    )
    beliefs = list(result.scalars().all())

    # If default course (cbap) has concepts, beliefs should be created
    if len(beliefs) > 0:
        for belief in beliefs:
            assert belief.alpha == pytest.approx(5.0)
            assert belief.beta == pytest.approx(5.0)


@pytest.mark.asyncio
async def test_register_with_new_familiarity(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cbap_course: Course,
    test_concepts: list[Concept]
):
    """Test registration with new familiarity (prior=0.1)."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "new_user_test@example.com",
            "password": "TestPass123",
            "onboarding_data": {
                "course": "cbap",
                "motivation": "learning",
                "familiarity": "new",
                "initial_belief_prior": 0.1
            }
        }
    )

    assert response.status_code == 201
    user_id = response.json()["user"]["id"]

    # Verify beliefs have alpha=1, beta=9
    result = await db_session.execute(
        select(BeliefState).where(BeliefState.user_id == user_id)
    )
    beliefs = list(result.scalars().all())

    for belief in beliefs:
        assert belief.alpha == pytest.approx(1.0)
        assert belief.beta == pytest.approx(9.0)


@pytest.mark.asyncio
async def test_register_with_invalid_familiarity_rejected(
    async_client: AsyncClient
):
    """Test registration with invalid familiarity value is rejected."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "invalid_familiarity@example.com",
            "password": "TestPass123",
            "onboarding_data": {
                "course": "cbap",
                "motivation": "learning",
                "familiarity": "advanced",  # Invalid: should be new/basics/intermediate/expert
                "initial_belief_prior": 0.5
            }
        }
    )

    # Should be rejected with 422 Validation Error
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_with_invalid_prior_rejected(
    async_client: AsyncClient
):
    """Test registration with invalid prior value (> 1.0) is rejected."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "invalid_prior@example.com",
            "password": "TestPass123",
            "onboarding_data": {
                "course": "cbap",
                "motivation": "learning",
                "familiarity": "basics",
                "initial_belief_prior": 1.5  # Invalid: must be <= 1.0
            }
        }
    )

    assert response.status_code == 422
    errors = response.json()["detail"]
    assert any("initial_belief_prior" in str(e) for e in errors)


@pytest.mark.asyncio
async def test_belief_states_have_correct_db_values(
    async_client: AsyncClient,
    db_session: AsyncSession,
    cbap_course: Course,
    test_concepts: list[Concept]
):
    """Verify belief_states table has correct alpha/beta values after registration."""
    response = await async_client.post(
        "/v1/auth/register",
        json={
            "email": "db_check_test@example.com",
            "password": "TestPass123",
            "onboarding_data": {
                "course": "cbap",
                "motivation": "certification",
                "familiarity": "intermediate",
                "initial_belief_prior": 0.5
            }
        }
    )

    assert response.status_code == 201
    user_id = response.json()["user"]["id"]

    # Query database directly to verify values
    result = await db_session.execute(
        select(BeliefState.alpha, BeliefState.beta)
        .where(BeliefState.user_id == user_id)
    )
    rows = result.all()

    assert len(rows) > 0, "Should have belief states in database"

    for alpha, beta in rows:
        assert alpha == pytest.approx(5.0), f"DB alpha should be 5.0, got {alpha}"
        assert beta == pytest.approx(5.0), f"DB beta should be 5.0, got {beta}"
        # Verify mean = alpha / (alpha + beta) = 0.5
        mean = alpha / (alpha + beta)
        assert mean == pytest.approx(0.5)
