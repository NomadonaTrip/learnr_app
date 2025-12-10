"""
Unit tests for question embedding generation.

Tests the embedding text formatting, batch processing, and retry logic.
"""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "scripts"))
sys.path.insert(0, str(project_root / "apps" / "api"))

from generate_question_embeddings import (  # noqa: E402
    batch_list,
    calculate_cost,
    format_embedding_text,
    retry_with_backoff,
)


class MockQuestion:
    """Mock Question model for testing."""

    def __init__(
        self,
        question_text: str = "What is BABOK?",
        option_a: str = "Business Analysis Body of Knowledge",
        option_b: str = "A certification exam",
        option_c: str = "A project management tool",
        option_d: str = "None of the above",
    ):
        self.question_text = question_text
        self.option_a = option_a
        self.option_b = option_b
        self.option_c = option_c
        self.option_d = option_d


class TestFormatEmbeddingText:
    """Tests for format_embedding_text function."""

    def test_format_embedding_text_produces_correct_format(self):
        """Test that embedding text is formatted correctly with all options."""
        question = MockQuestion(
            question_text="What is the primary purpose of stakeholder analysis?",
            option_a="Identify stakeholders",
            option_b="Document requirements",
            option_c="Manage risks",
            option_d="Allocate resources",
        )

        result = format_embedding_text(question)

        expected = "What is the primary purpose of stakeholder analysis? Identify stakeholders Document requirements Manage risks Allocate resources"
        assert result == expected

    def test_format_embedding_text_basic(self):
        """Test basic embedding text formatting."""
        question = MockQuestion()

        result = format_embedding_text(question)

        expected = "What is BABOK? Business Analysis Body of Knowledge A certification exam A project management tool None of the above"
        assert result == expected

    def test_format_embedding_text_with_special_characters(self):
        """Test formatting with special characters in text."""
        question = MockQuestion(
            question_text="What's the difference between 'shall' & 'should'?",
            option_a="'Shall' = mandatory",
            option_b="'Should' = optional",
            option_c="No difference",
            option_d="Both are mandatory",
        )

        result = format_embedding_text(question)

        assert question.question_text in result
        assert question.option_a in result
        assert question.option_b in result
        assert question.option_c in result
        assert question.option_d in result

    def test_format_embedding_text_with_long_text(self):
        """Test formatting with long question text."""
        long_text = "A" * 500
        question = MockQuestion(question_text=long_text)

        result = format_embedding_text(question)

        assert long_text in result
        assert len(result) > len(long_text)


class TestBatchList:
    """Tests for batch_list utility function."""

    def test_batch_list_splits_correctly(self):
        """Test that list is split into correct batch sizes."""
        items = list(range(10))
        batches = list(batch_list(items, batch_size=3))

        assert len(batches) == 4
        assert batches[0] == [0, 1, 2]
        assert batches[1] == [3, 4, 5]
        assert batches[2] == [6, 7, 8]
        assert batches[3] == [9]

    def test_batch_list_with_exact_multiple(self):
        """Test batching when items are exact multiple of batch size."""
        items = list(range(100))
        batches = list(batch_list(items, batch_size=100))

        assert len(batches) == 1
        assert len(batches[0]) == 100

    def test_batch_list_with_500_items(self):
        """Test batching 500 questions into batches of 100."""
        items = list(range(500))
        batches = list(batch_list(items, batch_size=100))

        assert len(batches) == 5
        for batch in batches:
            assert len(batch) == 100

    def test_batch_list_empty(self):
        """Test batching empty list."""
        items = []
        batches = list(batch_list(items, batch_size=100))

        assert len(batches) == 0

    def test_batch_list_smaller_than_batch_size(self):
        """Test when items are fewer than batch size."""
        items = list(range(50))
        batches = list(batch_list(items, batch_size=100))

        assert len(batches) == 1
        assert len(batches[0]) == 50


class TestRetryWithBackoff:
    """Tests for retry_with_backoff function."""

    @pytest.mark.asyncio
    async def test_retry_succeeds_first_try(self):
        """Test successful call on first attempt."""
        mock_func = AsyncMock(return_value="success")

        result = await retry_with_backoff(mock_func)

        assert result == "success"
        assert mock_func.call_count == 1

    @pytest.mark.asyncio
    async def test_retry_succeeds_after_rate_limit(self):
        """Test retry succeeds after rate limit error."""
        from openai import RateLimitError

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}

        mock_func = AsyncMock(
            side_effect=[
                RateLimitError("Rate limit", response=mock_response, body=None),
                "success",
            ]
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            result = await retry_with_backoff(mock_func, max_retries=3, base_delay=0.01)

        assert result == "success"
        assert mock_func.call_count == 2

    @pytest.mark.asyncio
    async def test_retry_raises_after_max_retries(self):
        """Test that exception is raised after max retries exceeded."""
        from openai import RateLimitError

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}

        mock_func = AsyncMock(
            side_effect=RateLimitError("Rate limit", response=mock_response, body=None)
        )

        with patch("asyncio.sleep", new_callable=AsyncMock):
            with pytest.raises(RateLimitError):
                await retry_with_backoff(mock_func, max_retries=3, base_delay=0.01)

        assert mock_func.call_count == 3

    @pytest.mark.asyncio
    async def test_retry_exponential_backoff_timing(self):
        """Test that backoff waits use exponential timing."""
        from openai import RateLimitError

        mock_response = MagicMock()
        mock_response.status_code = 429
        mock_response.headers = {}

        mock_func = AsyncMock(
            side_effect=[
                RateLimitError("Rate limit", response=mock_response, body=None),
                RateLimitError("Rate limit", response=mock_response, body=None),
                "success",
            ]
        )

        sleep_times = []

        async def mock_sleep(duration):
            sleep_times.append(duration)

        with patch("asyncio.sleep", side_effect=mock_sleep):
            result = await retry_with_backoff(mock_func, max_retries=3, base_delay=1.0)

        assert result == "success"
        # First retry: 1.0 * (2^0) = 1.0
        # Second retry: 1.0 * (2^1) = 2.0
        assert sleep_times == [1.0, 2.0]


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
