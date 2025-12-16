"""
Integration tests for question embedding generation and Qdrant upload.

Tests the QdrantUploadService for vector uploads and idempotency.
Updated to work with the refactored service-oriented architecture.
"""
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "apps" / "api"))

from src.services.embedding_service import EMBEDDING_DIMENSIONS  # noqa: E402
from src.services.qdrant_upload_service import (  # noqa: E402
    COLLECTION_NAME,
    QdrantUploadService,
    QuestionVectorItem,
)


def create_mock_vector_item(
    question_id=None,
    course_id=None,
    knowledge_area_id="ba-planning",
    difficulty=0.5,
    discrimination=0.7,
    concept_ids=None,
    concept_names=None,
    question_text="What is BABOK?",
    options=None,
    correct_answer="A",
):
    """Helper to create QuestionVectorItem for testing."""
    return QuestionVectorItem(
        question_id=question_id or uuid.uuid4(),
        course_id=course_id or uuid.uuid4(),
        vector=[0.1] * EMBEDDING_DIMENSIONS,
        knowledge_area_id=knowledge_area_id,
        difficulty=difficulty,
        discrimination=discrimination,
        concept_ids=concept_ids or ["concept-1", "concept-2"],
        concept_names=concept_names or ["Concept One", "Concept Two"],
        question_text=question_text,
        options=options or {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer=correct_answer,
    )


class TestQdrantUploadServiceVectorExists:
    """Tests for checking vector existence in Qdrant."""

    @pytest.mark.asyncio
    async def test_vector_exists_returns_true_when_found(self):
        """Test that vector_exists returns True when vector is found."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[MagicMock()])

        service = QdrantUploadService(qdrant_client=mock_client)

        question_id = uuid.uuid4()
        result = await service.vector_exists(question_id)

        assert result is True
        mock_client.retrieve.assert_called_once_with(
            collection_name=COLLECTION_NAME,
            ids=[str(question_id)]
        )

    @pytest.mark.asyncio
    async def test_vector_exists_returns_false_when_not_found(self):
        """Test that vector_exists returns False when vector is not found."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[])

        service = QdrantUploadService(qdrant_client=mock_client)

        question_id = uuid.uuid4()
        result = await service.vector_exists(question_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_vector_exists_returns_false_on_exception(self):
        """Test that vector_exists returns False on exception."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(side_effect=Exception("Connection error"))

        service = QdrantUploadService(qdrant_client=mock_client)

        question_id = uuid.uuid4()
        result = await service.vector_exists(question_id)

        assert result is False


class TestQdrantUploadServiceUpload:
    """Tests for uploading vectors to Qdrant."""

    @pytest.mark.asyncio
    async def test_upload_question_vector_with_correct_payload(self):
        """Test that vectors are uploaded with correct payload structure."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[])  # No existing vectors
        mock_client.upsert = AsyncMock()

        service = QdrantUploadService(qdrant_client=mock_client)

        item = create_mock_vector_item(
            knowledge_area_id="ba-planning",
            difficulty=0.6,
            discrimination=0.8,
            concept_ids=["id-1", "id-2"],
            concept_names=["Planning", "Monitoring"],
        )

        result = await service.upload_question_vector(item, skip_if_exists=False)

        assert result is True

        # Verify upsert was called
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args

        assert call_args.kwargs["collection_name"] == COLLECTION_NAME
        point = call_args.kwargs["points"][0]

        # Verify payload structure
        assert point.payload["question_id"] == str(item.question_id)
        assert point.payload["course_id"] == str(item.course_id)
        assert point.payload["knowledge_area_id"] == item.knowledge_area_id
        assert point.payload["difficulty"] == item.difficulty
        assert point.payload["discrimination"] == item.discrimination
        assert point.payload["concept_ids"] == item.concept_ids
        assert point.payload["concept_names"] == item.concept_names
        assert point.payload["question_text"] == item.question_text
        assert point.payload["correct_answer"] == item.correct_answer

    @pytest.mark.asyncio
    async def test_upload_question_vector_skips_existing(self):
        """Test that existing vectors are skipped (idempotency)."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[MagicMock()])  # Vector exists
        mock_client.upsert = AsyncMock()

        service = QdrantUploadService(qdrant_client=mock_client)

        item = create_mock_vector_item()
        result = await service.upload_question_vector(item, skip_if_exists=True)

        assert result is False
        mock_client.upsert.assert_not_called()


class TestQdrantUploadServiceBatchUpload:
    """Tests for batch uploading vectors to Qdrant."""

    @pytest.mark.asyncio
    async def test_batch_upload_question_vectors(self):
        """Test batch upload of multiple vectors."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[])  # No existing vectors
        mock_client.upsert = AsyncMock()

        service = QdrantUploadService(qdrant_client=mock_client)

        items = [create_mock_vector_item() for _ in range(5)]

        uploaded, skipped = await service.batch_upload_question_vectors(
            items,
            skip_if_exists=False,
            batch_size=100
        )

        assert uploaded == 5
        assert skipped == 0
        mock_client.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_upload_skips_existing(self):
        """Test that batch upload skips existing vectors."""
        item1 = create_mock_vector_item()
        item2 = create_mock_vector_item()

        mock_client = AsyncMock()
        # First question exists, second doesn't
        mock_client.retrieve = AsyncMock(
            side_effect=[[MagicMock()], []]
        )
        mock_client.upsert = AsyncMock()

        service = QdrantUploadService(qdrant_client=mock_client)

        uploaded, skipped = await service.batch_upload_question_vectors(
            [item1, item2],
            skip_if_exists=True,
            batch_size=100
        )

        assert uploaded == 1
        assert skipped == 1
        # Only one upsert call (for item2)
        assert mock_client.upsert.call_count == 1


class TestQdrantUploadServiceVerification:
    """Tests for verifying Qdrant upload."""

    @pytest.mark.asyncio
    async def test_verify_collection_count_passes(self):
        """Test verification passes when count matches expected."""
        mock_client = AsyncMock()
        mock_collection_info = MagicMock()
        mock_collection_info.points_count = 500
        mock_client.get_collection = AsyncMock(return_value=mock_collection_info)

        service = QdrantUploadService(qdrant_client=mock_client)

        result = await service.verify_collection_count(expected_count=500)

        assert result["verified"] is True
        assert result["actual_count"] == 500
        mock_client.get_collection.assert_called_once_with(COLLECTION_NAME)

    @pytest.mark.asyncio
    async def test_verify_collection_count_fails(self):
        """Test verification fails when count doesn't match."""
        mock_client = AsyncMock()
        mock_collection_info = MagicMock()
        mock_collection_info.points_count = 400  # Wrong count
        mock_client.get_collection = AsyncMock(return_value=mock_collection_info)

        service = QdrantUploadService(qdrant_client=mock_client)

        result = await service.verify_collection_count(expected_count=500)

        assert result["verified"] is False

    @pytest.mark.asyncio
    async def test_verify_collection_count_handles_exception(self):
        """Test verification returns False on exception."""
        mock_client = AsyncMock()
        mock_client.get_collection = AsyncMock(side_effect=Exception("Connection error"))

        service = QdrantUploadService(qdrant_client=mock_client)

        result = await service.verify_collection_count(expected_count=500)

        assert result["verified"] is False
        assert "error" in result


class TestIdempotency:
    """Tests for idempotency - re-running upload shouldn't duplicate vectors."""

    @pytest.mark.asyncio
    async def test_rerun_skips_all_existing(self):
        """Test that re-running with all existing vectors skips all."""
        mock_client = AsyncMock()
        # All vectors exist
        mock_client.retrieve = AsyncMock(return_value=[MagicMock()])
        mock_client.upsert = AsyncMock()

        service = QdrantUploadService(qdrant_client=mock_client)

        items = [create_mock_vector_item() for _ in range(10)]

        uploaded, skipped = await service.batch_upload_question_vectors(
            items,
            skip_if_exists=True,
            batch_size=100
        )

        assert uploaded == 0
        assert skipped == 10
        mock_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_rerun_uploads_new_only(self):
        """Test that partial re-run uploads only new vectors."""
        items = [create_mock_vector_item() for _ in range(10)]

        mock_client = AsyncMock()
        # First 5 exist, last 5 don't
        side_effects = [[MagicMock()] if i < 5 else [] for i in range(10)]
        mock_client.retrieve = AsyncMock(side_effect=side_effects)
        mock_client.upsert = AsyncMock()

        service = QdrantUploadService(qdrant_client=mock_client)

        uploaded, skipped = await service.batch_upload_question_vectors(
            items,
            skip_if_exists=True,
            batch_size=100
        )

        assert uploaded == 5
        assert skipped == 5


class TestCollectionName:
    """Tests for collection name constant."""

    def test_collection_name_value(self):
        """Test that collection name is correct."""
        assert COLLECTION_NAME == "questions"
