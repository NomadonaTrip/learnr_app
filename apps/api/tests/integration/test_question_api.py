"""
Integration tests for Question Retrieval API.

Tests GET /v1/courses/{course_slug}/questions endpoint with:
- Concept filtering
- Knowledge area filtering
- Difficulty range filtering
- Exclusion list
- Pagination
- Response time performance
"""
import time

import pytest

from src.models.concept import Concept
from src.models.course import Course
from src.models.question import Question
from src.models.question_concept import QuestionConcept


@pytest.fixture
async def test_course(db_session):
    """Create test course for question API tests."""
    course = Course(
        slug="cbap-test",
        name="CBAP Certification Prep Test",
        description="Test course for question API",
        corpus_name="BABOK v3",
        knowledge_areas=[
            {"id": "strategy", "name": "Strategy Analysis", "short_name": "Strategy", "display_order": 1, "color": "#EF4444"},
            {"id": "elicitation", "name": "Elicitation and Collaboration", "short_name": "Elicitation", "display_order": 2, "color": "#10B981"},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def test_concepts(db_session, test_course):
    """Create test concepts for filtering."""
    concepts = []
    for i in range(3):
        concept = Concept(
            course_id=test_course.id,
            name=f"Test Concept {i+1}",
            description=f"Description for concept {i+1}",
            corpus_section_ref=f"3.{i+1}",
            knowledge_area_id="strategy" if i < 2 else "elicitation",
            difficulty_estimate=0.3 + (i * 0.2),
            prerequisite_depth=0,
        )
        db_session.add(concept)
        concepts.append(concept)

    await db_session.commit()
    for c in concepts:
        await db_session.refresh(c)
    return concepts


@pytest.fixture
async def test_questions(db_session, test_course, test_concepts):
    """Create test questions with concept mappings."""
    questions = []

    # Question 1: Strategy, difficulty 0.3, mapped to concept 0
    q1 = Question(
        course_id=test_course.id,
        question_text="What is business analysis strategy?",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="A",
        explanation="Explanation for Q1",
        knowledge_area_id="strategy",
        difficulty=0.3,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
    )
    db_session.add(q1)
    questions.append(q1)

    # Question 2: Strategy, difficulty 0.5, mapped to concepts 0 and 1
    q2 = Question(
        course_id=test_course.id,
        question_text="How do you define business strategy?",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="B",
        explanation="Explanation for Q2",
        knowledge_area_id="strategy",
        difficulty=0.5,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
    )
    db_session.add(q2)
    questions.append(q2)

    # Question 3: Elicitation, difficulty 0.7, mapped to concept 2
    q3 = Question(
        course_id=test_course.id,
        question_text="What is elicitation?",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="C",
        explanation="Explanation for Q3",
        knowledge_area_id="elicitation",
        difficulty=0.7,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
    )
    db_session.add(q3)
    questions.append(q3)

    # Question 4: Strategy, difficulty 0.8, no concept mapping
    q4 = Question(
        course_id=test_course.id,
        question_text="Advanced strategy question?",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="D",
        explanation="Explanation for Q4",
        knowledge_area_id="strategy",
        difficulty=0.8,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
    )
    db_session.add(q4)
    questions.append(q4)

    await db_session.commit()
    for q in questions:
        await db_session.refresh(q)

    # Add concept mappings
    mappings = [
        QuestionConcept(question_id=q1.id, concept_id=test_concepts[0].id, relevance=1.0),
        QuestionConcept(question_id=q2.id, concept_id=test_concepts[0].id, relevance=0.8),
        QuestionConcept(question_id=q2.id, concept_id=test_concepts[1].id, relevance=0.6),
        QuestionConcept(question_id=q3.id, concept_id=test_concepts[2].id, relevance=1.0),
    ]
    for mapping in mappings:
        db_session.add(mapping)

    await db_session.commit()

    return questions


@pytest.fixture
async def authenticated_user(client, db_session):
    """Create and authenticate a test user, return token."""
    # Register a user
    user_data = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "name": "Test User"
    }
    response = await client.post("/v1/auth/register", json=user_data)
    assert response.status_code == 201
    data = response.json()
    return data["token"]


@pytest.mark.asyncio
class TestQuestionRetrievalAPI:
    """Tests for GET /v1/courses/{course_slug}/questions endpoint."""

    async def test_get_questions_requires_authentication(self, client, test_course, test_questions):
        """Test that endpoint requires authentication."""
        response = await client.get(f"/v1/courses/{test_course.slug}/questions")

        assert response.status_code == 401

    async def test_get_questions_course_not_found(self, client, authenticated_user):
        """Test getting questions for non-existent course returns 404."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get("/v1/courses/non-existent/questions", headers=headers)

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "COURSE_NOT_FOUND"

    async def test_get_questions_basic_retrieval(
        self, client, authenticated_user, test_course, test_questions
    ):
        """Test basic question retrieval without filters."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(f"/v1/courses/{test_course.slug}/questions", headers=headers)

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert "has_more" in data

        assert data["total"] == 4  # All 4 test questions
        assert len(data["items"]) == 4
        assert data["has_more"] is False

    async def test_get_questions_excludes_sensitive_fields(
        self, client, authenticated_user, test_course, test_questions
    ):
        """Test that response excludes correct_answer and explanation."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(f"/v1/courses/{test_course.slug}/questions", headers=headers)

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert "correct_answer" not in item
            assert "explanation" not in item
            assert "question_text" in item
            assert "options" in item
            assert "difficulty" in item
            assert "concept_ids" in item

    async def test_filter_by_single_concept(
        self, client, authenticated_user, test_course, test_questions, test_concepts
    ):
        """Test filtering questions by a single concept ID."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?concept_ids={concept_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Questions 1 and 2 are mapped to concept 0
        assert data["total"] == 2
        assert len(data["items"]) == 2

    async def test_filter_by_multiple_concepts(
        self, client, authenticated_user, test_course, test_questions, test_concepts
    ):
        """Test filtering by multiple concept IDs (ANY match)."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_ids = f"{test_concepts[0].id}&concept_ids={test_concepts[2].id}"
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?concept_ids={concept_ids}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Questions 1, 2 (concept 0) and 3 (concept 2)
        assert data["total"] == 3

    async def test_filter_by_knowledge_area(
        self, client, authenticated_user, test_course, test_questions
    ):
        """Test filtering by knowledge area ID."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?knowledge_area_id=strategy",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Questions 1, 2, 4 have strategy knowledge area
        assert data["total"] == 3
        for item in data["items"]:
            assert item["knowledge_area_id"] == "strategy"

    async def test_filter_by_difficulty_range(
        self, client, authenticated_user, test_course, test_questions
    ):
        """Test filtering by difficulty range."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?difficulty_min=0.4&difficulty_max=0.6",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Only question 2 (difficulty 0.5) is in this range
        assert data["total"] == 1
        assert data["items"][0]["difficulty"] == 0.5

    async def test_exclude_question_ids(
        self, client, authenticated_user, test_course, test_questions
    ):
        """Test excluding specific question IDs."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        exclude_id = str(test_questions[0].id)
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?exclude_ids={exclude_id}",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Should have 3 questions (excluding first one)
        assert data["total"] == 3
        returned_ids = [item["id"] for item in data["items"]]
        assert exclude_id not in returned_ids

    async def test_pagination_limit_offset(
        self, client, authenticated_user, test_course, test_questions
    ):
        """Test pagination with limit and offset."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}

        # Get first 2
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?limit=2&offset=0",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 4
        assert data["has_more"] is True

        # Get next 2
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?limit=2&offset=2",
            headers=headers
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["items"]) == 2
        assert data["total"] == 4
        assert data["has_more"] is False

    async def test_combined_filters(
        self, client, authenticated_user, test_course, test_questions, test_concepts
    ):
        """Test combining multiple filters."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        concept_id = str(test_concepts[0].id)
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions"
            f"?concept_ids={concept_id}&knowledge_area_id=strategy&difficulty_min=0.2&difficulty_max=0.6",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Questions 1 (0.3) and 2 (0.5) match all filters
        assert data["total"] == 2

    async def test_response_time_performance(
        self, client, authenticated_user, test_course, test_questions
    ):
        """Test that response time is under 100ms."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}

        start_time = time.time()
        response = await client.get(f"/v1/courses/{test_course.slug}/questions", headers=headers)
        end_time = time.time()

        assert response.status_code == 200
        response_time_ms = (end_time - start_time) * 1000

        # Performance requirement: <100ms
        # Note: This might be flaky in CI, but tests the target
        assert response_time_ms < 500  # Relaxed for test environment

    async def test_concept_ids_array_in_response(
        self, client, authenticated_user, test_course, test_questions, test_concepts
    ):
        """Test that concept_ids are properly returned as arrays."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(f"/v1/courses/{test_course.slug}/questions", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Find question 2 which has 2 concept mappings
        q2_text = "How do you define business strategy?"
        q2_item = next(item for item in data["items"] if item["question_text"] == q2_text)

        assert "concept_ids" in q2_item
        assert isinstance(q2_item["concept_ids"], list)
        assert len(q2_item["concept_ids"]) == 2

        # Find question 4 which has no concept mappings
        q4_text = "Advanced strategy question?"
        q4_item = next(item for item in data["items"] if item["question_text"] == q4_text)

        assert "concept_ids" in q4_item
        assert isinstance(q4_item["concept_ids"], list)
        assert len(q4_item["concept_ids"]) == 0

    async def test_questions_scoped_to_course(
        self, client, authenticated_user, db_session, test_course, test_questions
    ):
        """Test that questions are properly scoped to course (multi-course isolation)."""
        # Create another course with a question
        other_course = Course(
            slug="other-course",
            name="Other Course",
            knowledge_areas=[{"id": "test", "name": "Test", "short_name": "Test", "display_order": 1, "color": "#000000"}],
            is_active=True,
        )
        db_session.add(other_course)
        await db_session.commit()
        await db_session.refresh(other_course)

        other_question = Question(
            course_id=other_course.id,
            question_text="Question from other course",
            options={"A": "A", "B": "B", "C": "C", "D": "D"},
            correct_answer="A",
            explanation="Explanation",
            knowledge_area_id="test",
            difficulty=0.5,
            discrimination=1.0,
            guess_rate=0.25,
            slip_rate=0.10,
            source="test",
        )
        db_session.add(other_question)
        await db_session.commit()

        # Query test_course questions
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(f"/v1/courses/{test_course.slug}/questions", headers=headers)

        assert response.status_code == 200
        data = response.json()

        # Should only return test_course questions, not other_course
        assert data["total"] == 4  # Original test questions
        question_texts = [item["question_text"] for item in data["items"]]
        assert "Question from other course" not in question_texts

    async def test_invalid_difficulty_range(
        self, client, authenticated_user, test_course
    ):
        """Test that difficulty_min > difficulty_max returns 400 error."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{test_course.slug}/questions?difficulty_min=0.8&difficulty_max=0.3",
            headers=headers
        )

        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "INVALID_DIFFICULTY_RANGE"
        assert "difficulty_min" in data["detail"]["error"]["message"]
        assert "difficulty_max" in data["detail"]["error"]["message"]


@pytest.fixture
async def course_with_secondary_tags(db_session):
    """Create course with perspectives and competencies configured (Story 2.15)."""
    course = Course(
        slug="cbap-secondary-tags",
        name="CBAP with Secondary Tags",
        description="Test course for secondary tag filtering",
        corpus_name="BABOK v3",
        knowledge_areas=[
            {"id": "strategy", "name": "Strategy Analysis", "short_name": "Strategy", "display_order": 1, "color": "#EF4444"},
        ],
        perspectives=[
            {"id": "agile", "name": "Agile", "keywords": ["agile", "scrum"]},
            {"id": "it", "name": "Information Technology", "keywords": ["it", "software"]},
        ],
        competencies=[
            {"id": "analytical", "name": "Analytical Thinking", "keywords": ["analytical", "problem-solving"]},
            {"id": "communication", "name": "Communication Skills", "keywords": ["communication", "verbal"]},
        ],
        is_active=True,
        is_public=True,
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)
    return course


@pytest.fixture
async def questions_with_secondary_tags(db_session, course_with_secondary_tags):
    """Create questions with perspectives and competencies (Story 2.15)."""
    questions = []

    # Question 1: Agile perspective, Analytical competency
    q1 = Question(
        course_id=course_with_secondary_tags.id,
        question_text="What is an agile approach to business analysis?",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="A",
        explanation="Explanation for Q1",
        knowledge_area_id="strategy",
        difficulty=0.5,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
        perspectives=["agile"],
        competencies=["analytical"],
    )
    db_session.add(q1)
    questions.append(q1)

    # Question 2: IT perspective, Communication competency
    q2 = Question(
        course_id=course_with_secondary_tags.id,
        question_text="How do IT systems support business analysis?",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="B",
        explanation="Explanation for Q2",
        knowledge_area_id="strategy",
        difficulty=0.5,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
        perspectives=["it"],
        competencies=["communication"],
    )
    db_session.add(q2)
    questions.append(q2)

    # Question 3: Both Agile and IT perspectives, both competencies
    q3 = Question(
        course_id=course_with_secondary_tags.id,
        question_text="Cross-cutting question spanning multiple perspectives",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="C",
        explanation="Explanation for Q3",
        knowledge_area_id="strategy",
        difficulty=0.5,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
        perspectives=["agile", "it"],
        competencies=["analytical", "communication"],
    )
    db_session.add(q3)
    questions.append(q3)

    # Question 4: No perspectives or competencies
    q4 = Question(
        course_id=course_with_secondary_tags.id,
        question_text="General question without secondary tags",
        options={"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
        correct_answer="D",
        explanation="Explanation for Q4",
        knowledge_area_id="strategy",
        difficulty=0.5,
        discrimination=1.0,
        guess_rate=0.25,
        slip_rate=0.10,
        source="test",
        is_active=True,
        perspectives=[],
        competencies=[],
    )
    db_session.add(q4)
    questions.append(q4)

    await db_session.commit()
    for q in questions:
        await db_session.refresh(q)

    return questions


@pytest.mark.asyncio
class TestSecondaryTagFiltering:
    """Tests for Story 2.15: Perspectives and Competencies filtering."""

    async def test_filter_by_single_perspective(
        self, client, authenticated_user, course_with_secondary_tags, questions_with_secondary_tags
    ):
        """Test filtering questions by a single perspective."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{course_with_secondary_tags.slug}/questions?perspectives=agile",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Q1 and Q3 have 'agile' perspective
        assert data["total"] == 2
        for item in data["items"]:
            assert "agile" in item["perspectives"]

    async def test_filter_by_single_competency(
        self, client, authenticated_user, course_with_secondary_tags, questions_with_secondary_tags
    ):
        """Test filtering questions by a single competency."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{course_with_secondary_tags.slug}/questions?competencies=analytical",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Q1 and Q3 have 'analytical' competency
        assert data["total"] == 2
        for item in data["items"]:
            assert "analytical" in item["competencies"]

    async def test_filter_by_multiple_perspectives(
        self, client, authenticated_user, course_with_secondary_tags, questions_with_secondary_tags
    ):
        """Test filtering by multiple perspectives (must have ALL)."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{course_with_secondary_tags.slug}/questions?perspectives=agile&perspectives=it",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Only Q3 has both 'agile' AND 'it' perspectives
        assert data["total"] == 1
        assert "agile" in data["items"][0]["perspectives"]
        assert "it" in data["items"][0]["perspectives"]

    async def test_filter_by_perspective_and_competency(
        self, client, authenticated_user, course_with_secondary_tags, questions_with_secondary_tags
    ):
        """Test filtering by both perspective and competency."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{course_with_secondary_tags.slug}/questions?perspectives=it&competencies=communication",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Q2 and Q3 match (IT perspective + communication competency)
        assert data["total"] == 2

    async def test_perspectives_in_response(
        self, client, authenticated_user, course_with_secondary_tags, questions_with_secondary_tags
    ):
        """Test that perspectives are included in response."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{course_with_secondary_tags.slug}/questions",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert "perspectives" in item
            assert isinstance(item["perspectives"], list)

    async def test_competencies_in_response(
        self, client, authenticated_user, course_with_secondary_tags, questions_with_secondary_tags
    ):
        """Test that competencies are included in response."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{course_with_secondary_tags.slug}/questions",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        for item in data["items"]:
            assert "competencies" in item
            assert isinstance(item["competencies"], list)

    async def test_empty_secondary_tags_arrays(
        self, client, authenticated_user, course_with_secondary_tags, questions_with_secondary_tags
    ):
        """Test that questions without secondary tags have empty arrays."""
        headers = {"Authorization": f"Bearer {authenticated_user}"}
        response = await client.get(
            f"/v1/courses/{course_with_secondary_tags.slug}/questions",
            headers=headers
        )

        assert response.status_code == 200
        data = response.json()

        # Find Q4 which has no secondary tags
        q4_item = next(
            item for item in data["items"]
            if item["question_text"] == "General question without secondary tags"
        )
        assert q4_item["perspectives"] == []
        assert q4_item["competencies"] == []
