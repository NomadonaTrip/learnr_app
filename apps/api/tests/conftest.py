"""
Pytest Configuration and Fixtures

This file contains:
- Test fixtures (database, client, mock services)
- Test configuration
- Pytest hooks
"""

import os
import pytest
from typing import Generator, AsyncGenerator
from httpx import AsyncClient
from fastapi import FastAPI

# Set test environment variables before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["USE_MOCK_OPENAI"] = "true"
os.environ["USE_MOCK_EMAIL"] = "true"
os.environ["DATABASE_URL"] = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_test"
)

# Now we can import app modules
from src.main import app
from src.db.session import Base, AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.config import settings


# ============================================================================
# Test Application Fixture
# ============================================================================

@pytest.fixture
def test_app() -> FastAPI:
    """
    Fixture for FastAPI application instance.

    Use this for testing the app configuration, middleware, etc.
    """
    return app


# ============================================================================
# HTTP Client Fixtures
# ============================================================================

@pytest.fixture
async def client(test_app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client for testing API endpoints.

    Example:
        async def test_endpoint(client):
            response = await client.get("/health")
            assert response.status_code == 200
    """
    async with AsyncClient(app=test_app, base_url="http://test") as ac:
        yield ac


# ============================================================================
# Database Fixtures
# ============================================================================

@pytest.fixture(scope="session")
def event_loop():
    """
    Create event loop for async tests.
    Required for async fixtures and tests.
    """
    import asyncio
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """
    Create test database engine and initialize schema.
    Runs once per test session.
    """
    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        echo=False,  # Set True for SQL query logging in tests
        pool_pre_ping=True,
    )

    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """
    Provide a database session for tests.

    Each test gets a fresh session that's rolled back after the test.

    Example:
        async def test_create_user(db_session):
            user = User(email="test@example.com")
            db_session.add(user)
            await db_session.commit()
    """
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session
        await session.rollback()  # Rollback any changes after test


# ============================================================================
# Mock Service Fixtures
# ============================================================================

@pytest.fixture
def mock_openai_service():
    """
    Mock OpenAI API service.

    Returns deterministic responses for testing.
    """
    class MockOpenAIService:
        def generate_embedding(self, text: str):
            """Return deterministic embedding for testing."""
            import hashlib
            import numpy as np

            # Use hash of text as seed
            seed = int(hashlib.md5(text.encode()).hexdigest()[:8], 16)
            np.random.seed(seed)
            embedding = np.random.randn(3072)

            # Normalize
            norm = np.linalg.norm(embedding)
            return (embedding / norm).tolist()

        def generate_chat_completion(self, messages: list):
            """Return canned response for testing."""
            return {
                "choices": [{
                    "message": {
                        "role": "assistant",
                        "content": "This is a mock response for testing."
                    }
                }]
            }

    return MockOpenAIService()


@pytest.fixture
def mock_email_service():
    """
    Mock email service.

    Captures sent emails for testing verification.
    """
    class MockEmailService:
        def __init__(self):
            self.sent_emails = []

        async def send_email(self, to_email: str, subject: str, html_content: str, text_content: str = None):
            """Mock send email - just records the email."""
            self.sent_emails.append({
                "to": to_email,
                "subject": subject,
                "html": html_content,
                "text": text_content
            })
            return True

        async def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str = None):
            """Mock password reset email."""
            return await self.send_email(
                to_email=to_email,
                subject="Reset Your Password",
                html_content=f"Reset token: {reset_token}",
                text_content=f"Reset token: {reset_token}"
            )

        def get_sent_emails(self):
            """Get all sent emails for verification."""
            return self.sent_emails

        def clear(self):
            """Clear sent emails list."""
            self.sent_emails = []

    return MockEmailService()


@pytest.fixture
def mock_qdrant_service():
    """
    Mock Qdrant vector database.

    Stores vectors in memory for testing.
    """
    class MockQdrantService:
        def __init__(self):
            self.collections = {}

        def create_collection(self, collection_name: str, vector_size: int):
            """Create a collection."""
            self.collections[collection_name] = []

        def upsert(self, collection_name: str, points: list):
            """Insert or update points."""
            if collection_name not in self.collections:
                self.create_collection(collection_name, 3072)
            self.collections[collection_name].extend(points)

        def search(self, collection_name: str, query_vector: list, limit: int = 10):
            """Mock search - returns first N points."""
            if collection_name not in self.collections:
                return []
            return self.collections[collection_name][:limit]

        def get_collection_info(self, collection_name: str):
            """Get collection info."""
            if collection_name not in self.collections:
                return None
            return {
                "vectors_count": len(self.collections[collection_name]),
                "status": "green"
            }

    return MockQdrantService()


# ============================================================================
# Test Data Fixtures
# ============================================================================

@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "password": "SecurePassword123!",
        "name": "Test User"
    }


@pytest.fixture
def sample_question_data():
    """Sample question data for testing."""
    return {
        "question_text": "What is Business Analysis?",
        "options": [
            {"id": "a", "text": "Option A - Correct"},
            {"id": "b", "text": "Option B"},
            {"id": "c", "text": "Option C"},
            {"id": "d", "text": "Option D"}
        ],
        "correct_answer_id": "a",
        "knowledge_area": "Business Analysis Planning",
        "difficulty": 0.5,
        "explanation": "Option A is correct because..."
    }


@pytest.fixture
def sample_session_data():
    """Sample quiz session data for testing."""
    return {
        "user_id": "test-user-id",
        "started_at": "2025-01-01T00:00:00Z",
        "questions_answered": 0,
        "correct_count": 0
    }


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
def auth_headers():
    """
    Generate authentication headers for testing protected endpoints.

    Example:
        async def test_protected_endpoint(client, auth_headers):
            response = await client.get("/api/me", headers=auth_headers)
            assert response.status_code == 200
    """
    # TODO: Generate real JWT when auth is implemented
    fake_token = "fake-jwt-token-for-testing"
    return {"Authorization": f"Bearer {fake_token}"}


@pytest.fixture
def admin_auth_headers():
    """Authentication headers for admin user."""
    # TODO: Generate admin JWT when auth is implemented
    fake_admin_token = "fake-admin-jwt-token-for-testing"
    return {"Authorization": f"Bearer {fake_admin_token}"}


# ============================================================================
# Pytest Hooks
# ============================================================================

def pytest_configure(config):
    """Configure pytest before tests run."""
    # Register custom markers
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test items after collection."""
    # Auto-mark tests based on location
    for item in items:
        if "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)


# ============================================================================
# Utility Functions for Tests
# ============================================================================

def assert_valid_uuid(value: str):
    """Assert that a string is a valid UUID."""
    import uuid
    try:
        uuid.UUID(value)
    except ValueError:
        pytest.fail(f"'{value}' is not a valid UUID")


def assert_valid_email(value: str):
    """Assert that a string is a valid email."""
    import re
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_regex, value):
        pytest.fail(f"'{value}' is not a valid email")


def assert_valid_timestamp(value: str):
    """Assert that a string is a valid ISO 8601 timestamp."""
    from datetime import datetime
    try:
        datetime.fromisoformat(value.replace('Z', '+00:00'))
    except ValueError:
        pytest.fail(f"'{value}' is not a valid ISO 8601 timestamp")
