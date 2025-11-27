"""
Qdrant client configuration and connection management
Provides async Qdrant connection for vector database operations
"""

import logging
from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse
from src.config import settings

logger = logging.getLogger(__name__)

# Global Qdrant async client instance
qdrant_client: AsyncQdrantClient | None = None


def get_qdrant() -> AsyncQdrantClient:
    """
    Get async Qdrant client instance (singleton pattern).

    Returns:
        AsyncQdrantClient: Async Qdrant client instance

    Raises:
        UnexpectedResponse: If connection to Qdrant fails
    """
    global qdrant_client

    if qdrant_client is None:
        try:
            qdrant_client = AsyncQdrantClient(
                url=settings.QDRANT_URL,
                api_key=settings.QDRANT_API_KEY,
                timeout=settings.QDRANT_TIMEOUT
            )
            logger.info(f"Async Qdrant client initialized: {settings.QDRANT_URL}")
        except Exception as e:
            logger.error(f"Failed to initialize async Qdrant client: {str(e)}")
            raise

    return qdrant_client


async def close_qdrant() -> None:
    """
    Close async Qdrant client connection and cleanup.
    Should be called during application shutdown.
    """
    global qdrant_client
    if qdrant_client:
        await qdrant_client.close()
        qdrant_client = None
        logger.info("Async Qdrant client closed")


async def test_qdrant_connection() -> bool:
    """
    Test async Qdrant connection by fetching collections.

    Returns:
        bool: True if connection successful, False otherwise
    """
    try:
        client = get_qdrant()
        collections = await client.get_collections()
        logger.info(f"Qdrant connection successful. Collections: {len(collections.collections)}")
        return True
    except Exception as e:
        logger.error(f"Qdrant connection test failed: {str(e)}")
        return False
