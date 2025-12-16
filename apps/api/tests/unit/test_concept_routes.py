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

from src.dependencies import get_current_user
from src.models.concept import Concept
from src.models.course import Course
from src.models.question import Question
from src.models.user import User
from src.routes.concepts import (
    router,
    get_concept_repository,
    get_course_repository,
    get_question_repository,
)
from src.schemas.concept import (
    ConceptListParams,
    ConceptPrerequisitesResponse,
    ConceptQuestionsResponse,
    ConceptResponse,
    ConceptStatsResponse,
    PaginatedConceptResponse,
    QuestionSummary,
)


# Test data
TEST_COURSE_ID = uuid4()
TEST_COURSE_SLUG = "cbap"
TEST_CONCEPT_ID = uuid4()
TEST_USER_ID = uuid4()

# Mock user for dependency override
mock_user = MagicMock(spec=User)
mock_user.id = TEST_USER_ID
mock_user.email = "test@example.com"
mock_user.is_admin = False


def override_get_current_user():
    """Override get_current_user dependency for tests."""
    return mock_user


# Mock repositories as module-level so tests can configure them
mock_concept_repo = AsyncMock()
mock_course_repo = AsyncMock()
mock_question_repo = AsyncMock()


def override_concept_repo():
    return mock_concept_repo


def override_course_repo():
    return mock_course_repo


def override_question_repo():
    return mock_question_repo


# Test app setup with dependency overrides
app = FastAPI()
app.include_router(router)
app.dependency_overrides[get_current_user] = override_get_current_user
app.dependency_overrides[get_concept_repository] = override_concept_repo
app.dependency_overrides[get_course_repository] = override_course_repo
app.dependency_overrides[get_question_repository] = override_question_repo
client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_mocks():
    """Reset all module-level mocks before each test."""
    mock_concept_repo.reset_mock()
    mock_course_repo.reset_mock()
    mock_question_repo.reset_mock()
    yield


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
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="A",
        explanation="Stakeholder analysis is a key process in business analysis.",
        knowledge_area_id="ba-planning",
        difficulty=0.5,
        source="vendor",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )


class TestListConcepts:
    """Tests for GET /courses/{course_slug}/concepts endpoint."""

    @patch("src.routes.concepts.get_redis")
    def test_list_concepts_success(
        self,
        mock_get_redis,
        mock_concept,
        mock_course
    ):
        """Test successful concept list retrieval."""
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis

        # Configure mock repositories
        mock_course_repo.get_by_slug = AsyncMock(return_value=mock_course)
        mock_concept_repo.get_concepts_filtered = AsyncMock(
            return_value=([mock_concept], 1)
        )

        # Make request
        response = client.get(f"/courses/{TEST_COURSE_SLUG}/concepts")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Stakeholder Analysis"
        assert data["has_more"] is False

    @patch("src.routes.concepts.get_redis")
    def test_list_concepts_with_filters(
        self,
        mock_get_redis,
        mock_concept,
        mock_course
    ):
        """Test list concepts with knowledge area and search filters."""
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis

        # Configure mock repositories
        mock_course_repo.get_by_slug = AsyncMock(return_value=mock_course)
        mock_concept_repo.get_concepts_filtered = AsyncMock(
            return_value=([mock_concept], 1)
        )

        # Make request with filters
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts",
            params={
                "knowledge_area_id": "ba-planning",
                "search": "stakeholder",
                "limit": 10
            }
        )

        # Assert
        assert response.status_code == 200


class TestGetSingleConcept:
    """Tests for GET /courses/{course_slug}/concepts/{concept_id} endpoint."""

    def test_get_concept_success(
        self,
        mock_concept,
        mock_course
    ):
        """Test successful single concept retrieval."""
        # Configure mock repositories
        mock_course_repo.get_by_slug = AsyncMock(return_value=mock_course)
        mock_concept_repo.get_by_id = AsyncMock(return_value=mock_concept)

        # Make request
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts/{TEST_CONCEPT_ID}"
        )

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(TEST_CONCEPT_ID)
        assert data["name"] == "Stakeholder Analysis"

    def test_get_concept_not_found(
        self,
        mock_course
    ):
        """Test concept not found returns 404."""
        # Configure mock repositories
        mock_course_repo.get_by_slug = AsyncMock(return_value=mock_course)
        mock_concept_repo.get_by_id = AsyncMock(return_value=None)

        # Make request
        response = client.get(
            f"/courses/{TEST_COURSE_SLUG}/concepts/{uuid4()}"
        )

        # Assert
        assert response.status_code == 404


class TestGetPrerequisites:
    """Tests for GET /courses/{course_slug}/concepts/{concept_id}/prerequisites endpoint."""

    def test_get_prerequisites_success(
        self,
        mock_concept,
        mock_course
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

        # Configure mock repositories
        mock_course_repo.get_by_slug = AsyncMock(return_value=mock_course)
        mock_concept_repo.get_by_id = AsyncMock(return_value=mock_concept)
        mock_concept_repo.get_prerequisite_chain_for_course = AsyncMock(
            return_value=[prereq1]
        )

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

    def test_get_questions_success(
        self,
        mock_concept,
        mock_question,
        mock_course
    ):
        """Test successful question retrieval for concept."""
        # Configure mock repositories
        mock_course_repo.get_by_slug = AsyncMock(return_value=mock_course)
        mock_concept_repo.get_by_id = AsyncMock(return_value=mock_concept)
        mock_concept_repo.get_question_count_for_concept = AsyncMock(return_value=5)
        mock_question_repo.get_questions_by_concept = AsyncMock(
            return_value=[mock_question]
        )

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

    @patch("src.routes.concepts.get_redis")
    def test_get_stats_success(
        self,
        mock_get_redis,
        mock_course
    ):
        """Test successful stats retrieval."""
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock()
        mock_get_redis.return_value = mock_redis

        # Configure mock repositories
        mock_course_repo.get_by_slug = AsyncMock(return_value=mock_course)
        mock_concept_repo.get_corpus_stats = AsyncMock(return_value={
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
        # Create a test app without auth override
        no_auth_app = FastAPI()
        no_auth_app.include_router(router)
        no_auth_client = TestClient(no_auth_app)

        # Make request without auth
        response = no_auth_client.get(f"/courses/{TEST_COURSE_SLUG}/concepts")

        # Assert - should fail without auth
        assert response.status_code in [401, 403, 422]  # Depends on auth setup
