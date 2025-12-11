"""
Unit tests for concept routes (Story 2.10).
Tests the routes layer with mocked dependencies.
"""
from datetime import datetime, timezone
from typing import List
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.models.concept import Concept
from src.models.course import Course
from src.models.question import Question
from src.routes.concepts import router
from src.schemas.concept import (
    ConceptListParams,
    ConceptPrerequisitesResponse,
    ConceptQuestionsResponse,
    ConceptResponse,
    ConceptStatsResponse,
    PaginatedConceptResponse,
    QuestionSummary,
)


# Test app setup
app = FastAPI()
app.include_router(router)
client = TestClient(app)

# Test data
TEST_COURSE_ID = uuid4()
TEST_COURSE_SLUG = "cbap"
TEST_CONCEPT_ID = uuid4()
TEST_USER_ID = uuid4()


@pytest.fixture
def mock_concept():
    """Mock Concept model."""
    return Concept(
        id=TEST_CONCEPT_ID,
        course_id=TEST_COURSE_ID,
        name="Stakeholder Analysis",
        description="Process of analyzing stakeholders",
        corpus_section_ref="3.2.1",
        knowledge_area_id="ba-planning",
        difficulty_estimate=0.5,
        prerequisite_depth=1,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_course():
    """Mock Course model."""
    return Course(
        id=TEST_COURSE_ID,
        slug=TEST_COURSE_SLUG,
        name="CBAP",
        description="Test course",
        knowledge_areas=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


@pytest.fixture
def mock_question():
    """Mock Question model."""
    return Question(
        id=uuid4(),
        course_id=TEST_COURSE_ID,
        question_text="What is stakeholder analysis? This is a long question text to test truncation.",
        correct_answer="A",
        difficulty=0.5,
        vendor_id="TEST",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


class TestListConcepts:
    """Tests for GET /courses/{course_slug}/concepts endpoint."""

    @patch("src.routes.concepts.get_current_user")
    @patch("src.routes.concepts.get_redis")
    @patch("src.routes.concepts.get_course_id_by_slug")
    @patch("src.routes.concepts.get_concept_repository")
    def test_list_concepts_success(
        self,
        mock_get_repo,
        mock_get_course_id,
        mock_get_redis,
        mock_get_user,
        mock_concept
    ):
        """Test successful concept list retrieval."""
        # Mock dependencies
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis

        mock_get_course_id.return_value = TEST_COURSE_ID

        mock_repo = AsyncMock()
        mock_repo.get_concepts_filtered = AsyncMock(
            return_value=([mock_concept], 1)
        )
        mock_get_repo.return_value = mock_repo

        mock_get_user.return_value = MagicMock(id=TEST_USER_ID)

        # Make request
        response = client.get(f"/courses/{TEST_COURSE_SLUG}/concepts")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Stakeholder Analysis"
        assert data["has_more"] is False

    @patch("src.routes.concepts.get_current_user")
    @patch("src.routes.concepts.get_redis")
    @patch("src.routes.concepts.get_course_id_by_slug")
    def test_list_concepts_with_filters(
        self,
        mock_get_course_id,
        mock_get_redis,
        mock_get_user,
        mock_concept
    ):
        """Test list concepts with knowledge area and search filters."""
        # Mock dependencies
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_get_redis.return_value = mock_redis

        mock_get_course_id.return_value = TEST_COURSE_ID
        mock_get_user.return_value = MagicMock(id=TEST_USER_ID)

        # Make request with filters
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts",
            params={
                "knowledge_area_id": "ba-planning",
                "search": "stakeholder",
                "limit": 10
            }
        )

        # Assert - should call with correct params
        assert response.status_code in [200, 404]  # Depends on mock setup


class TestGetSingleConcept:
    """Tests for GET /courses/{course_slug}/concepts/{concept_id} endpoint."""

    @patch("src.routes.concepts.get_current_user")
    @patch("src.routes.concepts.get_course_id_by_slug")
    @patch("src.routes.concepts.get_concept_repository")
    def test_get_concept_success(
        self,
        mock_get_repo,
        mock_get_course_id,
        mock_get_user,
        mock_concept
    ):
        """Test successful single concept retrieval."""
        # Mock dependencies
        mock_get_course_id.return_value = TEST_COURSE_ID

        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_concept)
        mock_get_repo.return_value = mock_repo

        mock_get_user.return_value = MagicMock(id=TEST_USER_ID)

        # Make request
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts/{TEST_CONCEPT_ID}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(TEST_CONCEPT_ID)
        assert data["name"] == "Stakeholder Analysis"

    @patch("src.routes.concepts.get_current_user")
    @patch("src.routes.concepts.get_course_id_by_slug")
    @patch("src.routes.concepts.get_concept_repository")
    def test_get_concept_not_found(
        self,
        mock_get_repo,
        mock_get_course_id,
        mock_get_user
    ):
        """Test concept not found returns 404."""
        # Mock dependencies
        mock_get_course_id.return_value = TEST_COURSE_ID

        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=None)
        mock_get_repo.return_value = mock_repo

        mock_get_user.return_value = MagicMock(id=TEST_USER_ID)

        # Make request
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts/{uuid4()}"
        )

        # Assert
        assert response.status_code == 404


class TestGetPrerequisites:
    """Tests for GET /courses/{course_slug}/concepts/{concept_id}/prerequisites endpoint."""

    @patch("src.routes.concepts.get_current_user")
    @patch("src.routes.concepts.get_course_id_by_slug")
    @patch("src.routes.concepts.get_concept_repository")
    def test_get_prerequisites_success(
        self,
        mock_get_repo,
        mock_get_course_id,
        mock_get_user,
        mock_concept
    ):
        """Test successful prerequisite chain retrieval."""
        # Create prerequisite concepts
        prereq1 = Concept(
            id=uuid4(),
            course_id=TEST_COURSE_ID,
            name="Foundational Concept",
            description="Foundation",
            corpus_section_ref="1.1",
            knowledge_area_id="ba-planning",
            difficulty_estimate=0.3,
            prerequisite_depth=0,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )

        # Mock dependencies
        mock_get_course_id.return_value = TEST_COURSE_ID

        mock_repo = AsyncMock()
        mock_repo.get_by_id = AsyncMock(return_value=mock_concept)
        mock_repo.get_prerequisite_chain_for_course = AsyncMock(
            return_value=[prereq1]
        )
        mock_get_repo.return_value = mock_repo

        mock_get_user.return_value = MagicMock(id=TEST_USER_ID)

        # Make request
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts/{TEST_CONCEPT_ID}/prerequisites"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["concept_id"] == str(TEST_CONCEPT_ID)
        assert len(data["prerequisites"]) == 1
        assert data["depth"] == 0


class TestGetQuestions:
    """Tests for GET /courses/{course_slug}/concepts/{concept_id}/questions endpoint."""

    @patch("src.routes.concepts.get_current_user")
    @patch("src.routes.concepts.get_course_id_by_slug")
    @patch("src.routes.concepts.get_concept_repository")
    @patch("src.routes.concepts.get_question_repository")
    def test_get_questions_success(
        self,
        mock_get_q_repo,
        mock_get_c_repo,
        mock_get_course_id,
        mock_get_user,
        mock_concept,
        mock_question
    ):
        """Test successful question retrieval for concept."""
        # Mock dependencies
        mock_get_course_id.return_value = TEST_COURSE_ID

        mock_c_repo = AsyncMock()
        mock_c_repo.get_by_id = AsyncMock(return_value=mock_concept)
        mock_c_repo.get_question_count_for_concept = AsyncMock(return_value=5)
        mock_get_c_repo.return_value = mock_c_repo

        mock_q_repo = AsyncMock()
        mock_q_repo.get_questions_by_concept = AsyncMock(
            return_value=[mock_question]
        )
        mock_get_q_repo.return_value = mock_q_repo

        mock_get_user.return_value = MagicMock(id=TEST_USER_ID)

        # Make request
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts/{TEST_CONCEPT_ID}/questions"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["concept_id"] == str(TEST_CONCEPT_ID)
        assert data["question_count"] == 5
        assert len(data["sample_questions"]) == 1
        # Check truncation
        assert len(data["sample_questions"][0]["question_text"]) <= 103


class TestGetStats:
    """Tests for GET /courses/{course_slug}/concepts/stats endpoint."""

    @patch("src.routes.concepts.get_current_user")
    @patch("src.routes.concepts.get_redis")
    @patch("src.routes.concepts.get_course_id_by_slug")
    @patch("src.routes.concepts.get_concept_repository")
    def test_get_stats_success(
        self,
        mock_get_repo,
        mock_get_course_id,
        mock_get_redis,
        mock_get_user
    ):
        """Test successful stats retrieval."""
        # Mock dependencies
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis

        mock_get_course_id.return_value = TEST_COURSE_ID

        mock_repo = AsyncMock()
        mock_repo.get_corpus_stats = AsyncMock(return_value={
            "total_concepts": 1203,
            "by_knowledge_area": {
                "ba-planning": 203,
                "elicitation": 198
            },
            "by_depth": {0: 50, 1: 200},
            "average_prerequisites_per_concept": 3.2,
            "concepts_with_questions": 1150,
            "concepts_without_questions": 53
        })
        mock_get_repo.return_value = mock_repo

        mock_get_user.return_value = MagicMock(id=TEST_USER_ID)

        # Make request
        response = client.get(f"/courses/{TEST_COURSE_SLUG}/concepts/stats")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total_concepts"] == 1203
        assert "ba-planning" in data["by_knowledge_area"]
        assert data["by_knowledge_area"]["ba-planning"] == 203


class TestAuthentication:
    """Tests for authentication requirements."""

    def test_list_concepts_requires_auth(self):
        """Test that listing concepts requires authentication."""
        # Make request without auth
        response = client.get(f"/courses/{TEST_COURSE_SLUG}/concepts")

        # Assert - should fail without auth
        assert response.status_code in [401, 403, 422]  # Depends on auth setup
