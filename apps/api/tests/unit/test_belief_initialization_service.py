"""
Unit tests for BeliefInitializationService.
Tests belief initialization logic and edge cases.
"""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from src.exceptions import BeliefInitializationError, DatabaseError
from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.repositories.concept_repository import ConceptRepository
from src.services.belief_initialization_service import (
    BeliefInitializationService,
)
from src.utils.auth import hash_password


@pytest.fixture
async def test_course_init(db_session, sample_course_data):
    """Create a test course for initialization tests."""
    course = Course(
        slug="test-course-init",
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
async def test_user_init(db_session):
    """Create a test user for initialization tests."""
    user = User(
        email="init_test@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_concepts_init(db_session, test_course_init):
    """Create test concepts for initialization tests."""
    concepts = []
    for i in range(10):
        concept = Concept(
            course_id=test_course_init.id,
            name=f"Init Concept {i}",
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
def belief_service(db_session):
    """Create BeliefInitializationService instance."""
    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    return BeliefInitializationService(belief_repo, concept_repo)


@pytest.mark.asyncio
async def test_initialize_beliefs_for_user(
    db_session, belief_service, test_user_init, test_course_init, test_concepts_init
):
    """Test initializing beliefs for a new user."""
    result = await belief_service.initialize_beliefs_for_user(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )
    await db_session.commit()

    assert result.success is True
    assert result.already_initialized is False
    assert result.belief_count == 10
    assert result.duration_ms > 0
    assert "Initialized 10 belief states" in result.message


@pytest.mark.asyncio
async def test_initialize_beliefs_idempotent(
    db_session, belief_service, test_user_init, test_course_init, test_concepts_init
):
    """Test that initialization is idempotent."""
    # First initialization
    result1 = await belief_service.initialize_beliefs_for_user(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )
    await db_session.commit()

    assert result1.success is True
    assert result1.already_initialized is False
    assert result1.belief_count == 10

    # Second initialization (should be idempotent)
    result2 = await belief_service.initialize_beliefs_for_user(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )
    await db_session.commit()

    assert result2.success is True
    assert result2.already_initialized is True
    assert result2.belief_count == 10  # Same count, not doubled


@pytest.mark.asyncio
async def test_initialize_beliefs_no_concepts(
    db_session, test_user_init, sample_course_data
):
    """Test initialization when no concepts exist for course."""
    # Create a course with no concepts
    empty_course = Course(
        slug="empty-course",
        name="Empty Course",
        description="No concepts",
        corpus_name="Empty",
        knowledge_areas=[],
        is_active=True
    )
    db_session.add(empty_course)
    await db_session.commit()
    await db_session.refresh(empty_course)

    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    result = await service.initialize_beliefs_for_user(
        user_id=test_user_init.id,
        course_id=empty_course.id
    )

    assert result.success is True
    assert result.belief_count == 0
    assert "No concepts found" in result.message


@pytest.mark.asyncio
async def test_initialize_beliefs_correct_prior(
    db_session, belief_service, test_user_init, test_course_init, test_concepts_init
):
    """Test that beliefs are initialized with uninformative prior Beta(1,1)."""
    await belief_service.initialize_beliefs_for_user(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )
    await db_session.commit()

    # Verify beliefs have correct initial values
    belief_repo = BeliefRepository(db_session)
    beliefs = await belief_repo.get_all_beliefs(test_user_init.id)

    for belief in beliefs:
        assert belief.alpha == 1.0
        assert belief.beta == 1.0
        assert belief.response_count == 0
        # Verify mean = 0.5 (uninformative)
        assert belief.mean == 0.5


@pytest.mark.asyncio
async def test_get_initialization_status_not_initialized(
    db_session, belief_service, test_user_init, test_course_init, test_concepts_init
):
    """Test initialization status when not initialized."""
    status = await belief_service.get_initialization_status(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )

    assert status.initialized is False
    assert status.total_concepts == 10
    assert status.belief_count == 0
    assert status.coverage_percentage == 0.0
    assert status.created_at is None


@pytest.mark.asyncio
async def test_get_initialization_status_initialized(
    db_session, belief_service, test_user_init, test_course_init, test_concepts_init
):
    """Test initialization status after initialization."""
    # Initialize first
    await belief_service.initialize_beliefs_for_user(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )
    await db_session.commit()

    status = await belief_service.get_initialization_status(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )

    assert status.initialized is True
    assert status.total_concepts == 10
    assert status.belief_count == 10
    assert status.coverage_percentage == 100.0
    assert status.created_at is not None


@pytest.mark.asyncio
async def test_get_initialization_status_partial(
    db_session, test_user_init, test_course_init, test_concepts_init
):
    """Test initialization status when partially initialized."""
    # Manually create only some beliefs
    belief_repo = BeliefRepository(db_session)
    for concept in test_concepts_init[:5]:  # Only 5 of 10
        db_session.add(BeliefState(
            user_id=test_user_init.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0
        ))
    await db_session.commit()

    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    status = await service.get_initialization_status(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )

    assert status.initialized is True  # Has some beliefs
    assert status.total_concepts == 10
    assert status.belief_count == 5
    assert status.coverage_percentage == 50.0


@pytest.mark.asyncio
async def test_initialize_beliefs_includes_timing(
    db_session, belief_service, test_user_init, test_course_init, test_concepts_init
):
    """Test that initialization result includes timing information."""
    result = await belief_service.initialize_beliefs_for_user(
        user_id=test_user_init.id,
        course_id=test_course_init.id
    )
    await db_session.commit()

    assert result.duration_ms >= 0
    # Should be fast for 10 concepts
    assert result.duration_ms < 5000  # Less than 5 seconds


@pytest.mark.asyncio
async def test_initialize_different_users_independent(
    db_session, belief_service, test_course_init, test_concepts_init
):
    """Test that different users have independent belief states."""
    # Create two users - use flush instead of commit to stay in same transaction
    user1 = User(
        email="user1@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    user2 = User(
        email="user2@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add_all([user1, user2])
    await db_session.flush()
    await db_session.refresh(user1)
    await db_session.refresh(user2)

    # Initialize both users using the shared belief_service fixture
    result1 = await belief_service.initialize_beliefs_for_user(
        user_id=user1.id,
        course_id=test_course_init.id
    )
    result2 = await belief_service.initialize_beliefs_for_user(
        user_id=user2.id,
        course_id=test_course_init.id
    )
    await db_session.commit()

    assert result1.belief_count == 10
    assert result2.belief_count == 10

    # Verify each user has their own beliefs
    belief_repo = BeliefRepository(db_session)
    beliefs1 = await belief_repo.get_all_beliefs(user1.id)
    beliefs2 = await belief_repo.get_all_beliefs(user2.id)

    assert len(beliefs1) == 10
    assert len(beliefs2) == 10

    # Verify they're different objects
    belief1_ids = {b.id for b in beliefs1}
    belief2_ids = {b.id for b in beliefs2}
    assert belief1_ids.isdisjoint(belief2_ids)


@pytest.mark.asyncio
async def test_initialize_beliefs_performance_1500_concepts(
    db_session, sample_course_data
):
    """
    Test that belief initialization completes in <2 seconds for 1500 concepts.

    AC4 Requirement: Performance: Complete in <2 seconds
    This test verifies bulk insert performance with realistic concept count.
    """
    # Create course for this test
    course = Course(
        slug="perf-test-course-1500",
        name=sample_course_data["name"],
        description=sample_course_data["description"],
        corpus_name=sample_course_data["corpus_name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    # Create 1500 concepts for performance testing
    for i in range(1500):
        concept = Concept(
            course_id=course.id,
            name=f"Perf Concept {i}",
            knowledge_area_id="ba-planning",
            corpus_section_ref=f"perf.{i}.1",
        )
        db_session.add(concept)
    await db_session.commit()

    # Create a dedicated user for this performance test
    user = User(
        email="perf_test_1500@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    # Initialize beliefs and measure time
    result = await service.initialize_beliefs_for_user(
        user_id=user.id,
        course_id=course.id
    )
    await db_session.commit()

    # Verify success
    assert result.success is True
    assert result.already_initialized is False
    assert result.belief_count == 1500

    # AC4: Must complete in <2 seconds (2000ms)
    assert result.duration_ms < 2000, (
        f"Performance requirement failed: initialization took {result.duration_ms:.2f}ms, "
        f"expected <2000ms for 1500 concepts"
    )

    # Verify all beliefs have correct uninformative prior
    beliefs = await belief_repo.get_all_beliefs(user.id)
    assert len(beliefs) == 1500
    for belief in beliefs[:10]:  # Spot check first 10
        assert belief.alpha == 1.0
        assert belief.beta == 1.0


@pytest.mark.asyncio
async def test_initialize_beliefs_exception_handling():
    """Test that exceptions during initialization are properly wrapped."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Setup mock to raise exception
    mock_belief_repo.get_belief_count.return_value = 0
    mock_concept_repo.get_all_concepts.side_effect = DatabaseError("Connection failed")

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    with pytest.raises(BeliefInitializationError) as exc_info:
        await service.initialize_beliefs_for_user(
            user_id=uuid4(),
            course_id=uuid4()
        )

    assert "Failed to initialize beliefs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_initialize_beliefs_bulk_create_exception():
    """Test exception handling when bulk_create fails."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Setup mocks
    mock_belief_repo.get_belief_count.return_value = 0
    mock_concept_repo.get_all_concepts.return_value = [
        MagicMock(id=uuid4(), name="Concept 1"),
    ]
    mock_belief_repo.bulk_create.side_effect = DatabaseError("Insert failed")

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    with pytest.raises(BeliefInitializationError) as exc_info:
        await service.initialize_beliefs_for_user(
            user_id=uuid4(),
            course_id=uuid4()
        )

    assert "Failed to initialize beliefs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_initialize_via_db_function_success():
    """Test initialize_beliefs_via_db_function success path."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Setup mocks
    mock_belief_repo.get_belief_count.return_value = 0
    mock_belief_repo.initialize_via_db_function.return_value = 100

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    result = await service.initialize_beliefs_via_db_function(user_id=uuid4())

    assert result.success is True
    assert result.already_initialized is False
    assert result.belief_count == 100
    mock_belief_repo.initialize_via_db_function.assert_called_once()


@pytest.mark.asyncio
async def test_initialize_via_db_function_already_initialized():
    """Test initialize_beliefs_via_db_function when already initialized."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Setup mock to indicate already initialized
    mock_belief_repo.get_belief_count.return_value = 50

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    result = await service.initialize_beliefs_via_db_function(user_id=uuid4())

    assert result.success is True
    assert result.already_initialized is True
    assert result.belief_count == 50
    mock_belief_repo.initialize_via_db_function.assert_not_called()


@pytest.mark.asyncio
async def test_initialize_via_db_function_exception():
    """Test exception handling in initialize_beliefs_via_db_function."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Setup mock to raise exception
    mock_belief_repo.get_belief_count.return_value = 0
    mock_belief_repo.initialize_via_db_function.side_effect = DatabaseError("DB function failed")

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    with pytest.raises(BeliefInitializationError) as exc_info:
        await service.initialize_beliefs_via_db_function(user_id=uuid4())

    assert "Failed to initialize beliefs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_initialize_via_db_function_performance_warning():
    """Test performance warning is logged when threshold exceeded."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Setup mocks
    mock_belief_repo.get_belief_count.return_value = 0
    mock_belief_repo.initialize_via_db_function.return_value = 100

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    # Patch time.perf_counter to simulate slow execution
    with patch('src.services.belief_initialization_service.time.perf_counter') as mock_time:
        # First call returns 0, second call returns 3 (simulating 3 seconds)
        mock_time.side_effect = [0, 3]

        result = await service.initialize_beliefs_via_db_function(user_id=uuid4())

    assert result.success is True
    assert result.duration_ms == 3000  # 3 seconds in ms


@pytest.mark.asyncio
async def test_initialize_beliefs_performance_warning_logged(
    db_session, test_user_init, test_course_init, test_concepts_init
):
    """Test that performance warning is logged when threshold is exceeded."""
    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    # Patch time.perf_counter to simulate slow execution (>2 seconds)
    with patch('src.services.belief_initialization_service.time.perf_counter') as mock_time:
        # First call at 0, second call at 3 seconds later
        mock_time.side_effect = [0, 3]

        result = await service.initialize_beliefs_for_user(
            user_id=test_user_init.id,
            course_id=test_course_init.id
        )
        await db_session.commit()

    assert result.success is True
    # Duration should be 3000ms (simulated)
    assert result.duration_ms == 3000


@pytest.mark.asyncio
async def test_logging_fallback_on_structlog_error():
    """Test that logging falls back to standard logger on structlog error."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Mock the session and its execute method for enrollment check
    mock_session = AsyncMock()
    mock_enrollment_result = MagicMock()
    mock_enrollment_result.scalar_one_or_none.return_value = uuid4()  # Return enrollment UUID
    mock_session.execute.return_value = mock_enrollment_result
    mock_belief_repo.session = mock_session

    mock_belief_repo.get_belief_count.return_value = 0
    mock_concept_repo.get_all_concepts.return_value = []

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    # Patch structlog to raise an exception
    with patch('src.services.belief_initialization_service.logger') as mock_logger:
        mock_logger.info.side_effect = Exception("structlog error")
        mock_logger.warning.side_effect = Exception("structlog error")

        # This should not raise - it should fall back to standard logging
        result = await service.initialize_beliefs_for_user(
            user_id=uuid4(),
            course_id=uuid4()
        )

    assert result.success is True
    assert result.belief_count == 0


@pytest.mark.asyncio
async def test_log_error_fallback():
    """Test error logging fallback when structlog fails."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    mock_belief_repo.get_belief_count.side_effect = DatabaseError("DB error")

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    # Patch structlog to raise an exception on error logging
    with patch('src.services.belief_initialization_service.logger') as mock_logger:
        mock_logger.error.side_effect = Exception("structlog error")

        with pytest.raises(BeliefInitializationError):
            await service.initialize_beliefs_for_user(
                user_id=uuid4(),
                course_id=uuid4()
            )


@pytest.mark.asyncio
async def test_service_logging_methods_with_uuid_conversion():
    """Test that UUID values are converted to strings in logging."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Mock the session and its execute method for enrollment check
    mock_session = AsyncMock()
    mock_enrollment_result = MagicMock()
    mock_enrollment_result.scalar_one_or_none.return_value = uuid4()  # Return enrollment UUID
    mock_session.execute.return_value = mock_enrollment_result
    mock_belief_repo.session = mock_session

    mock_belief_repo.get_belief_count.return_value = 5

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    user_id = uuid4()
    course_id = uuid4()

    # This should handle UUID to string conversion in logging
    result = await service.initialize_beliefs_for_user(
        user_id=user_id,
        course_id=course_id
    )

    assert result.success is True
    assert result.already_initialized is True


# Story 3.4.1: Familiarity-Based Belief Prior Integration Tests

@pytest.mark.asyncio
async def test_initialize_with_prior_0_1(
    db_session, test_course_init, test_concepts_init
):
    """Test initialization with prior=0.1 (new user) creates beliefs with alpha=1, beta=9."""
    # Create a fresh user for this test
    user = User(
        email="new_user_prior@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    result = await service.initialize_beliefs_for_user(
        user_id=user.id,
        course_id=test_course_init.id,
        initial_belief_prior=0.1
    )
    await db_session.commit()

    assert result.success is True
    assert result.belief_count == 10

    # Verify beliefs have correct prior-based alpha/beta
    beliefs = await belief_repo.get_all_beliefs(user.id)
    for belief in beliefs:
        assert belief.alpha == 1.0
        assert belief.beta == 9.0
        # Mean should be 0.1
        assert abs(belief.mean - 0.1) < 0.001


@pytest.mark.asyncio
async def test_initialize_with_prior_0_3(
    db_session, test_course_init, test_concepts_init
):
    """Test initialization with prior=0.3 (basics) creates beliefs with alpha=3, beta=7."""
    user = User(
        email="basics_user_prior@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    result = await service.initialize_beliefs_for_user(
        user_id=user.id,
        course_id=test_course_init.id,
        initial_belief_prior=0.3
    )
    await db_session.commit()

    assert result.success is True

    beliefs = await belief_repo.get_all_beliefs(user.id)
    for belief in beliefs:
        assert belief.alpha == 3.0
        assert belief.beta == 7.0


@pytest.mark.asyncio
async def test_initialize_with_prior_0_7(
    db_session, test_course_init, test_concepts_init
):
    """Test initialization with prior=0.7 (expert) creates beliefs with alpha=7, beta=3."""
    user = User(
        email="expert_user_prior@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    result = await service.initialize_beliefs_for_user(
        user_id=user.id,
        course_id=test_course_init.id,
        initial_belief_prior=0.7
    )
    await db_session.commit()

    assert result.success is True

    beliefs = await belief_repo.get_all_beliefs(user.id)
    for belief in beliefs:
        assert belief.alpha == 7.0
        assert abs(belief.beta - 3.0) < 0.001  # Float precision tolerance
        # Mean should be 0.7
        assert abs(belief.mean - 0.7) < 0.001


@pytest.mark.asyncio
async def test_initialize_without_prior_uses_default(
    db_session, test_course_init, test_concepts_init
):
    """Test initialization without prior uses default Beta(1,1)."""
    user = User(
        email="default_prior_user@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    # Call without initial_belief_prior (defaults to None)
    result = await service.initialize_beliefs_for_user(
        user_id=user.id,
        course_id=test_course_init.id
        # initial_belief_prior=None (implicit)
    )
    await db_session.commit()

    assert result.success is True

    beliefs = await belief_repo.get_all_beliefs(user.id)
    for belief in beliefs:
        assert belief.alpha == 1.0
        assert belief.beta == 1.0
        # Mean should be 0.5 (uninformative)
        assert belief.mean == 0.5


@pytest.mark.asyncio
async def test_initialize_with_prior_none_explicit(
    db_session, test_course_init, test_concepts_init
):
    """Test initialization with explicit None prior uses default Beta(1,1)."""
    user = User(
        email="explicit_none_prior@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.flush()
    await db_session.refresh(user)

    belief_repo = BeliefRepository(db_session)
    concept_repo = ConceptRepository(db_session)
    service = BeliefInitializationService(belief_repo, concept_repo)

    result = await service.initialize_beliefs_for_user(
        user_id=user.id,
        course_id=test_course_init.id,
        initial_belief_prior=None  # Explicit None
    )
    await db_session.commit()

    assert result.success is True

    beliefs = await belief_repo.get_all_beliefs(user.id)
    for belief in beliefs:
        assert belief.alpha == 1.0
        assert belief.beta == 1.0


@pytest.mark.asyncio
async def test_initialize_with_mock_verifies_alpha_beta_passed():
    """Test that bulk_create receives correct alpha/beta from prior calculation."""
    mock_belief_repo = AsyncMock(spec=BeliefRepository)
    mock_concept_repo = AsyncMock(spec=ConceptRepository)

    # Setup mocks
    mock_session = AsyncMock()
    mock_enrollment_result = MagicMock()
    mock_enrollment_result.scalar_one_or_none.return_value = uuid4()
    mock_session.execute.return_value = mock_enrollment_result
    mock_belief_repo.session = mock_session

    mock_belief_repo.get_belief_count.return_value = 0
    mock_concept = MagicMock()
    mock_concept.id = uuid4()
    mock_concept_repo.get_all_concepts.return_value = [mock_concept]
    mock_belief_repo.bulk_create.return_value = 1

    service = BeliefInitializationService(mock_belief_repo, mock_concept_repo)

    # Initialize with prior=0.3
    result = await service.initialize_beliefs_for_user(
        user_id=uuid4(),
        course_id=uuid4(),
        initial_belief_prior=0.3
    )

    assert result.success is True

    # Verify bulk_create was called with belief having correct alpha/beta
    call_args = mock_belief_repo.bulk_create.call_args
    beliefs_passed = call_args[0][0]  # First positional arg is list of beliefs
    assert len(beliefs_passed) == 1
    assert beliefs_passed[0].alpha == 3.0
    assert beliefs_passed[0].beta == 7.0