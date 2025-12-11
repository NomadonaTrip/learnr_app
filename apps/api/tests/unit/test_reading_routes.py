"""
Unit tests for reading content retrieval routes.

Tests the GET /v1/courses/{course_slug}/reading endpoint logic
with mocked dependencies (repositories, services, database).

Per AC: Tests filter by concept, by knowledge area, relevance ranking,
semantic search fallback, and authentication requirement.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from datetime import datetime

from src.models.reading_chunk import ReadingChunk
from src.models.concept import Concept
from src.models.course import Course
from src.models.user import User
from src.routes.reading import get_reading_content
from src.schemas.reading_chunk import ReadingListResponse


# Mock Request object for response time tracking
class MockRequest:
    """Mock FastAPI Request object for testing."""

    def __init__(self):
        self.state = MagicMock()
        self.state.response_time_ms = None


@pytest.mark.asyncio
class TestReadingRoutesUnit:
    """Unit tests for reading retrieval routes layer."""

    async def test_get_reading_filter_by_concept(self):
        """Test filtering reading chunks by concept_ids."""
        # Setup test data
        course_id = uuid.uuid4()
        concept_id1 = uuid.uuid4()
        concept_id2 = uuid.uuid4()
        chunk_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True,
        )

        test_chunk = ReadingChunk(
            id=chunk_id,
            course_id=course_id,
            title="Stakeholder Analysis",
            content="Content about stakeholder analysis...",
            corpus_section="3.2.1",
            knowledge_area_id="strategy",
            concept_ids=[str(concept_id1), str(concept_id2)],
            estimated_read_time_minutes=5,
            chunk_index=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        test_concept1 = Concept(
            id=concept_id1,
            course_id=course_id,
            name="Stakeholder Analysis",
            description="Test description",
            corpus_section_ref="3.2.1",
            knowledge_area_id="strategy",
            prerequisite_depth=1,
        )

        test_concept2 = Concept(
            id=concept_id2,
            course_id=course_id,
            name="Communication",
            description="Test description",
            corpus_section_ref="3.2.2",
            knowledge_area_id="strategy",
            prerequisite_depth=1,
        )

        test_user = User(
            id=uuid.uuid4(), email="test@example.com", hashed_password="hashed"
        )

        # Mock repositories
        mock_chunk_repo = MagicMock()
        mock_chunk_repo.get_chunks_by_concepts = AsyncMock(
            return_value=([test_chunk], 1)
        )
        mock_chunk_repo.get_by_id = AsyncMock(return_value=None)

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_concept_repo = MagicMock()

        async def mock_get_by_id(concept_id):
            if concept_id == concept_id1:
                return test_concept1
            elif concept_id == concept_id2:
                return test_concept2
            return None

        mock_concept_repo.get_by_id = AsyncMock(side_effect=mock_get_by_id)

        mock_request = MockRequest()

        # Execute
        result = await get_reading_content(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=[concept_id1],
            knowledge_area_id=None,
            limit=5,
            chunk_repo=mock_chunk_repo,
            course_repo=mock_course_repo,
            concept_repo=mock_concept_repo,
            current_user=test_user,
        )

        # Assert
        assert isinstance(result, ReadingListResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == chunk_id
        assert result.items[0].title == "Stakeholder Analysis"
        assert result.fallback_used is False

        # Verify repository was called with correct params
        mock_chunk_repo.get_chunks_by_concepts.assert_called_once()

    async def test_get_reading_filter_by_knowledge_area(self):
        """Test filtering reading chunks by knowledge_area_id."""
        course_id = uuid.uuid4()
        concept_id = uuid.uuid4()
        chunk_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True,
        )

        test_chunk = ReadingChunk(
            id=chunk_id,
            course_id=course_id,
            title="Strategy Planning",
            content="Content about strategy...",
            corpus_section="2.1.1",
            knowledge_area_id="strategy",
            concept_ids=[str(concept_id)],
            estimated_read_time_minutes=5,
            chunk_index=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        test_concept = Concept(
            id=concept_id,
            course_id=course_id,
            name="Strategy Planning",
            description="Test",
            corpus_section_ref="2.1.1",
            knowledge_area_id="strategy",
            prerequisite_depth=1,
        )

        test_user = User(
            id=uuid.uuid4(), email="test@example.com", hashed_password="hashed"
        )

        mock_chunk_repo = MagicMock()
        mock_chunk_repo.get_chunks_by_concepts = AsyncMock(
            return_value=([test_chunk], 1)
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_concept_repo = MagicMock()
        mock_concept_repo.get_by_id = AsyncMock(return_value=test_concept)

        mock_request = MockRequest()

        # Execute with knowledge_area filter
        result = await get_reading_content(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=[concept_id],
            knowledge_area_id="strategy",
            limit=5,
            chunk_repo=mock_chunk_repo,
            course_repo=mock_course_repo,
            concept_repo=mock_concept_repo,
            current_user=test_user,
        )

        # Assert
        assert result.total == 1
        assert result.items[0].knowledge_area_id == "strategy"

        # Verify knowledge_area_id was passed to repository via params
        mock_chunk_repo.get_chunks_by_concepts.assert_called_once()

    async def test_get_reading_relevance_ranking(self):
        """Test that chunks are ranked by relevance (matching concept count)."""
        course_id = uuid.uuid4()
        concept_id1 = uuid.uuid4()
        concept_id2 = uuid.uuid4()
        concept_id3 = uuid.uuid4()
        chunk_id1 = uuid.uuid4()
        chunk_id2 = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True,
        )

        # Chunk with 2 matching concepts (higher relevance)
        chunk1 = ReadingChunk(
            id=chunk_id1,
            course_id=course_id,
            title="High Relevance",
            content="Content...",
            corpus_section="3.1",
            knowledge_area_id="strategy",
            concept_ids=[str(concept_id1), str(concept_id2)],
            estimated_read_time_minutes=5,
            chunk_index=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        # Chunk with 1 matching concept (lower relevance)
        chunk2 = ReadingChunk(
            id=chunk_id2,
            course_id=course_id,
            title="Low Relevance",
            content="Content...",
            corpus_section="3.2",
            knowledge_area_id="strategy",
            concept_ids=[str(concept_id1), str(concept_id3)],
            estimated_read_time_minutes=5,
            chunk_index=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        test_user = User(
            id=uuid.uuid4(), email="test@example.com", hashed_password="hashed"
        )

        # Repository returns chunks ordered by relevance (most matches first)
        mock_chunk_repo = MagicMock()
        mock_chunk_repo.get_chunks_by_concepts = AsyncMock(
            return_value=([chunk1, chunk2], 2)
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_concept_repo = MagicMock()
        mock_concept_repo.get_by_id = AsyncMock(return_value=None)

        mock_request = MockRequest()

        # Execute
        result = await get_reading_content(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=[concept_id1, concept_id2],
            knowledge_area_id=None,
            limit=5,
            chunk_repo=mock_chunk_repo,
            course_repo=mock_course_repo,
            concept_repo=mock_concept_repo,
            current_user=test_user,
        )

        # Assert that first chunk has higher relevance score
        assert len(result.items) == 2
        assert result.items[0].relevance_score == 2.0  # Matches both concepts
        assert result.items[1].relevance_score == 1.0  # Matches one concept

    async def test_get_reading_semantic_search_fallback(self):
        """Test semantic search fallback when no direct matches."""
        course_id = uuid.uuid4()
        concept_id = uuid.uuid4()
        chunk_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True,
        )

        test_chunk = ReadingChunk(
            id=chunk_id,
            course_id=course_id,
            title="Fallback Chunk",
            content="Content found via semantic search...",
            corpus_section="4.1",
            knowledge_area_id="elicitation",
            concept_ids=[],
            estimated_read_time_minutes=5,
            chunk_index=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        test_concept = Concept(
            id=concept_id,
            course_id=course_id,
            name="Elicitation Techniques",
            description="Test",
            corpus_section_ref="4.1",
            knowledge_area_id="elicitation",
            prerequisite_depth=1,
        )

        test_user = User(
            id=uuid.uuid4(), email="test@example.com", hashed_password="hashed"
        )

        # Mock repositories - no direct matches
        mock_chunk_repo = MagicMock()
        mock_chunk_repo.get_chunks_by_concepts = AsyncMock(return_value=([], 0))
        mock_chunk_repo.get_by_id = AsyncMock(return_value=test_chunk)

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_concept_repo = MagicMock()
        mock_concept_repo.get_by_id = AsyncMock(return_value=test_concept)

        mock_request = MockRequest()

        # Mock semantic search service
        with patch(
            "src.routes.reading.ReadingSearchService"
        ) as MockSearchService:
            mock_service_instance = MagicMock()
            mock_service_instance.search_chunks_by_concept_names = AsyncMock(
                return_value=[test_chunk]
            )
            mock_service_instance.close = AsyncMock()
            MockSearchService.return_value = mock_service_instance

            # Execute
            result = await get_reading_content(
                request=mock_request,
                course_slug="cbap-test",
                concept_ids=[concept_id],
                knowledge_area_id=None,
                limit=5,
                chunk_repo=mock_chunk_repo,
                course_repo=mock_course_repo,
                concept_repo=mock_concept_repo,
                current_user=test_user,
            )

            # Assert
            assert result.fallback_used is True
            assert len(result.items) == 1
            assert result.items[0].id == chunk_id

            # Verify semantic search was called
            mock_service_instance.search_chunks_by_concept_names.assert_called_once()

    async def test_get_reading_course_not_found(self):
        """Test 404 error when course doesn't exist."""
        test_user = User(
            id=uuid.uuid4(), email="test@example.com", hashed_password="hashed"
        )

        mock_chunk_repo = MagicMock()
        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=None)
        mock_concept_repo = MagicMock()

        mock_request = MockRequest()

        # Execute and assert exception
        with pytest.raises(HTTPException) as exc_info:
            await get_reading_content(
                request=mock_request,
                course_slug="nonexistent",
                concept_ids=[uuid.uuid4()],
                knowledge_area_id=None,
                limit=5,
                chunk_repo=mock_chunk_repo,
                course_repo=mock_course_repo,
                concept_repo=mock_concept_repo,
                current_user=test_user,
            )

        assert exc_info.value.status_code == 404
        assert "COURSE_NOT_FOUND" in str(exc_info.value.detail)

    async def test_get_reading_response_includes_concept_names(self):
        """Test that response includes human-readable concept names."""
        course_id = uuid.uuid4()
        concept_id = uuid.uuid4()
        chunk_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True,
        )

        test_chunk = ReadingChunk(
            id=chunk_id,
            course_id=course_id,
            title="Test Chunk",
            content="Content...",
            corpus_section="1.1",
            knowledge_area_id="strategy",
            concept_ids=[str(concept_id)],
            estimated_read_time_minutes=5,
            chunk_index=0,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )

        test_concept = Concept(
            id=concept_id,
            course_id=course_id,
            name="SWOT Analysis",
            description="Test",
            corpus_section_ref="1.1",
            knowledge_area_id="strategy",
            prerequisite_depth=1,
        )

        test_user = User(
            id=uuid.uuid4(), email="test@example.com", hashed_password="hashed"
        )

        mock_chunk_repo = MagicMock()
        mock_chunk_repo.get_chunks_by_concepts = AsyncMock(
            return_value=([test_chunk], 1)
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_concept_repo = MagicMock()
        mock_concept_repo.get_by_id = AsyncMock(return_value=test_concept)

        mock_request = MockRequest()

        # Execute
        result = await get_reading_content(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=[concept_id],
            knowledge_area_id=None,
            limit=5,
            chunk_repo=mock_chunk_repo,
            course_repo=mock_course_repo,
            concept_repo=mock_concept_repo,
            current_user=test_user,
        )

        # Assert concept names are included
        assert len(result.items) == 1
        assert "SWOT Analysis" in result.items[0].concept_names
