"""
Integration tests for question embedding generation and Qdrant upload.

Tests the full workflow from PostgreSQL fetch to Qdrant upload.
"""
import json
import sys
import uuid
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "apps" / "api"))

from generate_question_embeddings import (  # noqa: E402
    COLLECTION_NAME,
    EMBEDDING_DIMENSIONS,
    fetch_all_questions,
    upload_vectors_to_qdrant,
    vector_exists,
    verify_qdrant_upload,
)


class MockQuestion:
    """Mock Question model for testing."""

    _UNSET = object()  # Sentinel to distinguish None from unset

    def __init__(
        self,
        id=None,
        question_text: str = "What is BABOK?",
        option_a: str = "Business Analysis Body of Knowledge",
        option_b: str = "A certification exam",
        option_c: str = "A project management tool",
        option_d: str = "None of the above",
        correct_answer: str = "A",
        ka: str = "Business Analysis Planning and Monitoring",
        difficulty: str = "Medium",
        concept_tags=_UNSET,
    ):
        self.id = id or uuid.uuid4()
        self.question_text = question_text
        self.option_a = option_a
        self.option_b = option_b
        self.option_c = option_c
        self.option_d = option_d
        self.correct_answer = correct_answer
        self.ka = ka
        self.difficulty = difficulty
        # Use sentinel to distinguish explicit None from default
        if concept_tags is MockQuestion._UNSET:
            self.concept_tags = ["babok", "fundamentals"]
        else:
            self.concept_tags = concept_tags


class TestFetchAllQuestions:
    """Tests for fetching questions from PostgreSQL."""

    @pytest.mark.asyncio
    async def test_fetch_all_questions_returns_questions(self, db_session):
        """Test that questions are fetched from database successfully."""
        # This test uses the actual test database
        # Questions should be seeded by fixtures
        questions = await fetch_all_questions(db_session)

        # Should return a list (may be empty in test environment)
        assert isinstance(questions, list)

    @pytest.mark.asyncio
    async def test_fetch_all_questions_with_mock_db(self):
        """Test fetch with mocked database session."""
        mock_questions = [MockQuestion() for _ in range(5)]

        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = mock_questions

        mock_db = AsyncMock()
        mock_db.execute = AsyncMock(return_value=mock_result)

        questions = await fetch_all_questions(mock_db)

        assert len(questions) == 5
        mock_db.execute.assert_called_once()


class TestVectorExists:
    """Tests for checking vector existence in Qdrant."""

    @pytest.mark.asyncio
    async def test_vector_exists_returns_true_when_found(self):
        """Test that vector_exists returns True when vector is found."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[MagicMock()])

        question_id = str(uuid.uuid4())
        result = await vector_exists(mock_client, question_id)

        assert result is True
        mock_client.retrieve.assert_called_once_with(
            collection_name=COLLECTION_NAME,
            ids=[question_id]
        )

    @pytest.mark.asyncio
    async def test_vector_exists_returns_false_when_not_found(self):
        """Test that vector_exists returns False when vector is not found."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[])

        question_id = str(uuid.uuid4())
        result = await vector_exists(mock_client, question_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_vector_exists_returns_false_on_exception(self):
        """Test that vector_exists returns False on exception."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(side_effect=Exception("Connection error"))

        question_id = str(uuid.uuid4())
        result = await vector_exists(mock_client, question_id)

        assert result is False


class TestUploadVectorsToQdrant:
    """Tests for uploading vectors to Qdrant."""

    @pytest.mark.asyncio
    async def test_upload_vectors_with_correct_payload(self):
        """Test that vectors are uploaded with correct payload structure."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[])  # No existing vectors
        mock_client.upsert = AsyncMock()

        question = MockQuestion(
            ka="Business Analysis Planning and Monitoring",
            difficulty="Medium",
            concept_tags=["planning", "monitoring"],
        )
        embedding = [0.1] * EMBEDDING_DIMENSIONS

        uploaded, skipped = await upload_vectors_to_qdrant(
            mock_client,
            [question],
            [embedding],
            dry_run=False
        )

        assert uploaded == 1
        assert skipped == 0

        # Verify upsert was called
        mock_client.upsert.assert_called_once()
        call_args = mock_client.upsert.call_args

        assert call_args.kwargs["collection_name"] == COLLECTION_NAME
        point = call_args.kwargs["points"][0]

        # Verify payload structure
        assert point.payload["question_id"] == str(question.id)
        assert point.payload["ka"] == question.ka
        assert point.payload["difficulty"] == question.difficulty
        assert point.payload["concept_tags"] == question.concept_tags
        assert point.payload["question_text"] == question.question_text
        assert point.payload["correct_answer"] == question.correct_answer

        # Verify options is JSON string
        options = json.loads(point.payload["options"])
        assert options["a"] == question.option_a
        assert options["b"] == question.option_b
        assert options["c"] == question.option_c
        assert options["d"] == question.option_d

    @pytest.mark.asyncio
    async def test_upload_vectors_skips_existing(self):
        """Test that existing vectors are skipped (idempotency)."""
        question1 = MockQuestion()
        question2 = MockQuestion()

        mock_client = AsyncMock()
        # First question exists, second doesn't
        mock_client.retrieve = AsyncMock(
            side_effect=[[MagicMock()], []]
        )
        mock_client.upsert = AsyncMock()

        embeddings = [[0.1] * EMBEDDING_DIMENSIONS for _ in range(2)]

        uploaded, skipped = await upload_vectors_to_qdrant(
            mock_client,
            [question1, question2],
            embeddings,
            dry_run=False
        )

        assert uploaded == 1
        assert skipped == 1
        # Only one upsert call (for question2)
        assert mock_client.upsert.call_count == 1

    @pytest.mark.asyncio
    async def test_upload_vectors_dry_run(self):
        """Test that dry run doesn't actually upload."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[])  # No existing vectors

        questions = [MockQuestion() for _ in range(5)]
        embeddings = [[0.1] * EMBEDDING_DIMENSIONS for _ in range(5)]

        uploaded, skipped = await upload_vectors_to_qdrant(
            mock_client,
            questions,
            embeddings,
            dry_run=True
        )

        assert uploaded == 5
        assert skipped == 0
        # No upsert calls in dry run
        mock_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_upload_vectors_handles_empty_concept_tags(self):
        """Test that empty concept_tags are handled correctly."""
        mock_client = AsyncMock()
        mock_client.retrieve = AsyncMock(return_value=[])
        mock_client.upsert = AsyncMock()

        question = MockQuestion(concept_tags=None)
        embedding = [0.1] * EMBEDDING_DIMENSIONS

        await upload_vectors_to_qdrant(
            mock_client,
            [question],
            [embedding],
            dry_run=False
        )

        call_args = mock_client.upsert.call_args
        point = call_args.kwargs["points"][0]
        assert point.payload["concept_tags"] == []


class TestVerifyQdrantUpload:
    """Tests for verifying Qdrant upload."""

    @pytest.mark.asyncio
    async def test_verify_returns_true_when_count_matches(self):
        """Test verification passes when count matches expected."""
        mock_client = AsyncMock()
        mock_collection_info = MagicMock()
        mock_collection_info.points_count = 500
        mock_client.get_collection = AsyncMock(return_value=mock_collection_info)

        result = await verify_qdrant_upload(mock_client)

        assert result is True
        mock_client.get_collection.assert_called_once_with(COLLECTION_NAME)

    @pytest.mark.asyncio
    async def test_verify_returns_false_when_count_wrong(self):
        """Test verification fails when count doesn't match."""
        mock_client = AsyncMock()
        mock_collection_info = MagicMock()
        mock_collection_info.points_count = 400  # Wrong count
        mock_client.get_collection = AsyncMock(return_value=mock_collection_info)

        result = await verify_qdrant_upload(mock_client)

        assert result is False

    @pytest.mark.asyncio
    async def test_verify_returns_false_on_exception(self):
        """Test verification returns False on exception."""
        mock_client = AsyncMock()
        mock_client.get_collection = AsyncMock(side_effect=Exception("Connection error"))

        result = await verify_qdrant_upload(mock_client)

        assert result is False


class TestIdempotency:
    """Tests for idempotency - re-running script shouldn't duplicate vectors."""

    @pytest.mark.asyncio
    async def test_rerun_skips_all_existing(self):
        """Test that re-running with all existing vectors skips all."""
        mock_client = AsyncMock()
        # All vectors exist
        mock_client.retrieve = AsyncMock(return_value=[MagicMock()])
        mock_client.upsert = AsyncMock()

        questions = [MockQuestion() for _ in range(10)]
        embeddings = [[0.1] * EMBEDDING_DIMENSIONS for _ in range(10)]

        uploaded, skipped = await upload_vectors_to_qdrant(
            mock_client,
            questions,
            embeddings,
            dry_run=False
        )

        assert uploaded == 0
        assert skipped == 10
        mock_client.upsert.assert_not_called()

    @pytest.mark.asyncio
    async def test_partial_rerun_uploads_new_only(self):
        """Test that partial re-run uploads only new vectors."""
        questions = [MockQuestion() for _ in range(10)]

        mock_client = AsyncMock()
        # First 5 exist, last 5 don't
        side_effects = [[MagicMock()] if i < 5 else [] for i in range(10)]
        mock_client.retrieve = AsyncMock(side_effect=side_effects)
        mock_client.upsert = AsyncMock()

        embeddings = [[0.1] * EMBEDDING_DIMENSIONS for _ in range(10)]

        uploaded, skipped = await upload_vectors_to_qdrant(
            mock_client,
            questions,
            embeddings,
            dry_run=False
        )

        assert uploaded == 5
        assert skipped == 5
        assert mock_client.upsert.call_count == 5
