"""
Unit tests for question retrieval routes.

Tests the GET /v1/courses/{course_slug}/questions endpoint logic
with mocked dependencies (repositories, database).

Per AC 8: Tests filter by concept, by knowledge area, by difficulty range.
"""

import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException
from datetime import datetime

from src.models.question import Question
from src.models.course import Course
from src.models.user import User
from src.routes.questions import get_questions
from src.schemas.question import PaginatedQuestionResponse


# Mock Request object for response time tracking
class MockRequest:
    """Mock FastAPI Request object for testing."""
    def __init__(self):
        self.state = MagicMock()
        self.state.response_time_ms = None


@pytest.mark.asyncio
class TestQuestionRoutesUnit:
    """Unit tests for question retrieval routes layer."""

    async def test_get_questions_filter_by_concept(self):
        """Test filtering questions by concept_ids."""
        # Setup test data
        course_id = uuid.uuid4()
        concept_id1 = uuid.uuid4()
        concept_id2 = uuid.uuid4()
        question_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True
        )

        test_question = Question(
            id=question_id,
            course_id=course_id,
            question_text="Test question",
            options={"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
            correct_answer="A",
            explanation="Test explanation",
            knowledge_area_id="strategy",
            difficulty=0.5,
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            source="test",
            times_asked=0,
            times_correct=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        test_user = User(
            id=uuid.uuid4(),
            email="test@example.com",
            hashed_password="hashed"
        )

        # Mock repositories
        mock_question_repo = MagicMock()
        mock_question_repo.get_questions_filtered = AsyncMock(
            return_value=([(test_question, [concept_id1, concept_id2])], 1)
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_request = MockRequest()

        # Execute
        result = await get_questions(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=[concept_id1],
            knowledge_area_id=None,
            difficulty_min=0.0,
            difficulty_max=1.0,
            exclude_ids=None,
            limit=10,
            offset=0,
            question_repo=mock_question_repo,
            course_repo=mock_course_repo,
            current_user=test_user
        )

        # Assert
        assert isinstance(result, PaginatedQuestionResponse)
        assert result.total == 1
        assert len(result.items) == 1
        assert result.items[0].id == question_id
        assert result.items[0].concept_ids == [concept_id1, concept_id2]

        # Verify repository was called with correct params
        mock_question_repo.get_questions_filtered.assert_called_once_with(
            course_id=course_id,
            concept_ids=[concept_id1],
            knowledge_area_id=None,
            difficulty_min=0.0,
            difficulty_max=1.0,
            exclude_ids=None,
            limit=10,
            offset=0
        )

    async def test_get_questions_filter_by_knowledge_area(self):
        """Test filtering questions by knowledge_area_id."""
        course_id = uuid.uuid4()
        question_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True
        )

        test_question = Question(
            id=question_id,
            course_id=course_id,
            question_text="Strategy question",
            options={"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
            correct_answer="A",
            explanation="Explanation",
            knowledge_area_id="strategy",
            difficulty=0.5,
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            source="test",
            times_asked=0,
            times_correct=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        test_user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="hashed")

        mock_question_repo = MagicMock()
        mock_question_repo.get_questions_filtered = AsyncMock(
            return_value=([(test_question, [])], 1)
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_request = MockRequest()

        # Execute with knowledge_area filter
        result = await get_questions(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=None,
            knowledge_area_id="strategy",
            difficulty_min=0.0,
            difficulty_max=1.0,
            exclude_ids=None,
            limit=10,
            offset=0,
            question_repo=mock_question_repo,
            course_repo=mock_course_repo,
            current_user=test_user
        )

        # Assert
        assert result.total == 1
        assert result.items[0].knowledge_area_id == "strategy"

        # Verify knowledge_area_id was passed to repository
        mock_question_repo.get_questions_filtered.assert_called_once()
        call_kwargs = mock_question_repo.get_questions_filtered.call_args.kwargs
        assert call_kwargs['knowledge_area_id'] == "strategy"

    async def test_get_questions_filter_by_difficulty_range(self):
        """Test filtering questions by difficulty range."""
        course_id = uuid.uuid4()
        question_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True
        )

        test_question = Question(
            id=question_id,
            course_id=course_id,
            question_text="Medium difficulty question",
            options={"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
            correct_answer="A",
            explanation="Explanation",
            knowledge_area_id="strategy",
            difficulty=0.5,  # Within range 0.3-0.7
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            source="test",
            times_asked=0,
            times_correct=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        test_user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="hashed")

        mock_question_repo = MagicMock()
        mock_question_repo.get_questions_filtered = AsyncMock(
            return_value=([(test_question, [])], 1)
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_request = MockRequest()

        # Execute with difficulty range filter
        result = await get_questions(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=None,
            knowledge_area_id=None,
            difficulty_min=0.3,
            difficulty_max=0.7,
            exclude_ids=None,
            limit=10,
            offset=0,
            question_repo=mock_question_repo,
            course_repo=mock_course_repo,
            current_user=test_user
        )

        # Assert
        assert result.total == 1
        assert result.items[0].difficulty == 0.5

        # Verify difficulty range was passed to repository
        mock_question_repo.get_questions_filtered.assert_called_once()
        call_kwargs = mock_question_repo.get_questions_filtered.call_args.kwargs
        assert call_kwargs['difficulty_min'] == 0.3
        assert call_kwargs['difficulty_max'] == 0.7

    async def test_get_questions_course_not_found(self):
        """Test that 404 is raised when course does not exist."""
        test_user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="hashed")

        mock_question_repo = MagicMock()
        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=None)  # Course not found

        mock_request = MockRequest()

        # Execute and expect HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await get_questions(
                request=mock_request,
                course_slug="non-existent",
                concept_ids=None,
                knowledge_area_id=None,
                difficulty_min=0.0,
                difficulty_max=1.0,
                exclude_ids=None,
                limit=10,
                offset=0,
                question_repo=mock_question_repo,
                course_repo=mock_course_repo,
                current_user=test_user
            )

        # Assert 404 status code
        assert exc_info.value.status_code == 404
        assert "COURSE_NOT_FOUND" in str(exc_info.value.detail)

    async def test_get_questions_excludes_sensitive_fields(self):
        """Test that response excludes correct_answer and explanation."""
        course_id = uuid.uuid4()
        question_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True
        )

        test_question = Question(
            id=question_id,
            course_id=course_id,
            question_text="Test question",
            options={"A": "Opt A", "B": "Opt B", "C": "Opt C", "D": "Opt D"},
            correct_answer="A",  # Should be excluded from response
            explanation="Secret explanation",  # Should be excluded from response
            knowledge_area_id="strategy",
            difficulty=0.5,
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            source="test",
            times_asked=0,
            times_correct=0,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

        test_user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="hashed")

        mock_question_repo = MagicMock()
        mock_question_repo.get_questions_filtered = AsyncMock(
            return_value=([(test_question, [])], 1)
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_request = MockRequest()

        # Execute
        result = await get_questions(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=None,
            knowledge_area_id=None,
            difficulty_min=0.0,
            difficulty_max=1.0,
            exclude_ids=None,
            limit=10,
            offset=0,
            question_repo=mock_question_repo,
            course_repo=mock_course_repo,
            current_user=test_user
        )

        # Assert sensitive fields are not in response
        response_dict = result.items[0].model_dump()
        assert 'correct_answer' not in response_dict
        assert 'explanation' not in response_dict

        # Assert safe fields are present
        assert 'question_text' in response_dict
        assert 'options' in response_dict
        assert 'difficulty' in response_dict

    async def test_get_questions_pagination(self):
        """Test pagination metadata is correctly calculated."""
        course_id = uuid.uuid4()

        test_course = Course(
            id=course_id,
            slug="cbap-test",
            name="CBAP Test",
            corpus_name="BABOK v3",
            knowledge_areas=[],
            is_active=True
        )

        # Create 2 questions
        questions_with_concepts = [
            (
                Question(
                    id=uuid.uuid4(),
                    course_id=course_id,
                    question_text=f"Question {i}",
                    options={"A": "A", "B": "B", "C": "C", "D": "D"},
                    correct_answer="A",
                    explanation="Exp",
                    knowledge_area_id="strategy",
                    difficulty=0.5,
                    discrimination=1.0,
                    guess_rate=0.25,
                    slip_rate=0.10,
                    source="test",
                    times_asked=0,
                    times_correct=0,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                ),
                []
            )
            for i in range(2)
        ]

        test_user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="hashed")

        mock_question_repo = MagicMock()
        mock_question_repo.get_questions_filtered = AsyncMock(
            return_value=(questions_with_concepts, 4)  # 2 returned, 4 total
        )

        mock_course_repo = MagicMock()
        mock_course_repo.get_active_by_slug = AsyncMock(return_value=test_course)

        mock_request = MockRequest()

        # Execute with pagination
        result = await get_questions(
            request=mock_request,
            course_slug="cbap-test",
            concept_ids=None,
            knowledge_area_id=None,
            difficulty_min=0.0,
            difficulty_max=1.0,
            exclude_ids=None,
            limit=2,
            offset=0,
            question_repo=mock_question_repo,
            course_repo=mock_course_repo,
            current_user=test_user
        )

        # Assert pagination metadata
        assert result.total == 4
        assert result.limit == 2
        assert result.offset == 0
        assert len(result.items) == 2
        assert result.has_more is True  # 2 returned, 4 total -> more available

    async def test_get_questions_difficulty_min_greater_than_max(self):
        """Test that 400 is raised when difficulty_min > difficulty_max."""
        test_user = User(id=uuid.uuid4(), email="test@example.com", hashed_password="hashed")

        mock_question_repo = MagicMock()
        mock_course_repo = MagicMock()

        mock_request = MockRequest()

        # Execute with invalid difficulty range
        with pytest.raises(HTTPException) as exc_info:
            await get_questions(
                request=mock_request,
                course_slug="cbap-test",
                concept_ids=None,
                knowledge_area_id=None,
                difficulty_min=0.8,  # Greater than max
                difficulty_max=0.3,
                exclude_ids=None,
                limit=10,
                offset=0,
                question_repo=mock_question_repo,
                course_repo=mock_course_repo,
                current_user=test_user
            )

        # Assert 400 status code
        assert exc_info.value.status_code == 400
        assert "INVALID_DIFFICULTY_RANGE" in str(exc_info.value.detail)
