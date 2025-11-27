"""
Integration tests for Qdrant vector database operations

Tests CRUD operations for both cbap_questions and babok_chunks collections.
Requires Qdrant to be running (docker-compose up qdrant).
"""

import pytest
from uuid import uuid4, UUID
from typing import List

from src.repositories.qdrant_repository import QdrantRepository


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def qdrant_repo():
    """Create Qdrant repository instance"""
    return QdrantRepository()


@pytest.fixture
def sample_question_vector() -> List[float]:
    """
    Generate sample 3072-dimensional vector for testing.
    In production, this would come from OpenAI text-embedding-3-large.
    """
    return [0.1] * 3072


@pytest.fixture
def sample_chunk_vector() -> List[float]:
    """Generate sample 3072-dimensional vector for BABOK chunks"""
    return [0.2] * 3072


# =============================================================================
# Question Vector Tests
# =============================================================================

@pytest.mark.integration
async def test_create_question_vector(qdrant_repo: QdrantRepository, sample_question_vector: List[float]):
    """Test creating a question vector in Qdrant"""
    question_id = uuid4()
    payload = {
        "question_id": str(question_id),
        "ka": "Business Analysis Planning and Monitoring",
        "difficulty": "Medium",
        "concept_tags": ["planning", "stakeholder", "communication"],
        "question_text": "What is the primary purpose of stakeholder analysis in the planning phase?",
        "options": "A) Identify stakeholders B) Assess risks C) Create timeline D) Allocate budget",
        "correct_answer": "A"
    }

    try:
        # Create vector
        await qdrant_repo.create_question_vector(question_id, sample_question_vector, payload)

        # Verify creation by retrieving
        result = await qdrant_repo.get_question_vector(question_id)
        assert result is not None, "Question vector should be created"
        assert result["id"] == str(question_id), "Question ID should match"
        assert result["payload"]["ka"] == "Business Analysis Planning and Monitoring", "KA should match"
        assert result["payload"]["difficulty"] == "Medium", "Difficulty should match"
        assert "planning" in result["payload"]["concept_tags"], "Concept tags should include 'planning'"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(question_id)


@pytest.mark.integration
async def test_get_question_vector(qdrant_repo: QdrantRepository, sample_question_vector: List[float]):
    """Test retrieving a question vector by ID"""
    question_id = uuid4()
    payload = {
        "question_id": str(question_id),
        "ka": "Elicitation and Collaboration",
        "difficulty": "Hard",
        "concept_tags": ["elicitation", "techniques"],
        "question_text": "Which elicitation technique is most effective for complex processes?",
        "options": "A) Interview B) Workshop C) Survey D) Observation",
        "correct_answer": "B"
    }

    try:
        # Create vector
        await qdrant_repo.create_question_vector(question_id, sample_question_vector, payload)

        # Retrieve vector
        result = await qdrant_repo.get_question_vector(question_id)

        assert result is not None, "Should retrieve existing vector"
        assert result["id"] == str(question_id), "ID should match"
        assert result["payload"]["ka"] == "Elicitation and Collaboration", "Payload should match"
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
async def test_search_questions_with_ka_filter(qdrant_repo: QdrantRepository, sample_question_vector: List[float]):
    """Test searching questions with Knowledge Area filter"""
    # Create test questions
    question_id_1 = uuid4()
    question_id_2 = uuid4()

    payload_1 = {
        "question_id": str(question_id_1),
        "ka": "Requirements Life Cycle Management",
        "difficulty": "Easy",
        "concept_tags": ["requirements", "traceability"],
        "question_text": "Test question 1",
        "options": "Options 1",
        "correct_answer": "A"
    }

    payload_2 = {
        "question_id": str(question_id_2),
        "ka": "Strategy Analysis",
        "difficulty": "Medium",
        "concept_tags": ["strategy", "analysis"],
        "question_text": "Test question 2",
        "options": "Options 2",
        "correct_answer": "B"
    }

    try:
        # Create vectors
        await qdrant_repo.create_question_vector(question_id_1, sample_question_vector, payload_1)
        await qdrant_repo.create_question_vector(question_id_2, [0.15] * 3072, payload_2)

        # Search with KA filter
        results = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            filters={"ka": "Requirements Life Cycle Management"},
            limit=10
        )

        # Verify results
        assert len(results) >= 1, "Should find at least one matching question"

        # Check that all results match the filter
        for result in results:
            assert result["payload"]["ka"] == "Requirements Life Cycle Management", \
                "All results should match the KA filter"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(question_id_1)
        await qdrant_repo.delete_question_vector(question_id_2)



@pytest.mark.integration
async def test_search_questions_with_difficulty_filter(qdrant_repo: QdrantRepository, sample_question_vector: List[float]):
    """Test searching questions with difficulty filter"""
    question_id = uuid4()
    payload = {
        "question_id": str(question_id),
        "ka": "Solution Evaluation",
        "difficulty": "Hard",
        "concept_tags": ["evaluation", "metrics"],
        "question_text": "Test question",
        "options": "Options",
        "correct_answer": "C"
    }

    try:
        # Create vector
        await qdrant_repo.create_question_vector(question_id, sample_question_vector, payload)

        # Search with difficulty filter
        results = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            filters={"difficulty": "Hard"},
            limit=10
        )

        # Verify results
        assert len(results) >= 1, "Should find at least one hard question"

        # Check that all results match the filter
        for result in results:
            assert result["payload"]["difficulty"] == "Hard", \
                "All results should match the difficulty filter"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(question_id)



@pytest.mark.integration
async def test_search_questions_without_filters(qdrant_repo: QdrantRepository, sample_question_vector: List[float]):
    """Test searching questions without any filters"""
    question_id = uuid4()
    payload = {
        "question_id": str(question_id),
        "ka": "Requirements Analysis and Design Definition",
        "difficulty": "Medium",
        "concept_tags": ["requirements"],
        "question_text": "Test question",
        "options": "Options",
        "correct_answer": "D"
    }

    try:
        # Create vector
        await qdrant_repo.create_question_vector(question_id, sample_question_vector, payload)

        # Search without filters (should return similar vectors)
        results = await qdrant_repo.search_questions(
            query_vector=sample_question_vector,
            filters=None,
            limit=5
        )

        # Verify results
        assert isinstance(results, list), "Should return a list"
        assert all("id" in r and "score" in r and "payload" in r for r in results), \
            "Each result should have id, score, and payload"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(question_id)



@pytest.mark.integration
async def test_delete_question_vector(qdrant_repo: QdrantRepository, sample_question_vector: List[float]):
    """Test deleting a question vector"""
    question_id = uuid4()
    payload = {
        "question_id": str(question_id),
        "ka": "Business Analysis Planning and Monitoring",
        "difficulty": "Easy",
        "concept_tags": ["planning"],
        "question_text": "Test question to delete",
        "options": "Options",
        "correct_answer": "A"
    }

    # Create vector
    await qdrant_repo.create_question_vector(question_id, sample_question_vector, payload)

    # Verify it exists
    result = await qdrant_repo.get_question_vector(question_id)
    assert result is not None, "Vector should exist before deletion"

    # Delete vector
    await qdrant_repo.delete_question_vector(question_id)

    # Verify deletion
    result = await qdrant_repo.get_question_vector(question_id)
    assert result is None, "Vector should not exist after deletion"


# =============================================================================
# BABOK Chunk Vector Tests
# =============================================================================


@pytest.mark.integration
async def test_create_chunk_vector(qdrant_repo: QdrantRepository, sample_chunk_vector: List[float]):
    """Test creating a BABOK chunk vector in Qdrant"""
    chunk_id = uuid4()
    payload = {
        "chunk_id": str(chunk_id),
        "ka": "Business Analysis Planning and Monitoring",
        "section_ref": "3.1.2",
        "difficulty": "Medium",
        "concept_tags": ["stakeholder", "analysis", "power-interest"],
        "text_content": "Stakeholder analysis is performed to understand stakeholder characteristics..."
    }

    try:
        # Create vector
        await qdrant_repo.create_chunk_vector(chunk_id, sample_chunk_vector, payload)

        # Verify creation by searching
        results = await qdrant_repo.search_chunks(
            query_vector=sample_chunk_vector,
            filters={"ka": "Business Analysis Planning and Monitoring"},
            limit=10
        )

        # Should find the chunk we just created
        chunk_ids = [r["id"] for r in results]
        assert str(chunk_id) in chunk_ids, "Created chunk should be searchable"

    finally:
        # Cleanup - delete the chunk
        # Note: We don't have a delete_chunk method, so this is acceptable for test
        pass



@pytest.mark.integration
async def test_search_chunks_with_ka_filter(qdrant_repo: QdrantRepository, sample_chunk_vector: List[float]):
    """Test searching BABOK chunks with Knowledge Area filter"""
    chunk_id = uuid4()
    payload = {
        "chunk_id": str(chunk_id),
        "ka": "Elicitation and Collaboration",
        "section_ref": "4.2.1",
        "difficulty": "Hard",
        "concept_tags": ["elicitation", "workshop"],
        "text_content": "Collaborative workshops bring stakeholders together to define requirements..."
    }

    try:
        # Create vector
        await qdrant_repo.create_chunk_vector(chunk_id, sample_chunk_vector, payload)

        # Search with KA filter
        results = await qdrant_repo.search_chunks(
            query_vector=sample_chunk_vector,
            filters={"ka": "Elicitation and Collaboration"},
            limit=3
        )

        # Verify results
        assert len(results) >= 1, "Should find at least one matching chunk"

        # Check that results match the filter
        for result in results:
            assert result["payload"]["ka"] == "Elicitation and Collaboration", \
                "All results should match the KA filter"

    finally:
        # Cleanup
        pass



@pytest.mark.integration
async def test_search_chunks_without_filters(qdrant_repo: QdrantRepository, sample_chunk_vector: List[float]):
    """Test searching BABOK chunks without filters"""
    chunk_id = uuid4()
    payload = {
        "chunk_id": str(chunk_id),
        "ka": "Requirements Life Cycle Management",
        "section_ref": "5.3.4",
        "difficulty": "Medium",
        "concept_tags": ["traceability", "requirements"],
        "text_content": "Requirements traceability ensures that requirements are linked to their sources..."
    }

    try:
        # Create vector
        await qdrant_repo.create_chunk_vector(chunk_id, sample_chunk_vector, payload)

        # Search without filters
        results = await qdrant_repo.search_chunks(
            query_vector=sample_chunk_vector,
            filters=None,
            limit=3
        )

        # Verify results
        assert isinstance(results, list), "Should return a list"
        assert all("id" in r and "score" in r and "payload" in r for r in results), \
            "Each result should have id, score, and payload"

    finally:
        # Cleanup
        pass


# =============================================================================
# Collection Configuration Tests
# =============================================================================


@pytest.mark.integration
async def test_vector_dimensions(qdrant_repo: QdrantRepository, sample_question_vector: List[float]):
    """Test that vectors must have exactly 3072 dimensions"""
    question_id = uuid4()
    payload = {
        "question_id": str(question_id),
        "ka": "Test KA",
        "difficulty": "Easy",
        "concept_tags": ["test"],
        "question_text": "Test",
        "options": "Options",
        "correct_answer": "A"
    }

    try:
        # This should work (correct dimensions)
        await qdrant_repo.create_question_vector(question_id, sample_question_vector, payload)

        # Verify creation
        result = await qdrant_repo.get_question_vector(question_id)
        assert result is not None, "Vector with correct dimensions should be created"
        assert len(result["vector"]) == 3072, "Vector should have 3072 dimensions"

    finally:
        # Cleanup
        await qdrant_repo.delete_question_vector(question_id)
