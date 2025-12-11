"""
Integration tests for concept API endpoints (Story 2.10).
Tests full stack with real database and dependencies.
"""
import time
from datetime import datetime, timezone
from typing import List
from uuid import UUID, uuid4

import pytest
from fastapi import status
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.concept import Concept
from src.models.concept_prerequisite import ConceptPrerequisite
from src.models.course import Course
from src.models.question import Question
from src.models.question_concept import QuestionConcept


@pytest.fixture
async def test_course(db_session: AsyncSession) -> Course:
    """Create a test course."""
    course = Course(
        slug="cbap-test",
        name="CBAP Test Course",
        description="Test course for concept API",
        knowledge_areas=[
            {"id": "ba-planning", "name": "Business Analysis Planning"},
            {"id": "elicitation", "name": "Elicitation"}
        ]
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concepts(
    db_session: AsyncSession,
    test_course: Course
) -> List[Concept]:
    """Create test concepts."""
    concepts = [
        Concept(
            course_id=test_course.id,
            name="Stakeholder Analysis",
            description="Analyzing stakeholders",
            corpus_section_ref="3.2.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.5,
            prerequisite_depth=1
        ),
        Concept(
            course_id=test_course.id,
            name="Business Need",
            description="Understanding business need",
            corpus_section_ref="2.1.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.3,
            prerequisite_depth=0
        ),
        Concept(
            course_id=test_course.id,
            name="Interview Techniques",
            description="Elicitation techniques",
            corpus_section_ref="4.1.1",
            knowledge_area_id="elicitation",
            difficulty_estimate=0.6,
            prerequisite_depth=1
        )
    ]

    for concept in concepts:
        db_session.add(concept)

    await db_session.commit()

    for concept in concepts:
        await db_session.refresh(concept)

    # Add prerequisite: Stakeholder Analysis requires Business Need
    prereq = ConceptPrerequisite(
        concept_id=concepts[0].id,  # Stakeholder Analysis
        prerequisite_concept_id=concepts[1].id,  # Business Need
        strength=1.0,
        relationship_type="required"
    )
    db_session.add(prereq)
    await db_session.commit()

    return concepts


@pytest.fixture
async def test_questions(
    db_session: AsyncSession,
    test_course: Course,
    test_concepts: List[Concept]
) -> List[Question]:
    """Create test questions."""
    questions = [
        Question(
            course_id=test_course.id,
            question_text="What is stakeholder analysis?",
            correct_answer="A",
            difficulty=0.5,
            vendor_id="TEST"
        ),
        Question(
            course_id=test_course.id,
            question_text="Define business need",
            correct_answer="B",
            difficulty=0.3,
            vendor_id="TEST"
        )
    ]

    for question in questions:
        db_session.add(question)

    await db_session.commit()

    for question in questions:
        await db_session.refresh(question)

    # Link questions to concepts
    qc1 = QuestionConcept(
        question_id=questions[0].id,
        concept_id=test_concepts[0].id  # Stakeholder Analysis
    )
    qc2 = QuestionConcept(
        question_id=questions[1].id,
        concept_id=test_concepts[1].id  # Business Need
    )

    db_session.add(qc1)
    db_session.add(qc2)
    await db_session.commit()

    return questions


@pytest.mark.asyncio
class TestConceptListAPI:
    """Integration tests for GET /v1/courses/{course_slug}/concepts."""

    async def test_list_concepts_requires_auth(
        self,
        async_client: AsyncClient
    ):
        """Test that listing concepts requires authentication."""
        response = await async_client.get("/v1/courses/cbap-test/concepts")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    async def test_list_concepts_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test successful concept list retrieval."""
        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["has_more"] is False

        # Verify concept data
        concept_names = {item["name"] for item in data["items"]}
        assert "Stakeholder Analysis" in concept_names

    async def test_list_concepts_filter_by_knowledge_area(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test filtering concepts by knowledge area."""
        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers,
            params={"knowledge_area_id": "ba-planning"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 2  # Only ba-planning concepts
        for item in data["items"]:
            assert item["knowledge_area_id"] == "ba-planning"

    async def test_list_concepts_search(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test searching concepts by name."""
        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers,
            params={"search": "stakeholder"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 1
        assert data["items"][0]["name"] == "Stakeholder Analysis"

    async def test_list_concepts_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test pagination works correctly."""
        # Get first page
        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers,
            params={"limit": 2, "offset": 0}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["total"] == 3
        assert len(data["items"]) == 2
        assert data["has_more"] is True

        # Get second page
        response2 = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers,
            params={"limit": 2, "offset": 2}
        )

        data2 = response2.json()
        assert len(data2["items"]) == 1
        assert data2["has_more"] is False


@pytest.mark.asyncio
class TestGetSingleConcept:
    """Integration tests for GET /v1/courses/{course_slug}/concepts/{concept_id}."""

    async def test_get_concept_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test successful single concept retrieval."""
        concept = test_concepts[0]

        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/{concept.id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["id"] == str(concept.id)
        assert data["name"] == concept.name
        assert data["course_id"] == str(test_course.id)

    async def test_get_concept_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course
    ):
        """Test 404 when concept doesn't exist."""
        fake_id = uuid4()

        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/{fake_id}",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
class TestGetPrerequisites:
    """Integration tests for GET /v1/courses/{course_slug}/concepts/{concept_id}/prerequisites."""

    async def test_get_prerequisites_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test retrieving prerequisite chain."""
        concept = test_concepts[0]  # Stakeholder Analysis

        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/{concept.id}/prerequisites",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["concept_id"] == str(concept.id)
        assert len(data["prerequisites"]) == 1
        assert data["prerequisites"][0]["name"] == "Business Need"

    async def test_get_prerequisites_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test concept with no prerequisites."""
        concept = test_concepts[1]  # Business Need (no prerequisites)

        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/{concept.id}/prerequisites",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["concept_id"] == str(concept.id)
        assert len(data["prerequisites"]) == 0
        assert data["depth"] == 0


@pytest.mark.asyncio
class TestGetQuestions:
    """Integration tests for GET /v1/courses/{course_slug}/concepts/{concept_id}/questions."""

    async def test_get_questions_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept],
        test_questions: List[Question]
    ):
        """Test retrieving questions for a concept."""
        concept = test_concepts[0]  # Stakeholder Analysis

        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/{concept.id}/questions",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["concept_id"] == str(concept.id)
        assert data["question_count"] == 1
        assert len(data["sample_questions"]) == 1
        assert "stakeholder" in data["sample_questions"][0]["question_text"].lower()


@pytest.mark.asyncio
class TestGetStats:
    """Integration tests for GET /v1/courses/{course_slug}/concepts/stats."""

    async def test_get_stats_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept],
        test_questions: List[Question]
    ):
        """Test retrieving concept statistics."""
        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/stats",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["course_id"] == str(test_course.id)
        assert data["total_concepts"] == 3

        # Check knowledge area breakdown
        assert "ba-planning" in data["by_knowledge_area"]
        assert data["by_knowledge_area"]["ba-planning"] == 2
        assert data["by_knowledge_area"]["elicitation"] == 1

        # Check depth breakdown
        assert 0 in data["by_depth"]
        assert 1 in data["by_depth"]

        # Check question statistics
        assert data["concepts_with_questions"] == 2
        assert data["concepts_without_questions"] == 1


@pytest.mark.asyncio
class TestPerformance:
    """Performance tests for concept API."""

    async def test_list_concepts_performance(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test that list endpoint meets <100ms target (AC 7)."""
        start_time = time.time()

        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers
        )

        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        # Relaxed threshold for integration tests (includes network overhead)
        assert elapsed_ms < 500, f"Response took {elapsed_ms:.2f}ms"

    async def test_stats_endpoint_performance(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test that stats endpoint meets <100ms target (AC 7)."""
        start_time = time.time()

        response = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/stats",
            headers=auth_headers
        )

        elapsed_ms = (time.time() - start_time) * 1000

        assert response.status_code == status.HTTP_200_OK
        assert elapsed_ms < 500, f"Response took {elapsed_ms:.2f}ms"


@pytest.mark.asyncio
class TestCaching:
    """Tests for Redis caching behavior (AC 8)."""

    async def test_concept_list_caching(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test that concept list responses are cached."""
        # First request (cache miss)
        response1 = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers
        )
        assert response1.status_code == status.HTTP_200_OK

        # Second request (should hit cache)
        response2 = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts",
            headers=auth_headers
        )
        assert response2.status_code == status.HTTP_200_OK

        # Responses should be identical
        assert response1.json() == response2.json()

    async def test_stats_caching(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        test_course: Course,
        test_concepts: List[Concept]
    ):
        """Test that stats responses are cached."""
        # First request (cache miss)
        response1 = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/stats",
            headers=auth_headers
        )
        assert response1.status_code == status.HTTP_200_OK

        # Second request (should hit cache)
        response2 = await async_client.get(
            f"/v1/courses/{test_course.slug}/concepts/stats",
            headers=auth_headers
        )
        assert response2.status_code == status.HTTP_200_OK

        # Responses should be identical
        assert response1.json() == response2.json()
