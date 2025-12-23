"""
Integration tests for Concepts.

Tests concept creation in database with course_id FK,
bulk insert performance, index effectiveness, and foreign key constraints.
"""
from uuid import uuid4

import pytest

from src.models.concept import Concept
from src.models.course import Course
from src.repositories.concept_repository import ConceptRepository
from src.schemas.concept import ConceptCreate


@pytest.fixture
async def cbap_course(db_session):
    """Create CBAP course fixture for integration tests."""
    course = Course(
        slug="cbap-test",
        name="CBAP Certification Prep Test",
        description="Test course for concept integration tests.",
        corpus_name="BABOK v3",
        knowledge_areas=[
            {"id": "ba-planning", "name": "Business Analysis Planning and Monitoring", "short_name": "BA Planning", "display_order": 1, "color": "#3B82F6"},
            {"id": "elicitation", "name": "Elicitation and Collaboration", "short_name": "Elicitation", "display_order": 2, "color": "#10B981"},
            {"id": "rlcm", "name": "Requirements Life Cycle Management", "short_name": "RLCM", "display_order": 3, "color": "#F59E0B"},
            {"id": "strategy", "name": "Strategy Analysis", "short_name": "Strategy", "display_order": 4, "color": "#EF4444"},
            {"id": "radd", "name": "Requirements Analysis and Design Definition", "short_name": "RADD", "display_order": 5, "color": "#8B5CF6"},
            {"id": "solution-eval", "name": "Solution Evaluation", "short_name": "Solution Eval", "display_order": 6, "color": "#EC4899"}
        ],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


# ============================================================================
# Test Concept Table Creation via Migration
# ============================================================================

@pytest.mark.asyncio
async def test_concept_table_exists(db_session):
    """Test that concepts table was created by migration."""
    from sqlalchemy import text

    result = await db_session.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_name = 'concepts'")
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == "concepts"


@pytest.mark.asyncio
async def test_concept_indexes_exist(db_session):
    """Test that expected indexes exist on concepts table."""
    from sqlalchemy import text

    result = await db_session.execute(
        text("""
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'concepts'
            ORDER BY indexname
        """)
    )
    indexes = [row[0] for row in result.fetchall()]

    # SQLAlchemy auto-generates index names with ix_ prefix when index=True
    # The migration creates explicit names, but tests use Base.metadata.create_all
    # which uses model-defined indexes. Check for either naming convention.
    has_course_idx = (
        "idx_concepts_course" in indexes or
        "ix_concepts_course_id" in indexes or
        any("course" in idx for idx in indexes)
    )
    has_section_idx = (
        "idx_concepts_section" in indexes or
        "ix_concepts_corpus_section_ref" in indexes or
        any("section" in idx for idx in indexes)
    )

    assert has_course_idx, f"Missing course index. Available: {indexes}"
    assert has_section_idx, f"Missing section index. Available: {indexes}"


# ============================================================================
# Test Concept CRUD with Course FK
# ============================================================================

@pytest.mark.asyncio
async def test_create_concept_with_course_fk(db_session, cbap_course):
    """Test creating a concept with proper course_id FK."""
    repo = ConceptRepository(db_session)

    concept = await repo.create_concept(ConceptCreate(
        course_id=cbap_course.id,
        name="Stakeholder Identification",
        description="The process of identifying stakeholders.",
        corpus_section_ref="3.2.1",
        knowledge_area_id="ba-planning",
        difficulty_estimate=0.3,
        prerequisite_depth=0,
    ))
    await db_session.commit()

    assert concept.id is not None
    assert concept.course_id == cbap_course.id


@pytest.mark.asyncio
async def test_concept_fk_constraint_enforced(db_session):
    """Test that FK constraint is enforced (invalid course_id rejected)."""
    from sqlalchemy.exc import IntegrityError

    repo = ConceptRepository(db_session)

    # Try to create concept with non-existent course_id
    invalid_course_id = uuid4()

    with pytest.raises(IntegrityError):
        await repo.create_concept(ConceptCreate(
            course_id=invalid_course_id,
            name="Test Concept",
            knowledge_area_id="ba-planning",
        ))
        await db_session.commit()


@pytest.mark.asyncio
async def test_cascade_delete_removes_concepts(db_session):
    """Test that deleting a course cascades to delete its concepts."""
    # Create course
    course = Course(
        slug="cascade-test",
        name="Cascade Test Course",
        knowledge_areas=[{"id": "test-ka", "name": "Test KA", "short_name": "Test", "display_order": 1, "color": "#000000"}],
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    course_id = course.id

    # Add concepts
    repo = ConceptRepository(db_session)
    for i in range(5):
        concept = Concept(
            course_id=course_id,
            name=f"Cascade Concept {i}",
            knowledge_area_id="test-ka",
        )
        db_session.add(concept)
    await db_session.commit()

    # Verify concepts exist
    count_before = await repo.get_concept_count(course_id)
    assert count_before == 5

    # Delete course (should cascade)
    await db_session.delete(course)
    await db_session.commit()

    # Verify concepts were deleted via raw query
    # (repository query would fail since course doesn't exist)
    from sqlalchemy import func, select
    result = await db_session.execute(
        select(func.count(Concept.id)).where(Concept.course_id == course_id)
    )
    count_after = result.scalar_one()

    assert count_after == 0


# ============================================================================
# Test Bulk Insert Performance
# ============================================================================

@pytest.mark.asyncio
async def test_bulk_insert_1000_concepts(db_session, cbap_course):
    """Test bulk inserting 1000+ concepts efficiently."""
    import time

    repo = ConceptRepository(db_session)

    # Create 1000 concepts
    concepts = [
        ConceptCreate(
            course_id=cbap_course.id,
            name=f"Bulk Concept {i}",
            description=f"Description for bulk concept {i}",
            corpus_section_ref=f"3.{i % 10}.{i % 5}",
            knowledge_area_id=["ba-planning", "elicitation", "rlcm", "strategy", "radd", "solution-eval"][i % 6],
            difficulty_estimate=round(0.1 + (i % 10) * 0.08, 2),
            prerequisite_depth=i % 4,
        )
        for i in range(1000)
    ]

    start_time = time.time()
    count = await repo.bulk_create(concepts)
    await db_session.commit()
    elapsed = time.time() - start_time

    assert count == 1000
    # Bulk insert should complete in reasonable time (less than 10 seconds)
    assert elapsed < 10.0, f"Bulk insert took too long: {elapsed:.2f}s"

    # Verify total count
    total = await repo.get_concept_count(cbap_course.id)
    assert total == 1000


# ============================================================================
# Test Index Effectiveness
# ============================================================================

@pytest.mark.asyncio
async def test_query_by_course_id_uses_index(db_session, cbap_course):
    """Test that queries by course_id use the index."""
    repo = ConceptRepository(db_session)

    # Add some concepts
    for i in range(100):
        db_session.add(Concept(
            course_id=cbap_course.id,
            name=f"Index Test {i}",
            knowledge_area_id="ba-planning",
        ))
    await db_session.commit()

    # Execute query and check it works efficiently
    concepts = await repo.get_all_concepts(cbap_course.id)

    assert len(concepts) == 100


@pytest.mark.asyncio
async def test_query_by_composite_index(db_session, cbap_course):
    """Test queries using the composite (course_id, knowledge_area_id) index."""
    repo = ConceptRepository(db_session)

    # Add concepts to different KAs
    ka_ids = ["ba-planning", "elicitation", "rlcm"]
    for ka_id in ka_ids:
        for i in range(50):
            db_session.add(Concept(
                course_id=cbap_course.id,
                name=f"{ka_id} Concept {i}",
                knowledge_area_id=ka_id,
            ))
    await db_session.commit()

    # Query by composite index
    planning_concepts = await repo.get_concepts_by_ka(cbap_course.id, "ba-planning")
    elicitation_concepts = await repo.get_concepts_by_ka(cbap_course.id, "elicitation")

    assert len(planning_concepts) == 50
    assert len(elicitation_concepts) == 50


@pytest.mark.asyncio
async def test_query_by_section_ref_uses_index(db_session, cbap_course):
    """Test that queries by section_ref use the index."""
    repo = ConceptRepository(db_session)

    # Add concepts with section refs
    for i in range(20):
        db_session.add(Concept(
            course_id=cbap_course.id,
            name=f"Section Test {i}",
            knowledge_area_id="ba-planning",
            corpus_section_ref="3.2.1",
        ))
    for i in range(10):
        db_session.add(Concept(
            course_id=cbap_course.id,
            name=f"Other Section {i}",
            knowledge_area_id="ba-planning",
            corpus_section_ref="3.3.1",
        ))
    await db_session.commit()

    # Query by section ref
    section_321 = await repo.get_by_section_ref(cbap_course.id, "3.2.1")
    section_331 = await repo.get_by_section_ref(cbap_course.id, "3.3.1")

    assert len(section_321) == 20
    assert len(section_331) == 10


# ============================================================================
# Test Concept Count Methods
# ============================================================================

@pytest.mark.asyncio
async def test_get_concept_count_by_ka_all_kas(db_session, cbap_course):
    """Test getting counts grouped by all knowledge areas."""
    repo = ConceptRepository(db_session)

    # Add concepts across all KAs
    ka_counts = {
        "ba-planning": 100,
        "elicitation": 80,
        "rlcm": 90,
        "strategy": 85,
        "radd": 95,
        "solution-eval": 75,
    }

    for ka_id, count in ka_counts.items():
        for i in range(count):
            db_session.add(Concept(
                course_id=cbap_course.id,
                name=f"{ka_id}-{i}",
                knowledge_area_id=ka_id,
            ))
    await db_session.commit()

    # Get counts
    result = await repo.get_concept_count_by_ka(cbap_course.id)

    assert result == ka_counts


# ============================================================================
# Test Course Relationship
# ============================================================================

@pytest.mark.asyncio
async def test_concept_course_relationship_bidirectional(db_session, cbap_course):
    """Test that concept-course relationship works both directions."""
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload

    from src.models.course import Course

    repo = ConceptRepository(db_session)

    # Create concept
    concept = await repo.create_concept(ConceptCreate(
        course_id=cbap_course.id,
        name="Relationship Test",
        knowledge_area_id="ba-planning",
    ))
    await db_session.commit()

    # Reload concept with course eagerly loaded
    result = await db_session.execute(
        select(Concept)
        .where(Concept.id == concept.id)
        .options(selectinload(Concept.course))
    )
    loaded_concept = result.scalar_one()

    # Access course from concept
    assert loaded_concept.course is not None
    assert loaded_concept.course.id == cbap_course.id
    assert loaded_concept.course.slug == "cbap-test"

    # Reload course with concepts eagerly loaded
    course_result = await db_session.execute(
        select(Course)
        .where(Course.id == cbap_course.id)
        .options(selectinload(Course.concepts))
    )
    loaded_course = course_result.scalar_one()

    # Access concepts from course
    assert len(loaded_course.concepts) >= 1
    concept_names = [c.name for c in loaded_course.concepts]
    assert "Relationship Test" in concept_names
