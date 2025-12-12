"""
Embedding Service for generating OpenAI embeddings.

This service provides async methods for generating embeddings using OpenAI's
text-embedding-3-large model with batching and retry logic.
"""
from typing import TYPE_CHECKING

from openai import APIConnectionError, APIError, AsyncOpenAI, RateLimitError
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from ..config import settings
from ..utils.logging_config import get_logger

if TYPE_CHECKING:
    from ..models.concept import Concept
    from ..models.reading_chunk import ReadingChunk

logger = get_logger(__name__)

# Constants
EMBEDDING_MODEL = "text-embedding-3-large"
EMBEDDING_DIMENSIONS = 3072
MAX_BATCH_SIZE = 100  # OpenAI allows up to 2048, but we use 100 for safety
MAX_EMBEDDING_TOKENS = 8000  # OpenAI limit for text-embedding-3-large


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
    async def generate_embedding(self, text: str) -> list[float]:
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
    async def _batch_embed_texts(self, texts: list[str]) -> tuple[list[list[float]], int]:
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
        texts: list[str],
        batch_size: int = MAX_BATCH_SIZE,
        progress_callback=None
    ) -> tuple[list[list[float]], int]:
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

    @staticmethod
    def build_chunk_embedding_text(
        chunk: "ReadingChunk",
        concepts: list["Concept"]
    ) -> str:
        """
        Build embedding text for a reading chunk with concept metadata.

        Format: "{title}. {content} Concepts: {concept_names}"

        Args:
            chunk: ReadingChunk model with title and content
            concepts: List of Concept models linked to the chunk

        Returns:
            Formatted text string for embedding generation

        Examples:
            >>> chunk = ReadingChunk(title="Stakeholder Analysis", content="...", corpus_section="3.2.1")
            >>> concepts = [Concept(name="Stakeholder Analysis"), Concept(name="Communication")]
            >>> text = EmbeddingService.build_chunk_embedding_text(chunk, concepts)
            >>> # "Stakeholder Analysis. ... Concepts: Stakeholder Analysis, Communication"
        """
        # Build concept names string
        if concepts:
            concept_names = ", ".join([c.name for c in concepts])
            embedding_text = f"{chunk.title}. {chunk.content} Concepts: {concept_names}"
        else:
            # Fallback: use section reference if no concepts
            logger.warning(
                "chunk_has_no_concepts",
                chunk_id=str(chunk.id),
                section=chunk.corpus_section
            )
            embedding_text = f"{chunk.title}. {chunk.content} Section: {chunk.corpus_section}"

        # Truncate if exceeds max tokens (rare for 200-500 token chunks)
        # Rough estimate: 1 token ~= 4 characters
        max_chars = MAX_EMBEDDING_TOKENS * 4
        if len(embedding_text) > max_chars:
            logger.warning(
                "truncating_chunk_embedding_text",
                chunk_id=str(chunk.id),
                original_length=len(embedding_text),
                truncated_length=max_chars
            )
            embedding_text = embedding_text[:max_chars]

        return embedding_text

    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
