"""
Unit tests for Course repository.
"""
import pytest
from uuid import uuid4

from src.models.course import Course
from src.repositories.course_repository import CourseRepository


@pytest.mark.asyncio
async def test_get_all_active_returns_active_courses(db_session, sample_course_data):
    """Test that get_all_active returns only active courses."""
    # Create an active course
    active_course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        description=sample_course_data["description"],
        corpus_name=sample_course_data["corpus_name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(active_course)

    # Create an inactive course
    inactive_course = Course(
        slug="inactive-course",
        name="Inactive Course",
        knowledge_areas=[],
        is_active=False
    )
    db_session.add(inactive_course)
    await db_session.commit()

    repo = CourseRepository(db_session)
    courses = await repo.get_all_active()

    assert len(courses) == 1
    assert courses[0].slug == sample_course_data["slug"]
    assert courses[0].is_active is True


@pytest.mark.asyncio
async def test_get_all_active_returns_empty_list_when_no_active_courses(db_session):
    """Test that get_all_active returns empty list when no active courses exist."""
    repo = CourseRepository(db_session)
    courses = await repo.get_all_active()

    assert courses == []


@pytest.mark.asyncio
async def test_get_by_slug_returns_course(db_session, sample_course_data):
    """Test that get_by_slug returns the correct course."""
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        knowledge_areas=sample_course_data["knowledge_areas"]
    )
    db_session.add(course)
    await db_session.commit()

    repo = CourseRepository(db_session)
    found_course = await repo.get_by_slug(sample_course_data["slug"])

    assert found_course is not None
    assert found_course.slug == sample_course_data["slug"]
    assert found_course.name == sample_course_data["name"]


@pytest.mark.asyncio
async def test_get_by_slug_returns_none_when_not_found(db_session):
    """Test that get_by_slug returns None when course not found."""
    repo = CourseRepository(db_session)
    course = await repo.get_by_slug("nonexistent")

    assert course is None


@pytest.mark.asyncio
async def test_get_by_id_returns_course(db_session, sample_course_data):
    """Test that get_by_id returns the correct course."""
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        knowledge_areas=sample_course_data["knowledge_areas"]
    )
    db_session.add(course)
    await db_session.commit()
    await db_session.refresh(course)

    repo = CourseRepository(db_session)
    found_course = await repo.get_by_id(course.id)

    assert found_course is not None
    assert found_course.id == course.id
    assert found_course.slug == sample_course_data["slug"]


@pytest.mark.asyncio
async def test_get_by_id_returns_none_when_not_found(db_session):
    """Test that get_by_id returns None when course not found."""
    repo = CourseRepository(db_session)
    course = await repo.get_by_id(uuid4())

    assert course is None


@pytest.mark.asyncio
async def test_get_active_by_slug_returns_active_course(db_session, sample_course_data):
    """Test that get_active_by_slug returns active course."""
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        knowledge_areas=sample_course_data["knowledge_areas"],
        is_active=True
    )
    db_session.add(course)
    await db_session.commit()

    repo = CourseRepository(db_session)
    found_course = await repo.get_active_by_slug(sample_course_data["slug"])

    assert found_course is not None
    assert found_course.slug == sample_course_data["slug"]
    assert found_course.is_active is True


@pytest.mark.asyncio
async def test_get_active_by_slug_returns_none_for_inactive_course(db_session):
    """Test that get_active_by_slug returns None for inactive course."""
    course = Course(
        slug="inactive",
        name="Inactive Course",
        knowledge_areas=[],
        is_active=False
    )
    db_session.add(course)
    await db_session.commit()

    repo = CourseRepository(db_session)
    found_course = await repo.get_active_by_slug("inactive")

    assert found_course is None


@pytest.mark.asyncio
async def test_course_knowledge_areas_jsonb(db_session, sample_course_data):
    """Test that knowledge_areas JSONB is properly stored and retrieved."""
    course = Course(
        slug=sample_course_data["slug"],
        name=sample_course_data["name"],
        knowledge_areas=sample_course_data["knowledge_areas"]
    )
    db_session.add(course)
    await db_session.commit()

    repo = CourseRepository(db_session)
    found_course = await repo.get_by_slug(sample_course_data["slug"])

    assert found_course is not None
    assert len(found_course.knowledge_areas) == 6
    assert found_course.knowledge_areas[0]["id"] == "ba-planning"
    assert found_course.knowledge_areas[0]["name"] == "Business Analysis Planning and Monitoring"
    assert found_course.knowledge_areas[0]["short_name"] == "BA Planning"
    assert found_course.knowledge_areas[0]["display_order"] == 1
    assert found_course.knowledge_areas[0]["color"] == "#3B82F6"
