"""
Unit tests for Concept repository.
Tests CRUD operations with course_id FK support.
"""
import pytest
from uuid import uuid4

from src.models.concept import Concept
from src.models.course import Course
from src.repositories.concept_repository import ConceptRepository
from src.schemas.concept import ConceptCreate


@pytest.fixture
async def test_course(db_session, sample_course_data):
    """Create a test course for concept tests."""
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


@pytest.mark.asyncio
async def test_create_concept(db_session, test_course, sample_concept_data):
    """Test creating a single concept."""
    repo = ConceptRepository(db_session)

    concept_create = ConceptCreate(
        course_id=test_course.id,
        **sample_concept_data
    )

    concept = await repo.create_concept(concept_create)
    await db_session.commit()

    assert concept.id is not None
    assert concept.course_id == test_course.id
    assert concept.name == sample_concept_data["name"]
    assert concept.description == sample_concept_data["description"]
    assert concept.corpus_section_ref == sample_concept_data["corpus_section_ref"]
    assert concept.knowledge_area_id == sample_concept_data["knowledge_area_id"]
    assert concept.difficulty_estimate == sample_concept_data["difficulty_estimate"]
    assert concept.prerequisite_depth == sample_concept_data["prerequisite_depth"]


@pytest.mark.asyncio
async def test_bulk_create_concepts(db_session, test_course):
    """Test bulk creating multiple concepts."""
    repo = ConceptRepository(db_session)

    concepts_data = [
        ConceptCreate(
            course_id=test_course.id,
            name=f"Concept {i}",
            description=f"Description for concept {i}",
            corpus_section_ref=f"3.{i}.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.3 + (i * 0.1),
            prerequisite_depth=i
        )
        for i in range(5)
    ]

    count = await repo.bulk_create(concepts_data)
    await db_session.commit()

    assert count == 5

    # Verify they were created
    all_concepts = await repo.get_all_concepts(test_course.id)
    assert len(all_concepts) == 5


@pytest.mark.asyncio
async def test_get_by_id(db_session, test_course, sample_concept_data):
    """Test getting a concept by ID."""
    repo = ConceptRepository(db_session)

    # Create a concept first
    concept_create = ConceptCreate(course_id=test_course.id, **sample_concept_data)
    created = await repo.create_concept(concept_create)
    await db_session.commit()

    # Retrieve by ID
    found = await repo.get_by_id(created.id)

    assert found is not None
    assert found.id == created.id
    assert found.name == sample_concept_data["name"]


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found(db_session):
    """Test get_by_id returns None for non-existent ID."""
    repo = ConceptRepository(db_session)

    found = await repo.get_by_id(uuid4())

    assert found is None


@pytest.mark.asyncio
async def test_get_all_concepts(db_session, test_course):
    """Test getting all concepts for a course."""
    repo = ConceptRepository(db_session)

    # Create concepts for test course
    for i in range(3):
        concept = Concept(
            course_id=test_course.id,
            name=f"Concept {i}",
            knowledge_area_id="ba-planning",
            corpus_section_ref=f"3.{i}",
        )
        db_session.add(concept)
    await db_session.commit()

    concepts = await repo.get_all_concepts(test_course.id)

    assert len(concepts) == 3


@pytest.mark.asyncio
async def test_get_all_concepts_returns_empty_for_other_course(db_session, test_course):
    """Test get_all_concepts returns empty for non-existent course."""
    repo = ConceptRepository(db_session)

    # Create a concept for test_course
    concept = Concept(
        course_id=test_course.id,
        name="Some Concept",
        knowledge_area_id="ba-planning",
    )
    db_session.add(concept)
    await db_session.commit()

    # Query for different course
    other_course_id = uuid4()
    concepts = await repo.get_all_concepts(other_course_id)

    assert concepts == []


@pytest.mark.asyncio
async def test_get_concepts_by_ka(db_session, test_course):
    """Test getting concepts filtered by knowledge area."""
    repo = ConceptRepository(db_session)

    # Create concepts for different KAs
    db_session.add(Concept(
        course_id=test_course.id,
        name="Planning Concept 1",
        knowledge_area_id="ba-planning",
    ))
    db_session.add(Concept(
        course_id=test_course.id,
        name="Planning Concept 2",
        knowledge_area_id="ba-planning",
    ))
    db_session.add(Concept(
        course_id=test_course.id,
        name="Elicitation Concept",
        knowledge_area_id="elicitation",
    ))
    await db_session.commit()

    # Query for ba-planning
    planning_concepts = await repo.get_concepts_by_ka(test_course.id, "ba-planning")
    assert len(planning_concepts) == 2

    # Query for elicitation
    elicitation_concepts = await repo.get_concepts_by_ka(test_course.id, "elicitation")
    assert len(elicitation_concepts) == 1


@pytest.mark.asyncio
async def test_get_concept_count(db_session, test_course):
    """Test getting concept count for a course."""
    repo = ConceptRepository(db_session)

    # Initially empty
    count = await repo.get_concept_count(test_course.id)
    assert count == 0

    # Add concepts
    for i in range(10):
        db_session.add(Concept(
            course_id=test_course.id,
            name=f"Concept {i}",
            knowledge_area_id="ba-planning",
        ))
    await db_session.commit()

    count = await repo.get_concept_count(test_course.id)
    assert count == 10


@pytest.mark.asyncio
async def test_get_concept_count_by_ka(db_session, test_course):
    """Test getting concept count grouped by knowledge area."""
    repo = ConceptRepository(db_session)

    # Add concepts to different KAs
    for _ in range(5):
        db_session.add(Concept(
            course_id=test_course.id,
            name=f"Planning {_}",
            knowledge_area_id="ba-planning",
        ))
    for _ in range(3):
        db_session.add(Concept(
            course_id=test_course.id,
            name=f"Elicitation {_}",
            knowledge_area_id="elicitation",
        ))
    for _ in range(2):
        db_session.add(Concept(
            course_id=test_course.id,
            name=f"Strategy {_}",
            knowledge_area_id="strategy",
        ))
    await db_session.commit()

    counts = await repo.get_concept_count_by_ka(test_course.id)

    assert counts["ba-planning"] == 5
    assert counts["elicitation"] == 3
    assert counts["strategy"] == 2


@pytest.mark.asyncio
async def test_get_by_section_ref(db_session, test_course):
    """Test getting concepts by section reference."""
    repo = ConceptRepository(db_session)

    # Add concepts with section refs
    db_session.add(Concept(
        course_id=test_course.id,
        name="Concept A",
        knowledge_area_id="ba-planning",
        corpus_section_ref="3.2.1",
    ))
    db_session.add(Concept(
        course_id=test_course.id,
        name="Concept B",
        knowledge_area_id="ba-planning",
        corpus_section_ref="3.2.1",
    ))
    db_session.add(Concept(
        course_id=test_course.id,
        name="Concept C",
        knowledge_area_id="ba-planning",
        corpus_section_ref="3.3.1",
    ))
    await db_session.commit()

    concepts = await repo.get_by_section_ref(test_course.id, "3.2.1")

    assert len(concepts) == 2
    assert all(c.corpus_section_ref == "3.2.1" for c in concepts)


@pytest.mark.asyncio
async def test_delete_all_for_course(db_session, test_course, sample_course_data):
    """Test deleting all concepts for a course."""
    repo = ConceptRepository(db_session)

    # Add concepts
    for i in range(5):
        db_session.add(Concept(
            course_id=test_course.id,
            name=f"Concept {i}",
            knowledge_area_id="ba-planning",
        ))
    await db_session.commit()

    # Verify they exist
    count_before = await repo.get_concept_count(test_course.id)
    assert count_before == 5

    # Delete all
    deleted = await repo.delete_all_for_course(test_course.id)
    await db_session.commit()

    assert deleted == 5

    # Verify they're gone
    count_after = await repo.get_concept_count(test_course.id)
    assert count_after == 0


@pytest.mark.asyncio
async def test_concept_course_relationship(db_session, test_course, sample_concept_data):
    """Test that concept properly relates to course."""
    repo = ConceptRepository(db_session)

    concept_create = ConceptCreate(course_id=test_course.id, **sample_concept_data)
    concept = await repo.create_concept(concept_create)
    await db_session.commit()
    await db_session.refresh(concept)

    # Access the relationship
    assert concept.course is not None
    assert concept.course.id == test_course.id
    assert concept.course.slug == "cbap"
