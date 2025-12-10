"""
Qdrant Repository
Provides data access layer for vector database operations with multi-course support
"""

import logging
from uuid import UUID
from typing import List, Dict, Any, Optional

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import (
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
    MatchAny,
    Range,
)

from src.db.qdrant_client import get_qdrant

logger = logging.getLogger(__name__)

# Collection name constants (course-agnostic)
QUESTIONS_COLLECTION = "questions"
CHUNKS_COLLECTION = "reading_chunks"


class QdrantRepository:
    """Repository for async Qdrant vector database operations with multi-course support"""

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
        course_id: UUID,
        payload: Dict[str, Any]
    ) -> None:
        """
        Insert question vector into Qdrant.

        Args:
            question_id: Question UUID
            vector: 3072-dimensional embedding vector from text-embedding-3-large
            course_id: Course UUID for multi-course scoping
            payload: Metadata dict with keys:
                - knowledge_area_id: str (matches course.knowledge_areas[].id)
                - difficulty: float (0.0-1.0)
                - concept_ids: List[str] (UUID strings)
                - question_text: str
                - options: str (formatted options)
                - correct_answer: str

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            # Ensure course_id and question_id are in payload
            payload["course_id"] = str(course_id)
            payload["question_id"] = str(question_id)

            point = PointStruct(
                id=str(question_id),
                vector=vector,
                payload=payload
            )

            await self.client.upsert(
                collection_name=QUESTIONS_COLLECTION,
                points=[point]
            )

            logger.info(f"Created question vector: {question_id} (course: {course_id})")

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
                collection_name=QUESTIONS_COLLECTION,
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
        course_id: Optional[UUID] = None,
        knowledge_area_id: Optional[str] = None,
        difficulty_min: Optional[float] = None,
        difficulty_max: Optional[float] = None,
        concept_ids: Optional[List[UUID]] = None,
        exclude_ids: Optional[List[UUID]] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for questions with multi-course support.

        Args:
            query_vector: 3072-dimensional query embedding
            course_id: Filter by course (recommended for all queries)
            knowledge_area_id: Filter by knowledge area
            difficulty_min: Minimum difficulty (0.0-1.0)
            difficulty_max: Maximum difficulty (0.0-1.0)
            concept_ids: Filter by concepts tested (any match)
            exclude_ids: Question IDs to exclude from results
            limit: Maximum results to return (default: 10)

        Returns:
            List of dicts with keys: id, score, payload

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            must_conditions = []

            # Course filter (should almost always be set)
            if course_id:
                must_conditions.append(
                    FieldCondition(
                        key="course_id",
                        match=MatchValue(value=str(course_id))
                    )
                )

            # Knowledge area filter
            if knowledge_area_id:
                must_conditions.append(
                    FieldCondition(
                        key="knowledge_area_id",
                        match=MatchValue(value=knowledge_area_id)
                    )
                )

            # Difficulty range filter
            if difficulty_min is not None or difficulty_max is not None:
                must_conditions.append(
                    FieldCondition(
                        key="difficulty",
                        range=Range(
                            gte=difficulty_min,
                            lte=difficulty_max
                        )
                    )
                )

            # Concept filter (any match)
            if concept_ids:
                must_conditions.append(
                    FieldCondition(
                        key="concept_ids",
                        match=MatchAny(any=[str(c) for c in concept_ids])
                    )
                )

            filter_conditions = Filter(must=must_conditions) if must_conditions else None

            # Execute async search
            results = await self.client.search(
                collection_name=QUESTIONS_COLLECTION,
                query_vector=query_vector,
                query_filter=filter_conditions,
                limit=limit + (len(exclude_ids) if exclude_ids else 0)
            )

            # Filter out excluded IDs
            if exclude_ids:
                exclude_set = {str(eid) for eid in exclude_ids}
                results = [r for r in results if r.id not in exclude_set][:limit]

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
                collection_name=QUESTIONS_COLLECTION,
                points_selector=[str(question_id)]
            )

            logger.info(f"Deleted question vector: {question_id}")

        except Exception as e:
            logger.error(f"Failed to delete question vector {question_id}: {str(e)}")
            raise

    # =========================================================================
    # Reading Chunk Vector Methods
    # =========================================================================

    async def create_chunk_vector(
        self,
        chunk_id: UUID,
        vector: List[float],
        course_id: UUID,
        payload: Dict[str, Any]
    ) -> None:
        """
        Insert reading chunk vector into Qdrant.

        Args:
            chunk_id: Chunk UUID
            vector: 3072-dimensional embedding vector
            course_id: Course UUID for multi-course scoping
            payload: Metadata dict with keys:
                - knowledge_area_id: str (matches course.knowledge_areas[].id)
                - section_ref: str (e.g., "3.2.1")
                - difficulty: float (0.0-1.0)
                - concept_ids: List[str] (UUID strings)
                - text_content: str (chunk text)

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            # Ensure course_id and chunk_id are in payload
            payload["course_id"] = str(course_id)
            payload["chunk_id"] = str(chunk_id)

            point = PointStruct(
                id=str(chunk_id),
                vector=vector,
                payload=payload
            )

            await self.client.upsert(
                collection_name=CHUNKS_COLLECTION,
                points=[point]
            )

            logger.info(f"Created chunk vector: {chunk_id} (course: {course_id})")

        except Exception as e:
            logger.error(f"Failed to create chunk vector {chunk_id}: {str(e)}")
            raise

    async def get_chunk_vector(self, chunk_id: UUID) -> Dict[str, Any] | None:
        """
        Retrieve chunk vector by ID.

        Args:
            chunk_id: Chunk UUID

        Returns:
            Dict with vector and payload if found, None otherwise

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            result = await self.client.retrieve(
                collection_name=CHUNKS_COLLECTION,
                ids=[str(chunk_id)],
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
            logger.error(f"Failed to retrieve chunk vector {chunk_id}: {str(e)}")
            raise

    async def search_chunks(
        self,
        query_vector: List[float],
        course_id: Optional[UUID] = None,
        knowledge_area_id: Optional[str] = None,
        section_ref: Optional[str] = None,
        difficulty_min: Optional[float] = None,
        difficulty_max: Optional[float] = None,
        concept_ids: Optional[List[UUID]] = None,
        limit: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Semantic search for reading chunks with multi-course support.

        Args:
            query_vector: 3072-dimensional query embedding
            course_id: Filter by course (recommended for all queries)
            knowledge_area_id: Filter by knowledge area
            section_ref: Filter by section reference (e.g., "3.2.1")
            difficulty_min: Minimum difficulty (0.0-1.0)
            difficulty_max: Maximum difficulty (0.0-1.0)
            concept_ids: Filter by concepts (any match)
            limit: Maximum results to return (default: 3)

        Returns:
            List of dicts with keys: id, score, payload

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            must_conditions = []

            # Course filter
            if course_id:
                must_conditions.append(
                    FieldCondition(
                        key="course_id",
                        match=MatchValue(value=str(course_id))
                    )
                )

            # Knowledge area filter
            if knowledge_area_id:
                must_conditions.append(
                    FieldCondition(
                        key="knowledge_area_id",
                        match=MatchValue(value=knowledge_area_id)
                    )
                )

            # Section reference filter
            if section_ref:
                must_conditions.append(
                    FieldCondition(
                        key="section_ref",
                        match=MatchValue(value=section_ref)
                    )
                )

            # Difficulty range filter
            if difficulty_min is not None or difficulty_max is not None:
                must_conditions.append(
                    FieldCondition(
                        key="difficulty",
                        range=Range(
                            gte=difficulty_min,
                            lte=difficulty_max
                        )
                    )
                )

            # Concept filter (any match)
            if concept_ids:
                must_conditions.append(
                    FieldCondition(
                        key="concept_ids",
                        match=MatchAny(any=[str(c) for c in concept_ids])
                    )
                )

            filter_conditions = Filter(must=must_conditions) if must_conditions else None

            # Execute async search
            results = await self.client.search(
                collection_name=CHUNKS_COLLECTION,
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

    async def delete_chunk_vector(self, chunk_id: UUID) -> None:
        """
        Delete chunk vector from Qdrant.

        Args:
            chunk_id: Chunk UUID

        Raises:
            UnexpectedResponse: If Qdrant operation fails
        """
        try:
            await self.client.delete(
                collection_name=CHUNKS_COLLECTION,
                points_selector=[str(chunk_id)]
            )

            logger.info(f"Deleted chunk vector: {chunk_id}")

        except Exception as e:
            logger.error(f"Failed to delete chunk vector {chunk_id}: {str(e)}")
            raise
