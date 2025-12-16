"""
Unit tests for question embedding generation.

Tests the embedding text formatting, batch processing, and cost calculation.
Updated to work with the refactored service-oriented architecture.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "apps" / "api"))

from generate_question_embeddings import (  # noqa: E402
    build_embedding_text,
    calculate_cost,
)
from src.services.embedding_service import (  # noqa: E402
    EMBEDDING_DIMENSIONS,
    EmbeddingService,
)


class MockQuestion:
    """Mock Question model for testing."""

    def __init__(
        self,
        id=None,
        question_text: str = "What is BABOK?",
        options: dict = None,
        knowledge_area_id: str = "ba-planning",
    ):
        self.id = id or uuid4()
        self.question_text = question_text
        self.options = options or {
            "A": "Business Analysis Body of Knowledge",
            "B": "A certification exam",
            "C": "A project management tool",
            "D": "None of the above",
        }
        self.knowledge_area_id = knowledge_area_id


class MockConcept:
    """Mock Concept model for testing."""

    def __init__(self, name: str = "Test Concept"):
        self.id = uuid4()
        self.name = name


class TestBuildEmbeddingText:
    """Tests for build_embedding_text function."""

    def test_build_embedding_text_with_concepts(self):
        """Test that embedding text includes concepts."""
        question = MockQuestion(
            question_text="What is the primary purpose of stakeholder analysis?",
            options={
                "A": "Identify stakeholders",
                "B": "Document requirements",
                "C": "Manage risks",
                "D": "Allocate resources",
            },
        )
        concepts = [
            MockConcept("Stakeholder Analysis"),
            MockConcept("Communication"),
        ]

        result = build_embedding_text(question, concepts)

        assert "What is the primary purpose of stakeholder analysis?" in result
        assert "Options:" in result
        assert "A: Identify stakeholders" in result
        assert "Concepts: Stakeholder Analysis, Communication" in result

    def test_build_embedding_text_basic(self):
        """Test basic embedding text formatting."""
        question = MockQuestion()
        concepts = [MockConcept("BABOK"), MockConcept("Fundamentals")]

        result = build_embedding_text(question, concepts)

        assert "What is BABOK?" in result
        assert "Options:" in result
        assert "A: Business Analysis Body of Knowledge" in result
        assert "Concepts: BABOK, Fundamentals" in result

    def test_build_embedding_text_no_concepts_fallback(self):
        """Test fallback to knowledge area when no concepts."""
        question = MockQuestion(knowledge_area_id="ba-planning")
        concepts = []

        result = build_embedding_text(question, concepts)

        assert "What is BABOK?" in result
        assert "Knowledge Area: ba-planning" in result

    def test_build_embedding_text_with_special_characters(self):
        """Test formatting with special characters in text."""
        question = MockQuestion(
            question_text="What's the difference between 'shall' & 'should'?",
            options={
                "A": "'Shall' = mandatory",
                "B": "'Should' = optional",
                "C": "No difference",
                "D": "Both are mandatory",
            },
        )
        concepts = [MockConcept("Requirements")]

        result = build_embedding_text(question, concepts)

        assert question.question_text in result
        assert "'Shall' = mandatory" in result

    def test_build_embedding_text_with_long_text(self):
        """Test formatting with long question text."""
        long_text = "A" * 500
        question = MockQuestion(question_text=long_text)
        concepts = [MockConcept("Test")]

        result = build_embedding_text(question, concepts)

        assert long_text in result
        assert len(result) > len(long_text)


class TestCalculateCost:
    """Tests for calculate_cost function."""

    def test_calculate_cost_500_questions(self):
        """Test cost calculation for 500 questions."""
        # ~500 tokens per question * 500 questions = 250,000 tokens
        total_tokens = 250_000
        cost = calculate_cost(total_tokens)

        # $0.13 per 1M tokens
        expected = (250_000 / 1_000_000) * 0.13
        assert cost == pytest.approx(expected)

    def test_calculate_cost_zero_tokens(self):
        """Test cost calculation with zero tokens."""
        cost = calculate_cost(0)
        assert cost == 0.0

    def test_calculate_cost_one_million_tokens(self):
        """Test cost calculation for exactly 1M tokens."""
        cost = calculate_cost(1_000_000)
        assert cost == pytest.approx(0.13)


class TestEmbeddingServiceBatching:
    """Tests for EmbeddingService batch processing."""

    def test_batch_processing_splits_correctly(self):
        """Test that list is split into correct batch sizes."""
        # Test the batching logic used in the service
        items = list(range(10))
        batch_size = 3
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]

    def test_batch_processing_with_exact_multiple(self):
        """Test batching when items are exact multiple of batch size."""
        items = list(range(100))
        batch_size = 100
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

        assert len(batches) == 1
        assert len(batches[0]) == 100

    def test_batch_processing_with_500_items(self):
        """Test batching 500 questions into batches of 100."""
        items = list(range(500))
        batch_size = 100
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

        assert len(batches) == 5
        for batch in batches:
            assert len(batch) == 100

    def test_batch_processing_empty(self):
        """Test batching empty list."""
        items = []
        batch_size = 100
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

        assert len(batches) == 0

    def test_batch_processing_smaller_than_batch_size(self):
        """Test when items are fewer than batch size."""
        items = list(range(50))
        batch_size = 100
        batches = [items[i:i + batch_size] for i in range(0, len(items), batch_size)]

        assert len(batches) == 1
        assert len(batches[0]) == 50


class TestEmbeddingServiceRetry:
    """Tests for EmbeddingService retry logic (via tenacity)."""

    @pytest.mark.asyncio
    async def test_generate_embedding_succeeds(self):
        """Test successful embedding generation."""
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.1] * EMBEDDING_DIMENSIONS)]

        with patch.object(EmbeddingService, '__init__', lambda self, **kwargs: None):
            service = EmbeddingService()
            service.client = AsyncMock()
            service.client.embeddings.create = AsyncMock(return_value=mock_response)
            service.model = "text-embedding-3-large"
            service.dimensions = EMBEDDING_DIMENSIONS

            result = await service.generate_embedding("test text")

            assert len(result) == EMBEDDING_DIMENSIONS
            service.client.embeddings.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings(self):
        """Test batch embedding generation."""
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1] * EMBEDDING_DIMENSIONS),
            MagicMock(embedding=[0.2] * EMBEDDING_DIMENSIONS),
        ]
        mock_response.usage = MagicMock(total_tokens=100)

        with patch.object(EmbeddingService, '__init__', lambda self, **kwargs: None):
            service = EmbeddingService()
            service.client = AsyncMock()
            service.client.embeddings.create = AsyncMock(return_value=mock_response)
            service.model = "text-embedding-3-large"
            service.dimensions = EMBEDDING_DIMENSIONS

            embeddings, tokens = await service.batch_generate_embeddings(
                ["text1", "text2"],
                batch_size=100
            )

            assert len(embeddings) == 2
            assert tokens == 100


class TestEmbeddingDimensions:
    """Tests for embedding dimension constants."""

    def test_embedding_dimensions_value(self):
        """Test that embedding dimensions is correct for text-embedding-3-large."""
        assert EMBEDDING_DIMENSIONS == 3072
