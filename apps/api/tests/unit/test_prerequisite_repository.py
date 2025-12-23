"""
Unit tests for Concept prerequisite repository methods.
Tests CRUD operations and prerequisite chain queries.
"""
from uuid import uuid4

import pytest

from src.models.concept import Concept
from src.models.course import Course
from src.repositories.concept_repository import ConceptRepository
from src.schemas.concept_prerequisite import PrerequisiteCreate, RelationshipType


@pytest.fixture
async def test_course(db_session, sample_course_data):
    """Create a test course for prerequisite tests."""
    course = Course(
        slug=f"test-{uuid4().hex[:8]}",
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
    """Create a set of test concepts with varying depths."""
    concepts = []
    for i in range(5):
        concept = Concept(
            course_id=test_course.id,
            name=f"Concept {i}",
            description=f"Description for concept {i}",
            corpus_section_ref=f"3.{i}.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.2 + (i * 0.15),
            prerequisite_depth=0
        )
        db_session.add(concept)
        concepts.append(concept)
    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.mark.asyncio
async def test_add_prerequisite(db_session, test_concepts):
    """Test adding a single prerequisite relationship."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b = test_concepts[0], test_concepts[1]

    prereq = await repo.add_prerequisite(
        concept_id=concept_b.id,
        prereq_id=concept_a.id,
        strength=0.8,
        relationship_type="required"
    )
    await db_session.commit()

    assert prereq.concept_id == concept_b.id
    assert prereq.prerequisite_concept_id == concept_a.id
    assert prereq.strength == 0.8
    assert prereq.relationship_type == "required"


@pytest.mark.asyncio
async def test_get_prerequisites(db_session, test_concepts):
    """Test getting direct prerequisites for a concept."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c = test_concepts[0], test_concepts[1], test_concepts[2]

    # C depends on both A and B
    await repo.add_prerequisite(concept_c.id, concept_a.id, 0.9, "required")
    await repo.add_prerequisite(concept_c.id, concept_b.id, 0.7, "helpful")
    await db_session.commit()

    prereqs = await repo.get_prerequisites(concept_c.id)

    assert len(prereqs) == 2
    prereq_ids = [p.id for p in prereqs]
    assert concept_a.id in prereq_ids
    assert concept_b.id in prereq_ids


@pytest.mark.asyncio
async def test_get_prerequisites_with_strength(db_session, test_concepts):
    """Test getting prerequisites with strength and relationship type."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c = test_concepts[0], test_concepts[1], test_concepts[2]

    await repo.add_prerequisite(concept_c.id, concept_a.id, 0.9, "required")
    await repo.add_prerequisite(concept_c.id, concept_b.id, 0.5, "related")
    await db_session.commit()

    prereqs = await repo.get_prerequisites_with_strength(concept_c.id)

    assert len(prereqs) == 2
    # Should be ordered by strength descending
    assert prereqs[0][1] == 0.9  # Highest strength first
    assert prereqs[0][2] == "required"
    assert prereqs[1][1] == 0.5
    assert prereqs[1][2] == "related"


@pytest.mark.asyncio
async def test_get_prerequisites_returns_empty_for_root(db_session, test_concepts):
    """Test that concepts with no prerequisites return empty list."""
    repo = ConceptRepository(db_session)

    prereqs = await repo.get_prerequisites(test_concepts[0].id)

    assert prereqs == []


@pytest.mark.asyncio
async def test_get_dependents(db_session, test_concepts):
    """Test getting concepts that depend on a given concept."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c, concept_d = test_concepts[:4]

    # B and C both depend on A
    await repo.add_prerequisite(concept_b.id, concept_a.id, 0.8, "required")
    await repo.add_prerequisite(concept_c.id, concept_a.id, 0.7, "helpful")
    # D depends on B
    await repo.add_prerequisite(concept_d.id, concept_b.id, 0.6, "required")
    await db_session.commit()

    dependents_of_a = await repo.get_dependents(concept_a.id)

    assert len(dependents_of_a) == 2
    dependent_ids = [d.id for d in dependents_of_a]
    assert concept_b.id in dependent_ids
    assert concept_c.id in dependent_ids
    assert concept_d.id not in dependent_ids  # D depends on B, not directly on A


@pytest.mark.asyncio
async def test_bulk_add_prerequisites(db_session, test_concepts):
    """Test bulk adding prerequisite relationships."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c, concept_d = test_concepts[:4]

    prereqs = [
        PrerequisiteCreate(
            concept_id=concept_b.id,
            prerequisite_concept_id=concept_a.id,
            strength=0.9,
            relationship_type=RelationshipType.REQUIRED
        ),
        PrerequisiteCreate(
            concept_id=concept_c.id,
            prerequisite_concept_id=concept_a.id,
            strength=0.7,
            relationship_type=RelationshipType.HELPFUL
        ),
        PrerequisiteCreate(
            concept_id=concept_d.id,
            prerequisite_concept_id=concept_b.id,
            strength=0.8,
            relationship_type=RelationshipType.REQUIRED
        ),
    ]

    count = await repo.bulk_add_prerequisites(prereqs)
    await db_session.commit()

    assert count == 3

    # Verify relationships
    b_prereqs = await repo.get_prerequisites(concept_b.id)
    assert len(b_prereqs) == 1
    assert b_prereqs[0].id == concept_a.id


@pytest.mark.asyncio
async def test_get_root_concepts(db_session, test_course, test_concepts):
    """Test getting concepts with no prerequisites."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c = test_concepts[:3]

    # B depends on A, C depends on A
    # A has no prerequisites (root)
    await repo.add_prerequisite(concept_b.id, concept_a.id, 0.8, "required")
    await repo.add_prerequisite(concept_c.id, concept_a.id, 0.7, "required")
    await db_session.commit()

    roots = await repo.get_root_concepts(test_course.id)

    # Concepts 0, 3, 4 should be roots (no prerequisites)
    # Concepts 1, 2 have prerequisites
    root_ids = [r.id for r in roots]
    assert concept_a.id in root_ids  # Concept 0 is root
    assert concept_b.id not in root_ids  # Concept 1 has prereq
    assert concept_c.id not in root_ids  # Concept 2 has prereq


@pytest.mark.asyncio
async def test_get_root_concepts_with_dependent_count(db_session, test_course, test_concepts):
    """Test getting root concepts with their dependent counts."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c, concept_d = test_concepts[:4]

    # A is root with 2 dependents (B, C)
    # D is root with 0 dependents
    await repo.add_prerequisite(concept_b.id, concept_a.id, 0.8, "required")
    await repo.add_prerequisite(concept_c.id, concept_a.id, 0.7, "required")
    await db_session.commit()

    roots = await repo.get_root_concepts_with_dependent_count(test_course.id)

    # Find concept_a in roots
    a_entry = next((r for r in roots if r[0].id == concept_a.id), None)
    assert a_entry is not None
    assert a_entry[1] == 2  # Two dependents

    # Find concept_d in roots (no dependents)
    d_entry = next((r for r in roots if r[0].id == concept_d.id), None)
    assert d_entry is not None
    assert d_entry[1] == 0


@pytest.mark.asyncio
async def test_delete_all_prerequisites_for_course(db_session, test_course, test_concepts):
    """Test deleting all prerequisites for a course."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c = test_concepts[:3]

    await repo.add_prerequisite(concept_b.id, concept_a.id, 0.8, "required")
    await repo.add_prerequisite(concept_c.id, concept_a.id, 0.7, "required")
    await db_session.commit()

    # Verify prerequisites exist
    prereqs_before = await repo.get_prerequisites(concept_b.id)
    assert len(prereqs_before) == 1

    # Delete all
    deleted = await repo.delete_all_prerequisites_for_course(test_course.id)
    await db_session.commit()

    assert deleted == 2

    # Verify deleted
    prereqs_after = await repo.get_prerequisites(concept_b.id)
    assert len(prereqs_after) == 0


@pytest.mark.asyncio
async def test_update_prerequisite_depths(db_session, test_concepts):
    """Test bulk updating prerequisite depths."""
    repo = ConceptRepository(db_session)

    depth_map = {
        test_concepts[0].id: 0,
        test_concepts[1].id: 1,
        test_concepts[2].id: 1,
        test_concepts[3].id: 2,
        test_concepts[4].id: 3,
    }

    updated = await repo.update_prerequisite_depths(depth_map)
    await db_session.commit()

    assert updated == 5

    # Verify depths
    for concept in test_concepts:
        await db_session.refresh(concept)

    assert test_concepts[0].prerequisite_depth == 0
    assert test_concepts[1].prerequisite_depth == 1
    assert test_concepts[2].prerequisite_depth == 1
    assert test_concepts[3].prerequisite_depth == 2
    assert test_concepts[4].prerequisite_depth == 3


@pytest.mark.asyncio
async def test_get_all_prerequisites_for_course(db_session, test_course, test_concepts):
    """Test getting all prerequisite relationships for a course."""
    repo = ConceptRepository(db_session)
    concept_a, concept_b, concept_c, concept_d = test_concepts[:4]

    await repo.add_prerequisite(concept_b.id, concept_a.id, 0.8, "required")
    await repo.add_prerequisite(concept_c.id, concept_a.id, 0.7, "helpful")
    await repo.add_prerequisite(concept_d.id, concept_b.id, 0.6, "related")
    await db_session.commit()

    all_prereqs = await repo.get_all_prerequisites_for_course(test_course.id)

    assert len(all_prereqs) == 3


@pytest.mark.asyncio
async def test_prerequisite_chain_query(db_session, test_concepts):
    """Test recursive prerequisite chain query."""
    repo = ConceptRepository(db_session)
    # Build chain: A <- B <- C <- D
    # D depends on C, C depends on B, B depends on A
    concept_a, concept_b, concept_c, concept_d = test_concepts[:4]

    await repo.add_prerequisite(concept_b.id, concept_a.id, 0.9, "required")
    await repo.add_prerequisite(concept_c.id, concept_b.id, 0.8, "required")
    await repo.add_prerequisite(concept_d.id, concept_c.id, 0.7, "required")
    await db_session.commit()

    # Get chain for D
    chain = await repo.get_prerequisite_chain(concept_d.id)

    assert len(chain) == 3
    # Should be ordered by depth
    chain_ids = [c.id for c, depth in chain]
    assert concept_c.id in chain_ids  # Direct prereq (depth 1)
    assert concept_b.id in chain_ids  # Depth 2
    assert concept_a.id in chain_ids  # Depth 3

    # Verify depths
    depth_map = {c.id: d for c, d in chain}
    assert depth_map[concept_c.id] == 1
    assert depth_map[concept_b.id] == 2
    assert depth_map[concept_a.id] == 3


@pytest.mark.asyncio
async def test_prerequisite_chain_with_max_depth(db_session, test_concepts):
    """Test that max_depth limits chain traversal."""
    repo = ConceptRepository(db_session)
    # Build chain: A <- B <- C <- D <- E
    concepts = test_concepts[:5]

    for i in range(1, 5):
        await repo.add_prerequisite(
            concepts[i].id, concepts[i-1].id, 0.8, "required"
        )
    await db_session.commit()

    # Get chain with max_depth=2
    chain = await repo.get_prerequisite_chain(concepts[4].id, max_depth=2)

    # Should only include concepts at depth 1 and 2
    assert len(chain) == 2
    chain_ids = [c.id for c, d in chain]
    assert concepts[3].id in chain_ids  # Depth 1
    assert concepts[2].id in chain_ids  # Depth 2
    assert concepts[1].id not in chain_ids  # Depth 3, excluded
    assert concepts[0].id not in chain_ids  # Depth 4, excluded


@pytest.mark.asyncio
async def test_prerequisite_chain_empty_for_root(db_session, test_concepts):
    """Test that root concepts have empty prerequisite chain."""
    repo = ConceptRepository(db_session)

    chain = await repo.get_prerequisite_chain(test_concepts[0].id)

    assert chain == []
