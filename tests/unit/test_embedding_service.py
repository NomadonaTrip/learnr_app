"""
Unit tests for Embedding Service.

Tests embedding generation, batching, and retry logic.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from apps.api.src.services.embedding_service import EmbeddingService


# Mock response objects
class MockEmbeddingData:
    def __init__(self, embedding):
        self.embedding = embedding


class MockEmbeddingUsage:
    def __init__(self, total_tokens):
        self.total_tokens = total_tokens


class MockEmbeddingResponse:
    def __init__(self, embeddings, total_tokens):
        self.data = [MockEmbeddingData(emb) for emb in embeddings]
        self.usage = MockEmbeddingUsage(total_tokens)


@pytest.fixture
def mock_openai_client():
    """Create a mock OpenAI client."""
    client = MagicMock()
    client.embeddings = MagicMock()
    client.close = AsyncMock()
    return client


@pytest.fixture
async def embedding_service(mock_openai_client):
    """Create an EmbeddingService instance with mocked client."""
    with patch('apps.api.src.services.embedding_service.AsyncOpenAI', return_value=mock_openai_client):
        service = EmbeddingService(api_key="test-key")
        yield service
        await service.close()


class TestEmbeddingService:
    """Test suite for EmbeddingService."""

    @pytest.mark.asyncio
    async def test_generate_single_embedding(self, embedding_service, mock_openai_client):
        """Test generating a single embedding."""
        # Setup mock response
        expected_embedding = [0.1] * 3072
        mock_response = MockEmbeddingResponse([expected_embedding], total_tokens=10)
        mock_openai_client.embeddings.create = AsyncMock(return_value=mock_response)

        # Generate embedding
        result = await embedding_service.generate_embedding("test text")

        # Assertions
        assert result == expected_embedding
        assert len(result) == 3072
        mock_openai_client.embeddings.create.assert_called_once()

        # Check call arguments
        call_args = mock_openai_client.embeddings.create.call_args
        assert call_args.kwargs["model"] == "text-embedding-3-large"
        assert call_args.kwargs["input"] == ["test text"]
        assert call_args.kwargs["dimensions"] == 3072

    @pytest.mark.asyncio
    async def test_batch_generate_embeddings(self, embedding_service, mock_openai_client):
        """Test generating embeddings in batches."""
        # Setup mock response
        texts = [f"text {i}" for i in range(250)]  # 3 batches of 100
        embeddings = [[0.1 * (i + 1)] * 3072 for i in range(len(texts))]

        # Mock will be called 3 times (250 texts / 100 batch_size)
        mock_responses = [
            MockEmbeddingResponse(embeddings[0:100], total_tokens=1000),
            MockEmbeddingResponse(embeddings[100:200], total_tokens=1000),
            MockEmbeddingResponse(embeddings[200:250], total_tokens=500),
        ]
        mock_openai_client.embeddings.create = AsyncMock(side_effect=mock_responses)

        # Generate embeddings
        result_embeddings, total_tokens = await embedding_service.batch_generate_embeddings(
            texts, batch_size=100
        )

        # Assertions
        assert len(result_embeddings) == 250
        assert total_tokens == 2500
        assert mock_openai_client.embeddings.create.call_count == 3

    @pytest.mark.asyncio
    async def test_batch_generate_with_progress_callback(self, embedding_service, mock_openai_client):
        """Test batch generation with progress callback."""
        texts = [f"text {i}" for i in range(150)]
        embeddings = [[0.1] * 3072 for _ in range(len(texts))]

        mock_responses = [
            MockEmbeddingResponse(embeddings[0:100], total_tokens=1000),
            MockEmbeddingResponse(embeddings[100:150], total_tokens=500),
        ]
        mock_openai_client.embeddings.create = AsyncMock(side_effect=mock_responses)

        # Track progress callbacks
        progress_calls = []

        def progress_callback(processed, total):
            progress_calls.append((processed, total))

        # Generate embeddings
        await embedding_service.batch_generate_embeddings(
            texts, batch_size=100, progress_callback=progress_callback
        )

        # Assertions
        assert len(progress_calls) == 2
        assert progress_calls[0] == (100, 150)
        assert progress_calls[1] == (150, 150)

    @pytest.mark.asyncio
    async def test_batch_size_exceeds_maximum(self, embedding_service):
        """Test that batch size exceeding maximum raises ValueError."""
        texts = ["text"] * 200

        with pytest.raises(ValueError, match="exceeds maximum"):
            await embedding_service.batch_generate_embeddings(texts, batch_size=150)

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, embedding_service, mock_openai_client):
        """Test retry logic on rate limit error."""
        from openai import RateLimitError

        # First call raises RateLimitError, second succeeds
        expected_embedding = [0.1] * 3072
        mock_response = MockEmbeddingResponse([expected_embedding], total_tokens=10)

        mock_openai_client.embeddings.create = AsyncMock(
            side_effect=[
                RateLimitError("Rate limit exceeded", response=MagicMock(), body=None),
                mock_response
            ]
        )

        # Generate embedding (should retry and succeed)
        result = await embedding_service.generate_embedding("test text")

        # Assertions
        assert result == expected_embedding
        assert mock_openai_client.embeddings.create.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_exhausted(self, embedding_service, mock_openai_client):
        """Test that retry is exhausted after max attempts."""
        from openai import RateLimitError

        # All calls raise RateLimitError
        mock_openai_client.embeddings.create = AsyncMock(
            side_effect=RateLimitError("Rate limit exceeded", response=MagicMock(), body=None)
        )

        # Generate embedding (should fail after retries)
        with pytest.raises(RateLimitError):
            await embedding_service.generate_embedding("test text")

        # Should have attempted 3 times
        assert mock_openai_client.embeddings.create.call_count == 3

    @pytest.mark.asyncio
    async def test_context_manager(self, mock_openai_client):
        """Test async context manager usage."""
        with patch('apps.api.src.services.embedding_service.AsyncOpenAI', return_value=mock_openai_client):
            async with EmbeddingService(api_key="test-key") as service:
                assert service is not None

            # Client should be closed
            mock_openai_client.close.assert_called_once()


class TestEmbeddingTextBuilding:
    """Test suite for building embedding texts from questions."""

    def test_build_embedding_text_with_concepts(self):
        """Test building embedding text with concepts."""
        from scripts.generate_question_embeddings import build_embedding_text
        from apps.api.src.models.question import Question
        from apps.api.src.models.concept import Concept
        from uuid import uuid4

        # Create mock question
        question = Question(
            id=uuid4(),
            course_id=uuid4(),
            question_text="Which technique is BEST?",
            options={
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
            },
            correct_answer="B",
            explanation="Explanation",
            knowledge_area_id="ba-planning",
            difficulty=0.5
        )

        # Create mock concepts
        concepts = [
            Concept(id=uuid4(), course_id=question.course_id, name="Stakeholder Analysis"),
            Concept(id=uuid4(), course_id=question.course_id, name="Communication Planning"),
        ]

        # Build text
        text = build_embedding_text(question, concepts)

        # Assertions
        assert "Which technique is BEST?" in text
        assert "Options:" in text
        assert "A: Option A" in text
        assert "B: Option B" in text
        assert "C: Option C" in text
        assert "D: Option D" in text
        assert "Concepts: Stakeholder Analysis, Communication Planning" in text

    def test_build_embedding_text_without_concepts(self):
        """Test building embedding text without concepts (fallback to KA)."""
        from scripts.generate_question_embeddings import build_embedding_text
        from apps.api.src.models.question import Question
        from uuid import uuid4

        # Create mock question
        question = Question(
            id=uuid4(),
            course_id=uuid4(),
            question_text="Test question?",
            options={
                "A": "Option A",
                "B": "Option B",
                "C": "Option C",
                "D": "Option D"
            },
            correct_answer="A",
            explanation="Explanation",
            knowledge_area_id="ba-planning",
            difficulty=0.5
        )

        # Build text without concepts
        text = build_embedding_text(question, [])

        # Assertions
        assert "Test question?" in text
        assert "Knowledge Area: ba-planning" in text
        assert "Concepts:" not in text

    def test_build_embedding_text_truncates_long_text(self):
        """Test that very long embedding text is truncated."""
        from scripts.generate_question_embeddings import build_embedding_text
        from apps.api.src.models.question import Question
        from uuid import uuid4

        # Create question with very long text
        long_text = "A" * 40000  # Exceeds max chars
        question = Question(
            id=uuid4(),
            course_id=uuid4(),
            question_text=long_text,
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Explanation",
            knowledge_area_id="ba-planning",
            difficulty=0.5
        )

        # Build text
        text = build_embedding_text(question, [])

        # Assertions
        MAX_CHARS = 8000 * 4
        assert len(text) <= MAX_CHARS
