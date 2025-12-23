"""
Integration tests for Courses API endpoints.
Tests GET /v1/courses and GET /v1/courses/{slug} endpoints.
"""

import pytest

from src.models.course import Course


@pytest.fixture
async def test_courses(db_session):
    """Create test courses for API tests."""
    courses = []

    # Active public course
    course1 = Course(
        slug="cbap-api-test",
        name="CBAP Certification Prep",
        description="Comprehensive preparation for CBAP certification.",
        corpus_name="BABOK v3",
        knowledge_areas=[
            {"id": "ba-planning", "name": "Business Analysis Planning", "short_name": "BA Planning", "display_order": 1, "color": "#3B82F6"},
            {"id": "elicitation", "name": "Elicitation and Collaboration", "short_name": "Elicitation", "display_order": 2, "color": "#10B981"},
        ],
        is_active=True,
        is_public=True,
        icon_url="https://example.com/cbap.png",
        color_hex="#3B82F6",
        default_diagnostic_count=20,
        mastery_threshold=0.8,
        gap_threshold=0.3,
        confidence_threshold=0.7,
    )
    db_session.add(course1)
    courses.append(course1)

    # Another active course
    course2 = Course(
        slug="ccba-api-test",
        name="CCBA Certification Prep",
        description="Comprehensive preparation for CCBA certification.",
        corpus_name="BABOK v3",
        knowledge_areas=[
            {"id": "strategy", "name": "Strategy Analysis", "short_name": "Strategy", "display_order": 1, "color": "#EF4444"},
        ],
        is_active=True,
        is_public=True,
        icon_url="https://example.com/ccba.png",
        color_hex="#10B981",
    )
    db_session.add(course2)
    courses.append(course2)

    # Inactive course (should not appear in list)
    course3 = Course(
        slug="inactive-api-test",
        name="Inactive Course",
        description="This course is not active.",
        knowledge_areas=[],
        is_active=False,
        is_public=True,
    )
    db_session.add(course3)
    courses.append(course3)

    await db_session.commit()
    for c in courses:
        await db_session.refresh(c)

    return courses


@pytest.mark.asyncio
class TestCoursesListEndpoint:
    """Tests for GET /v1/courses endpoint."""

    async def test_list_courses_success(self, client, test_courses):
        """Test listing courses returns active courses."""
        response = await client.get("/v1/courses")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "meta" in data

        # Should have at least 2 active courses
        assert len(data["data"]) >= 2

        # Verify inactive course not in list
        slugs = [c["slug"] for c in data["data"]]
        assert "inactive-api-test" not in slugs

    async def test_list_courses_response_format(self, client, test_courses):
        """Test list courses response format."""
        response = await client.get("/v1/courses")

        assert response.status_code == 200
        data = response.json()

        # Check meta format
        assert "timestamp" in data["meta"]
        assert "version" in data["meta"]
        assert "count" in data["meta"]
        assert data["meta"]["version"] == "v1"

        # Check course item format
        course_item = next((c for c in data["data"] if c["slug"] == "cbap-api-test"), None)
        assert course_item is not None
        assert "id" in course_item
        assert "slug" in course_item
        assert "name" in course_item
        assert "description" in course_item
        assert "knowledge_area_count" in course_item
        assert "icon_url" in course_item
        assert "color_hex" in course_item

    async def test_list_courses_knowledge_area_count(self, client, test_courses):
        """Test knowledge area count is correctly returned."""
        response = await client.get("/v1/courses")

        assert response.status_code == 200
        data = response.json()

        cbap_course = next((c for c in data["data"] if c["slug"] == "cbap-api-test"), None)
        assert cbap_course is not None
        assert cbap_course["knowledge_area_count"] == 2

        ccba_course = next((c for c in data["data"] if c["slug"] == "ccba-api-test"), None)
        assert ccba_course is not None
        assert ccba_course["knowledge_area_count"] == 1

    async def test_list_courses_no_auth_required(self, client, test_courses):
        """Test listing courses does not require authentication."""
        # No auth headers
        response = await client.get("/v1/courses")

        assert response.status_code == 200


@pytest.mark.asyncio
class TestCourseDetailEndpoint:
    """Tests for GET /v1/courses/{slug} endpoint."""

    async def test_get_course_by_slug_success(self, client, test_courses):
        """Test getting course by slug returns full details."""
        response = await client.get("/v1/courses/cbap-api-test")

        assert response.status_code == 200
        data = response.json()

        assert "data" in data
        assert "meta" in data

        course = data["data"]
        assert course["slug"] == "cbap-api-test"
        assert course["name"] == "CBAP Certification Prep"
        assert course["corpus_name"] == "BABOK v3"

    async def test_get_course_includes_knowledge_areas(self, client, test_courses):
        """Test course details include full knowledge areas."""
        response = await client.get("/v1/courses/cbap-api-test")

        assert response.status_code == 200
        data = response.json()

        course = data["data"]
        assert "knowledge_areas" in course
        assert len(course["knowledge_areas"]) == 2

        ka_ids = [ka["id"] for ka in course["knowledge_areas"]]
        assert "ba-planning" in ka_ids
        assert "elicitation" in ka_ids

    async def test_get_course_includes_thresholds(self, client, test_courses):
        """Test course details include threshold configuration."""
        response = await client.get("/v1/courses/cbap-api-test")

        assert response.status_code == 200
        data = response.json()

        course = data["data"]
        assert course["default_diagnostic_count"] == 20
        assert course["mastery_threshold"] == 0.8
        assert course["gap_threshold"] == 0.3
        assert course["confidence_threshold"] == 0.7

    async def test_get_course_not_found(self, client, test_courses):
        """Test getting non-existent course returns 404."""
        response = await client.get("/v1/courses/non-existent-course")

        assert response.status_code == 404
        data = response.json()

        assert "detail" in data
        assert "error" in data["detail"]
        assert data["detail"]["error"]["code"] == "COURSE_NOT_FOUND"

    async def test_get_inactive_course_returns_404(self, client, test_courses):
        """Test getting inactive course returns 404."""
        response = await client.get("/v1/courses/inactive-api-test")

        assert response.status_code == 404

    async def test_get_course_no_auth_required(self, client, test_courses):
        """Test getting course does not require authentication."""
        response = await client.get("/v1/courses/cbap-api-test")

        assert response.status_code == 200

    async def test_get_course_response_timestamps(self, client, test_courses):
        """Test course response includes timestamps."""
        response = await client.get("/v1/courses/cbap-api-test")

        assert response.status_code == 200
        data = response.json()

        course = data["data"]
        assert "created_at" in course
        assert "updated_at" in course

        # Verify meta timestamp
        assert "timestamp" in data["meta"]
