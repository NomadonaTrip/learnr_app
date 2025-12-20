"""
Integration tests for Qdrant vector database operations with multi-course support

Tests CRUD operations for both questions and reading_chunks collections.
Requires Qdrant to be running (docker-compose up qdrant).
"""

from uuid import UUID, uuid4

import pytest
from qdrant_client.models import Distance, VectorParams

from src.db.qdrant_client import get_qdrant
from src.repositories.qdrant_repository import (
    CHUNKS_COLLECTION,
    QUESTIONS_COLLECTION,
    QdrantRepository,
)

# =============================================================================
# Test Course IDs (consistent across tests)
# =============================================================================

TEST_COURSE_ID = uuid4()
ANOTHER_COURSE_ID = uuid4()

# Vector dimensions for text-embedding-3-large
VECTOR_SIZE = 3072


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture(scope="session", autouse=True)
async def ensure_qdrant_collections():
    """
    Ensure Qdrant collections exist before running tests.
    Creates collections if they don't exist.
    """
    client = get_qdrant()

    # Check and create questions collection
    try:
        await client.get_collection(QUESTIONS_COLLECTION)
    except Exception:
        await client.create_collection(
            collection_name=QUESTIONS_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

    # Check and create reading_chunks collection
    try:
        await client.get_collection(CHUNKS_COLLECTION)
    except Exception:
        await client.create_collection(
            collection_name=CHUNKS_COLLECTION,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE)
        )

    yield

    # Cleanup is optional - leave collections for inspection


@pytest.fixture
def qdrant_repo():
    """Create Qdrant repository instance"""
    return QdrantRepository()


@pytest.fixture
def sample_question_vector() -> list[float]:
    """
    Generate sample 3072-dimensional vector for testing.
    In production, this would come from OpenAI text-embedding-3-large.
    """
    return [0.1] * 3072


@pytest.fixture
def sample_chunk_vector() -> list[float]:
    """Generate sample 3072-dimensional vector for reading chunks"""
    return [0.2] * 3072


@pytest.fixture
def test_course_id() -> UUID:
    """Consistent test course ID"""
    return TEST_COURSE_ID


@pytest.fixture
def another_course_id() -> UUID:
    """Another course ID for cross-course tests"""
    return ANOTHER_COURSE_ID


# =============================================================================
# Question Vector Tests (Multi-Course)
# =============================================================================

@pytest.mark.integration
async def test_create_question_vector_with_course_id(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID
):
    """Test creating a question vector with course_id in Qdrant"""
    question_id = uuid4()
    payload = {
        "knowledge_area_id": "ba-planning",
        "difficulty": 0.5,
        "concept_ids": [str(uuid4()), str(uuid4())],
        "question_text": "What is the primary purpose of stakeholder analysis in the planning phase?",
        "options": "A) Identify stakeholders B) Assess risks C) Create timeline D) Allocate budget",
        "correct_answer": "A"
    }

    try:
        # Create vector with course_id
        await qdrant_repo.create_question_vector(
            question_id, sample_question_vector, test_course_id, payload
        )

        # Verify creation by retrieving
        result = await qdrant_repo.get_question_vector(question_id)
        assert result is not None, "Question vector should be created"
        assert result["id"] == str(question_id), "Question ID should match"
        assert result["payload"]["course_id"] == str(test_course_id), "Course ID should be stored"
        assert result["payload"]["knowledge_area_id"] == "ba-planning", "KA ID should match"
        assert result["payload"]["difficulty"] == 0.5, "Difficulty should match"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(question_id)


@pytest.mark.integration
async def test_get_question_vector(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID
):
    """Test retrieving a question vector by ID"""
    question_id = uuid4()
    payload = {
        "knowledge_area_id": "elicitation",
        "difficulty": 0.8,
        "concept_ids": [],
        "question_text": "Which elicitation technique is most effective for complex processes?",
        "options": "A) Interview B) Workshop C) Survey D) Observation",
        "correct_answer": "B"
    }

    try:
        # Create vector
        await qdrant_repo.create_question_vector(
            question_id, sample_question_vector, test_course_id, payload
        )

        # Retrieve vector
        result = await qdrant_repo.get_question_vector(question_id)

        assert result is not None, "Should retrieve existing vector"
        assert result["id"] == str(question_id), "ID should match"
        assert result["payload"]["knowledge_area_id"] == "elicitation", "Payload should match"
        assert len(result["vector"]) == 3072, "Vector should have 3072 dimensions"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(question_id)


@pytest.mark.integration
async def test_get_nonexistent_question_vector(qdrant_repo: QdrantRepository):
    """Test retrieving a question vector that doesn't exist"""
    nonexistent_id = uuid4()
    result = await qdrant_repo.get_question_vector(nonexistent_id)
    assert result is None, "Should return None for nonexistent vector"


@pytest.mark.integration
async def test_search_questions_by_course_id(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID,
    another_course_id: UUID
):
    """Test that course_id filter isolates results"""
    # Create question in TEST_COURSE_ID
    q1_id = uuid4()
    await qdrant_repo.create_question_vector(
        question_id=q1_id,
        vector=sample_question_vector,
        course_id=test_course_id,
        payload={
            "knowledge_area_id": "ba-planning",
            "difficulty": 0.5,
            "concept_ids": [],
            "question_text": "Course 1 question",
            "options": "A) B) C) D)",
            "correct_answer": "A"
        }
    )

    # Create question in ANOTHER_COURSE_ID
    q2_id = uuid4()
    await qdrant_repo.create_question_vector(
        question_id=q2_id,
        vector=sample_question_vector,
        course_id=another_course_id,
        payload={
            "knowledge_area_id": "ba-planning",
            "difficulty": 0.5,
            "concept_ids": [],
            "question_text": "Course 2 question",
            "options": "A) B) C) D)",
            "correct_answer": "A"
        }
    )

    try:
        # Search with course filter - should only find q1
        results = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            course_id=test_course_id,
            limit=10
        )

        result_ids = [r["id"] for r in results]
        assert str(q1_id) in result_ids, "Should find question from test course"
        assert str(q2_id) not in result_ids, "Should NOT find question from another course"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(q1_id)
        await qdrant_repo.delete_question_vector(q2_id)


@pytest.mark.integration
async def test_search_questions_cross_course_isolation(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID,
    another_course_id: UUID
):
    """Test that courses are properly isolated"""
    # Create questions in both courses
    q1_id = uuid4()
    q2_id = uuid4()

    await qdrant_repo.create_question_vector(
        question_id=q1_id,
        vector=sample_question_vector,
        course_id=test_course_id,
        payload={
            "knowledge_area_id": "rlcm",
            "difficulty": 0.3,
            "concept_ids": [],
            "question_text": "Test course question",
            "options": "Options",
            "correct_answer": "A"
        }
    )

    await qdrant_repo.create_question_vector(
        question_id=q2_id,
        vector=sample_question_vector,
        course_id=another_course_id,
        payload={
            "knowledge_area_id": "rlcm",
            "difficulty": 0.3,
            "concept_ids": [],
            "question_text": "Another course question",
            "options": "Options",
            "correct_answer": "B"
        }
    )

    try:
        # Search in test course
        results_course1 = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            course_id=test_course_id,
            limit=10
        )

        # Search in another course
        results_course2 = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            course_id=another_course_id,
            limit=10
        )

        # Verify isolation
        course1_ids = {r["id"] for r in results_course1}
        course2_ids = {r["id"] for r in results_course2}

        assert str(q1_id) in course1_ids, "q1 should be in course1 results"
        assert str(q1_id) not in course2_ids, "q1 should NOT be in course2 results"
        assert str(q2_id) in course2_ids, "q2 should be in course2 results"
        assert str(q2_id) not in course1_ids, "q2 should NOT be in course1 results"

    finally:
        await qdrant_repo.delete_question_vector(q1_id)
        await qdrant_repo.delete_question_vector(q2_id)


@pytest.mark.integration
async def test_search_questions_with_knowledge_area_filter(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID
):
    """Test searching questions with knowledge_area_id filter"""
    question_id_1 = uuid4()
    question_id_2 = uuid4()

    payload_1 = {
        "knowledge_area_id": "rlcm",
        "difficulty": 0.3,
        "concept_ids": [],
        "question_text": "Test question 1",
        "options": "Options 1",
        "correct_answer": "A"
    }

    payload_2 = {
        "knowledge_area_id": "strategy",
        "difficulty": 0.5,
        "concept_ids": [],
        "question_text": "Test question 2",
        "options": "Options 2",
        "correct_answer": "B"
    }

    try:
        await qdrant_repo.create_question_vector(
            question_id_1, sample_question_vector, test_course_id, payload_1
        )
        await qdrant_repo.create_question_vector(
            question_id_2, [0.15] * 3072, test_course_id, payload_2
        )

        # Search with knowledge_area_id filter
        results = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            course_id=test_course_id,
            knowledge_area_id="rlcm",
            limit=10
        )

        assert len(results) >= 1, "Should find at least one matching question"
        for result in results:
            assert result["payload"]["knowledge_area_id"] == "rlcm", \
                "All results should match the knowledge_area_id filter"

    finally:
        await qdrant_repo.delete_question_vector(question_id_1)
        await qdrant_repo.delete_question_vector(question_id_2)


@pytest.mark.integration
async def test_search_questions_with_difficulty_range(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID
):
    """Test searching questions with difficulty range filter"""
    question_id = uuid4()
    payload = {
        "knowledge_area_id": "solution-eval",
        "difficulty": 0.7,
        "concept_ids": [],
        "question_text": "Test question",
        "options": "Options",
        "correct_answer": "C"
    }

    try:
        await qdrant_repo.create_question_vector(
            question_id, sample_question_vector, test_course_id, payload
        )

        # Search with difficulty range filter
        results = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            course_id=test_course_id,
            difficulty_min=0.5,
            difficulty_max=0.9,
            limit=10
        )

        assert len(results) >= 1, "Should find at least one question in range"
        for result in results:
            assert 0.5 <= result["payload"]["difficulty"] <= 0.9, \
                "All results should be within difficulty range"

    finally:
        await qdrant_repo.delete_question_vector(question_id)


@pytest.mark.integration
async def test_search_questions_without_filters(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID
):
    """Test searching questions without any filters (returns all courses)"""
    question_id = uuid4()
    payload = {
        "knowledge_area_id": "radd",
        "difficulty": 0.5,
        "concept_ids": [],
        "question_text": "Test question",
        "options": "Options",
        "correct_answer": "D"
    }

    try:
        await qdrant_repo.create_question_vector(
            question_id, sample_question_vector, test_course_id, payload
        )

        # Search without filters (should return similar vectors from any course)
        results = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            limit=5
        )

        assert isinstance(results, list), "Should return a list"
        assert all("id" in r and "score" in r and "payload" in r for r in results), \
            "Each result should have id, score, and payload"

    finally:
        await qdrant_repo.delete_question_vector(question_id)


@pytest.mark.integration
async def test_delete_question_vector(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID
):
    """Test deleting a question vector"""
    question_id = uuid4()
    payload = {
        "knowledge_area_id": "ba-planning",
        "difficulty": 0.3,
        "concept_ids": [],
        "question_text": "Test question to delete",
        "options": "Options",
        "correct_answer": "A"
    }

    await qdrant_repo.create_question_vector(
        question_id, sample_question_vector, test_course_id, payload
    )

    result = await qdrant_repo.get_question_vector(question_id)
    assert result is not None, "Vector should exist before deletion"

    await qdrant_repo.delete_question_vector(question_id)

    result = await qdrant_repo.get_question_vector(question_id)
    assert result is None, "Vector should not exist after deletion"


# =============================================================================
# Reading Chunk Vector Tests (Multi-Course)
# =============================================================================

@pytest.mark.integration
async def test_create_chunk_vector_with_course_id(
    qdrant_repo: QdrantRepository,
    sample_chunk_vector: list[float],
    test_course_id: UUID
):
    """Test creating a reading chunk vector with course_id"""
    chunk_id = uuid4()
    payload = {
        "knowledge_area_id": "ba-planning",
        "section_ref": "3.1.2",
        "difficulty": 0.5,
        "concept_ids": [str(uuid4())],
        "text_content": "Stakeholder analysis is performed to understand stakeholder characteristics..."
    }

    try:
        await qdrant_repo.create_chunk_vector(
            chunk_id, sample_chunk_vector, test_course_id, payload
        )

        result = await qdrant_repo.get_chunk_vector(chunk_id)
        assert result is not None, "Chunk vector should be created"
        assert result["payload"]["course_id"] == str(test_course_id), "Course ID should be stored"
        assert result["payload"]["knowledge_area_id"] == "ba-planning", "KA ID should match"

    finally:
        await qdrant_repo.delete_chunk_vector(chunk_id)


@pytest.mark.integration
async def test_search_chunks_by_course_id(
    qdrant_repo: QdrantRepository,
    sample_chunk_vector: list[float],
    test_course_id: UUID,
    another_course_id: UUID
):
    """Test that course_id filter isolates chunk results"""
    chunk1_id = uuid4()
    chunk2_id = uuid4()

    await qdrant_repo.create_chunk_vector(
        chunk_id=chunk1_id,
        vector=sample_chunk_vector,
        course_id=test_course_id,
        payload={
            "knowledge_area_id": "ba-planning",
            "section_ref": "3.1",
            "difficulty": 0.5,
            "concept_ids": [],
            "text_content": "Course 1 chunk content"
        }
    )

    await qdrant_repo.create_chunk_vector(
        chunk_id=chunk2_id,
        vector=sample_chunk_vector,
        course_id=another_course_id,
        payload={
            "knowledge_area_id": "ba-planning",
            "section_ref": "3.1",
            "difficulty": 0.5,
            "concept_ids": [],
            "text_content": "Course 2 chunk content"
        }
    )

    try:
        results = await qdrant_repo.search_chunks(
            query_vector=sample_chunk_vector,
            course_id=test_course_id,
            limit=10
        )

        result_ids = [r["id"] for r in results]
        assert str(chunk1_id) in result_ids, "Should find chunk from test course"
        assert str(chunk2_id) not in result_ids, "Should NOT find chunk from another course"

    finally:
        await qdrant_repo.delete_chunk_vector(chunk1_id)
        await qdrant_repo.delete_chunk_vector(chunk2_id)


@pytest.mark.integration
async def test_search_chunks_with_knowledge_area_filter(
    qdrant_repo: QdrantRepository,
    sample_chunk_vector: list[float],
    test_course_id: UUID
):
    """Test searching chunks with knowledge_area_id filter"""
    chunk_id = uuid4()
    payload = {
        "knowledge_area_id": "elicitation",
        "section_ref": "4.2.1",
        "difficulty": 0.8,
        "concept_ids": [],
        "text_content": "Collaborative workshops bring stakeholders together..."
    }

    try:
        await qdrant_repo.create_chunk_vector(
            chunk_id, sample_chunk_vector, test_course_id, payload
        )

        results = await qdrant_repo.search_chunks(
            query_vector=sample_chunk_vector,
            course_id=test_course_id,
            knowledge_area_id="elicitation",
            limit=3
        )

        assert len(results) >= 1, "Should find at least one matching chunk"
        for result in results:
            assert result["payload"]["knowledge_area_id"] == "elicitation", \
                "All results should match the knowledge_area_id filter"

    finally:
        await qdrant_repo.delete_chunk_vector(chunk_id)


@pytest.mark.integration
async def test_search_chunks_without_filters(
    qdrant_repo: QdrantRepository,
    sample_chunk_vector: list[float],
    test_course_id: UUID
):
    """Test searching chunks without filters"""
    chunk_id = uuid4()
    payload = {
        "knowledge_area_id": "rlcm",
        "section_ref": "5.3.4",
        "difficulty": 0.5,
        "concept_ids": [],
        "text_content": "Requirements traceability ensures that requirements are linked..."
    }

    try:
        await qdrant_repo.create_chunk_vector(
            chunk_id, sample_chunk_vector, test_course_id, payload
        )

        results = await qdrant_repo.search_chunks(
            query_vector=sample_chunk_vector,
            limit=3
        )

        assert isinstance(results, list), "Should return a list"
        assert all("id" in r and "score" in r and "payload" in r for r in results), \
            "Each result should have id, score, and payload"

    finally:
        await qdrant_repo.delete_chunk_vector(chunk_id)


# =============================================================================
# Collection Configuration Tests
# =============================================================================

@pytest.mark.integration
async def test_vector_dimensions(
    qdrant_repo: QdrantRepository,
    sample_question_vector: list[float],
    test_course_id: UUID
):
    """Test that vectors must have exactly 3072 dimensions"""
    question_id = uuid4()
    payload = {
        "knowledge_area_id": "test-ka",
        "difficulty": 0.3,
        "concept_ids": [],
        "question_text": "Test",
        "options": "Options",
        "correct_answer": "A"
    }

    try:
        await qdrant_repo.create_question_vector(
            question_id, sample_question_vector, test_course_id, payload
        )

        result = await qdrant_repo.get_question_vector(question_id)
        assert result is not None, "Vector with correct dimensions should be created"
        assert len(result["vector"]) == 3072, "Vector should have 3072 dimensions"

    finally:
        await qdrant_repo.delete_question_vector(question_id)
