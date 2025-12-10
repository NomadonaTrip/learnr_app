"""
Embedding Service for generating OpenAI embeddings.

This service provides async methods for generating embeddings using OpenAI's
text-embedding-3-large model with batching and retry logic.
"""
from typing import List

from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072
MAX_BATCH_SIZE = 100  # OpenAI allows up to 2048, but we use 100 for safety


class EmbeddingService:
    """
    Service for generating embeddings using OpenAI API.

    Provides batch processing, retry logic with exponential backoff,
    and proper error handling for rate limits and API errors.
    """

    def __init__(self, api_key: str | None = None):
        """
        Initialize the Embedding Service.

        Args:
            api_key: OpenAI API key (defaults to settings.OPENAI_API_KEY)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = EMBEDDING_MODEL
        self.dimensions = EMBEDDING_DIMENSIONS

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector (3072 dimensions)

        Raises:
            RateLimitError: If rate limit exceeded after retries
            APIError: If API error occurs after retries
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=[text],
            dimensions=self.dimensions
        )
        return response.data[0].embedding

    @retry(
        retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=60),
        reraise=True,
    )
    async def _batch_embed_texts(self, texts: List[str]) -> tuple[List[List[float]], int]:
        """
        Internal method to generate embeddings for a batch of texts with retry.

        Args:
            texts: List of texts to embed (max 100)

        Returns:
            Tuple of (embeddings, tokens_used)

        Raises:
            RateLimitError: If rate limit exceeded after retries
            APIError: If API error occurs after retries
        """
        if len(texts) > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {len(texts)} exceeds maximum {MAX_BATCH_SIZE}")

        response = await self.client.embeddings.create(
            model=self.model,
            input=texts,
            dimensions=self.dimensions
        )

        embeddings = [item.embedding for item in response.data]
        tokens_used = response.usage.total_tokens

        return embeddings, tokens_used

    async def batch_generate_embeddings(
        self,
        texts: List[str],
        batch_size: int = MAX_BATCH_SIZE,
        progress_callback=None
    ) -> tuple[List[List[float]], int]:
        """
        Generate embeddings for multiple texts in batches.

        Args:
            texts: List of texts to embed
            batch_size: Number of texts per API call (default: 100)
            progress_callback: Optional callback function(processed, total) for progress tracking

        Returns:
            Tuple of (list of embedding vectors, total tokens used)

        Raises:
            ValueError: If batch_size exceeds MAX_BATCH_SIZE
        """
        if batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {batch_size} exceeds maximum {MAX_BATCH_SIZE}")

        all_embeddings = []
        total_tokens = 0
        processed_count = 0

        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                embeddings, tokens = await self._batch_embed_texts(batch)
                all_embeddings.extend(embeddings)
                total_tokens += tokens
                processed_count += len(batch)

                # Call progress callback if provided
                if progress_callback:
                    progress_callback(processed_count, len(texts))

                logger.debug(
                    "embedded_batch",
                    batch_number=i // batch_size + 1,
                    processed=processed_count,
                    total=len(texts),
                    tokens=tokens
                )

            except (RateLimitError, APIError) as e:
                logger.error("batch_embedding_failed", batch_start_index=i, error=str(e))
                raise

        logger.info(
            "embedding_generation_complete",
            embeddings_count=len(all_embeddings),
            total_tokens=total_tokens
        )

        return all_embeddings, total_tokens

    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
