"""
Integration tests for database functionality.
Tests that database connection, session management, and basic CRUD operations work.
"""
import uuid

import pytest

from src.models.user import User


@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_connection(db_session):
    """Test that database connection works."""
    # This test passes if db_session fixture initializes without error
    assert db_session is not None


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_and_query_user(db_session):
    """Test creating and querying a user from database."""
    from sqlalchemy import select

    # Create a user
    user = User(
        id=uuid.uuid4(),
        email="testuser@example.com",
        hashed_password="hashed_password_here",
        is_admin=False,
        dark_mode="auto"
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Query the user back
    result = await db_session.execute(
        select(User).where(User.email == "testuser@example.com")
    )
    queried_user = result.scalar_one_or_none()

    # Verify
    assert queried_user is not None
    assert queried_user.email == "testuser@example.com"
    assert queried_user.hashed_password == "hashed_password_here"
    assert queried_user.is_admin is False
    assert queried_user.dark_mode == "auto"
    assert queried_user.created_at is not None
    assert queried_user.updated_at is not None
