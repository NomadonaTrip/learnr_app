"""
Integration tests for question embedding generation and Qdrant upload.

Tests the full workflow of embedding generation and vector storage.
"""
import pytest
from uuid import uuid4

from apps.api.src.db.session import AsyncSessionLocal
from apps.api.src.models.concept import Concept
from apps.api.src.models.course import Course
from apps.api.src.models.question import Question
from apps.api.src.models.question_concept import QuestionConcept
from apps.api.src.services.qdrant_upload_service import (
    QdrantUploadService,
    QuestionVectorItem,
)
from qdrant_client import AsyncQdrantClient
from qdrant_client.models import Distance, FieldCondition, Filter, MatchValue, VectorParams
from sqlalchemy import select


@pytest.fixture
async def test_course(db_session):
    """Create a test course."""
    course = Course(
        id=uuid4(),
        slug="test-cbap",
        name="Test CBAP Course",
        description="Test course for embeddings",
        knowledge_areas=[
            {
                "id": "ba-planning",
                "name": "Business Analysis Planning and Monitoring",
                "short_name": "BA Planning"
            }
        ],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concept(db_session, test_course):
    """Create a test concept."""
    concept = Concept(
        id=uuid4(),
        course_id=test_course.id,
        name="Stakeholder Analysis",
        definition="Analysis of stakeholders",
        knowledge_area_id="ba-planning",
        prerequisite_depth=0
    )
    db_session.add(concept)
    await db_session.commit()
    await db_session.refresh(concept)
    return concept


@pytest.fixture
async def test_question(db_session, test_course, test_concept):
    """Create a test question with concept mapping."""
    question = Question(
        id=uuid4(),
        course_id=test_course.id,
        question_text="Which technique is BEST for stakeholder analysis?",
        options={
            "A": "SWOT Analysis",
            "B": "Stakeholder Map",
            "C": "RACI Matrix",
            "D": "Process Flow"
        },
        correct_answer="B",
        explanation="Stakeholder Map is designed for stakeholder analysis",
        knowledge_area_id="ba-planning",
        difficulty=0.5,
        discrimination=1.0,
        is_active=True
    )
    db_session.add(question)
    await db_session.flush()

    # Add concept mapping
    qc = QuestionConcept(
        question_id=question.id,
        concept_id=test_concept.id,
        relevance=1.0
    )
    db_session.add(qc)
    await db_session.commit()
    await db_session.refresh(question)

    return question


@pytest.fixture
async def qdrant_test_client():
    """Create a test Qdrant client and cleanup after."""
    from apps.api.src.config import settings

    client = AsyncQdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY,
        timeout=settings.QDRANT_TIMEOUT
    )

    # Create test collection
    test_collection = "test_questions"
    try:
        await client.delete_collection(test_collection)
    except Exception:
        pass

    await client.create_collection(
        collection_name=test_collection,
        vectors_config=VectorParams(size=3072, distance=Distance.COSINE)
    )

    yield client, test_collection

    # Cleanup
    try:
        await client.delete_collection(test_collection)
    except Exception:
        pass
    await client.close()


class TestQdrantUploadService:
    """Test suite for QdrantUploadService."""

    @pytest.mark.asyncio
    async def test_upload_single_vector(self, qdrant_test_client, test_question, test_concept):
        """Test uploading a single question vector."""
        client, collection_name = qdrant_test_client

        # Create upload service
        upload_service = QdrantUploadService(qdrant_client=client)
        upload_service.collection_name = collection_name  # Use test collection

        # Create vector item
        vector_item = QuestionVectorItem(
            question_id=test_question.id,
            course_id=test_question.course_id,
            vector=[0.1] * 3072,
            knowledge_area_id=test_question.knowledge_area_id,
            difficulty=test_question.difficulty,
            discrimination=test_question.discrimination,
            concept_ids=[str(test_concept.id)],
            concept_names=[test_concept.name],
            question_text=test_question.question_text,
            options=test_question.options,
            correct_answer=test_question.correct_answer
        )

        # Upload vector
        uploaded = await upload_service.upload_question_vector(vector_item, skip_if_exists=False)

        # Assertions
        assert uploaded is True

        # Verify in Qdrant
        result = await client.retrieve(
            collection_name=collection_name,
            ids=[str(test_question.id)]
        )
        assert len(result) == 1
        assert result[0].id == str(test_question.id)
        assert result[0].payload["course_id"] == str(test_question.course_id)
        assert result[0].payload["knowledge_area_id"] == test_question.knowledge_area_id
        assert result[0].payload["concept_ids"] == [str(test_concept.id)]

    @pytest.mark.asyncio
    async def test_upsert_idempotency(self, qdrant_test_client, test_question, test_concept):
        """Test that upsert is idempotent (can upload same vector twice)."""
        client, collection_name = qdrant_test_client

        upload_service = QdrantUploadService(qdrant_client=client)
        upload_service.collection_name = collection_name

        vector_item = QuestionVectorItem(
            question_id=test_question.id,
            course_id=test_question.course_id,
            vector=[0.1] * 3072,
            knowledge_area_id=test_question.knowledge_area_id,
            difficulty=test_question.difficulty,
            discrimination=test_question.discrimination,
            concept_ids=[str(test_concept.id)],
            concept_names=[test_concept.name],
            question_text=test_question.question_text,
            options=test_question.options,
            correct_answer=test_question.correct_answer
        )

        # Upload first time
        uploaded1 = await upload_service.upload_question_vector(vector_item, skip_if_exists=False)
        assert uploaded1 is True

        # Upload second time (skip_if_exists=True)
        uploaded2 = await upload_service.upload_question_vector(vector_item, skip_if_exists=True)
        assert uploaded2 is False  # Should skip

        # Upload third time (skip_if_exists=False, force upsert)
        uploaded3 = await upload_service.upload_question_vector(vector_item, skip_if_exists=False)
        assert uploaded3 is True  # Should upload again

        # Verify still only one vector
        result = await client.retrieve(
            collection_name=collection_name,
            ids=[str(test_question.id)]
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_batch_upload_vectors(self, qdrant_test_client, test_course, test_concept):
        """Test batch upload of multiple vectors."""
        client, collection_name = qdrant_test_client

        upload_service = QdrantUploadService(qdrant_client=client)
        upload_service.collection_name = collection_name

        # Create multiple vector items
        vector_items = []
        for i in range(10):
            vector_item = QuestionVectorItem(
                question_id=uuid4(),
                course_id=test_course.id,
                vector=[0.1 * (i + 1)] * 3072,
                knowledge_area_id="ba-planning",
                difficulty=0.5,
                discrimination=1.0,
                concept_ids=[str(test_concept.id)],
                concept_names=[test_concept.name],
                question_text=f"Test question {i}",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A"
            )
            vector_items.append(vector_item)

        # Batch upload
        uploaded_count, skipped_count = await upload_service.batch_upload_question_vectors(
            vector_items, skip_if_exists=False, batch_size=5
        )

        # Assertions
        assert uploaded_count == 10
        assert skipped_count == 0

        # Verify in Qdrant
        collection_info = await client.get_collection(collection_name)
        assert collection_info.points_count == 10

    @pytest.mark.asyncio
    async def test_verify_course_vectors(self, qdrant_test_client, test_course, test_concept):
        """Test verifying vectors for a specific course."""
        client, collection_name = qdrant_test_client

        upload_service = QdrantUploadService(qdrant_client=client)
        upload_service.collection_name = collection_name

        # Upload 5 vectors for test course
        vector_items = []
        for i in range(5):
            vector_item = QuestionVectorItem(
                question_id=uuid4(),
                course_id=test_course.id,
                vector=[0.1] * 3072,
                knowledge_area_id="ba-planning",
                difficulty=0.5,
                discrimination=1.0,
                concept_ids=[str(test_concept.id)],
                concept_names=[test_concept.name],
                question_text=f"Test question {i}",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A"
            )
            vector_items.append(vector_item)

        await upload_service.batch_upload_question_vectors(vector_items, skip_if_exists=False)

        # Verify course vectors
        result = await upload_service.verify_course_vectors(test_course.id, expected_count=5)

        # Assertions
        assert result["actual_count"] == 5
        assert result["expected_count"] == 5
        assert result["verified"] is True

    @pytest.mark.asyncio
    async def test_vector_search_with_course_filter(self, qdrant_test_client, test_course, test_concept):
        """Test searching vectors with course filter."""
        client, collection_name = qdrant_test_client

        upload_service = QdrantUploadService(qdrant_client=client)
        upload_service.collection_name = collection_name

        # Upload vector
        question_id = uuid4()
        vector_item = QuestionVectorItem(
            question_id=question_id,
            course_id=test_course.id,
            vector=[0.1] * 3072,
            knowledge_area_id="ba-planning",
            difficulty=0.5,
            discrimination=1.0,
            concept_ids=[str(test_concept.id)],
            concept_names=[test_concept.name],
            question_text="Test question",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A"
        )

        await upload_service.upload_question_vector(vector_item, skip_if_exists=False)

        # Search with course filter
        search_results = await client.search(
            collection_name=collection_name,
            query_vector=[0.1] * 3072,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="course_id",
                        match=MatchValue(value=str(test_course.id))
                    )
                ]
            ),
            limit=5
        )

        # Assertions
        assert len(search_results) == 1
        assert search_results[0].id == str(question_id)
        assert search_results[0].payload["course_id"] == str(test_course.id)

    @pytest.mark.asyncio
    async def test_payload_correctness(self, qdrant_test_client, test_question, test_concept):
        """Test that all payload fields are correct."""
        client, collection_name = qdrant_test_client

        upload_service = QdrantUploadService(qdrant_client=client)
        upload_service.collection_name = collection_name

        vector_item = QuestionVectorItem(
            question_id=test_question.id,
            course_id=test_question.course_id,
            vector=[0.1] * 3072,
            knowledge_area_id=test_question.knowledge_area_id,
            difficulty=test_question.difficulty,
            discrimination=test_question.discrimination,
            concept_ids=[str(test_concept.id)],
            concept_names=[test_concept.name],
            question_text=test_question.question_text,
            options=test_question.options,
            correct_answer=test_question.correct_answer
        )

        await upload_service.upload_question_vector(vector_item, skip_if_exists=False)

        # Retrieve and check payload
        result = await client.retrieve(
            collection_name=collection_name,
            ids=[str(test_question.id)]
        )

        payload = result[0].payload

        # Check all required fields
        assert payload["question_id"] == str(test_question.id)
        assert payload["course_id"] == str(test_question.course_id)
        assert payload["knowledge_area_id"] == test_question.knowledge_area_id
        assert payload["difficulty"] == test_question.difficulty
        assert payload["discrimination"] == test_question.discrimination
        assert payload["concept_ids"] == [str(test_concept.id)]
        assert payload["concept_names"] == [test_concept.name]
        assert payload["question_text"] == test_question.question_text
        assert payload["options"] == test_question.options
        assert payload["correct_answer"] == test_question.correct_answer
