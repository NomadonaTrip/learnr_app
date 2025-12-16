"""
Integration tests for vendor question import with database.
These tests require a running PostgreSQL and Qdrant instance.
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest
import pytest_asyncio
from sqlalchemy import select

# Add paths for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "apps" / "api"))
sys.path.insert(0, str(project_root / "scripts"))

from src.db.session import AsyncSessionLocal
from src.models.concept import Concept
from src.models.course import Course
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.repositories.concept_repository import ConceptRepository
from src.repositories.question_repository import QuestionRepository


# Skip all tests if database is not available
pytestmark = pytest.mark.skipif(
    os.getenv("SKIP_INTEGRATION_TESTS", "true").lower() == "true",
    reason="Integration tests disabled (set SKIP_INTEGRATION_TESTS=false to run)"
)


@pytest_asyncio.fixture
async def db_session():
    """Create a database session for testing."""
    async with AsyncSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def test_course(db_session):
    """Create a test course for integration tests."""
    course = Course(
        id=uuid4(),
        slug="test-integration-course",
        name="Test Integration Course",
        description="Course for integration testing",
        knowledge_areas=[
            {"id": "ka-1", "name": "Knowledge Area 1", "short_name": "KA1", "display_order": 1},
            {"id": "ka-2", "name": "Knowledge Area 2", "short_name": "KA2", "display_order": 2},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    yield course

    # Cleanup
    await db_session.delete(course)
    await db_session.commit()


@pytest_asyncio.fixture
async def test_concepts(db_session, test_course):
    """Create test concepts for integration tests."""
    concept_repo = ConceptRepository(db_session)

    concepts = []
    for i in range(3):
        concept = Concept(
            id=uuid4(),
            course_id=test_course.id,
            name=f"Test Concept {i + 1}",
            description=f"Description for test concept {i + 1}",
            knowledge_area_id="ka-1" if i < 2 else "ka-2",
            corpus_section_ref=f"1.{i + 1}",
        )
        db_session.add(concept)
        concepts.append(concept)

    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)

    yield concepts

    # Cleanup handled by cascade from course


class TestQuestionRepositoryIntegration:
    """Integration tests for QuestionRepository."""

    @pytest.mark.asyncio
    async def test_create_question(self, db_session, test_course):
        """Test creating a question in the database."""
        repo = QuestionRepository(db_session)

        question_data = {
            "course_id": test_course.id,
            "question_text": "What is integration testing?",
            "options": {
                "A": "Testing individual units",
                "B": "Testing module interactions",
                "C": "Testing user interface",
                "D": "Testing performance",
            },
            "correct_answer": "B",
            "explanation": "Integration testing focuses on module interactions.",
            "knowledge_area_id": "ka-1",
            "difficulty": 0.5,
            "source": "test",
        }

        question = await repo.create_question(question_data)

        assert question.id is not None
        assert question.course_id == test_course.id
        assert question.question_text == "What is integration testing?"
        assert question.options["B"] == "Testing module interactions"

        # Cleanup
        await db_session.delete(question)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_bulk_create_questions(self, db_session, test_course):
        """Test bulk creating questions."""
        repo = QuestionRepository(db_session)

        questions_data = [
            {
                "course_id": test_course.id,
                "question_text": f"Bulk question {i}?",
                "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
                "correct_answer": "A",
                "explanation": f"Explanation {i}",
                "knowledge_area_id": "ka-1",
                "difficulty": 0.5,
                "source": "test",
            }
            for i in range(5)
        ]

        count = await repo.bulk_create_questions(questions_data)

        assert count == 5

        # Verify questions exist
        questions, total = await repo.get_questions_by_course(test_course.id)
        assert total >= 5

        # Cleanup
        for q in questions:
            await db_session.delete(q)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_questions_by_ka(self, db_session, test_course):
        """Test retrieving questions by knowledge area."""
        repo = QuestionRepository(db_session)

        # Create questions in different KAs
        q1 = Question(
            course_id=test_course.id,
            question_text="KA1 Question",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
        )
        q2 = Question(
            course_id=test_course.id,
            question_text="KA2 Question",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="B",
            explanation="Test",
            knowledge_area_id="ka-2",
            difficulty=0.5,
            source="test",
        )
        db_session.add_all([q1, q2])
        await db_session.commit()

        # Retrieve by KA
        ka1_questions = await repo.get_questions_by_ka(test_course.id, "ka-1")
        ka2_questions = await repo.get_questions_by_ka(test_course.id, "ka-2")

        assert len([q for q in ka1_questions if q.question_text == "KA1 Question"]) == 1
        assert len([q for q in ka2_questions if q.question_text == "KA2 Question"]) == 1

        # Cleanup
        await db_session.delete(q1)
        await db_session.delete(q2)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_concept_mapping(self, db_session, test_course, test_concepts):
        """Test adding concept mappings to questions."""
        repo = QuestionRepository(db_session)

        # Create a question
        question = Question(
            course_id=test_course.id,
            question_text="Concept mapping test question",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
        )
        db_session.add(question)
        await db_session.commit()
        await db_session.refresh(question)

        # Add concept mapping
        mapping = await repo.add_concept_mapping(
            question_id=question.id,
            concept_id=test_concepts[0].id,
            relevance=0.9,
        )

        assert mapping.question_id == question.id
        assert mapping.concept_id == test_concepts[0].id
        assert mapping.relevance == 0.9

        # Retrieve mappings
        mappings = await repo.get_concept_mappings_for_question(question.id)
        assert len(mappings) == 1

        # Cleanup
        await db_session.delete(question)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_questions_by_concept(self, db_session, test_course, test_concepts):
        """Test retrieving questions mapped to a concept."""
        repo = QuestionRepository(db_session)

        # Create questions and mappings
        q1 = Question(
            course_id=test_course.id,
            question_text="Q1 for concept",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
        )
        q2 = Question(
            course_id=test_course.id,
            question_text="Q2 for concept",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="B",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
        )
        db_session.add_all([q1, q2])
        await db_session.commit()
        await db_session.refresh(q1)
        await db_session.refresh(q2)

        # Add mappings - both to same concept
        await repo.add_concept_mapping(q1.id, test_concepts[0].id, 0.9)
        await repo.add_concept_mapping(q2.id, test_concepts[0].id, 0.8)

        # Retrieve by concept
        questions = await repo.get_questions_by_concept(
            concept_id=test_concepts[0].id,
            course_id=test_course.id,
        )

        assert len(questions) == 2

        # Cleanup
        await db_session.delete(q1)
        await db_session.delete(q2)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_get_questions_without_concepts(self, db_session, test_course, test_concepts):
        """Test finding questions without concept mappings."""
        repo = QuestionRepository(db_session)

        # Create questions - one with mapping, one without
        q_mapped = Question(
            course_id=test_course.id,
            question_text="Mapped question",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
        )
        q_unmapped = Question(
            course_id=test_course.id,
            question_text="Unmapped question",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="B",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
        )
        db_session.add_all([q_mapped, q_unmapped])
        await db_session.commit()
        await db_session.refresh(q_mapped)
        await db_session.refresh(q_unmapped)

        # Add mapping to one question
        await repo.add_concept_mapping(q_mapped.id, test_concepts[0].id, 0.9)

        # Get unmapped questions
        unmapped = await repo.get_questions_without_concepts(test_course.id)

        # Should include q_unmapped
        unmapped_ids = [q.id for q in unmapped]
        assert q_unmapped.id in unmapped_ids
        assert q_mapped.id not in unmapped_ids

        # Cleanup
        await db_session.delete(q_mapped)
        await db_session.delete(q_unmapped)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_question_count_by_ka(self, db_session, test_course):
        """Test getting question counts by knowledge area."""
        repo = QuestionRepository(db_session)

        # Create questions in different KAs
        questions = []
        for i in range(3):
            q = Question(
                course_id=test_course.id,
                question_text=f"KA count test {i}",
                options={"A": "A", "B": "B", "C": "C", "D": "D"},
                correct_answer="A",
                explanation="Test",
                knowledge_area_id="ka-1" if i < 2 else "ka-2",
                difficulty=0.5,
                source="test",
            )
            questions.append(q)
        db_session.add_all(questions)
        await db_session.commit()

        # Get counts
        counts = await repo.get_question_count_by_ka(test_course.id)

        assert counts.get("ka-1", 0) >= 2
        assert counts.get("ka-2", 0) >= 1

        # Cleanup
        for q in questions:
            await db_session.delete(q)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_deactivate_questions(self, db_session, test_course):
        """Test soft-deleting questions."""
        repo = QuestionRepository(db_session)

        # Create questions
        q = Question(
            course_id=test_course.id,
            question_text="To be deactivated",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
            is_active=True,
        )
        db_session.add(q)
        await db_session.commit()
        await db_session.refresh(q)

        # Deactivate
        count = await repo.deactivate_questions_by_ids([q.id])
        assert count == 1

        # Verify deactivated
        await db_session.refresh(q)
        assert q.is_active is False

        # Should not appear in active queries
        active_questions = await repo.get_all_questions(test_course.id)
        active_ids = [aq.id for aq in active_questions]
        assert q.id not in active_ids

        # Cleanup
        await db_session.delete(q)
        await db_session.commit()


class TestQuestionModel:
    """Integration tests for Question model properties."""

    @pytest.mark.asyncio
    async def test_empirical_difficulty(self, db_session, test_course):
        """Test empirical difficulty calculation."""
        q = Question(
            course_id=test_course.id,
            question_text="Empirical difficulty test",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            times_asked=10,
            times_correct=7,
            source="test",
        )
        db_session.add(q)
        await db_session.commit()
        await db_session.refresh(q)

        # Empirical difficulty = 1 - (correct/asked) = 1 - 0.7 = 0.3
        assert abs(q.empirical_difficulty - 0.3) < 0.001

        # Cleanup
        await db_session.delete(q)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_empirical_difficulty_no_responses(self, db_session, test_course):
        """Test empirical difficulty with no responses falls back to difficulty."""
        q = Question(
            course_id=test_course.id,
            question_text="No responses test",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test",
            knowledge_area_id="ka-1",
            difficulty=0.6,
            times_asked=0,
            times_correct=0,
            source="test",
        )
        db_session.add(q)
        await db_session.commit()
        await db_session.refresh(q)

        # Should return initial difficulty
        assert q.empirical_difficulty == 0.6

        # Cleanup
        await db_session.delete(q)
        await db_session.commit()


class TestDuplicateQuestionHandling:
    """Integration tests for duplicate question detection via unique constraint."""

    @pytest.mark.asyncio
    async def test_duplicate_question_text_rejected(self, db_session, test_course):
        """Test that duplicate question_text is rejected by unique index on md5(question_text)."""
        from sqlalchemy.exc import IntegrityError

        repo = QuestionRepository(db_session)

        question_text = "What is the primary purpose of stakeholder analysis in business analysis?"

        # Create first question
        q1_data = {
            "course_id": test_course.id,
            "question_text": question_text,
            "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            "correct_answer": "A",
            "explanation": "Stakeholder analysis helps identify stakeholder concerns.",
            "knowledge_area_id": "ka-1",
            "difficulty": 0.5,
            "source": "test",
        }

        q1 = await repo.create_question(q1_data)
        assert q1.id is not None

        # Attempt to create duplicate with same question_text
        q2_data = {
            "course_id": test_course.id,
            "question_text": question_text,  # Same text
            "options": {"A": "Different A", "B": "Different B", "C": "Different C", "D": "Different D"},
            "correct_answer": "B",
            "explanation": "Different explanation.",
            "knowledge_area_id": "ka-2",
            "difficulty": 0.7,
            "source": "test",
        }

        # Should raise IntegrityError due to unique constraint on md5(question_text)
        with pytest.raises(IntegrityError):
            await repo.create_question(q2_data)

        # Cleanup - rollback the failed transaction first
        await db_session.rollback()

        # Delete the first question
        await db_session.delete(q1)
        await db_session.commit()

    @pytest.mark.asyncio
    async def test_bulk_create_handles_duplicates(self, db_session, test_course):
        """Test that bulk_create_questions handles duplicates gracefully."""
        repo = QuestionRepository(db_session)

        question_text = "Which technique is BEST for identifying stakeholder concerns?"

        # Create first question directly
        q1 = Question(
            course_id=test_course.id,
            question_text=question_text,
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Test explanation",
            knowledge_area_id="ka-1",
            difficulty=0.5,
            source="test",
        )
        db_session.add(q1)
        await db_session.commit()
        await db_session.refresh(q1)

        # Attempt bulk insert with one duplicate and one new
        questions_data = [
            {
                "course_id": test_course.id,
                "question_text": question_text,  # Duplicate
                "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
                "correct_answer": "B",
                "explanation": "Duplicate explanation",
                "knowledge_area_id": "ka-1",
                "difficulty": 0.5,
                "source": "test",
            },
            {
                "course_id": test_course.id,
                "question_text": "This is a completely unique question text for testing?",
                "options": {"A": "A", "B": "B", "C": "C", "D": "D"},
                "correct_answer": "C",
                "explanation": "Unique explanation",
                "knowledge_area_id": "ka-2",
                "difficulty": 0.6,
                "source": "test",
            },
        ]

        # Should insert 1 (the unique one), skip 1 (the duplicate)
        inserted_count = await repo.bulk_create_questions(questions_data)
        assert inserted_count == 1

        # Verify only 2 questions total (original + 1 new)
        total = await repo.get_question_count(test_course.id)
        assert total == 2

        # Cleanup
        questions, _ = await repo.get_questions_by_course(test_course.id, is_active=None)
        for q in questions:
            await db_session.delete(q)
        await db_session.commit()
