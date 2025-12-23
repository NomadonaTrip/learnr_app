"""
Integration tests for ReadingChunks.

Tests reading_chunks table creation, bulk insert, GIN index queries,
and section queries with multi-course support.
"""
from uuid import uuid4

import pytest

from src.models.course import Course
from src.repositories.reading_chunk_repository import ReadingChunkRepository
from src.schemas.reading_chunk import ChunkCreate


@pytest.fixture
async def cbap_course(db_session):
    """Create CBAP course fixture for integration tests."""
    course = Course(
        slug="cbap-test-chunks",
        name="CBAP Certification Test",
        description="Test course for reading chunk integration tests.",
        corpus_name="BABOK v3",
        knowledge_areas=[
            {"id": "ba-planning", "name": "BA Planning", "section_prefix": "3"},
            {"id": "elicitation", "name": "Elicitation", "section_prefix": "4"},
            {"id": "rlcm", "name": "RLCM", "section_prefix": "5"},
        ],
        is_active=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def other_course(db_session):
    """Create another course for cross-course filtering tests."""
    course = Course(
        slug="other-test-chunks",
        name="Other Certification Test",
        description="Test course for cross-course filtering.",
        corpus_name="Other Guide",
        knowledge_areas=[
            {"id": "ka-1", "name": "Knowledge Area 1", "section_prefix": "1"},
        ],
        is_active=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


# ============================================================================
# Test Table Creation via Migration
# ============================================================================


@pytest.mark.asyncio
async def test_reading_chunks_table_exists(db_session):
    """Test that reading_chunks table was created by migration."""
    from sqlalchemy import text

    result = await db_session.execute(
        text(
            "SELECT table_name FROM information_schema.tables WHERE table_name = 'reading_chunks'"
        )
    )
    row = result.fetchone()

    assert row is not None
    assert row[0] == "reading_chunks"


@pytest.mark.asyncio
async def test_reading_chunks_indexes_exist(db_session):
    """Test that expected indexes exist on reading_chunks table."""
    from sqlalchemy import text

    result = await db_session.execute(
        text(
            """
            SELECT indexname FROM pg_indexes
            WHERE tablename = 'reading_chunks'
            ORDER BY indexname
        """
        )
    )
    indexes = [row[0] for row in result.fetchall()]

    # Check for required indexes
    has_course_idx = any("course" in idx for idx in indexes)
    has_section_idx = any("section" in idx for idx in indexes)
    has_concepts_idx = any("concept_ids" in idx for idx in indexes)

    assert has_course_idx, f"Missing course index. Available: {indexes}"
    assert has_section_idx, f"Missing section index. Available: {indexes}"
    assert has_concepts_idx, f"Missing concepts GIN index. Available: {indexes}"


@pytest.mark.asyncio
async def test_reading_chunks_gin_index_type(db_session):
    """Test that concept_ids index uses GIN indexing."""
    from sqlalchemy import text

    result = await db_session.execute(
        text(
            """
            SELECT indexname, indexdef
            FROM pg_indexes
            WHERE tablename = 'reading_chunks'
            AND indexdef LIKE '%USING gin%'
        """
        )
    )
    gin_indexes = result.fetchall()

    # Should have at least 1 GIN index (for concept_ids array)
    assert len(gin_indexes) >= 1
    # Check that it's the concept_ids index
    assert any("concept_ids" in idx[0].lower() for idx in gin_indexes)


# ============================================================================
# Test Chunk CRUD with Course FK
# ============================================================================


@pytest.mark.asyncio
async def test_create_chunk_with_course_fk(db_session, cbap_course):
    """Test creating a reading chunk with proper course_id FK."""
    repo = ReadingChunkRepository(db_session)

    chunk = await repo.create_chunk(
        ChunkCreate(
            course_id=cbap_course.id,
            title="Stakeholder Analysis - Part 1",
            content="Content about stakeholder analysis...",
            corpus_section="3.2.1",
            knowledge_area_id="ba-planning",
            concept_ids=[],
            estimated_read_time_minutes=5,
            chunk_index=0,
        )
    )

    assert chunk.id is not None
    assert chunk.course_id == cbap_course.id
    assert chunk.title == "Stakeholder Analysis - Part 1"
    assert chunk.corpus_section == "3.2.1"


@pytest.mark.asyncio
async def test_chunk_cascade_delete_with_course(db_session, cbap_course):
    """Test that chunks are deleted when course is deleted (CASCADE)."""
    repo = ReadingChunkRepository(db_session)

    # Create a chunk
    chunk = await repo.create_chunk(
        ChunkCreate(
            course_id=cbap_course.id,
            title="Test Chunk",
            content="Test content",
            corpus_section="3.1",
            knowledge_area_id="ba-planning",
            concept_ids=[],
            estimated_read_time_minutes=1,
            chunk_index=0,
        )
    )
    chunk_id = chunk.id
    await db_session.commit()

    # Delete the course
    await db_session.delete(cbap_course)
    await db_session.commit()

    # Chunk should be deleted
    deleted_chunk = await repo.get_by_id(chunk_id)
    assert deleted_chunk is None


# ============================================================================
# Test Bulk Insert
# ============================================================================


@pytest.mark.asyncio
async def test_bulk_create_chunks(db_session, cbap_course):
    """Test bulk creating multiple chunks efficiently."""
    repo = ReadingChunkRepository(db_session)

    concept_id1 = uuid4()
    concept_id2 = uuid4()

    chunks = [
        ChunkCreate(
            course_id=cbap_course.id,
            title=f"Chunk {i}",
            content=f"Content for chunk {i}...",
            corpus_section=f"3.{i}.1",
            knowledge_area_id="ba-planning",
            concept_ids=[concept_id1] if i % 2 == 0 else [concept_id2],
            estimated_read_time_minutes=3,
            chunk_index=0,
        )
        for i in range(1, 11)  # Create 10 chunks
    ]

    count = await repo.bulk_create(chunks)
    await db_session.commit()

    assert count == 10

    # Verify chunks were created
    all_chunks = await repo.get_all_chunks(cbap_course.id)
    assert len(all_chunks) >= 10


# ============================================================================
# Test GIN Index Queries (Concept Array Queries)
# ============================================================================


@pytest.mark.asyncio
async def test_get_chunks_by_concept_gin_index(db_session, cbap_course):
    """Test GIN index query for concept_ids array."""
    repo = ReadingChunkRepository(db_session)

    concept_id = uuid4()

    # Create chunks with and without the concept
    await repo.bulk_create(
        [
            ChunkCreate(
                course_id=cbap_course.id,
                title="Chunk with Concept",
                content="Content...",
                corpus_section="3.1.1",
                knowledge_area_id="ba-planning",
                concept_ids=[concept_id],  # Contains target concept
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="Chunk without Concept",
                content="Content...",
                corpus_section="3.1.2",
                knowledge_area_id="ba-planning",
                concept_ids=[],  # No concepts
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="Chunk with Different Concept",
                content="Content...",
                corpus_section="3.1.3",
                knowledge_area_id="ba-planning",
                concept_ids=[uuid4()],  # Different concept
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
        ]
    )
    await db_session.commit()

    # Query using GIN index
    chunks = await repo.get_chunks_by_concept(concept_id, cbap_course.id)

    # Should only match the one chunk with the concept
    assert len(chunks) == 1
    assert chunks[0].title == "Chunk with Concept"
    assert concept_id in chunks[0].concept_ids


@pytest.mark.asyncio
async def test_get_chunks_by_concept_multiple_concepts(db_session, cbap_course):
    """Test GIN index with chunks having multiple concepts."""
    repo = ReadingChunkRepository(db_session)

    concept_a = uuid4()
    concept_b = uuid4()
    concept_c = uuid4()

    # Create chunk with multiple concepts
    await repo.create_chunk(
        ChunkCreate(
            course_id=cbap_course.id,
            title="Multi-Concept Chunk",
            content="Content covering multiple concepts...",
            corpus_section="3.2.1",
            knowledge_area_id="ba-planning",
            concept_ids=[concept_a, concept_b, concept_c],
            estimated_read_time_minutes=5,
            chunk_index=0,
        )
    )
    await db_session.commit()

    # Query for each concept - should all return the same chunk
    chunks_a = await repo.get_chunks_by_concept(concept_a, cbap_course.id)
    chunks_b = await repo.get_chunks_by_concept(concept_b, cbap_course.id)
    chunks_c = await repo.get_chunks_by_concept(concept_c, cbap_course.id)

    assert len(chunks_a) == 1
    assert len(chunks_b) == 1
    assert len(chunks_c) == 1
    assert chunks_a[0].id == chunks_b[0].id == chunks_c[0].id


# ============================================================================
# Test Section Queries
# ============================================================================


@pytest.mark.asyncio
async def test_get_chunks_by_section(db_session, cbap_course):
    """Test querying chunks by corpus section reference."""
    repo = ReadingChunkRepository(db_session)

    # Create chunks in different sections
    await repo.bulk_create(
        [
            ChunkCreate(
                course_id=cbap_course.id,
                title="Chunk 3.2.1 - Part 1",
                content="Content...",
                corpus_section="3.2.1",
                knowledge_area_id="ba-planning",
                concept_ids=[],
                estimated_read_time_minutes=3,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="Chunk 3.2.1 - Part 2",
                content="Content...",
                corpus_section="3.2.1",
                knowledge_area_id="ba-planning",
                concept_ids=[],
                estimated_read_time_minutes=3,
                chunk_index=1,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="Chunk 3.2.2",
                content="Content...",
                corpus_section="3.2.2",
                knowledge_area_id="ba-planning",
                concept_ids=[],
                estimated_read_time_minutes=3,
                chunk_index=0,
            ),
        ]
    )
    await db_session.commit()

    # Query for section 3.2.1
    chunks = await repo.get_chunks_by_section("3.2.1", cbap_course.id)

    assert len(chunks) == 2
    assert all(c.corpus_section == "3.2.1" for c in chunks)
    # Should be ordered by chunk_index
    assert chunks[0].chunk_index == 0
    assert chunks[1].chunk_index == 1


@pytest.mark.asyncio
async def test_get_chunks_by_knowledge_area(db_session, cbap_course):
    """Test querying chunks by knowledge area."""
    repo = ReadingChunkRepository(db_session)

    # Create chunks in different KAs
    await repo.bulk_create(
        [
            ChunkCreate(
                course_id=cbap_course.id,
                title="BA Planning Chunk",
                content="Content...",
                corpus_section="3.1.1",
                knowledge_area_id="ba-planning",
                concept_ids=[],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="Elicitation Chunk",
                content="Content...",
                corpus_section="4.1.1",
                knowledge_area_id="elicitation",
                concept_ids=[],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
        ]
    )
    await db_session.commit()

    # Query for ba-planning
    chunks = await repo.get_chunks_by_knowledge_area("ba-planning", cbap_course.id)

    assert len(chunks) == 1
    assert chunks[0].knowledge_area_id == "ba-planning"


# ============================================================================
# Test Multi-Course Filtering
# ============================================================================


@pytest.mark.asyncio
async def test_multi_course_filtering(db_session, cbap_course, other_course):
    """Test that chunks are properly filtered by course_id."""
    repo = ReadingChunkRepository(db_session)

    concept_id = uuid4()

    # Create chunks for both courses with same concept
    await repo.bulk_create(
        [
            ChunkCreate(
                course_id=cbap_course.id,
                title="CBAP Chunk",
                content="Content...",
                corpus_section="3.1.1",
                knowledge_area_id="ba-planning",
                concept_ids=[concept_id],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=other_course.id,
                title="Other Course Chunk",
                content="Content...",
                corpus_section="1.1.1",
                knowledge_area_id="ka-1",
                concept_ids=[concept_id],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
        ]
    )
    await db_session.commit()

    # Query for CBAP course
    cbap_chunks = await repo.get_chunks_by_concept(concept_id, cbap_course.id)
    assert len(cbap_chunks) == 1
    assert cbap_chunks[0].course_id == cbap_course.id

    # Query for other course
    other_chunks = await repo.get_chunks_by_concept(concept_id, other_course.id)
    assert len(other_chunks) == 1
    assert other_chunks[0].course_id == other_course.id


# ============================================================================
# Test Aggregation Queries
# ============================================================================


@pytest.mark.asyncio
async def test_get_chunk_count(db_session, cbap_course):
    """Test chunk count aggregation."""
    repo = ReadingChunkRepository(db_session)

    await repo.bulk_create(
        [
            ChunkCreate(
                course_id=cbap_course.id,
                title=f"Chunk {i}",
                content="Content...",
                corpus_section=f"3.{i}",
                knowledge_area_id="ba-planning",
                concept_ids=[],
                estimated_read_time_minutes=2,
                chunk_index=0,
            )
            for i in range(1, 6)
        ]
    )
    await db_session.commit()

    count = await repo.get_chunk_count(cbap_course.id)
    assert count == 5


@pytest.mark.asyncio
async def test_get_chunk_count_by_ka(db_session, cbap_course):
    """Test chunk count grouped by knowledge area."""
    repo = ReadingChunkRepository(db_session)

    await repo.bulk_create(
        [
            ChunkCreate(
                course_id=cbap_course.id,
                title="BA Planning Chunk 1",
                content="Content...",
                corpus_section="3.1",
                knowledge_area_id="ba-planning",
                concept_ids=[],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="BA Planning Chunk 2",
                content="Content...",
                corpus_section="3.2",
                knowledge_area_id="ba-planning",
                concept_ids=[],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="Elicitation Chunk",
                content="Content...",
                corpus_section="4.1",
                knowledge_area_id="elicitation",
                concept_ids=[],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
        ]
    )
    await db_session.commit()

    counts = await repo.get_chunk_count_by_ka(cbap_course.id)

    assert counts["ba-planning"] == 2
    assert counts["elicitation"] == 1


@pytest.mark.asyncio
async def test_get_chunks_without_concepts(db_session, cbap_course):
    """Test finding orphan chunks (chunks with no concepts)."""
    repo = ReadingChunkRepository(db_session)

    await repo.bulk_create(
        [
            ChunkCreate(
                course_id=cbap_course.id,
                title="Chunk with Concepts",
                content="Content...",
                corpus_section="3.1",
                knowledge_area_id="ba-planning",
                concept_ids=[uuid4()],
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
            ChunkCreate(
                course_id=cbap_course.id,
                title="Orphan Chunk",
                content="Content...",
                corpus_section="3.2",
                knowledge_area_id="ba-planning",
                concept_ids=[],  # No concepts
                estimated_read_time_minutes=2,
                chunk_index=0,
            ),
        ]
    )
    await db_session.commit()

    orphans = await repo.get_chunks_without_concepts(cbap_course.id)

    assert len(orphans) == 1
    assert orphans[0].title == "Orphan Chunk"
    assert len(orphans[0].concept_ids) == 0
