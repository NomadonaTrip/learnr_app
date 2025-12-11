"""
Reading Search Service for semantic search fallback.

This service provides semantic search capabilities for reading chunks
using OpenAI embeddings and Qdrant vector database.
"""
from typing import List
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Filter, FieldCondition, MatchValue

from src.db.qdrant_client import get_qdrant
from src.models.reading_chunk import ReadingChunk
from src.repositories.reading_chunk_repository import ReadingChunkRepository
from src.services.embedding_service import EmbeddingService
from src.utils.logging_config import get_logger

logger = get_logger(__name__)

# Collection name for reading chunks in Qdrant
READING_CHUNKS_COLLECTION = "reading_chunks"


class ReadingSearchService:
    """
    Service for semantic search of reading chunks.

    Uses OpenAI embeddings and Qdrant vector database for similarity search
    with course-scoped filtering.
    """

    def __init__(
        self,
        qdrant_client: AsyncQdrantClient | None = None,
        embedding_service: EmbeddingService | None = None,
    ):
        """
        Initialize the Reading Search Service.

        Args:
            qdrant_client: Async Qdrant client (defaults to get_qdrant())
            embedding_service: Embedding service (defaults to new EmbeddingService())
        """
        self.qdrant_client = qdrant_client or get_qdrant()
        self.embedding_service = embedding_service or EmbeddingService()

    async def search_chunks_by_concept_names(
        self,
        course_id: UUID,
        concept_names: List[str],
        chunk_repository: ReadingChunkRepository,
        limit: int = 5,
    ) -> List[ReadingChunk]:
        """
        Search for reading chunks using semantic similarity to concept names.

        This is the fallback method when no chunks are found with direct
        concept_id filtering. It uses the concept names to generate a search
        query embedding and finds similar chunks via vector search.

        Args:
            course_id: Course UUID to filter by
            concept_names: List of concept names to search for
            chunk_repository: Repository to fetch full chunk objects
            limit: Maximum number of chunks to return

        Returns:
            List of ReadingChunk models ranked by semantic similarity

        Raises:
            Exception: If embedding generation or Qdrant search fails
        """
        if not concept_names:
            logger.warning(
                "semantic_search_with_empty_concepts",
                course_id=str(course_id),
            )
            return []

        # Combine concept names into search query
        search_text = " ".join(concept_names)
        logger.info(
            "semantic_search_initiated",
            course_id=str(course_id),
            search_text=search_text[:100],  # Log first 100 chars
            limit=limit,
        )

        try:
            # Generate embedding for search query
            query_embedding = await self.embedding_service.generate_embedding(
                search_text
            )

            # Search Qdrant with course filter
            search_results = await self.qdrant_client.search(
                collection_name=READING_CHUNKS_COLLECTION,
                query_vector=query_embedding,
                query_filter=Filter(
                    must=[
                        FieldCondition(
                            key="course_id", match=MatchValue(value=str(course_id))
                        )
                    ]
                ),
                limit=limit,
            )

            if not search_results:
                logger.info(
                    "semantic_search_no_results",
                    course_id=str(course_id),
                    concept_names=concept_names,
                )
                return []

            # Extract chunk_ids from search results
            chunk_ids = [UUID(result.payload["chunk_id"]) for result in search_results]

            logger.info(
                "semantic_search_results",
                course_id=str(course_id),
                results_count=len(chunk_ids),
                top_score=search_results[0].score if search_results else 0,
            )

            # Fetch full chunk objects from database
            chunks = []
            for chunk_id in chunk_ids:
                chunk = await chunk_repository.get_by_id(chunk_id)
                if chunk:
                    chunks.append(chunk)

            return chunks

        except Exception as e:
            logger.error(
                "semantic_search_failed",
                course_id=str(course_id),
                concept_names=concept_names,
                error=str(e),
            )
            raise

    async def close(self):
        """Clean up resources."""
        await self.embedding_service.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
