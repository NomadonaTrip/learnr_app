"""
Qdrant Repository
Provides data access layer for vector database operations
"""

import logging
from uuid import UUID
from typing import List, Dict, Any

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct, Filter, FieldCondition, MatchValue
from qdrant_client.http.exceptions import UnexpectedResponse

from src.db.qdrant_client import get_qdrant

logger = logging.getLogger(__name__)


class QdrantRepository:
    """Repository for async Qdrant vector database operations"""

    def __init__(self):
        """Initialize repository with async Qdrant client"""
        self.client: AsyncQdrantClient = get_qdrant()

    # =========================================================================
    # Question Vector Methods
    # =========================================================================

    async def create_question_vector(
        self,
        question_id: UUID,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """
        Insert question vector into Qdrant.

        Args:
            question_id: Question UUID
            vector: 3072-dimensional embedding vector from text-embedding-3-large
            payload: Metadata dict with keys:
                - question_id: str (UUID as string)
                - ka: str (Knowledge Area)
                - difficulty: str (Easy/Medium/Hard)
                - concept_tags: List[str]
                - question_text: str
                - options: str (formatted options)
                - correct_answer: str

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            point = PointStruct(
                id=str(question_id),
                vector=vector,
                payload=payload
            )

            await self.client.upsert(
                collection_name="cbap_questions",
                points=[point]
            )

            logger.info(f"Created question vector: {question_id}")

        except Exception as e:
            logger.error(f"Failed to create question vector {question_id}: {str(e)}")
            raise

    async def get_question_vector(self, question_id: UUID) -> Dict[str, Any] | None:
        """
        Retrieve question vector by ID.

        Args:
            question_id: Question UUID

        Returns:
            Dict with vector and payload if found, None otherwise

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            result = await self.client.retrieve(
                collection_name="cbap_questions",
                ids=[str(question_id)],
                with_vectors=True
            )

            if result:
                point = result[0]
                return {
                    "id": point.id,
                    "vector": point.vector,
                    "payload": point.payload
                }
            return None

        except Exception as e:
            logger.error(f"Failed to retrieve question vector {question_id}: {str(e)}")
            raise

    async def search_questions(
        self,
        query_vector: List[float],
        filters: Dict[str, Any] | None = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for questions.

        Args:
            query_vector: 3072-dimensional query embedding
            filters: Optional filters dict with keys:
                - ka: str (filter by Knowledge Area)
                - difficulty: str (filter by difficulty level)
                - concept_tags: str (filter by concept tag)
            limit: Maximum results to return (default: 10)

        Returns:
            List of dicts with keys: id, score, payload

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            # Build filter conditions
            filter_conditions = None
            if filters:
                must_conditions = []

                if "ka" in filters:
                    must_conditions.append(
                        FieldCondition(
                            key="ka",
                            match=MatchValue(value=filters["ka"])
                        )
                    )

                if "difficulty" in filters:
                    must_conditions.append(
                        FieldCondition(
                            key="difficulty",
                            match=MatchValue(value=filters["difficulty"])
                        )
                    )

                if "concept_tags" in filters:
                    must_conditions.append(
                        FieldCondition(
                            key="concept_tags",
                            match=MatchValue(value=filters["concept_tags"])
                        )
                    )

                if must_conditions:
                    filter_conditions = Filter(must=must_conditions)

            # Execute async search
            results = await self.client.search(
                collection_name="cbap_questions",
                query_vector=query_vector,
                query_filter=filter_conditions,
                limit=limit
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Failed to search questions: {str(e)}")
            raise

    async def delete_question_vector(self, question_id: UUID) -> None:
        """
        Delete question vector from Qdrant.

        Args:
            question_id: Question UUID

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            await self.client.delete(
                collection_name="cbap_questions",
                points_selector=[str(question_id)]
            )

            logger.info(f"Deleted question vector: {question_id}")

        except Exception as e:
            logger.error(f"Failed to delete question vector {question_id}: {str(e)}")
            raise

    # =========================================================================
    # BABOK Chunk Vector Methods
    # =========================================================================

    async def create_chunk_vector(
        self,
        chunk_id: UUID,
        vector: List[float],
        payload: Dict[str, Any]
    ) -> None:
        """
        Insert BABOK chunk vector into Qdrant.

        Args:
            chunk_id: Chunk UUID
            vector: 3072-dimensional embedding vector
            payload: Metadata dict with keys:
                - chunk_id: str (UUID as string)
                - ka: str (Knowledge Area)
                - section_ref: str (BABOK section reference)
                - difficulty: str (Easy/Medium/Hard)
                - concept_tags: List[str]
                - text_content: str (chunk text)

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            point = PointStruct(
                id=str(chunk_id),
                vector=vector,
                payload=payload
            )

            await self.client.upsert(
                collection_name="babok_chunks",
                points=[point]
            )

            logger.info(f"Created chunk vector: {chunk_id}")

        except Exception as e:
            logger.error(f"Failed to create chunk vector {chunk_id}: {str(e)}")
            raise

    async def search_chunks(
        self,
        query_vector: List[float],
        filters: Dict[str, Any] | None = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for BABOK chunks.

        Args:
            query_vector: 3072-dimensional query embedding
            filters: Optional filters dict with keys:
                - ka: str (filter by Knowledge Area)
                - section_ref: str (filter by BABOK section)
                - difficulty: str (filter by difficulty level)
            limit: Maximum results to return (default: 3)

        Returns:
            List of dicts with keys: id, score, payload

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            # Build filter conditions
            filter_conditions = None
            if filters:
                must_conditions = []

                if "ka" in filters:
                    must_conditions.append(
                        FieldCondition(
                            key="ka",
                            match=MatchValue(value=filters["ka"])
                        )
                    )

                if "section_ref" in filters:
                    must_conditions.append(
                        FieldCondition(
                            key="section_ref",
                            match=MatchValue(value=filters["section_ref"])
                        )
                    )

                if "difficulty" in filters:
                    must_conditions.append(
                        FieldCondition(
                            key="difficulty",
                            match=MatchValue(value=filters["difficulty"])
                        )
                    )

                if must_conditions:
                    filter_conditions = Filter(must=must_conditions)

            # Execute async search
            results = await self.client.search(
                collection_name="babok_chunks",
                query_vector=query_vector,
                query_filter=filter_conditions,
                limit=limit
            )

            return [
                {
                    "id": result.id,
                    "score": result.score,
                    "payload": result.payload
                }
                for result in results
            ]

        except Exception as e:
            logger.error(f"Failed to search chunks: {str(e)}")
            raise
