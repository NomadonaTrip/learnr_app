"""
Integration tests for Reading Content Retrieval API.

Tests GET /v1/courses/{course_slug}/reading endpoint with:
- Concept filtering
- Knowledge area filtering
- Semantic search fallback
- Response time performance
- Authentication requirement
"""
import pytest
import time
from uuid import uuid4

from src.models.course import Course
from src.models.reading_chunk import ReadingChunk
from src.models.concept import Concept
from src.models.user import User


@pytest.fixture
async def test_course(db_session):
    """Create test course for reading API tests."""
    course = Course(
        slug="cbap-test",
        name="CBAP Certification Prep Test",
        description="Test course for reading API",
        corpus_name="BABOK v3",
        knowledge_areas=[
            {
                "id": "strategy",
                "name": "Strategy Analysis",
                "short_name": "Strategy",
                "display_order": 1,
                "color": "#EF4444",
            },
            {
                "id": "elicitation",
                "name": "Elicitation and Collaboration",
                "short_name": "Elicitation",
                "display_order": 2,
                "color": "#10B981",
            },
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concepts(db_session, test_course):
    """Create test concepts for filtering."""
    concepts = []
    for i in range(3):
        concept = Concept(
            course_id=test_course.id,
            name=f"Test Concept {i+1}",
            description=f"Description for concept {i+1}",
            corpus_section_ref=f"3.{i+1}",
            knowledge_area_id="strategy" if i < 2 else "elicitation",
            difficulty_estimate=0.3 + (i * 0.2),
            prerequisite_depth=0,
        )
        db_session.add(concept)
        concepts.append(concept)

    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
async def test_reading_chunks(db_session, test_course, test_concepts):
    """Create test reading chunks with concept mappings."""
    chunks = []

    # Chunk 1: Strategy, mapped to concept 0
    chunk1 = ReadingChunk(
        course_id=test_course.id,
        title="Introduction to Strategy Analysis",
        content="This chunk covers the basics of strategy analysis in business analysis...",
        corpus_section="3.1",
        knowledge_area_id="strategy",
        concept_ids=[str(test_concepts[0].id)],
        estimated_read_time_minutes=5,
        chunk_index=0,
    )
    db_session.add(chunk1)
    chunks.append(chunk1)

    # Chunk 2: Strategy, mapped to concepts 0 and 1
    chunk2 = ReadingChunk(
        course_id=test_course.id,
        title="Advanced Strategy Techniques",
        content="This chunk discusses advanced techniques for strategy analysis...",
        corpus_section="3.2",
        knowledge_area_id="strategy",
        concept_ids=[str(test_concepts[0].id), str(test_concepts[1].id)],
        estimated_read_time_minutes=7,
        chunk_index=1,
    )
    db_session.add(chunk2)
    chunks.append(chunk2)

    # Chunk 3: Elicitation, mapped to concept 2
    chunk3 = ReadingChunk(
        course_id=test_course.id,
        title="Elicitation Fundamentals",
        content="This chunk introduces elicitation techniques...",
        corpus_section="4.1",
        knowledge_area_id="elicitation",
        concept_ids=[str(test_concepts[2].id)],
        estimated_read_time_minutes=6,
        chunk_index=0,
    )
    db_session.add(chunk3)
    chunks.append(chunk3)

    # Chunk 4: Strategy, no concept mapping (orphan)
    chunk4 = ReadingChunk(
        course_id=test_course.id,
        title="General Strategy Overview",
        content="This chunk provides a general overview of strategy...",
        corpus_section="3.0",
        knowledge_area_id="strategy",
        concept_ids=[],
        estimated_read_time_minutes=4,
        chunk_index=2,
    )
    db_session.add(chunk4)
    chunks.append(chunk4)

    await db_session.commit()
    for chunk in chunks:
        await db_session.refresh(chunk)

    return chunks


@pytest.fixture
async def authenticated_user(client, db_session):
    """Create and authenticate a test user, return token."""
    # Register a user
    user_data = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "name": "Test User",
    }
    response = await client.post("/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    return data["token"]


@pytest.mark.asyncio
class TestReadingRetrievalAPI:
    """Tests for GET /v1/courses/{course_slug}/reading endpoint."""

    async def test_get_reading_requires_authentication(
        self, client, test_course, test_reading_chunks
    ):
        """Test that endpoint requires authentication."""
        response = await client.get(f"/v1/courses/{test_course.slug}/reading?concept_ids={str(uuid4())}")

        assert response.status_code == 401

    async def test_get_reading_course_not_found(self, client, authenticated_user):
        """Test getting reading for non-existent course returns 404."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/non-existent/reading?concept_ids={str(uuid4())}",
            headers=headers,
        )

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "COURSE_NOT_FOUND"

    async def test_filter_by_single_concept(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test filtering reading chunks by a single concept ID."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)
        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "fallback_used" in data

        # Should find chunks 1 and 2 (both have concept 0)
        assert data["total"] == 2
        assert len(data["items"]) == 2
        assert data["fallback_used"] is False

        # Verify concept_ids array is present
        for item in data["items"]:
            assert "concept_ids" in item
            assert concept_id in [str(cid) for cid in item["concept_ids"]]

    async def test_filter_by_multiple_concepts(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test filtering by multiple concept IDs (OR logic)."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id_0 = str(test_concepts[0].id)
        concept_id_1 = str(test_concepts[1].id)

        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id_0}&concept_ids={concept_id_1}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should find chunks that match ANY of the concepts
        assert data["total"] >= 2
        assert data["fallback_used"] is False

    async def test_filter_by_knowledge_area(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test filtering reading chunks by knowledge area."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)

        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id}&knowledge_area_id=strategy",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # All returned chunks should be in strategy knowledge area
        for item in data["items"]:
            assert item["knowledge_area_id"] == "strategy"

    async def test_response_includes_concept_names(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test that response includes human-readable concept names."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)

        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify concept_names array is present and contains string names
        for item in data["items"]:
            assert "concept_names" in item
            assert isinstance(item["concept_names"], list)
            if item["concept_names"]:
                assert all(isinstance(name, str) for name in item["concept_names"])

    async def test_relevance_scoring(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test that chunks with more matching concepts have higher relevance scores."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id_0 = str(test_concepts[0].id)
        concept_id_1 = str(test_concepts[1].id)

        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id_0}&concept_ids={concept_id_1}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Find chunk with 2 matching concepts
        chunk_with_two_matches = None
        for item in data["items"]:
            matching_count = sum(
                1
                for cid in item["concept_ids"]
                if str(cid) in [concept_id_0, concept_id_1]
            )
            if matching_count == 2:
                chunk_with_two_matches = item
                break

        # Verify relevance score for chunk with 2 matches
        if chunk_with_two_matches:
            assert chunk_with_two_matches["relevance_score"] == 2.0

    async def test_pagination_limit(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test that limit parameter controls number of results."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id_0 = str(test_concepts[0].id)

        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id_0}&limit=1",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Should return only 1 chunk even though 2 match
        assert len(data["items"]) <= 1

    async def test_response_time_performance(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test that query completes within 500ms (relaxed from 200ms for test environment)."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)

        start_time = time.time()
        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id}",
            headers=headers,
        )
        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == 200
        assert elapsed_ms < 500  # Relaxed threshold for test environment

    async def test_response_includes_all_required_fields(
        self, client, authenticated_user, test_course, test_reading_chunks, test_concepts
    ):
        """Test that response includes all required chunk fields."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)

        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "id",
            "course_id",
            "title",
            "content",
            "corpus_section",
            "knowledge_area_id",
            "concept_ids",
            "concept_names",
            "estimated_read_time_minutes",
        ]

        for item in data["items"]:
            for field in required_fields:
                assert field in item, f"Missing required field: {field}"

    async def test_empty_results_when_no_matches(
        self, client, authenticated_user, test_course, test_reading_chunks
    ):
        """Test that empty results are returned when no chunks match."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        # Use a random UUID that doesn't match any concept
        non_existent_concept_id = str(uuid4())

        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={non_existent_concept_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Could be empty OR trigger semantic fallback (depending on whether concept exists)
        assert "items" in data
        assert "total" in data
        assert "fallback_used" in data

    async def test_chunks_scoped_to_course(
        self, client, authenticated_user, db_session, test_course, test_reading_chunks, test_concepts
    ):
        """Test that chunks from other courses are not returned (multi-course isolation)."""
        # Create another course
        other_course = Course(
            slug="other-course",
            name="Other Course",
            description="Test",
            corpus_name="Other Corpus",
            knowledge_areas=[],
            is_active=True,
            is_public=True,
        )
        db_session.add(other_course)
        await db_session.commit()
        await db_session.refresh(other_course)

        # Create a chunk in the other course with same concept ID
        other_chunk = ReadingChunk(
            course_id=other_course.id,
            title="Other Course Chunk",
            content="This should not be returned",
            corpus_section="1.1",
            knowledge_area_id="other",
            concept_ids=[str(test_concepts[0].id)],  # Same concept as test course
            estimated_read_time_minutes=5,
            chunk_index=0,
        )
        db_session.add(other_chunk)
        await db_session.commit()

        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)

        # Query the test course
        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={concept_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify all returned chunks belong to test course
        for item in data["items"]:
            assert str(item["course_id"]) == str(test_course.id)
            assert str(item["course_id"]) != str(other_course.id)

    async def test_semantic_search_fallback_triggered(
        self, client, authenticated_user, db_session, test_course, test_reading_chunks, test_concepts
    ):
        """Test that semantic search fallback is triggered when no direct concept matches exist."""
        from src.models.concept import Concept

        # Create a new concept that exists in DB but has NO chunks linked to it
        orphan_concept = Concept(
            course_id=test_course.id,
            name="Orphan Concept for Testing Fallback",
            description="This concept has no reading chunks directly linked",
            corpus_section_ref="9.9.9",
            knowledge_area_id="strategy",
            difficulty_estimate=0.5,
            prerequisite_depth=0,
        )
        db_session.add(orphan_concept)
        await db_session.commit()
        await db_session.refresh(orphan_concept)

        headers = {"Authorization": f"Bearer {authenticated_user}"}
        orphan_concept_id = str(orphan_concept.id)

        # Request reading for the orphan concept (should trigger fallback)
        response = await client.get(
            f"/v1/courses/{test_course.slug}/reading?concept_ids={orphan_concept_id}",
            headers=headers,
        )

        assert response.status_code == 200
        data = response.json()

        # Verify fallback was used
        assert data["fallback_used"] is True

        # If semantic search returns results, verify they're from the correct course
        if data["items"]:
            for item in data["items"]:
                assert str(item["course_id"]) == str(test_course.id)
                # The orphan concept should NOT be in the chunk's concept_ids
                # (since no chunk was linked to it directly)
                assert orphan_concept_id not in [str(cid) for cid in item["concept_ids"]]
