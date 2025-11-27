"""
Integration tests for QuestionRepository.
Tests database operations for question import.
"""
import pytest
from sqlalchemy.exc import SQLAlchemyError

from src.models.question import Question
from src.repositories.question_repository import QuestionRepository


@pytest.mark.asyncio
class TestQuestionRepository:
    """Integration tests for QuestionRepository."""

    async def test_create_question(self, db_session):
        """Test creating a single question."""
        repo = QuestionRepository(db_session)

        question_data = {
            "question_text": "What is the purpose of elicitation?",
            "option_a": "Gather requirements",
            "option_b": "Design solutions",
            "option_c": "Test software",
            "option_d": "Deploy applications",
            "correct_answer": "A",
            "explanation": "Elicitation is the process of gathering requirements from stakeholders",
            "ka": "Elicitation and Collaboration",
            "difficulty": "Easy",
            "concept_tags": ["elicitation", "requirements"],
            "source": "vendor",
        }

        question = await repo.create_question(question_data)

        assert question.id is not None
        assert question.question_text == "What is the purpose of elicitation?"
        assert question.correct_answer == "A"
        assert question.ka == "Elicitation and Collaboration"
        assert question.difficulty == "Easy"
        assert question.concept_tags == ["elicitation", "requirements"]

    async def test_bulk_create_questions(self, db_session):
        """Test bulk creating questions with transaction support."""
        repo = QuestionRepository(db_session)

        questions = [
            {
                "question_text": f"Test question {i}",
                "option_a": "Option A",
                "option_b": "Option B",
                "option_c": "Option C",
                "option_d": "Option D",
                "correct_answer": "A",
                "explanation": f"Explanation {i}",
                "ka": "Business Analysis Planning and Monitoring",
                "difficulty": "Medium",
                "concept_tags": ["test"],
            }
            for i in range(5)
        ]

        count = await repo.bulk_create_questions(questions)

        assert count == 5

        # Verify questions were inserted
        ka_questions = await repo.get_questions_by_ka(
            "Business Analysis Planning and Monitoring"
        )
        assert len(ka_questions) == 5

    async def test_get_question_by_id(self, db_session):
        """Test retrieving a question by ID."""
        repo = QuestionRepository(db_session)

        # Create a question first
        question_data = {
            "question_text": "Test question",
            "option_a": "A",
            "option_b": "B",
            "option_c": "C",
            "option_d": "D",
            "correct_answer": "A",
            "explanation": "Test",
            "ka": "Strategy Analysis",
            "difficulty": "Hard",
        }
        created_question = await repo.create_question(question_data)

        # Retrieve it
        retrieved_question = await repo.get_question_by_id(created_question.id)

        assert retrieved_question is not None
        assert retrieved_question.id == created_question.id
        assert retrieved_question.question_text == "Test question"

    async def test_get_question_by_id_not_found(self, db_session):
        """Test retrieving a non-existent question returns None."""
        import uuid

        repo = QuestionRepository(db_session)

        non_existent_id = uuid.uuid4()
        result = await repo.get_question_by_id(non_existent_id)

        assert result is None

    async def test_get_questions_by_ka(self, db_session):
        """Test retrieving questions filtered by knowledge area."""
        repo = QuestionRepository(db_session)

        # Create questions in different KAs
        ka1_questions = [
            {
                "question_text": f"Strategy question {i}",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Explanation",
                "ka": "Strategy Analysis",
                "difficulty": "Medium",
            }
            for i in range(3)
        ]

        ka2_questions = [
            {
                "question_text": "Evaluation question",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "B",
                "explanation": "Explanation",
                "ka": "Solution Evaluation",
                "difficulty": "Easy",
            }
        ]

        await repo.bulk_create_questions(ka1_questions)
        await repo.bulk_create_questions(ka2_questions)

        # Retrieve by KA
        strategy_questions = await repo.get_questions_by_ka("Strategy Analysis")
        evaluation_questions = await repo.get_questions_by_ka("Solution Evaluation")

        assert len(strategy_questions) == 3
        assert len(evaluation_questions) == 1
        assert all(q.ka == "Strategy Analysis" for q in strategy_questions)

    async def test_get_question_count_by_ka(self, db_session):
        """Test counting questions by knowledge area."""
        repo = QuestionRepository(db_session)

        questions = [
            {
                "question_text": f"Question {i}",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Explanation",
                "ka": ka,
                "difficulty": "Medium",
            }
            for i, ka in enumerate(
                [
                    "Business Analysis Planning and Monitoring",
                    "Business Analysis Planning and Monitoring",
                    "Elicitation and Collaboration",
                    "Strategy Analysis",
                ]
            )
        ]

        await repo.bulk_create_questions(questions)

        counts = await repo.get_question_count_by_ka()

        assert counts["Business Analysis Planning and Monitoring"] == 2
        assert counts["Elicitation and Collaboration"] == 1
        assert counts["Strategy Analysis"] == 1

    async def test_get_question_count_by_difficulty(self, db_session):
        """Test counting questions by difficulty."""
        repo = QuestionRepository(db_session)

        questions = [
            {
                "question_text": f"Question {i}",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Explanation",
                "ka": "Requirements Life Cycle Management",
                "difficulty": diff,
            }
            for i, diff in enumerate(["Easy", "Easy", "Medium", "Hard", "Hard", "Hard"])
        ]

        await repo.bulk_create_questions(questions)

        counts = await repo.get_question_count_by_difficulty()

        assert counts["Easy"] == 2
        assert counts["Medium"] == 1
        assert counts["Hard"] == 3

    async def test_bulk_create_rollback_on_error(self, db_session):
        """Test that transaction rolls back on error during bulk insert."""
        repo = QuestionRepository(db_session)

        # Create one invalid question (missing required field)
        invalid_questions = [
            {
                "question_text": "Valid question",
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Explanation",
                "ka": "Strategy Analysis",
                "difficulty": "Medium",
            },
            {
                # Missing question_text - should cause error
                "option_a": "A",
                "option_b": "B",
                "option_c": "C",
                "option_d": "D",
                "correct_answer": "A",
                "explanation": "Explanation",
                "ka": "Strategy Analysis",
                "difficulty": "Medium",
            },
        ]

        # Should raise error and rollback
        with pytest.raises(Exception):
            await repo.bulk_create_questions(invalid_questions)

        # Verify no questions were inserted (transaction rolled back)
        all_questions = await repo.get_questions_by_ka("Strategy Analysis")
        assert len(all_questions) == 0
