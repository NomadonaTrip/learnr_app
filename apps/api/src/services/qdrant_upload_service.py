"""
Qdrant Upload Service for managing question and chunk vector uploads.

This service handles uploading question and reading chunk embeddings to Qdrant
with proper payload structure, batching, and idempotency support.
"""
from dataclasses import dataclass
from uuid import UUID

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import PointStruct

from ..config import settings
from ..utils.logging_config import get_logger

logger = get_logger(__name__)

# Constants
COLLECTION_NAME = "questions"  # Multi-course: shared collection for all courses
CHUNKS_COLLECTION_NAME = "reading_chunks"  # Multi-course: shared collection for reading chunks
MAX_BATCH_SIZE = 100  # Qdrant batch upload limit


@dataclass(kw_only=True)
class QuestionVectorItem:
    """
    Data class for question vector upload.

    Uses kw_only=True to enforce keyword arguments for better
    maintainability and IDE support.
    """
    question_id: UUID
    course_id: UUID
    vector: list[float]
    knowledge_area_id: str
    difficulty: float
    discrimination: float
    concept_ids: list[str]
    concept_names: list[str]
    question_text: str
    options: dict[str, str]
    correct_answer: str


@dataclass(kw_only=True)
class ChunkVectorItem:
    """
    Data class for reading chunk vector upload.

    Uses kw_only=True to enforce keyword arguments for better
    maintainability and IDE support.
    """
    chunk_id: UUID
    course_id: UUID
    vector: list[float]
    title: str
    knowledge_area_id: str
    corpus_section: str
    concept_ids: list[str]
    concept_names: list[str]
    text_content: str
    estimated_read_time: int


class QdrantUploadService:
    """
    Service for uploading question vectors to Qdrant.

    Provides batched uploads, idempotency checks, and proper payload formatting
    for multi-course architecture.
    """

    def __init__(self, qdrant_client: AsyncQdrantClient | None = None):
        """
        Initialize the Qdrant Upload Service.

        Args:
            qdrant_client: Optional AsyncQdrantClient instance (creates new if None)
        """
        self.client = qdrant_client or AsyncQdrantClient(
            url=settings.QDRANT_URL,
            api_key=settings.QDRANT_API_KEY,
            timeout=settings.QDRANT_TIMEOUT
        )
        self.collection_name = COLLECTION_NAME

    async def vector_exists(self, question_id: UUID) -> bool:
        """
        Check if vector already exists in Qdrant.

        Args:
            question_id: Question UUID

        Returns:
            True if vector exists, False otherwise
        """
        try:
            result = await self.client.retrieve(
                collection_name=self.collection_name,
                ids=[str(question_id)]
            )
            return len(result) > 0
        except Exception as e:
            logger.warning("vector_existence_check_failed", question_id=str(question_id), error=str(e))
            return False

    def _build_payload(self, item: QuestionVectorItem) -> dict:
        """
        Build Qdrant payload from QuestionVectorItem.

        Args:
            item: QuestionVectorItem with all required fields

        Returns:
            Payload dictionary for Qdrant
        """
        return {
            "question_id": str(item.question_id),
            "course_id": str(item.course_id),  # NEW - required for multi-course
            "knowledge_area_id": item.knowledge_area_id,  # CHANGED from "ka"
            "difficulty": item.difficulty,
            "discrimination": item.discrimination,
            "concept_ids": item.concept_ids,  # List of UUID strings
            "concept_names": item.concept_names,  # List of concept names
            "question_text": item.question_text,
            "options": item.options,  # {"A": "...", "B": "...", "C": "...", "D": "..."}
            "correct_answer": item.correct_answer
        }

    async def upload_question_vector(
        self,
        item: QuestionVectorItem,
        skip_if_exists: bool = True
    ) -> bool:
        """
        Upload a single question vector to Qdrant.

        Args:
            item: QuestionVectorItem with vector and metadata
            skip_if_exists: If True, skip upload if vector already exists

        Returns:
            True if uploaded, False if skipped
        """
        question_id_str = str(item.question_id)

        # Check if already exists (idempotency)
        if skip_if_exists and await self.vector_exists(item.question_id):
            logger.debug("vector_already_exists", question_id=question_id_str)
            return False

        # Build point
        point = PointStruct(
            id=question_id_str,
            vector=item.vector,
            payload=self._build_payload(item)
        )

        # Upload to Qdrant (upsert is idempotent)
        await self.client.upsert(
            collection_name=self.collection_name,
            points=[point]
        )

        logger.debug("vector_uploaded", question_id=question_id_str)
        return True

    async def batch_upload_question_vectors(
        self,
        items: list[QuestionVectorItem],
        skip_if_exists: bool = True,
        batch_size: int = MAX_BATCH_SIZE,
        progress_callback=None
    ) -> tuple[int, int]:
        """
        Upload multiple question vectors to Qdrant in batches.

        Args:
            items: List of QuestionVectorItem objects
            skip_if_exists: If True, skip vectors that already exist
            batch_size: Number of vectors per batch (default: 100)
            progress_callback: Optional callback function(uploaded, skipped, total)

        Returns:
            Tuple of (uploaded_count, skipped_count)
        """
        if batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {batch_size} exceeds maximum {MAX_BATCH_SIZE}")

        uploaded_count = 0
        skipped_count = 0

        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_points = []

            for item in batch:
                question_id_str = str(item.question_id)

                # Check if already exists (idempotency)
                if skip_if_exists and await self.vector_exists(item.question_id):
                    skipped_count += 1
                    logger.debug("vector_already_exists_batch", question_id=question_id_str)
                    continue

                # Build point
                point = PointStruct(
                    id=question_id_str,
                    vector=item.vector,
                    payload=self._build_payload(item)
                )
                batch_points.append(point)

            # Upload batch if there are points
            if batch_points:
                await self.client.upsert(
                    collection_name=self.collection_name,
                    points=batch_points
                )
                uploaded_count += len(batch_points)

                logger.debug(
                    "batch_uploaded",
                    batch_number=i // batch_size + 1,
                    vectors_in_batch=len(batch_points)
                )

            # Call progress callback if provided
            if progress_callback:
                progress_callback(uploaded_count, skipped_count, len(items))

        logger.info(
            "batch_upload_complete",
            uploaded=uploaded_count,
            skipped=skipped_count
        )

        return uploaded_count, skipped_count

    async def verify_collection_count(self, expected_count: int | None = None) -> dict:
        """
        Verify the number of vectors in the collection.

        Args:
            expected_count: Expected number of vectors (optional)

        Returns:
            Dictionary with verification results
        """
        try:
            collection_info = await self.client.get_collection(self.collection_name)
            actual_count = collection_info.points_count

            result = {
                "collection": self.collection_name,
                "actual_count": actual_count,
                "expected_count": expected_count,
                "verified": expected_count is None or actual_count == expected_count
            }

            if result["verified"]:
                logger.info(
                    "verification_passed",
                    actual_count=actual_count,
                    collection=self.collection_name
                )
            else:
                logger.warning(
                    "verification_failed",
                    expected=expected_count,
                    actual=actual_count,
                    collection=self.collection_name
                )

            return result

        except Exception as e:
            logger.error("verification_error", error=str(e))
            return {
                "collection": self.collection_name,
                "actual_count": 0,
                "expected_count": expected_count,
                "verified": False,
                "error": str(e)
            }

    async def verify_course_vectors(self, course_id: UUID, expected_count: int | None = None) -> dict:
        """
        Verify the number of vectors for a specific course.

        Uses Qdrant count API for efficient counting without pagination.

        Args:
            course_id: Course UUID to filter by
            expected_count: Expected number of vectors for this course (optional)

        Returns:
            Dictionary with verification results
        """
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        try:
            # Use count API for efficient counting (no pagination needed)
            count_result = await self.client.count(
                collection_name=self.collection_name,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="course_id",
                            match=MatchValue(value=str(course_id))
                        )
                    ]
                ),
                exact=True  # Ensure exact count
            )

            actual_count = count_result.count

            verification_result = {
                "collection": self.collection_name,
                "course_id": str(course_id),
                "actual_count": actual_count,
                "expected_count": expected_count,
                "verified": expected_count is None or actual_count == expected_count
            }

            if verification_result["verified"]:
                logger.info(
                    "course_verification_passed",
                    actual_count=actual_count,
                    course_id=str(course_id)
                )
            else:
                logger.warning(
                    "course_verification_failed",
                    expected=expected_count,
                    actual=actual_count,
                    course_id=str(course_id)
                )

            return verification_result

        except Exception as e:
            logger.error("course_verification_error", course_id=str(course_id), error=str(e))
            return {
                "collection": self.collection_name,
                "course_id": str(course_id),
                "actual_count": 0,
                "expected_count": expected_count,
                "verified": False,
                "error": str(e)
            }

    # ==================== Reading Chunk Methods ====================

    async def chunk_vector_exists(self, chunk_id: UUID) -> bool:
        """
        Check if chunk vector already exists in Qdrant.

        Args:
            chunk_id: Chunk UUID

        Returns:
            True if vector exists, False otherwise
        """
        try:
            result = await self.client.retrieve(
                collection_name=CHUNKS_COLLECTION_NAME,
                ids=[str(chunk_id)]
            )
            return len(result) > 0
        except Exception as e:
            logger.warning("chunk_vector_existence_check_failed", chunk_id=str(chunk_id), error=str(e))
            return False

    def _build_chunk_payload(self, item: ChunkVectorItem) -> dict:
        """
        Build Qdrant payload from ChunkVectorItem.

        Args:
            item: ChunkVectorItem with all required fields

        Returns:
            Payload dictionary for Qdrant
        """
        return {
            "chunk_id": str(item.chunk_id),
            "course_id": str(item.course_id),
            "title": item.title,
            "knowledge_area_id": item.knowledge_area_id,
            "corpus_section": item.corpus_section,
            "concept_ids": item.concept_ids,  # List of UUID strings
            "concept_names": item.concept_names,  # List of concept names
            "text_content": item.text_content,
            "estimated_read_time": item.estimated_read_time
        }

    async def upload_chunk_vector(
        self,
        item: ChunkVectorItem,
        skip_if_exists: bool = True
    ) -> bool:
        """
        Upload a single chunk vector to Qdrant.

        Args:
            item: ChunkVectorItem with vector and metadata
            skip_if_exists: If True, skip upload if vector already exists

        Returns:
            True if uploaded, False if skipped
        """
        chunk_id_str = str(item.chunk_id)

        # Check if already exists (idempotency)
        if skip_if_exists and await self.chunk_vector_exists(item.chunk_id):
            logger.debug("chunk_vector_already_exists", chunk_id=chunk_id_str)
            return False

        # Build point
        point = PointStruct(
            id=chunk_id_str,
            vector=item.vector,
            payload=self._build_chunk_payload(item)
        )

        # Upload to Qdrant (upsert is idempotent)
        await self.client.upsert(
            collection_name=CHUNKS_COLLECTION_NAME,
            points=[point]
        )

        logger.debug("chunk_vector_uploaded", chunk_id=chunk_id_str)
        return True

    async def batch_upload_chunk_vectors(
        self,
        items: list[ChunkVectorItem],
        skip_if_exists: bool = True,
        batch_size: int = MAX_BATCH_SIZE,
        progress_callback=None
    ) -> tuple[int, int]:
        """
        Upload multiple chunk vectors to Qdrant in batches.

        Args:
            items: List of ChunkVectorItem objects
            skip_if_exists: If True, skip vectors that already exist
            batch_size: Number of vectors per batch (default: 100)
            progress_callback: Optional callback function(uploaded, skipped, total)

        Returns:
            Tuple of (uploaded_count, skipped_count)
        """
        if batch_size > MAX_BATCH_SIZE:
            raise ValueError(f"Batch size {batch_size} exceeds maximum {MAX_BATCH_SIZE}")

        uploaded_count = 0
        skipped_count = 0

        # Process in batches
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            batch_points = []

            for item in batch:
                chunk_id_str = str(item.chunk_id)

                # Check if already exists (idempotency)
                if skip_if_exists and await self.chunk_vector_exists(item.chunk_id):
                    skipped_count += 1
                    logger.debug("chunk_vector_already_exists_batch", chunk_id=chunk_id_str)
                    continue

                # Build point
                point = PointStruct(
                    id=chunk_id_str,
                    vector=item.vector,
                    payload=self._build_chunk_payload(item)
                )
                batch_points.append(point)

            # Upload batch if there are points
            if batch_points:
                await self.client.upsert(
                    collection_name=CHUNKS_COLLECTION_NAME,
                    points=batch_points
                )
                uploaded_count += len(batch_points)

                logger.debug(
                    "chunk_batch_uploaded",
                    batch_number=i // batch_size + 1,
                    vectors_in_batch=len(batch_points)
                )

            # Call progress callback if provided
            if progress_callback:
                progress_callback(uploaded_count, skipped_count, len(items))

        logger.info(
            "chunk_batch_upload_complete",
            uploaded=uploaded_count,
            skipped=skipped_count
        )

        return uploaded_count, skipped_count

    async def verify_chunk_collection_count(self, expected_count: int | None = None) -> dict:
        """
        Verify the number of chunk vectors in the collection.

        Args:
            expected_count: Expected number of vectors (optional)

        Returns:
            Dictionary with verification results
        """
        try:
            collection_info = await self.client.get_collection(CHUNKS_COLLECTION_NAME)
            actual_count = collection_info.points_count

            result = {
                "collection": CHUNKS_COLLECTION_NAME,
                "actual_count": actual_count,
                "expected_count": expected_count,
                "verified": expected_count is None or actual_count == expected_count
            }

            if result["verified"]:
                logger.info(
                    "chunk_verification_passed",
                    actual_count=actual_count,
                    collection=CHUNKS_COLLECTION_NAME
                )
            else:
                logger.warning(
                    "chunk_verification_failed",
                    expected=expected_count,
                    actual=actual_count,
                    collection=CHUNKS_COLLECTION_NAME
                )

            return result

        except Exception as e:
            logger.error("chunk_verification_error", error=str(e))
            return {
                "collection": CHUNKS_COLLECTION_NAME,
                "actual_count": 0,
                "expected_count": expected_count,
                "verified": False,
                "error": str(e)
            }

    async def verify_chunk_course_vectors(
        self,
        course_id: UUID,
        expected_count: int | None = None
    ) -> dict:
        """
        Verify the number of chunk vectors for a specific course.

        Uses Qdrant count API for efficient counting without pagination.

        Args:
            course_id: Course UUID to filter by
            expected_count: Expected number of vectors for this course (optional)

        Returns:
            Dictionary with verification results
        """
        from qdrant_client.models import FieldCondition, Filter, MatchValue

        try:
            # Use count API for efficient counting (no pagination needed)
            count_result = await self.client.count(
                collection_name=CHUNKS_COLLECTION_NAME,
                count_filter=Filter(
                    must=[
                        FieldCondition(
                            key="course_id",
                            match=MatchValue(value=str(course_id))
                        )
                    ]
                ),
                exact=True  # Ensure exact count
            )

            actual_count = count_result.count

            verification_result = {
                "collection": CHUNKS_COLLECTION_NAME,
                "course_id": str(course_id),
                "actual_count": actual_count,
                "expected_count": expected_count,
                "verified": expected_count is None or actual_count == expected_count
            }

            if verification_result["verified"]:
                logger.info(
                    "chunk_course_verification_passed",
                    actual_count=actual_count,
                    course_id=str(course_id)
                )
            else:
                logger.warning(
                    "chunk_course_verification_failed",
                    expected=expected_count,
                    actual=actual_count,
                    course_id=str(course_id)
                )

            return verification_result

        except Exception as e:
            logger.error("chunk_course_verification_error", course_id=str(course_id), error=str(e))
            return {
                "collection": CHUNKS_COLLECTION_NAME,
                "course_id": str(course_id),
                "actual_count": 0,
                "expected_count": expected_count,
                "verified": False,
                "error": str(e)
            }

    async def close(self):
        """Close the Qdrant client."""
        await self.client.close()

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
