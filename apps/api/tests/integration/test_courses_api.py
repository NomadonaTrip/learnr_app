"""
Integration tests for Course API endpoints.
"""
import pytest
from httpx import AsyncClient

from src.models.course import Course


@pytest.mark.asyncio
async def test_list_courses_returns_empty_list(client: AsyncClient):
    """Test GET /v1/courses returns empty list when no courses exist."""
    response = await client.get("/v1/courses")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"] == []
    assert "meta" in data
    assert data["meta"]["count"] == 0


@pytest.mark.asyncio
async def test_list_courses_returns_active_courses(
    client: AsyncClient,
    db_session,
    sample_course_data
):
    """Test GET /v1/courses returns active courses."""
    # Create a course in the database
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        description=sample_course_data["description"],
        corpus_name=sample_course_data["corpus_name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True,
        is_public=True
    )
    db_session.add(course)
    await db_session.commit()

    response = await client.get("/v1/courses")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1
    assert data["data"][0]["slug"] == sample_course_data["slug"]
    assert data["data"][0]["name"] == sample_course_data["name"]
    assert data["data"][0]["knowledge_area_count"] == 6
    assert data["meta"]["count"] == 1


@pytest.mark.asyncio
async def test_list_courses_excludes_inactive_courses(
    client: AsyncClient,
    db_session,
    sample_course_data
):
    """Test GET /v1/courses excludes inactive courses."""
    # Create an inactive course
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=False
    )
    db_session.add(course)
    await db_session.commit()

    response = await client.get("/v1/courses")

    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 0


@pytest.mark.asyncio
async def test_get_course_by_slug_returns_course(
    client: AsyncClient,
    db_session,
    sample_course_data
):
    """Test GET /v1/courses/{slug} returns course details."""
    # Create a course
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        description=sample_course_data["description"],
        corpus_name=sample_course_data["corpus_name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()

    response = await client.get(f"/v1/courses/{sample_course_data['slug']}")

    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert data["data"]["slug"] == sample_course_data["slug"]
    assert data["data"]["name"] == sample_course_data["name"]
    assert data["data"]["description"] == sample_course_data["description"]
    assert data["data"]["corpus_name"] == sample_course_data["corpus_name"]
    assert len(data["data"]["knowledge_areas"]) == 6


@pytest.mark.asyncio
async def test_get_course_by_slug_returns_404_for_nonexistent(client: AsyncClient):
    """Test GET /v1/courses/{slug} returns 404 for nonexistent course."""
    response = await client.get("/v1/courses/nonexistent")

    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert data["detail"]["error"]["code"] == "COURSE_NOT_FOUND"


@pytest.mark.asyncio
async def test_get_course_by_slug_returns_404_for_inactive(
    client: AsyncClient,
    db_session
):
    """Test GET /v1/courses/{slug} returns 404 for inactive course."""
    # Create an inactive course
    course = Course(
        slug="inactive-course",
        name="Inactive Course",
        knowledge_areas=[],
        is_active=False
    )
    db_session.add(course)
    await db_session.commit()

    response = await client.get("/v1/courses/inactive-course")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_course_knowledge_areas_structure(
    client: AsyncClient,
    db_session,
    sample_course_data
):
    """Test that knowledge areas have correct structure."""
    # Create a course
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()

    response = await client.get(f"/v1/courses/{sample_course_data['slug']}")

    assert response.status_code == 200
    data = response.json()
    ka = data["data"]["knowledge_areas"][0]

    # Verify knowledge area structure
    assert "id" in ka
    assert "name" in ka
    assert "short_name" in ka
    assert "display_order" in ka
    assert "color" in ka

    # Verify first knowledge area values
    assert ka["id"] == "ba-planning"
    assert ka["name"] == "Business Analysis Planning and Monitoring"
    assert ka["short_name"] == "BA Planning"
    assert ka["display_order"] == 1
    assert ka["color"] == "#3B82F6"


@pytest.mark.asyncio
async def test_list_courses_response_meta_contains_timestamp(
    client: AsyncClient
):
    """Test that list courses response meta contains timestamp."""
    response = await client.get("/v1/courses")

    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert "timestamp" in data["meta"]
    assert "version" in data["meta"]
    assert data["meta"]["version"] == "v1"


@pytest.mark.asyncio
async def test_get_course_response_meta_contains_timestamp(
    client: AsyncClient,
    db_session,
    sample_course_data
):
    """Test that get course response meta contains timestamp."""
    # Create a course
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()

    response = await client.get(f"/v1/courses/{sample_course_data['slug']}")

    assert response.status_code == 200
    data = response.json()
    assert "meta" in data
    assert "timestamp" in data["meta"]
    assert "version" in data["meta"]
    assert data["meta"]["version"] == "v1"
