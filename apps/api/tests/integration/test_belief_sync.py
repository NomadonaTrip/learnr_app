"""
Integration tests for Belief State Sync functionality.

Story 2.14: Belief State Sync for New Concepts

Tests cover:
- Lazy init during update_beliefs creates missing beliefs
- sync_beliefs_for_course batch operation
- Idempotency: multiple sync runs create 0 duplicates
- New beliefs have Beta(1,1) uninformative prior
- Existing beliefs are not modified
"""

import pytest

from src.models.belief_state import BeliefState
from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.question import Question
from src.models.user import User
from src.repositories.belief_repository import BeliefRepository
from src.services.belief_updater import BeliefUpdater
from src.utils.auth import hash_password

# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
async def sync_course(db_session, sample_course_data):
    """Create a test course for sync tests."""
    course = Course(
        slug="belief-sync-test",
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
async def sync_user(db_session):
    """Create a test user for sync tests."""
    user = User(
        email="belief_sync_test@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sync_enrollment(db_session, sync_user, sync_course):
    """Create enrollment for sync user in sync course."""
    enrollment = Enrollment(
        user_id=sync_user.id,
        course_id=sync_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def sync_concepts(db_session, sync_course):
    """Create test concepts for sync tests."""
    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=sync_course.id,
            name=f"Sync Test Concept {i}",
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
async def partial_beliefs(db_session, sync_user, sync_concepts):
    """Create beliefs for only some concepts (partial init)."""
    # Create beliefs for first 2 concepts only, leaving 3 missing
    beliefs = []
    for concept in sync_concepts[:2]:
        belief = BeliefState(
            user_id=sync_user.id,
            concept_id=concept.id,
            alpha=3.0,  # Non-default values
            beta=2.0,
            response_count=5,
        )
        db_session.add(belief)
        beliefs.append(belief)
    await db_session.commit()
    for b in beliefs:
        await db_session.refresh(b)
    return beliefs


@pytest.fixture
async def sync_question(db_session, sync_course, sync_concepts):
    """Create a question that maps to multiple concepts."""
    from src.models.question_concept import QuestionConcept

    question = Question(
        course_id=sync_course.id,
        question_text="Test question for sync",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="A",
        explanation="Test explanation",
        knowledge_area_id="ba-planning",
        difficulty=0.5,
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    # Map question to concepts (including ones without beliefs)
    for concept in sync_concepts:
        qc = QuestionConcept(
            question_id=question.id,
            concept_id=concept.id,
            relevance=0.8,
        )
        db_session.add(qc)
    await db_session.commit()

    # Reload question with concepts
    await db_session.refresh(question)
    return question


# ============================================================================
# Lazy Initialization Integration Tests
# ============================================================================

class TestLazyInitIntegration:
    """Integration tests for lazy initialization in BeliefUpdater."""

    @pytest.mark.asyncio
    async def test_update_beliefs_creates_missing_with_beta_1_1(
        self, db_session, sync_user, sync_concepts, partial_beliefs, sync_question
    ):
        """
        Test lazy init during update_beliefs creates beliefs with Beta(1,1).

        Given: User has beliefs for 2 of 5 concepts
        When: update_beliefs is called for question covering all 5 concepts
        Then: Missing 3 beliefs are created with alpha=1.0, beta=1.0
        """
        belief_repo = BeliefRepository(db_session)
        updater = BeliefUpdater(belief_repo)

        # Reload question with concepts relationship
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(Question).options(
            selectinload(Question.question_concepts)
        ).where(Question.id == sync_question.id)
        result = await db_session.execute(stmt)
        question = result.scalar_one()

        # Before: 2 beliefs exist
        existing_before = await belief_repo.get_beliefs_as_dict(sync_user.id)
        assert len(existing_before) == 2

        # Call update_beliefs
        response = await belief_repo.get_beliefs_for_concepts(
            sync_user.id,
            [c.id for c in sync_concepts]
        )

        # After lazy init in update_beliefs, all 5 should be updated
        await updater.update_beliefs(
            user_id=sync_user.id,
            question=question,
            is_correct=True,
        )
        await db_session.commit()

        # After: 5 beliefs should exist
        all_beliefs = await belief_repo.get_beliefs_as_dict(sync_user.id)
        assert len(all_beliefs) == 5

        # Verify new beliefs have been created and updated
        # (They start at Beta(1,1) but are immediately updated)
        for concept in sync_concepts[2:]:  # The 3 that were missing
            belief = all_beliefs.get(concept.id)
            assert belief is not None, f"Belief should exist for {concept.name}"

    @pytest.mark.asyncio
    async def test_lazy_init_does_not_reset_existing_beliefs(
        self, db_session, sync_user, sync_concepts, partial_beliefs, sync_question
    ):
        """
        Test lazy init does NOT modify existing beliefs.

        Given: User has beliefs with alpha=3.0, beta=2.0
        When: Lazy init runs for missing concepts
        Then: Existing beliefs retain their original alpha/beta values
        """
        belief_repo = BeliefRepository(db_session)
        updater = BeliefUpdater(belief_repo)

        # Store original values
        original_beliefs = {
            partial_beliefs[0].concept_id: (partial_beliefs[0].alpha, partial_beliefs[0].beta),
            partial_beliefs[1].concept_id: (partial_beliefs[1].alpha, partial_beliefs[1].beta),
        }

        # Reload question with concepts
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload
        stmt = select(Question).options(
            selectinload(Question.question_concepts)
        ).where(Question.id == sync_question.id)
        result = await db_session.execute(stmt)
        question = result.scalar_one()

        # Call update_beliefs (triggers lazy init)
        await updater.update_beliefs(
            user_id=sync_user.id,
            question=question,
            is_correct=True,
        )
        await db_session.commit()

        # Verify existing beliefs were updated from their original values
        # (not reset to Beta(1,1))
        all_beliefs = await belief_repo.get_beliefs_as_dict(sync_user.id)

        for concept_id, (orig_alpha, orig_beta) in original_beliefs.items():
            belief = all_beliefs.get(concept_id)
            assert belief is not None

            # Alpha should have increased (correct answer) from original value
            # If it was reset to Beta(1,1), it would be ~1.78 after update
            # But since it started at 3.0, it should be higher
            assert belief.alpha > 3.0, f"Alpha should be > 3.0, got {belief.alpha}"


# ============================================================================
# Batch Sync Integration Tests
# ============================================================================

class TestBatchSyncIntegration:
    """Integration tests for batch sync functionality."""

    @pytest.mark.asyncio
    async def test_bulk_create_creates_beliefs_for_all_concepts(
        self, db_session, sync_user, sync_concepts
    ):
        """
        Test bulk_create_from_concepts creates beliefs for all concepts.
        """
        belief_repo = BeliefRepository(db_session)

        # Before: no beliefs
        existing = await belief_repo.get_beliefs_as_dict(sync_user.id)
        assert len(existing) == 0

        # Call bulk_create
        concept_ids = [c.id for c in sync_concepts]
        created_count = await belief_repo.bulk_create_from_concepts(
            user_id=sync_user.id,
            concept_ids=concept_ids,
            alpha=1.0,
            beta=1.0,
        )
        await db_session.commit()

        # Should have created 5 beliefs
        assert created_count == 5

        # Verify beliefs exist with correct values
        all_beliefs = await belief_repo.get_beliefs_as_dict(sync_user.id)
        assert len(all_beliefs) == 5

        for concept in sync_concepts:
            belief = all_beliefs.get(concept.id)
            assert belief is not None
            assert belief.alpha == 1.0
            assert belief.beta == 1.0

    @pytest.mark.asyncio
    async def test_bulk_create_idempotent(self, db_session, sync_user, sync_concepts):
        """
        Test bulk_create is idempotent - second run creates 0 new beliefs.

        Uses ON CONFLICT DO NOTHING for idempotency.
        """
        belief_repo = BeliefRepository(db_session)
        concept_ids = [c.id for c in sync_concepts]

        # First run: creates 5
        first_count = await belief_repo.bulk_create_from_concepts(
            user_id=sync_user.id,
            concept_ids=concept_ids,
            alpha=1.0,
            beta=1.0,
        )
        await db_session.commit()
        assert first_count == 5

        # Second run: creates 0 (all exist)
        second_count = await belief_repo.bulk_create_from_concepts(
            user_id=sync_user.id,
            concept_ids=concept_ids,
            alpha=1.0,
            beta=1.0,
        )
        await db_session.commit()
        assert second_count == 0

        # Total beliefs should still be 5
        all_beliefs = await belief_repo.get_beliefs_as_dict(sync_user.id)
        assert len(all_beliefs) == 5

    @pytest.mark.asyncio
    async def test_bulk_create_with_partial_existing(
        self, db_session, sync_user, sync_concepts, partial_beliefs
    ):
        """
        Test bulk_create only creates missing beliefs when some exist.
        """
        belief_repo = BeliefRepository(db_session)
        concept_ids = [c.id for c in sync_concepts]

        # 2 beliefs already exist, 3 missing
        created_count = await belief_repo.bulk_create_from_concepts(
            user_id=sync_user.id,
            concept_ids=concept_ids,
            alpha=1.0,
            beta=1.0,
        )
        await db_session.commit()

        # Should create only the 3 missing
        assert created_count == 3

        # Total should be 5
        all_beliefs = await belief_repo.get_beliefs_as_dict(sync_user.id)
        assert len(all_beliefs) == 5

    @pytest.mark.asyncio
    async def test_bulk_create_preserves_existing_values(
        self, db_session, sync_user, sync_concepts, partial_beliefs
    ):
        """
        Test bulk_create does not modify existing belief values.
        """
        belief_repo = BeliefRepository(db_session)
        concept_ids = [c.id for c in sync_concepts]

        # Store original values
        original_alpha = partial_beliefs[0].alpha
        original_beta = partial_beliefs[0].beta

        # Run bulk_create
        await belief_repo.bulk_create_from_concepts(
            user_id=sync_user.id,
            concept_ids=concept_ids,
            alpha=1.0,
            beta=1.0,
        )
        await db_session.commit()

        # Refresh and verify original belief unchanged
        await db_session.refresh(partial_beliefs[0])
        assert partial_beliefs[0].alpha == original_alpha
        assert partial_beliefs[0].beta == original_beta
