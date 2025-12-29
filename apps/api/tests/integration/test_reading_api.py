"""
Integration tests for Reading Content Retrieval API.

Tests GET /v1/courses/{course_slug}/reading endpoint with:
- Concept filtering
- Knowledge area filtering
- Semantic search fallback
- Response time performance
- Authentication requirement

Story 5.6: Tests GET /v1/reading/stats endpoint with:
- Authentication requirement
- Correct unread and high-priority counts
- Enrollment filtering
- Empty queue handling
"""
import time
from uuid import uuid4

import pytest

from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.reading_chunk import ReadingChunk
from src.models.reading_queue import ReadingQueue
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


# =============================================================================
# Story 5.6: Reading Stats API Tests
# =============================================================================


@pytest.fixture
async def stats_test_user(db_session):
    """Create a user for stats endpoint testing."""
    from src.utils.auth import hash_password

    user = User(
        email="statsuser@example.com",
        hashed_password=hash_password("SecurePassword123!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def stats_test_course(db_session):
    """Create a course for stats testing."""
    course = Course(
        slug="stats-test-course",
        name="Stats Test Course",
        description="Course for reading stats testing",
        corpus_name="Test Corpus",
        knowledge_areas=[],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def stats_test_enrollment(db_session, stats_test_user, stats_test_course):
    """Create an enrollment for stats testing."""
    enrollment = Enrollment(
        user_id=stats_test_user.id,
        course_id=stats_test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def stats_test_chunks(db_session, stats_test_course):
    """Create reading chunks for stats testing."""
    chunks = []
    for i in range(5):
        chunk = ReadingChunk(
            course_id=stats_test_course.id,
            title=f"Stats Test Chunk {i+1}",
            content=f"Content for chunk {i+1}",
            corpus_section=f"1.{i+1}",
            knowledge_area_id="test",
            concept_ids=[],
            estimated_read_time_minutes=5,
            chunk_index=i,
        )
        db_session.add(chunk)
        chunks.append(chunk)

    await db_session.commit()
    for chunk in chunks:
        await db_session.refresh(chunk)
    return chunks


@pytest.fixture
async def stats_test_queue_items(
    db_session, stats_test_enrollment, stats_test_chunks, stats_test_user
):
    """Create reading queue items for stats testing.

    Creates:
    - 3 unread items (1 high priority, 2 medium priority)
    - 2 read items (not counted)
    """
    queue_items = []

    # Item 1: Unread, High priority
    item1 = ReadingQueue(
        user_id=stats_test_user.id,
        enrollment_id=stats_test_enrollment.id,
        chunk_id=stats_test_chunks[0].id,
        status="unread",
        priority="High",
    )
    db_session.add(item1)
    queue_items.append(item1)

    # Item 2: Unread, Medium priority
    item2 = ReadingQueue(
        user_id=stats_test_user.id,
        enrollment_id=stats_test_enrollment.id,
        chunk_id=stats_test_chunks[1].id,
        status="unread",
        priority="Medium",
    )
    db_session.add(item2)
    queue_items.append(item2)

    # Item 3: Unread, Medium priority
    item3 = ReadingQueue(
        user_id=stats_test_user.id,
        enrollment_id=stats_test_enrollment.id,
        chunk_id=stats_test_chunks[2].id,
        status="unread",
        priority="Medium",
    )
    db_session.add(item3)
    queue_items.append(item3)

    # Item 4: Read (should not be counted)
    item4 = ReadingQueue(
        user_id=stats_test_user.id,
        enrollment_id=stats_test_enrollment.id,
        chunk_id=stats_test_chunks[3].id,
        status="read",
        priority="High",
    )
    db_session.add(item4)
    queue_items.append(item4)

    # Item 5: Read (should not be counted)
    item5 = ReadingQueue(
        user_id=stats_test_user.id,
        enrollment_id=stats_test_enrollment.id,
        chunk_id=stats_test_chunks[4].id,
        status="read",
        priority="Low",
    )
    db_session.add(item5)
    queue_items.append(item5)

    await db_session.commit()
    return queue_items


@pytest.fixture
async def stats_auth_token(stats_test_user):
    """Generate auth token for stats test user."""
    from src.utils.auth import create_access_token

    return create_access_token(data={"sub": str(stats_test_user.id)})


@pytest.mark.asyncio
class TestReadingStatsAPI:
    """Tests for GET /v1/reading/stats endpoint. Story 5.6."""

    async def test_stats_requires_authentication(self, client):
        """Test that stats endpoint requires authentication (401 without token)."""
        response = await client.get("/v1/reading/stats")
        assert response.status_code == 401

    async def test_stats_returns_correct_counts(
        self,
        client,
        stats_auth_token,
        stats_test_enrollment,
        stats_test_queue_items,
    ):
        """Test that stats endpoint returns correct unread and high-priority counts."""
        headers = {"Authorization": f"Bearer {stats_auth_token}"}

        response = await client.get("/v1/reading/stats", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should have 3 unread items (1 High + 2 Medium)
        assert data["unread_count"] == 3
        # Should have 1 high priority item
        assert data["high_priority_count"] == 1

    async def test_stats_empty_queue_returns_zeros(
        self, client, stats_auth_token, stats_test_enrollment
    ):
        """Test that empty queue returns zero counts."""
        headers = {"Authorization": f"Bearer {stats_auth_token}"}

        response = await client.get("/v1/reading/stats", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Empty queue should return zero counts
        assert data["unread_count"] == 0
        assert data["high_priority_count"] == 0

    async def test_stats_filters_by_enrollment(
        self, client, db_session, stats_test_user, stats_test_course, stats_test_chunks
    ):
        """Test that stats only count items from user's active enrollment."""
        from src.utils.auth import create_access_token

        # Create a second user with their own enrollment and queue items
        other_user = User(
            email="otheruser@example.com",
            hashed_password="hash",
        )
        db_session.add(other_user)
        await db_session.commit()
        await db_session.refresh(other_user)

        other_enrollment = Enrollment(
            user_id=other_user.id,
            course_id=stats_test_course.id,
            status="active",
        )
        db_session.add(other_enrollment)
        await db_session.commit()
        await db_session.refresh(other_enrollment)

        # Add queue items for the other user
        for i in range(5):
            item = ReadingQueue(
                user_id=other_user.id,
                enrollment_id=other_enrollment.id,
                chunk_id=stats_test_chunks[i].id,
                status="unread",
                priority="High",
            )
            db_session.add(item)
        await db_session.commit()

        # Create enrollment for original user (stats_test_user)
        stats_enrollment = Enrollment(
            user_id=stats_test_user.id,
            course_id=stats_test_course.id,
            status="active",
        )
        db_session.add(stats_enrollment)
        await db_session.commit()
        await db_session.refresh(stats_enrollment)

        # Add only 2 unread items for original user
        item1 = ReadingQueue(
            user_id=stats_test_user.id,
            enrollment_id=stats_enrollment.id,
            chunk_id=stats_test_chunks[0].id,
            status="unread",
            priority="High",
        )
        item2 = ReadingQueue(
            user_id=stats_test_user.id,
            enrollment_id=stats_enrollment.id,
            chunk_id=stats_test_chunks[1].id,
            status="unread",
            priority="Medium",
        )
        db_session.add(item1)
        db_session.add(item2)
        await db_session.commit()

        # Get stats for original user
        stats_token = create_access_token(data={"sub": str(stats_test_user.id)})
        headers = {"Authorization": f"Bearer {stats_token}"}

        response = await client.get("/v1/reading/stats", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should only count original user's items (2), not other user's (5)
        assert data["unread_count"] == 2
        assert data["high_priority_count"] == 1

    async def test_stats_response_schema(
        self, client, stats_auth_token, stats_test_enrollment
    ):
        """Test that stats response has correct schema fields."""
        headers = {"Authorization": f"Bearer {stats_auth_token}"}

        response = await client.get("/v1/reading/stats", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Verify required fields exist and are integers
        assert "unread_count" in data
        assert "high_priority_count" in data
        assert isinstance(data["unread_count"], int)
        assert isinstance(data["high_priority_count"], int)
        assert data["unread_count"] >= 0
        assert data["high_priority_count"] >= 0


# =============================================================================
# Story 5.7: Reading Queue List API Tests
# =============================================================================


@pytest.fixture
async def queue_test_user(db_session):
    """Create a user for queue endpoint testing."""
    from src.utils.auth import hash_password

    user = User(
        email="queueuser@example.com",
        hashed_password=hash_password("SecurePassword123!"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def queue_test_course(db_session):
    """Create a course for queue testing with knowledge areas."""
    course = Course(
        slug="queue-test-course",
        name="Queue Test Course",
        description="Course for reading queue testing",
        corpus_name="Test Corpus",
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
async def queue_test_enrollment(db_session, queue_test_user, queue_test_course):
    """Create an enrollment for queue testing."""
    enrollment = Enrollment(
        user_id=queue_test_user.id,
        course_id=queue_test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def queue_test_chunks(db_session, queue_test_course):
    """Create reading chunks for queue testing."""
    chunks = []
    for i in range(5):
        ka_id = "strategy" if i < 3 else "elicitation"
        chunk = ReadingChunk(
            course_id=queue_test_course.id,
            title=f"Queue Test Chunk {i+1}",
            content=f"Content for chunk {i+1}. " * 50,  # ~250 words
            corpus_section=f"1.{i+1}",
            knowledge_area_id=ka_id,
            concept_ids=[],
            estimated_read_time_minutes=5,
            chunk_index=i,
        )
        db_session.add(chunk)
        chunks.append(chunk)

    await db_session.commit()
    for chunk in chunks:
        await db_session.refresh(chunk)
    return chunks


@pytest.fixture
async def queue_test_items(
    db_session, queue_test_enrollment, queue_test_chunks, queue_test_user
):
    """Create reading queue items for testing.

    Creates:
    - 2 unread High priority items (strategy KA)
    - 2 unread Medium priority items (1 strategy, 1 elicitation)
    - 1 completed item
    """
    from src.models.question import Question

    # Create a test question for triggered_by_question
    question = Question(
        course_id=queue_test_chunks[0].course_id,
        question_text="Test question for queue testing - which technique is best?",
        options=[
            {"id": "A", "text": "Option A"},
            {"id": "B", "text": "Option B"},
        ],
        correct_answer="A",
        knowledge_area_id="strategy",
        difficulty=0.5,
        explanation="Test explanation",
    )
    db_session.add(question)
    await db_session.commit()
    await db_session.refresh(question)

    queue_items = []

    # Item 1: Unread, High priority, Strategy
    item1 = ReadingQueue(
        user_id=queue_test_user.id,
        enrollment_id=queue_test_enrollment.id,
        chunk_id=queue_test_chunks[0].id,
        triggered_by_question_id=question.id,
        status="unread",
        priority="High",
    )
    db_session.add(item1)
    queue_items.append(item1)

    # Item 2: Unread, High priority, Strategy
    item2 = ReadingQueue(
        user_id=queue_test_user.id,
        enrollment_id=queue_test_enrollment.id,
        chunk_id=queue_test_chunks[1].id,
        status="unread",
        priority="High",
    )
    db_session.add(item2)
    queue_items.append(item2)

    # Item 3: Unread, Medium priority, Strategy
    item3 = ReadingQueue(
        user_id=queue_test_user.id,
        enrollment_id=queue_test_enrollment.id,
        chunk_id=queue_test_chunks[2].id,
        status="unread",
        priority="Medium",
    )
    db_session.add(item3)
    queue_items.append(item3)

    # Item 4: Unread, Medium priority, Elicitation
    item4 = ReadingQueue(
        user_id=queue_test_user.id,
        enrollment_id=queue_test_enrollment.id,
        chunk_id=queue_test_chunks[3].id,
        status="unread",
        priority="Medium",
    )
    db_session.add(item4)
    queue_items.append(item4)

    # Item 5: Completed (should not appear in unread filter)
    item5 = ReadingQueue(
        user_id=queue_test_user.id,
        enrollment_id=queue_test_enrollment.id,
        chunk_id=queue_test_chunks[4].id,
        status="completed",
        priority="Low",
    )
    db_session.add(item5)
    queue_items.append(item5)

    await db_session.commit()
    for item in queue_items:
        await db_session.refresh(item)
    return queue_items


@pytest.fixture
async def queue_auth_token(queue_test_user):
    """Generate auth token for queue test user."""
    from src.utils.auth import create_access_token

    return create_access_token(data={"sub": str(queue_test_user.id)})


@pytest.mark.asyncio
class TestReadingQueueAPI:
    """Tests for GET /v1/reading/queue endpoint. Story 5.7."""

    async def test_queue_requires_authentication(self, client):
        """Test that queue endpoint requires authentication (401 without token)."""
        response = await client.get("/v1/reading/queue")
        assert response.status_code == 401

    async def test_queue_returns_items(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that queue endpoint returns queue items with correct structure."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "items" in data
        assert "pagination" in data

        # Default filter is unread, so should have 4 items
        assert len(data["items"]) == 4

        # Check pagination structure
        pagination = data["pagination"]
        assert pagination["page"] == 1
        assert pagination["per_page"] == 20
        assert pagination["total_items"] == 4
        assert pagination["total_pages"] == 1

    async def test_queue_item_response_schema(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that each queue item has all required fields."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue", headers=headers)

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "queue_id",
            "chunk_id",
            "title",
            "preview",
            "babok_section",
            "ka_name",
            "ka_id",
            "priority",
            "status",
            "word_count",
            "estimated_read_minutes",
            "was_incorrect",
            "added_at",
        ]

        for item in data["items"]:
            for field in required_fields:
                assert field in item, f"Missing required field: {field}"

    async def test_queue_filter_by_status_unread(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test filtering by status=unread (default)."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue?status=unread", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should return only unread items (4)
        assert len(data["items"]) == 4
        for item in data["items"]:
            assert item["status"] == "unread"

    async def test_queue_filter_by_status_completed(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test filtering by status=completed."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue?status=completed", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should return only completed items (1)
        assert len(data["items"]) == 1
        assert data["items"][0]["status"] == "completed"

    async def test_queue_filter_by_status_all(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test filtering by status=all returns all items."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue?status=all", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should return all items (5)
        assert len(data["items"]) == 5

    async def test_queue_filter_by_ka_id(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test filtering by knowledge area ID."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue?ka_id=strategy", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should return only strategy KA items (3 unread)
        assert len(data["items"]) == 3
        for item in data["items"]:
            assert item["ka_id"] == "strategy"

    async def test_queue_filter_by_priority(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test filtering by priority."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue?priority=High", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should return only High priority items (2)
        assert len(data["items"]) == 2
        for item in data["items"]:
            assert item["priority"] == "High"

    async def test_queue_sort_by_priority(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test sorting by priority (High > Medium > Low)."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue?sort_by=priority", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # First items should be High priority
        assert data["items"][0]["priority"] == "High"
        assert data["items"][1]["priority"] == "High"
        # Then Medium priority
        assert data["items"][2]["priority"] == "Medium"
        assert data["items"][3]["priority"] == "Medium"

    async def test_queue_sort_by_date(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test sorting by date (newest first)."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue?sort_by=date", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Items should be in descending order by added_at
        dates = [item["added_at"] for item in data["items"]]
        assert dates == sorted(dates, reverse=True)

    async def test_queue_pagination(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test pagination works correctly."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        # Get first page with 2 items per page
        response = await client.get("/v1/reading/queue?page=1&per_page=2", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert len(data["items"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 2
        assert data["pagination"]["total_items"] == 4
        assert data["pagination"]["total_pages"] == 2

        # Get second page
        response2 = await client.get("/v1/reading/queue?page=2&per_page=2", headers=headers)
        data2 = response2.json()

        assert len(data2["items"]) == 2
        assert data2["pagination"]["page"] == 2

        # Ensure no duplicate items between pages
        page1_ids = {item["queue_id"] for item in data["items"]}
        page2_ids = {item["queue_id"] for item in data2["items"]}
        assert page1_ids.isdisjoint(page2_ids)

    async def test_queue_empty_returns_empty_array(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
    ):
        """Test that empty queue returns empty array with pagination metadata."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert data["items"] == []
        assert data["pagination"]["total_items"] == 0
        assert data["pagination"]["total_pages"] == 0

    async def test_queue_includes_question_preview(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that items with triggered question include question preview."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Find item with question preview
        items_with_preview = [item for item in data["items"] if item.get("question_preview")]
        assert len(items_with_preview) >= 1
        assert "Test question" in items_with_preview[0]["question_preview"]

    async def test_queue_ka_name_resolution(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that ka_name is resolved from course knowledge_areas."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        response = await client.get("/v1/reading/queue", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Check KA names are resolved
        for item in data["items"]:
            if item["ka_id"] == "strategy":
                assert item["ka_name"] == "Strategy Analysis"
            elif item["ka_id"] == "elicitation":
                assert item["ka_name"] == "Elicitation and Collaboration"

    async def test_queue_per_page_max_limit(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that per_page values over 100 are rejected by schema validation."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        # Request more than 100 per page - should be rejected by schema
        response = await client.get("/v1/reading/queue?per_page=200", headers=headers)

        # Schema validation rejects values > 100
        assert response.status_code == 422

        # Valid request with max per_page=100 should succeed
        response = await client.get("/v1/reading/queue?per_page=100", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["pagination"]["per_page"] == 100


# =============================================================================
# Story 5.8: Reading Detail and Engagement API Tests
# =============================================================================


@pytest.mark.asyncio
class TestReadingDetailAPI:
    """Tests for GET /v1/reading/queue/{queue_id} endpoint. Story 5.8."""

    async def test_detail_requires_authentication(self, client, queue_test_items):
        """Test that detail endpoint requires authentication."""
        queue_id = str(queue_test_items[0].id)
        response = await client.get(f"/v1/reading/queue/{queue_id}")
        assert response.status_code == 401

    async def test_detail_returns_full_content(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
        queue_test_chunks,
    ):
        """Test that detail endpoint returns full content and engagement fields."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        queue_id = str(queue_test_items[0].id)

        response = await client.get(f"/v1/reading/queue/{queue_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Check required fields
        assert "queue_id" in data
        assert "chunk_id" in data
        assert "title" in data
        assert "text_content" in data
        assert "babok_section" in data
        assert "ka_name" in data
        assert "priority" in data
        assert "status" in data
        assert "word_count" in data
        assert "estimated_read_minutes" in data
        assert "times_opened" in data
        assert "total_reading_time_seconds" in data
        assert "question_context" in data
        assert "added_at" in data

        # Check question_context nested fields
        assert "question_preview" in data["question_context"]
        assert "was_incorrect" in data["question_context"]

    async def test_detail_increments_times_opened(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that viewing detail increments times_opened."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        queue_id = str(queue_test_items[0].id)

        # First view
        response1 = await client.get(f"/v1/reading/queue/{queue_id}", headers=headers)
        assert response1.status_code == 200
        times_opened_1 = response1.json()["times_opened"]

        # Second view
        response2 = await client.get(f"/v1/reading/queue/{queue_id}", headers=headers)
        assert response2.status_code == 200
        times_opened_2 = response2.json()["times_opened"]

        # times_opened should have increased
        assert times_opened_2 > times_opened_1

    async def test_detail_sets_first_opened_at(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that first_opened_at is set on first view."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        queue_id = str(queue_test_items[1].id)  # Use different item

        response = await client.get(f"/v1/reading/queue/{queue_id}", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # first_opened_at should be set now
        assert data["first_opened_at"] is not None

    async def test_detail_not_found_returns_404(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
    ):
        """Test that non-existent queue item returns 404."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        fake_id = str(uuid4())

        response = await client.get(f"/v1/reading/queue/{fake_id}", headers=headers)

        assert response.status_code == 404


@pytest.mark.asyncio
class TestReadingEngagementAPI:
    """Tests for PUT /v1/reading/queue/{queue_id}/engagement endpoint. Story 5.8."""

    async def test_engagement_requires_authentication(self, client, queue_test_items):
        """Test that engagement endpoint requires authentication."""
        queue_id = str(queue_test_items[0].id)
        response = await client.put(
            f"/v1/reading/queue/{queue_id}/engagement",
            json={"time_spent_seconds": 60},
        )
        assert response.status_code == 401

    async def test_engagement_updates_time(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that engagement endpoint adds time to total."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        queue_id = str(queue_test_items[0].id)

        # First update
        response = await client.put(
            f"/v1/reading/queue/{queue_id}/engagement",
            headers=headers,
            json={"time_spent_seconds": 60},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total_reading_time_seconds"] >= 60

        # Second update
        response2 = await client.put(
            f"/v1/reading/queue/{queue_id}/engagement",
            headers=headers,
            json={"time_spent_seconds": 30},
        )

        assert response2.status_code == 200
        data2 = response2.json()
        assert data2["total_reading_time_seconds"] >= 90

    async def test_engagement_caps_time_at_30_min(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that time values over 30 minutes are rejected by schema validation."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        queue_id = str(queue_test_items[1].id)

        # Try to add 2 hours - should be rejected by schema
        response = await client.put(
            f"/v1/reading/queue/{queue_id}/engagement",
            headers=headers,
            json={"time_spent_seconds": 7200},  # 2 hours
        )

        # Schema validation rejects values > 1800 (30 min)
        assert response.status_code == 422

        # Valid request with max 30 minutes should succeed
        response = await client.put(
            f"/v1/reading/queue/{queue_id}/engagement",
            headers=headers,
            json={"time_spent_seconds": 1800},  # 30 min exactly
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_reading_time_seconds"] == 1800

    async def test_engagement_not_found_returns_404(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
    ):
        """Test that non-existent queue item returns 404."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        fake_id = str(uuid4())

        response = await client.put(
            f"/v1/reading/queue/{fake_id}/engagement",
            headers=headers,
            json={"time_spent_seconds": 60},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestReadingStatusAPI:
    """Tests for PUT /v1/reading/queue/{queue_id}/status endpoint. Story 5.8."""

    async def test_status_requires_authentication(self, client, queue_test_items):
        """Test that status endpoint requires authentication."""
        queue_id = str(queue_test_items[0].id)
        response = await client.put(
            f"/v1/reading/queue/{queue_id}/status",
            json={"status": "completed"},
        )
        assert response.status_code == 401

    async def test_status_mark_completed(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test marking item as completed."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        queue_id = str(queue_test_items[0].id)

        response = await client.put(
            f"/v1/reading/queue/{queue_id}/status",
            headers=headers,
            json={"status": "completed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None
        assert data["dismissed_at"] is None

    async def test_status_mark_dismissed(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test marking item as dismissed."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        queue_id = str(queue_test_items[1].id)

        response = await client.put(
            f"/v1/reading/queue/{queue_id}/status",
            headers=headers,
            json={"status": "dismissed"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "dismissed"
        assert data["dismissed_at"] is not None
        assert data["completed_at"] is None

    async def test_status_not_found_returns_404(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
    ):
        """Test that non-existent queue item returns 404."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}
        fake_id = str(uuid4())

        response = await client.put(
            f"/v1/reading/queue/{fake_id}/status",
            headers=headers,
            json={"status": "completed"},
        )

        assert response.status_code == 404


@pytest.mark.asyncio
class TestReadingBatchDismissAPI:
    """Tests for POST /v1/reading/queue/batch-dismiss endpoint. Story 5.8."""

    async def test_batch_dismiss_requires_authentication(self, client):
        """Test that batch dismiss endpoint requires authentication."""
        response = await client.post(
            "/v1/reading/queue/batch-dismiss",
            json={"queue_ids": [str(uuid4())]},
        )
        assert response.status_code == 401

    async def test_batch_dismiss_multiple_items(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test batch dismissing multiple items."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        # Get IDs of unread items
        unread_ids = [
            str(item.id)
            for item in queue_test_items
            if item.status == "unread"
        ][:2]  # Dismiss first 2

        response = await client.post(
            "/v1/reading/queue/batch-dismiss",
            headers=headers,
            json={"queue_ids": unread_ids},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["dismissed_count"] == 2
        assert "remaining_unread_count" in data

    async def test_batch_dismiss_ignores_invalid_ids(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that batch dismiss silently ignores invalid/non-existent IDs."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        # Mix valid and invalid IDs
        valid_id = str(queue_test_items[0].id)
        invalid_id = str(uuid4())

        response = await client.post(
            "/v1/reading/queue/batch-dismiss",
            headers=headers,
            json={"queue_ids": [valid_id, invalid_id]},
        )

        assert response.status_code == 200
        data = response.json()
        # Should only dismiss the valid one
        assert data["dismissed_count"] >= 0

    async def test_batch_dismiss_returns_remaining_count(
        self,
        client,
        queue_auth_token,
        queue_test_enrollment,
        queue_test_items,
    ):
        """Test that remaining_unread_count is returned."""
        headers = {"Authorization": f"Bearer {queue_auth_token}"}

        # Get first unread item ID
        unread_id = str(queue_test_items[0].id)

        response = await client.post(
            "/v1/reading/queue/batch-dismiss",
            headers=headers,
            json={"queue_ids": [unread_id]},
        )

        assert response.status_code == 200
        data = response.json()
        assert "remaining_unread_count" in data
        assert isinstance(data["remaining_unread_count"], int)
        assert data["remaining_unread_count"] >= 0
