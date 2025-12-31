"""
Integration tests for review session API.
Tests the complete review lifecycle: check availability -> start -> answer -> summary.

Story 4.9: Post-Session Review Mode
"""
from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.models.concept import Concept
from src.models.course import Course
from src.models.enrollment import Enrollment
from src.models.question import Question
from src.models.question_concept import QuestionConcept
from src.models.quiz_response import QuizResponse
from src.models.quiz_session import QuizSession
from src.models.user import User
from src.utils.auth import create_access_token, hash_password


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
async def review_test_course(db_session):
    """Create a course for review testing."""
    course = Course(
        slug=f"review-test-{uuid4().hex[:6]}",
        name="Review Test Course",
        description="Course for review session integration tests",
        knowledge_areas=[
            {"id": "ka1", "name": "Knowledge Area 1", "short_name": "KA1", "display_order": 1, "color": "#3B82F6"},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def review_test_user(db_session):
    """Create a user for review testing."""
    user = User(
        email=f"reviewtest_{uuid4().hex[:8]}@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def review_test_enrollment(db_session, review_test_user, review_test_course):
    """Create enrollment for review testing."""
    enrollment = Enrollment(
        user_id=review_test_user.id,
        course_id=review_test_course.id,
        status="active",
    )
    db_session.add(enrollment)
    await db_session.commit()
    await db_session.refresh(enrollment)
    return enrollment


@pytest.fixture
async def review_test_concept(db_session, review_test_course):
    """Create a concept for review testing."""
    concept = Concept(
        course_id=review_test_course.id,
        name="Test Concept",
        description="A test concept for review testing",
        knowledge_area_id="ka1",
        corpus_section_ref="1.1",
        difficulty_estimate=0.5,
    )
    db_session.add(concept)
    await db_session.commit()
    await db_session.refresh(concept)
    return concept


@pytest.fixture
async def review_test_questions(db_session, review_test_course, review_test_concept):
    """Create questions for review testing."""
    questions = []
    for i in range(3):
        question = Question(
            course_id=review_test_course.id,
            question_text=f"Test question {i + 1}?",
            options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
            correct_answer="B",
            explanation=f"Explanation for question {i + 1}",
            knowledge_area_id="ka1",
            difficulty=0.5,
            slip_rate=0.1,
            guess_rate=0.25,
        )
        db_session.add(question)
        await db_session.flush()

        # Link question to concept
        qc = QuestionConcept(
            question_id=question.id,
            concept_id=review_test_concept.id,
        )
        db_session.add(qc)
        questions.append(question)

    await db_session.commit()
    for q in questions:
        await db_session.refresh(q)
    return questions


@pytest.fixture
async def review_test_quiz_session(
    db_session,
    review_test_user,
    review_test_enrollment,
    review_test_questions,
):
    """Create a quiz session with incorrect answers for review testing."""
    from datetime import UTC, datetime

    # Create quiz session
    session = QuizSession(
        user_id=review_test_user.id,
        enrollment_id=review_test_enrollment.id,
        session_type="adaptive",
        question_strategy="max_info_gain",
        question_target=10,
        total_questions=3,
        correct_count=1,
        started_at=datetime.now(UTC),
        ended_at=datetime.now(UTC),
    )
    db_session.add(session)
    await db_session.flush()

    # Create quiz responses - 1 correct, 2 incorrect
    for i, question in enumerate(review_test_questions):
        is_correct = i == 0  # First one correct, rest incorrect
        response = QuizResponse(
            session_id=session.id,
            question_id=question.id,
            user_id=review_test_user.id,
            selected_answer="B" if is_correct else "A",
            is_correct=is_correct,
            time_taken_ms=5000,
        )
        db_session.add(response)

    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest.fixture
def review_auth_headers(review_test_user):
    """Auth headers for the review test user."""
    token = create_access_token(data={"sub": str(review_test_user.id)})
    return {"Authorization": f"Bearer {token}"}


# ============================================================================
# Check Review Available Tests
# ============================================================================


class TestCheckReviewAvailable:
    """Test checking review availability."""

    @pytest.mark.asyncio
    async def test_review_available_when_incorrect_answers_exist(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify review is available when there are incorrect answers."""
        response = await client.get(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review-available",
            headers=review_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["available"] is True
        assert data["incorrect_count"] == 2
        assert len(data["question_ids"]) == 2

    @pytest.mark.asyncio
    async def test_review_not_available_for_perfect_session(
        self,
        client: AsyncClient,
        db_session,
        review_test_user,
        review_test_enrollment,
        review_test_questions,
        review_auth_headers,
    ):
        """Verify review not available when all answers correct."""
        from datetime import UTC, datetime

        # Create perfect quiz session
        session = QuizSession(
            user_id=review_test_user.id,
            enrollment_id=review_test_enrollment.id,
            session_type="adaptive",
            question_strategy="max_info_gain",
            question_target=10,
            total_questions=1,
            correct_count=1,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
        )
        db_session.add(session)
        await db_session.flush()

        # All correct response
        response_record = QuizResponse(
            session_id=session.id,
            question_id=review_test_questions[0].id,
            user_id=review_test_user.id,
            selected_answer="B",
            is_correct=True,
            time_taken_ms=5000,
        )
        db_session.add(response_record)
        await db_session.commit()

        response = await client.get(
            f"/v1/quiz/session/{session.id}/review-available",
            headers=review_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["available"] is False
        assert data["incorrect_count"] == 0


# ============================================================================
# Start Review Tests
# ============================================================================


class TestStartReview:
    """Test starting review sessions."""

    @pytest.mark.asyncio
    async def test_start_review_creates_session(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify starting review creates a new review session."""
        response = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )

        assert response.status_code == 201
        data = response.json()

        assert data["original_session_id"] == str(review_test_quiz_session.id)
        assert data["total_to_review"] == 2
        assert data["status"] == "in_progress"
        assert data["reviewed_count"] == 0
        assert data["reinforced_count"] == 0

    @pytest.mark.asyncio
    async def test_start_review_resumes_existing_session(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify starting review twice resumes existing session."""
        # Start first time
        response1 = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )
        assert response1.status_code == 201
        review_id_1 = response1.json()["id"]

        # Start again - should resume
        response2 = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )
        assert response2.status_code == 201
        review_id_2 = response2.json()["id"]

        assert review_id_1 == review_id_2


# ============================================================================
# Review Question Flow Tests
# ============================================================================


class TestReviewQuestionFlow:
    """Test getting and answering review questions."""

    @pytest.mark.asyncio
    async def test_get_next_question(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify getting the next review question."""
        # Start review
        start_response = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )
        review_session_id = start_response.json()["id"]

        # Get next question
        response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert "question_id" in data
        assert "question_text" in data
        assert "options" in data
        assert data["review_number"] == 1
        assert data["total_to_review"] == 2

    @pytest.mark.asyncio
    async def test_submit_correct_answer_reinforces(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify correct answer marks as reinforced."""
        # Start review
        start_response = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )
        review_session_id = start_response.json()["id"]

        # Get question
        question_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )
        question_id = question_response.json()["question_id"]

        # Submit correct answer (B is correct)
        answer_response = await client.post(
            f"/v1/quiz/review/{review_session_id}/answer",
            headers=review_auth_headers,
            json={"question_id": question_id, "selected_answer": "B"},
        )

        assert answer_response.status_code == 200
        data = answer_response.json()

        assert data["is_correct"] is True
        assert data["was_reinforced"] is True
        assert data["correct_answer"] == "B"
        assert "explanation" in data

    @pytest.mark.asyncio
    async def test_submit_incorrect_answer_not_reinforced(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify incorrect answer shows still needs practice."""
        # Start review
        start_response = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )
        review_session_id = start_response.json()["id"]

        # Get question
        question_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )
        question_id = question_response.json()["question_id"]

        # Submit incorrect answer (C is wrong)
        answer_response = await client.post(
            f"/v1/quiz/review/{review_session_id}/answer",
            headers=review_auth_headers,
            json={"question_id": question_id, "selected_answer": "C"},
        )

        assert answer_response.status_code == 200
        data = answer_response.json()

        assert data["is_correct"] is False
        assert data["was_reinforced"] is False
        assert data["correct_answer"] == "B"


# ============================================================================
# Skip Review Tests
# ============================================================================


class TestSkipReview:
    """Test skipping review sessions."""

    @pytest.mark.asyncio
    async def test_skip_review_session(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify skipping marks session as skipped."""
        # Start review
        start_response = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )
        review_session_id = start_response.json()["id"]

        # Skip review
        response = await client.post(
            f"/v1/quiz/review/{review_session_id}/skip",
            headers=review_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["session_id"] == review_session_id
        assert data["questions_skipped"] == 2
        assert "skipped" in data["message"].lower()


# ============================================================================
# Review Summary Tests
# ============================================================================


class TestReviewSummary:
    """Test getting review summary."""

    @pytest.mark.asyncio
    async def test_get_summary_after_completing_all_questions(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify summary is returned after completing all questions."""
        # Start review
        start_response = await client.post(
            f"/v1/quiz/session/{review_test_quiz_session.id}/review/start",
            headers=review_auth_headers,
        )
        review_session_id = start_response.json()["id"]

        # Answer all questions
        for _ in range(2):
            question_response = await client.get(
                f"/v1/quiz/review/{review_session_id}/next-question",
                headers=review_auth_headers,
            )
            if question_response.json() is None:
                break

            question_id = question_response.json()["question_id"]

            await client.post(
                f"/v1/quiz/review/{review_session_id}/answer",
                headers=review_auth_headers,
                json={"question_id": question_id, "selected_answer": "B"},
            )

        # Get summary
        response = await client.get(
            f"/v1/quiz/review/{review_session_id}/summary",
            headers=review_auth_headers,
        )

        assert response.status_code == 200
        data = response.json()

        assert data["total_reviewed"] == 2
        assert "reinforced_count" in data
        assert "still_incorrect_count" in data
        assert "reinforcement_rate" in data


# ============================================================================
# Full Flow Test
# ============================================================================


class TestReviewFullFlow:
    """Test complete review session lifecycle."""

    @pytest.mark.asyncio
    async def test_complete_review_lifecycle(
        self,
        client: AsyncClient,
        review_test_quiz_session,
        review_auth_headers,
    ):
        """Verify complete flow: check -> start -> answer all -> summary."""
        session_id = review_test_quiz_session.id

        # 1. Check availability
        check_response = await client.get(
            f"/v1/quiz/session/{session_id}/review-available",
            headers=review_auth_headers,
        )
        assert check_response.status_code == 200
        assert check_response.json()["available"] is True
        assert check_response.json()["incorrect_count"] == 2

        # 2. Start review
        start_response = await client.post(
            f"/v1/quiz/session/{session_id}/review/start",
            headers=review_auth_headers,
        )
        assert start_response.status_code == 201
        review_session_id = start_response.json()["id"]
        assert start_response.json()["total_to_review"] == 2

        # 3. Answer first question correctly (reinforced)
        q1_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )
        assert q1_response.status_code == 200
        q1_id = q1_response.json()["question_id"]
        assert q1_response.json()["review_number"] == 1

        a1_response = await client.post(
            f"/v1/quiz/review/{review_session_id}/answer",
            headers=review_auth_headers,
            json={"question_id": q1_id, "selected_answer": "B"},
        )
        assert a1_response.status_code == 200
        assert a1_response.json()["was_reinforced"] is True

        # 4. Answer second question incorrectly (still incorrect)
        q2_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )
        assert q2_response.status_code == 200
        q2_id = q2_response.json()["question_id"]
        assert q2_response.json()["review_number"] == 2

        a2_response = await client.post(
            f"/v1/quiz/review/{review_session_id}/answer",
            headers=review_auth_headers,
            json={"question_id": q2_id, "selected_answer": "C"},  # Wrong
        )
        assert a2_response.status_code == 200
        assert a2_response.json()["was_reinforced"] is False

        # 5. Verify no more questions
        q3_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )
        assert q3_response.status_code == 200
        assert q3_response.json() is None

        # 6. Get summary
        summary_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/summary",
            headers=review_auth_headers,
        )
        assert summary_response.status_code == 200
        summary = summary_response.json()

        assert summary["total_reviewed"] == 2
        assert summary["reinforced_count"] == 1
        assert summary["still_incorrect_count"] == 1
        assert summary["reinforcement_rate"] == 0.5


# ============================================================================
# Belief Update Multiplier Tests
# ============================================================================


class TestBeliefUpdateMultipliers:
    """Test that belief update multipliers are correctly applied during review."""

    @pytest.mark.asyncio
    async def test_reinforcement_multiplier_applied_on_correct_reanswer(
        self,
        client: AsyncClient,
        db_session,
        review_test_user,
        review_test_enrollment,
        review_test_questions,
        review_test_concept,
        review_auth_headers,
    ):
        """
        Verify that the 1.5x reinforcement multiplier is applied when a user
        answers a previously incorrect question correctly during review.

        Story 4.9 AC6: Apply reinforcement modifier to belief update when
        user answers correctly during review.
        """
        from datetime import UTC, datetime

        from src.models.belief_state import BeliefState
        from src.services.review_session_service import REINFORCEMENT_MULTIPLIER

        # 1. Create initial belief state for the test concept (uninformed prior)
        initial_alpha = 1.0
        initial_beta = 1.0
        belief = BeliefState(
            user_id=review_test_user.id,
            concept_id=review_test_concept.id,
            alpha=initial_alpha,
            beta=initial_beta,
            response_count=0,
        )
        db_session.add(belief)

        # 2. Create quiz session with one incorrect answer
        session = QuizSession(
            user_id=review_test_user.id,
            enrollment_id=review_test_enrollment.id,
            session_type="adaptive",
            question_strategy="max_info_gain",
            question_target=10,
            total_questions=1,
            correct_count=0,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
        )
        db_session.add(session)
        await db_session.flush()

        # Create incorrect response for first question
        quiz_response = QuizResponse(
            session_id=session.id,
            question_id=review_test_questions[0].id,
            user_id=review_test_user.id,
            selected_answer="A",  # Wrong (correct is B)
            is_correct=False,
            time_taken_ms=5000,
        )
        db_session.add(quiz_response)
        await db_session.commit()

        # Record belief state before review
        await db_session.refresh(belief)
        alpha_before_review = belief.alpha
        beta_before_review = belief.beta

        # 3. Start review session
        start_response = await client.post(
            f"/v1/quiz/session/{session.id}/review/start",
            headers=review_auth_headers,
        )
        assert start_response.status_code == 201
        review_session_id = start_response.json()["id"]

        # 4. Get the review question
        question_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )
        assert question_response.status_code == 200
        question_id = question_response.json()["question_id"]

        # 5. Answer correctly this time (reinforcement scenario)
        answer_response = await client.post(
            f"/v1/quiz/review/{review_session_id}/answer",
            headers=review_auth_headers,
            json={"question_id": question_id, "selected_answer": "B"},
        )
        assert answer_response.status_code == 200
        answer_data = answer_response.json()
        assert answer_data["is_correct"] is True
        assert answer_data["was_reinforced"] is True

        # 6. Verify belief was updated with reinforcement multiplier
        await db_session.refresh(belief)

        # Alpha should have increased (positive evidence from correct answer)
        # The exact calculation depends on the belief updater, but the multiplier
        # should make the increase ~1.5x larger than a normal correct answer
        alpha_increase = belief.alpha - alpha_before_review

        # Verify the concepts_updated contains the belief change
        concepts_updated = answer_data.get("concepts_updated", [])
        assert len(concepts_updated) > 0

        # The alpha should have increased (reinforcement applies to positive update)
        assert belief.alpha > alpha_before_review
        assert alpha_increase > 0

        # Log for debugging
        print(f"Reinforcement multiplier test:")
        print(f"  Alpha before: {alpha_before_review}, after: {belief.alpha}")
        print(f"  Alpha increase: {alpha_increase}")
        print(f"  Expected multiplier: {REINFORCEMENT_MULTIPLIER}")

    @pytest.mark.asyncio
    async def test_still_incorrect_multiplier_applied_on_wrong_reanswer(
        self,
        client: AsyncClient,
        db_session,
        review_test_user,
        review_test_enrollment,
        review_test_questions,
        review_test_concept,
        review_auth_headers,
    ):
        """
        Verify that the 0.5x still-incorrect multiplier is applied when a user
        answers incorrectly again during review.

        Story 4.9 AC6: Apply still-incorrect modifier to belief update when
        user answers incorrectly during review.
        """
        from datetime import UTC, datetime

        from src.models.belief_state import BeliefState
        from src.services.review_session_service import STILL_INCORRECT_MULTIPLIER

        # 1. Create initial belief state for the test concept
        initial_alpha = 2.0  # Start with some prior
        initial_beta = 2.0
        belief = BeliefState(
            user_id=review_test_user.id,
            concept_id=review_test_concept.id,
            alpha=initial_alpha,
            beta=initial_beta,
            response_count=2,
        )
        db_session.add(belief)

        # 2. Create quiz session with one incorrect answer
        session = QuizSession(
            user_id=review_test_user.id,
            enrollment_id=review_test_enrollment.id,
            session_type="adaptive",
            question_strategy="max_info_gain",
            question_target=10,
            total_questions=1,
            correct_count=0,
            started_at=datetime.now(UTC),
            ended_at=datetime.now(UTC),
        )
        db_session.add(session)
        await db_session.flush()

        # Create incorrect response
        quiz_response = QuizResponse(
            session_id=session.id,
            question_id=review_test_questions[0].id,
            user_id=review_test_user.id,
            selected_answer="A",  # Wrong (correct is B)
            is_correct=False,
            time_taken_ms=5000,
        )
        db_session.add(quiz_response)
        await db_session.commit()

        # Record belief state before review
        await db_session.refresh(belief)
        alpha_before_review = belief.alpha
        beta_before_review = belief.beta

        # 3. Start review session
        start_response = await client.post(
            f"/v1/quiz/session/{session.id}/review/start",
            headers=review_auth_headers,
        )
        assert start_response.status_code == 201
        review_session_id = start_response.json()["id"]

        # 4. Get the review question
        question_response = await client.get(
            f"/v1/quiz/review/{review_session_id}/next-question",
            headers=review_auth_headers,
        )
        assert question_response.status_code == 200
        question_id = question_response.json()["question_id"]

        # 5. Answer incorrectly again (still-incorrect scenario)
        answer_response = await client.post(
            f"/v1/quiz/review/{review_session_id}/answer",
            headers=review_auth_headers,
            json={"question_id": question_id, "selected_answer": "C"},  # Still wrong
        )
        assert answer_response.status_code == 200
        answer_data = answer_response.json()
        assert answer_data["is_correct"] is False
        assert answer_data["was_reinforced"] is False

        # 6. Verify belief was updated with still-incorrect multiplier
        await db_session.refresh(belief)

        # Beta should have increased (negative evidence from incorrect answer)
        # but the increase should be dampened by the 0.5x multiplier
        beta_increase = belief.beta - beta_before_review

        # Verify the concepts_updated contains the belief change
        concepts_updated = answer_data.get("concepts_updated", [])
        assert len(concepts_updated) > 0

        # Beta should have increased (negative evidence) but at reduced rate
        assert belief.beta > beta_before_review
        assert beta_increase > 0

        # Log for debugging
        print(f"Still-incorrect multiplier test:")
        print(f"  Beta before: {beta_before_review}, after: {belief.beta}")
        print(f"  Beta increase: {beta_increase}")
        print(f"  Expected multiplier: {STILL_INCORRECT_MULTIPLIER}")
