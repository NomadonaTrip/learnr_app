"""
Unit tests for Belief repository.
Tests CRUD operations and belief state management.
"""
from uuid import uuid4

import pytest

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.utils.auth import hash_password


@pytest.fixture
async def test_course(db_session, sample_course_data):
    """Create a test course for belief tests."""
    course = Course(
        slug=sample_course_data["slug"],
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
async def test_user_belief(db_session):
    """Create a test user for belief tests."""
    user = User(
        email="belief_test@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def test_concepts(db_session, test_course):
    """Create test concepts for belief tests."""
    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=test_course.id,
            name=f"Test Concept {i}",
            knowledge_area_id="ba-planning",
            corpus_section_ref=f"3.{i}.1",
        )
        db_session.add(concept)
        concepts.append(concept)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.mark.asyncio
async def test_bulk_create(db_session, test_user_belief, test_concepts):
    """Test bulk creating belief states."""
    repo = BeliefRepository(db_session)

    beliefs = [
        BeliefState(
            user_id=test_user_belief.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0,
            response_count=0
        )
        for concept in test_concepts
    ]

    count = await repo.bulk_create(beliefs)
    await db_session.commit()

    assert count == 5

    # Verify they were created
    all_beliefs = await repo.get_all_beliefs(test_user_belief.id)
    assert len(all_beliefs) == 5


@pytest.mark.asyncio
async def test_bulk_create_idempotent(db_session, test_user_belief, test_concepts):
    """Test that bulk_create is idempotent (ON CONFLICT DO NOTHING)."""
    repo = BeliefRepository(db_session)

    beliefs = [
        BeliefState(
            user_id=test_user_belief.id,
            concept_id=test_concepts[0].id,
            alpha=1.0,
            beta=1.0,
            response_count=0
        )
    ]

    # First insert
    count1 = await repo.bulk_create(beliefs)
    await db_session.commit()
    assert count1 == 1

    # Second insert (should be ignored due to ON CONFLICT DO NOTHING)
    count2 = await repo.bulk_create(beliefs)
    await db_session.commit()
    assert count2 == 0

    # Verify only one exists
    all_beliefs = await repo.get_all_beliefs(test_user_belief.id)
    assert len(all_beliefs) == 1


@pytest.mark.asyncio
async def test_bulk_create_from_concepts(db_session, test_user_belief, test_concepts):
    """Test bulk creating beliefs from concept IDs."""
    repo = BeliefRepository(db_session)

    concept_ids = [c.id for c in test_concepts]

    count = await repo.bulk_create_from_concepts(
        user_id=test_user_belief.id,
        concept_ids=concept_ids,
        alpha=1.0,
        beta=1.0
    )
    await db_session.commit()

    assert count == 5

    # Verify correct alpha/beta values
    beliefs = await repo.get_all_beliefs(test_user_belief.id)
    for belief in beliefs:
        assert belief.alpha == 1.0
        assert belief.beta == 1.0
        assert belief.response_count == 0


@pytest.mark.asyncio
async def test_get_all_beliefs(db_session, test_user_belief, test_concepts):
    """Test getting all beliefs for a user."""
    repo = BeliefRepository(db_session)

    # Create beliefs
    for concept in test_concepts:
        db_session.add(BeliefState(
            user_id=test_user_belief.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0
        ))
    await db_session.commit()

    beliefs = await repo.get_all_beliefs(test_user_belief.id)

    assert len(beliefs) == 5


@pytest.mark.asyncio
async def test_get_beliefs_as_dict(db_session, test_user_belief, test_concepts):
    """Test getting beliefs as dictionary keyed by concept_id."""
    repo = BeliefRepository(db_session)

    # Create beliefs
    for concept in test_concepts:
        db_session.add(BeliefState(
            user_id=test_user_belief.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0
        ))
    await db_session.commit()

    beliefs_dict = await repo.get_beliefs_as_dict(test_user_belief.id)

    assert len(beliefs_dict) == 5
    for concept in test_concepts:
        assert concept.id in beliefs_dict
        assert beliefs_dict[concept.id].user_id == test_user_belief.id


@pytest.mark.asyncio
async def test_get_belief(db_session, test_user_belief, test_concepts):
    """Test getting a specific belief state."""
    repo = BeliefRepository(db_session)

    # Create a belief
    belief = BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=2.0,
        beta=3.0
    )
    db_session.add(belief)
    await db_session.commit()

    found = await repo.get_belief(test_user_belief.id, test_concepts[0].id)

    assert found is not None
    assert found.alpha == 2.0
    assert found.beta == 3.0


@pytest.mark.asyncio
async def test_get_belief_returns_none_when_not_found(db_session, test_user_belief):
    """Test get_belief returns None for non-existent belief."""
    repo = BeliefRepository(db_session)

    found = await repo.get_belief(test_user_belief.id, uuid4())

    assert found is None


@pytest.mark.asyncio
async def test_get_belief_count(db_session, test_user_belief, test_concepts):
    """Test getting belief count for a user."""
    repo = BeliefRepository(db_session)

    # Initially empty
    count = await repo.get_belief_count(test_user_belief.id)
    assert count == 0

    # Add beliefs
    for concept in test_concepts[:3]:
        db_session.add(BeliefState(
            user_id=test_user_belief.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0
        ))
    await db_session.commit()

    count = await repo.get_belief_count(test_user_belief.id)
    assert count == 3


@pytest.mark.asyncio
async def test_check_initialization_status(db_session, test_user_belief, test_concepts):
    """Test checking if beliefs are initialized."""
    repo = BeliefRepository(db_session)

    # Initially not initialized
    is_initialized = await repo.check_initialization_status(test_user_belief.id)
    assert is_initialized is False

    # Add a belief
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=1.0,
        beta=1.0
    ))
    await db_session.commit()

    # Now initialized
    is_initialized = await repo.check_initialization_status(test_user_belief.id)
    assert is_initialized is True


@pytest.mark.asyncio
async def test_update_belief(db_session, test_user_belief, test_concepts):
    """Test updating a belief state."""
    repo = BeliefRepository(db_session)

    # Create a belief
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=1.0,
        beta=1.0,
        response_count=0
    ))
    await db_session.commit()

    # Update it
    updated = await repo.update_belief(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=2.0,
        beta=1.5,
        increment_response=True
    )
    await db_session.commit()
    # Refresh to get server-computed values
    await db_session.refresh(updated)

    assert updated is not None
    assert updated.alpha == 2.0
    assert updated.beta == 1.5
    assert updated.response_count == 1
    assert updated.last_response_at is not None


@pytest.mark.asyncio
async def test_delete_all_for_user(db_session, test_user_belief, test_concepts):
    """Test deleting all beliefs for a user."""
    repo = BeliefRepository(db_session)

    # Create beliefs
    for concept in test_concepts:
        db_session.add(BeliefState(
            user_id=test_user_belief.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0
        ))
    await db_session.commit()

    # Verify they exist
    count_before = await repo.get_belief_count(test_user_belief.id)
    assert count_before == 5

    # Delete all
    deleted = await repo.delete_all_for_user(test_user_belief.id)
    await db_session.commit()

    assert deleted == 5

    # Verify they're gone
    count_after = await repo.get_belief_count(test_user_belief.id)
    assert count_after == 0


@pytest.mark.asyncio
async def test_belief_mean_calculation(db_session, test_user_belief, test_concepts):
    """Test that belief mean is calculated correctly."""
    repo = BeliefRepository(db_session)

    # Create belief with alpha=3, beta=1 -> mean = 3/(3+1) = 0.75
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=3.0,
        beta=1.0
    ))
    await db_session.commit()

    belief = await repo.get_belief(test_user_belief.id, test_concepts[0].id)

    assert belief.mean == 0.75


@pytest.mark.asyncio
async def test_belief_confidence_calculation(db_session, test_user_belief, test_concepts):
    """Test that belief confidence is calculated correctly."""
    repo = BeliefRepository(db_session)

    # Create belief with alpha=5, beta=5 -> confidence = 10/(10+2) = 0.833...
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=5.0,
        beta=5.0
    ))
    await db_session.commit()

    belief = await repo.get_belief(test_user_belief.id, test_concepts[0].id)

    expected_confidence = 10 / 12  # 0.8333...
    assert abs(belief.confidence - expected_confidence) < 0.001


@pytest.mark.asyncio
async def test_belief_status_mastered(db_session, test_user_belief, test_concepts):
    """Test belief status is 'mastered' when mean >= 0.8 and high confidence."""
    repo = BeliefRepository(db_session)

    # High alpha, low beta -> high mean, high confidence
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=20.0,
        beta=2.0  # mean = 20/22 = 0.909, confidence = 22/24 = 0.917
    ))
    await db_session.commit()

    belief = await repo.get_belief(test_user_belief.id, test_concepts[0].id)

    assert belief.status == "mastered"


@pytest.mark.asyncio
async def test_belief_status_gap(db_session, test_user_belief, test_concepts):
    """Test belief status is 'gap' when mean < 0.5 and high confidence."""
    repo = BeliefRepository(db_session)

    # Low alpha, high beta -> low mean, high confidence
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=2.0,
        beta=20.0  # mean = 2/22 = 0.09, confidence = 22/24 = 0.917
    ))
    await db_session.commit()

    belief = await repo.get_belief(test_user_belief.id, test_concepts[0].id)

    assert belief.status == "gap"


@pytest.mark.asyncio
async def test_belief_status_uncertain(db_session, test_user_belief, test_concepts):
    """Test belief status is 'uncertain' when confidence < 0.7."""
    repo = BeliefRepository(db_session)

    # Uninformative prior -> uncertain
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=1.0,
        beta=1.0  # mean = 0.5, confidence = 2/4 = 0.5
    ))
    await db_session.commit()

    belief = await repo.get_belief(test_user_belief.id, test_concepts[0].id)

    assert belief.status == "uncertain"


@pytest.mark.asyncio
async def test_get_belief_summary(db_session, test_user_belief, test_concepts):
    """Test getting belief summary statistics."""
    repo = BeliefRepository(db_session)

    # Create beliefs with different statuses
    # Mastered: high alpha
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=20.0,
        beta=2.0
    ))
    # Gap: low alpha
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[1].id,
        alpha=2.0,
        beta=20.0
    ))
    # Uncertain: uninformative prior
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[2].id,
        alpha=1.0,
        beta=1.0
    ))
    await db_session.commit()

    summary = await repo.get_belief_summary(test_user_belief.id)

    assert summary["total"] == 3
    assert summary["mastered"] == 1
    assert summary["gap"] == 1
    assert summary["uncertain"] == 1
    assert "average_mean" in summary


@pytest.mark.asyncio
async def test_get_belief_summary_empty(db_session, test_user_belief):
    """Test getting belief summary when no beliefs exist."""
    repo = BeliefRepository(db_session)

    summary = await repo.get_belief_summary(test_user_belief.id)

    assert summary["total"] == 0
    assert summary["average_mean"] == 0.0


@pytest.mark.asyncio
async def test_bulk_create_empty_list(db_session, test_user_belief):
    """Test bulk_create with empty list returns 0."""
    repo = BeliefRepository(db_session)

    count = await repo.bulk_create([])

    assert count == 0


@pytest.mark.asyncio
async def test_bulk_create_from_concepts_empty_list(db_session, test_user_belief):
    """Test bulk_create_from_concepts with empty concept_ids returns 0."""
    repo = BeliefRepository(db_session)

    count = await repo.bulk_create_from_concepts(
        user_id=test_user_belief.id,
        concept_ids=[],
        alpha=1.0,
        beta=1.0
    )

    assert count == 0


@pytest.mark.asyncio
async def test_update_belief_returns_none_when_not_found(db_session, test_user_belief):
    """Test update_belief returns None when belief doesn't exist."""
    repo = BeliefRepository(db_session)

    result = await repo.update_belief(
        user_id=test_user_belief.id,
        concept_id=uuid4(),  # Non-existent concept
        alpha=2.0,
        beta=2.0
    )

    assert result is None


@pytest.mark.asyncio
async def test_update_belief_without_increment(db_session, test_user_belief, test_concepts):
    """Test update_belief with increment_response=False."""
    repo = BeliefRepository(db_session)

    # Create a belief
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=1.0,
        beta=1.0,
        response_count=5
    ))
    await db_session.commit()

    # Update without incrementing response count
    updated = await repo.update_belief(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=3.0,
        beta=2.0,
        increment_response=False
    )
    await db_session.commit()

    assert updated is not None
    assert updated.alpha == 3.0
    assert updated.beta == 2.0
    assert updated.response_count == 5  # Not incremented


@pytest.mark.asyncio
async def test_bulk_update(db_session, test_user_belief, test_concepts):
    """Test bulk updating multiple beliefs."""
    repo = BeliefRepository(db_session)

    # Create beliefs
    beliefs = []
    for concept in test_concepts[:3]:
        belief = BeliefState(
            user_id=test_user_belief.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0
        )
        db_session.add(belief)
        beliefs.append(belief)
    await db_session.commit()
    for b in beliefs:
        await db_session.refresh(b)

    # Prepare updates
    updates = {
        beliefs[0].id: {"alpha": 5.0, "beta": 2.0},
        beliefs[1].id: {"alpha": 3.0, "beta": 4.0},
    }

    updated_count = await repo.bulk_update(updates)
    await db_session.commit()

    assert updated_count == 2

    # Verify updates
    updated_belief0 = await repo.get_belief(test_user_belief.id, test_concepts[0].id)
    updated_belief1 = await repo.get_belief(test_user_belief.id, test_concepts[1].id)

    assert updated_belief0.alpha == 5.0
    assert updated_belief0.beta == 2.0
    assert updated_belief1.alpha == 3.0
    assert updated_belief1.beta == 4.0


@pytest.mark.asyncio
async def test_bulk_update_empty_dict(db_session):
    """Test bulk_update with empty dict returns 0."""
    repo = BeliefRepository(db_session)

    count = await repo.bulk_update({})

    assert count == 0


@pytest.mark.asyncio
async def test_bulk_update_nonexistent_belief(db_session):
    """Test bulk_update ignores non-existent belief IDs."""
    repo = BeliefRepository(db_session)

    updates = {
        uuid4(): {"alpha": 5.0, "beta": 2.0},  # Non-existent
    }

    count = await repo.bulk_update(updates)

    assert count == 0


@pytest.mark.asyncio
async def test_get_beliefs_by_status(db_session, test_user_belief, test_concepts):
    """Test getting beliefs grouped by status."""
    repo = BeliefRepository(db_session)

    # Create beliefs with different statuses
    # Mastered: high alpha, low beta, high confidence
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=20.0,
        beta=2.0  # mean=0.91, confidence=0.92 -> mastered
    ))
    # Gap: low alpha, high beta, high confidence
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[1].id,
        alpha=2.0,
        beta=20.0  # mean=0.09, confidence=0.92 -> gap
    ))
    # Borderline: medium alpha/beta, high confidence
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[2].id,
        alpha=10.0,
        beta=10.0  # mean=0.5, confidence=0.91 -> borderline
    ))
    # Uncertain: low confidence
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[3].id,
        alpha=1.0,
        beta=1.0  # mean=0.5, confidence=0.5 -> uncertain
    ))
    await db_session.commit()

    grouped = await repo.get_beliefs_by_status(test_user_belief.id)

    assert len(grouped["mastered"]) == 1
    assert len(grouped["gap"]) == 1
    assert len(grouped["borderline"]) == 1
    assert len(grouped["uncertain"]) == 1


@pytest.mark.asyncio
async def test_get_beliefs_by_status_empty(db_session, test_user_belief):
    """Test get_beliefs_by_status when no beliefs exist."""
    repo = BeliefRepository(db_session)

    grouped = await repo.get_beliefs_by_status(test_user_belief.id)

    assert grouped["mastered"] == []
    assert grouped["gap"] == []
    assert grouped["borderline"] == []
    assert grouped["uncertain"] == []


@pytest.mark.asyncio
async def test_belief_status_borderline(db_session, test_user_belief, test_concepts):
    """Test belief status is 'borderline' when 0.5 <= mean < 0.8 and high confidence."""
    repo = BeliefRepository(db_session)

    # Medium alpha and beta -> mean around 0.6, high confidence
    db_session.add(BeliefState(
        user_id=test_user_belief.id,
        concept_id=test_concepts[0].id,
        alpha=12.0,
        beta=8.0  # mean = 12/20 = 0.6, confidence = 20/22 = 0.91
    ))
    await db_session.commit()

    belief = await repo.get_belief(test_user_belief.id, test_concepts[0].id)

    assert belief.status == "borderline"


@pytest.mark.asyncio
async def test_get_earliest_created_at(db_session, test_user_belief, test_concepts):
    """Test getting earliest created_at for user beliefs."""
    repo = BeliefRepository(db_session)

    # Initially no beliefs
    earliest = await repo.get_earliest_created_at(test_user_belief.id)
    assert earliest is None

    # Add some beliefs
    for concept in test_concepts[:3]:
        db_session.add(BeliefState(
            user_id=test_user_belief.id,
            concept_id=concept.id,
            alpha=1.0,
            beta=1.0
        ))
    await db_session.commit()

    earliest = await repo.get_earliest_created_at(test_user_belief.id)
    assert earliest is not None


@pytest.mark.asyncio
async def test_bulk_create_database_error():
    """Test bulk_create raises DatabaseError on failure."""
    from unittest.mock import AsyncMock

    from src.exceptions import DatabaseError

    # Create a mock session that raises an exception
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("Connection lost")

    repo = BeliefRepository(mock_session)

    beliefs = [
        BeliefState(
            user_id=uuid4(),
            concept_id=uuid4(),
            alpha=1.0,
            beta=1.0,
            response_count=0
        )
    ]

    with pytest.raises(DatabaseError) as exc_info:
        await repo.bulk_create(beliefs)

    assert "Failed to bulk create beliefs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_bulk_create_from_concepts_database_error():
    """Test bulk_create_from_concepts raises DatabaseError on failure."""
    from unittest.mock import AsyncMock

    from src.exceptions import DatabaseError

    # Create a mock session that raises an exception
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("Connection lost")

    repo = BeliefRepository(mock_session)

    with pytest.raises(DatabaseError) as exc_info:
        await repo.bulk_create_from_concepts(
            user_id=uuid4(),
            concept_ids=[uuid4(), uuid4()],
            alpha=1.0,
            beta=1.0
        )

    assert "Failed to bulk create beliefs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_initialize_via_db_function_database_error():
    """Test initialize_via_db_function raises DatabaseError on failure."""
    from unittest.mock import AsyncMock

    from src.exceptions import DatabaseError

    # Create a mock session that raises an exception
    mock_session = AsyncMock()
    mock_session.execute.side_effect = Exception("Function not found")

    repo = BeliefRepository(mock_session)

    with pytest.raises(DatabaseError) as exc_info:
        await repo.initialize_via_db_function(uuid4())

    assert "Failed to initialize beliefs" in str(exc_info.value)


@pytest.mark.asyncio
async def test_initialize_via_db_function_success():
    """Test initialize_via_db_function returns count on success."""
    from unittest.mock import AsyncMock, MagicMock

    # Create a mock session with successful execution
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = 150
    mock_session.execute.return_value = mock_result

    repo = BeliefRepository(mock_session)

    count = await repo.initialize_via_db_function(uuid4())

    assert count == 150
    mock_session.flush.assert_called_once()
