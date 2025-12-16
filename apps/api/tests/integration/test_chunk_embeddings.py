"""
Integration tests for chunk embedding upload to Qdrant.

Tests:
- Vector upload to reading_chunks collection
- Upsert idempotency
- Semantic search with concept and course filter
- Payload field correctness including course_id
"""
import pytest
from uuid import uuid4

from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, VectorParams

from src.config import settings
from src.services.qdrant_upload_service import ChunkVectorItem, QdrantUploadService

# Test collection name (separate from production)
TEST_COLLECTION = "test_reading_chunks"


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
async def qdrant_client():
    """Create a Qdrant client for testing."""
    client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=settings.QDRANT_TIMEOUT
    )
    yield client
    await client.close()


@pytest.fixture
async def test_collection(qdrant_client):
    """
    Create a test collection for chunk embeddings.

    This fixture creates a fresh collection before each test and
    cleans it up after the test completes.
    """
    # Create test collection
    try:
        await qdrant_client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass  # Collection doesn't exist yet

    await qdrant_client.create_collection(
        collection_name=TEST_COLLECTION,
        vectors_config=VectorParams(
            size=3072,  # text-embedding-3-large dimensions
            distance=Distance.COSINE
        )
    )

    yield TEST_COLLECTION

    # Cleanup
    try:
        await qdrant_client.delete_collection(TEST_COLLECTION)
    except Exception:
        pass


@pytest.fixture
def sample_chunk_vector_item():
    """Create a sample ChunkVectorItem for testing."""
    return ChunkVectorItem(
        chunk_id=uuid4(),
        course_id=uuid4(),
        vector=[0.1] * 3072,  # Dummy vector
        title="Stakeholder Analysis Techniques",
        knowledge_area_id="ba-planning",
        corpus_section="3.2.1",
        concept_ids=[str(uuid4()), str(uuid4())],
        concept_names=["Stakeholder Analysis", "Communication Planning"],
        text_content="Stakeholder analysis is the process of analyzing stakeholders...",
        estimated_read_time=3
    )


@pytest.fixture
def cbap_course_id():
    """Return a consistent CBAP course ID for testing."""
    return uuid4()


@pytest.fixture
def psm_course_id():
    """Return a consistent PSM course ID for testing."""
    return uuid4()


# =============================================================================
# Test Vector Upload
# =============================================================================

class TestVectorUpload:
    """Test vector upload to reading_chunks collection."""

    @pytest.mark.asyncio
    async def test_upload_single_chunk_vector(
        self,
        qdrant_client,
        test_collection,
        sample_chunk_vector_item
    ):
        """Test uploading a single chunk vector to Qdrant."""
        # Override collection name for testing
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            # Upload vector
            uploaded = await service.upload_chunk_vector(
                item=sample_chunk_vector_item,
                skip_if_exists=False
            )

            assert uploaded is True

            # Verify vector exists
            result = await qdrant_client.retrieve(
                collection_name=TEST_COLLECTION,
                ids=[str(sample_chunk_vector_item.chunk_id)]
            )

            assert len(result) == 1
            assert result[0].id == str(sample_chunk_vector_item.chunk_id)

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection

    @pytest.mark.asyncio
    async def test_upload_batch_chunk_vectors(
        self,
        qdrant_client,
        test_collection,
        cbap_course_id
    ):
        """Test batch upload of chunk vectors."""
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            # Create multiple items
            items = []
            for i in range(10):
                items.append(ChunkVectorItem(
                    chunk_id=uuid4(),
                    course_id=cbap_course_id,
                    vector=[0.1 + i * 0.01] * 3072,
                    title=f"Chunk {i}",
                    knowledge_area_id="ba-planning",
                    corpus_section=f"3.{i}.1",
                    concept_ids=[str(uuid4())],
                    concept_names=[f"Concept {i}"],
                    text_content=f"Content for chunk {i}",
                    estimated_read_time=2 + i
                ))

            # Batch upload
            uploaded, skipped = await service.batch_upload_chunk_vectors(
                items=items,
                skip_if_exists=False,
                batch_size=5
            )

            assert uploaded == 10
            assert skipped == 0

            # Verify all vectors exist
            collection_info = await qdrant_client.get_collection(TEST_COLLECTION)
            assert collection_info.points_count == 10

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection


# =============================================================================
# Test Idempotency
# =============================================================================

class TestIdempotency:
    """Test upsert idempotency."""

    @pytest.mark.asyncio
    async def test_upsert_idempotency(
        self,
        qdrant_client,
        test_collection,
        sample_chunk_vector_item
    ):
        """Test that uploading the same vector twice uses upsert (no duplicates)."""
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            # Upload first time
            uploaded1 = await service.upload_chunk_vector(
                item=sample_chunk_vector_item,
                skip_if_exists=False  # Don't skip
            )
            assert uploaded1 is True

            # Upload second time (should upsert, not duplicate)
            uploaded2 = await service.upload_chunk_vector(
                item=sample_chunk_vector_item,
                skip_if_exists=False  # Don't skip
            )
            assert uploaded2 is True

            # Verify only one vector exists
            result = await qdrant_client.retrieve(
                collection_name=TEST_COLLECTION,
                ids=[str(sample_chunk_vector_item.chunk_id)]
            )
            assert len(result) == 1

            # Verify total count is 1
            collection_info = await qdrant_client.get_collection(TEST_COLLECTION)
            assert collection_info.points_count == 1

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection

    @pytest.mark.asyncio
    async def test_skip_if_exists(
        self,
        qdrant_client,
        test_collection,
        sample_chunk_vector_item
    ):
        """Test skip_if_exists flag."""
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            # Upload first time
            uploaded1 = await service.upload_chunk_vector(
                item=sample_chunk_vector_item,
                skip_if_exists=True
            )
            assert uploaded1 is True

            # Upload second time with skip_if_exists=True
            uploaded2 = await service.upload_chunk_vector(
                item=sample_chunk_vector_item,
                skip_if_exists=True
            )
            assert uploaded2 is False  # Skipped

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection


# =============================================================================
# Test Payload Correctness
# =============================================================================

class TestPayloadCorrectness:
    """Test payload field correctness including course_id."""

    @pytest.mark.asyncio
    async def test_payload_fields(
        self,
        qdrant_client,
        test_collection,
        sample_chunk_vector_item
    ):
        """Test that all payload fields are correctly stored."""
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            # Upload vector
            await service.upload_chunk_vector(
                item=sample_chunk_vector_item,
                skip_if_exists=False
            )

            # Retrieve and verify payload
            result = await qdrant_client.retrieve(
                collection_name=TEST_COLLECTION,
                ids=[str(sample_chunk_vector_item.chunk_id)],
                with_payload=True,
                with_vectors=True
            )

            assert len(result) == 1
            point = result[0]
            payload = point.payload

            # Verify all required fields
            assert payload["chunk_id"] == str(sample_chunk_vector_item.chunk_id)
            assert payload["course_id"] == str(sample_chunk_vector_item.course_id)
            assert payload["title"] == sample_chunk_vector_item.title
            assert payload["knowledge_area_id"] == sample_chunk_vector_item.knowledge_area_id
            assert payload["corpus_section"] == sample_chunk_vector_item.corpus_section
            assert payload["concept_ids"] == sample_chunk_vector_item.concept_ids
            assert payload["concept_names"] == sample_chunk_vector_item.concept_names
            assert payload["text_content"] == sample_chunk_vector_item.text_content
            assert payload["estimated_read_time"] == sample_chunk_vector_item.estimated_read_time

            # Verify vector is stored
            assert point.vector is not None
            assert len(point.vector) == 3072

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection


# =============================================================================
# Test Multi-Course Filtering
# =============================================================================

class TestMultiCourseFiltering:
    """Test semantic search with course filtering."""

    @pytest.mark.asyncio
    async def test_course_filtering(
        self,
        qdrant_client,
        test_collection,
        cbap_course_id,
        psm_course_id
    ):
        """Test that course filtering works correctly."""
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            # Upload chunks for CBAP course
            cbap_items = []
            for i in range(5):
                cbap_items.append(ChunkVectorItem(
                    chunk_id=uuid4(),
                    course_id=cbap_course_id,
                    vector=[0.1] * 3072,
                    title=f"CBAP Chunk {i}",
                    knowledge_area_id="ba-planning",
                    corpus_section=f"3.{i}.1",
                    concept_ids=[str(uuid4())],
                    concept_names=[f"CBAP Concept {i}"],
                    text_content=f"CBAP content {i}",
                    estimated_read_time=3
                ))

            # Upload chunks for PSM course
            psm_items = []
            for i in range(3):
                psm_items.append(ChunkVectorItem(
                    chunk_id=uuid4(),
                    course_id=psm_course_id,
                    vector=[0.2] * 3072,
                    title=f"PSM Chunk {i}",
                    knowledge_area_id="scrum-framework",
                    corpus_section=f"1.{i}.1",
                    concept_ids=[str(uuid4())],
                    concept_names=[f"PSM Concept {i}"],
                    text_content=f"PSM content {i}",
                    estimated_read_time=2
                ))

            # Upload all items
            await service.batch_upload_chunk_vectors(cbap_items, skip_if_exists=False)
            await service.batch_upload_chunk_vectors(psm_items, skip_if_exists=False)

            # Verify total count
            collection_info = await qdrant_client.get_collection(TEST_COLLECTION)
            assert collection_info.points_count == 8

            # Search with CBAP course filter
            cbap_results = await qdrant_client.search(
                collection_name=TEST_COLLECTION,
                query_vector=[0.1] * 3072,
                query_filter=Filter(
                    must=[FieldCondition(key="course_id", match=MatchValue(value=str(cbap_course_id)))]
                ),
                limit=10
            )

            # Should only return CBAP chunks
            assert len(cbap_results) == 5
            for result in cbap_results:
                assert result.payload["course_id"] == str(cbap_course_id)

            # Search with PSM course filter
            psm_results = await qdrant_client.search(
                collection_name=TEST_COLLECTION,
                query_vector=[0.2] * 3072,
                query_filter=Filter(
                    must=[FieldCondition(key="course_id", match=MatchValue(value=str(psm_course_id)))]
                ),
                limit=10
            )

            # Should only return PSM chunks
            assert len(psm_results) == 3
            for result in psm_results:
                assert result.payload["course_id"] == str(psm_course_id)

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection


# =============================================================================
# Test Concept Filtering
# =============================================================================

class TestConceptFiltering:
    """Test semantic search with concept filtering."""

    @pytest.mark.asyncio
    async def test_concept_id_filtering(
        self,
        qdrant_client,
        test_collection,
        cbap_course_id
    ):
        """Test filtering chunks by concept_id."""
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            target_concept_id = str(uuid4())

            # Upload chunks with different concept IDs
            items = []
            for i in range(5):
                concept_ids = [target_concept_id] if i < 3 else [str(uuid4())]
                items.append(ChunkVectorItem(
                    chunk_id=uuid4(),
                    course_id=cbap_course_id,
                    vector=[0.1 + i * 0.01] * 3072,
                    title=f"Chunk {i}",
                    knowledge_area_id="ba-planning",
                    corpus_section=f"3.{i}.1",
                    concept_ids=concept_ids,
                    concept_names=[f"Concept {i}"],
                    text_content=f"Content {i}",
                    estimated_read_time=2
                ))

            await service.batch_upload_chunk_vectors(items, skip_if_exists=False)

            # Filter by specific concept_id
            from qdrant_client.models import FieldCondition, Filter, MatchAny

            results = await qdrant_client.search(
                collection_name=TEST_COLLECTION,
                query_vector=[0.1] * 3072,
                query_filter=Filter(
                    must=[
                        FieldCondition(key="concept_ids", match=MatchAny(any=[target_concept_id]))
                    ]
                ),
                limit=10
            )

            # Should only return chunks with the target concept
            assert len(results) == 3
            for result in results:
                assert target_concept_id in result.payload["concept_ids"]

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection


# =============================================================================
# Test Verification Methods
# =============================================================================

class TestVerificationMethods:
    """Test verification methods."""

    @pytest.mark.asyncio
    async def test_verify_chunk_course_vectors(
        self,
        qdrant_client,
        test_collection,
        cbap_course_id
    ):
        """Test course-specific vector count verification."""
        from src.services.qdrant_upload_service import CHUNKS_COLLECTION_NAME
        import src.services.qdrant_upload_service as upload_module
        original_collection = upload_module.CHUNKS_COLLECTION_NAME
        upload_module.CHUNKS_COLLECTION_NAME = TEST_COLLECTION

        try:
            service = QdrantUploadService(qdrant_client=qdrant_client)

            # Upload 7 chunks
            items = []
            for i in range(7):
                items.append(ChunkVectorItem(
                    chunk_id=uuid4(),
                    course_id=cbap_course_id,
                    vector=[0.1] * 3072,
                    title=f"Chunk {i}",
                    knowledge_area_id="ba-planning",
                    corpus_section=f"3.{i}.1",
                    concept_ids=[str(uuid4())],
                    concept_names=[f"Concept {i}"],
                    text_content=f"Content {i}",
                    estimated_read_time=2
                ))

            await service.batch_upload_chunk_vectors(items, skip_if_exists=False)

            # Verify count
            result = await service.verify_chunk_course_vectors(
                course_id=cbap_course_id,
                expected_count=7
            )

            assert result["verified"] is True
            assert result["actual_count"] == 7
            assert result["expected_count"] == 7
            assert result["course_id"] == str(cbap_course_id)

        finally:
            upload_module.CHUNKS_COLLECTION_NAME = original_collection


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
