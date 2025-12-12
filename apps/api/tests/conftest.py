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
# Use local Qdrant for tests (override cloud URL from .env)
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ["QDRANT_API_KEY"] = ""

# Now we can import app modules
from src.main import app
from src.db.session import Base, AsyncSessionLocal
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.config import settings
from src.utils.auth import create_access_token
from uuid import uuid4


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


@pytest.fixture(autouse=True)
def reset_rate_limiter(test_app):
    """
    Reset rate limiter state before each test.
    This ensures tests don't interfere with each other's rate limit counts.
    """
    from src.utils.rate_limiter import limiter

    # Reset the limiter's storage using its built-in reset method
    limiter.reset()

    # Also reset the app's limiter state reference
    if hasattr(test_app.state, 'limiter'):
        test_app.state.limiter.reset()
    yield


@pytest.fixture(autouse=True)
async def reset_redis_rate_limits_and_cache():
    """
    Reset Redis-based rate limits and caches before each test.
    This clears rate_limit:*, user_cache:*, and concepts:* keys from Redis.
    """
    from src.db.redis_client import get_redis
    try:
        redis = await get_redis()
        # Delete all rate limit keys
        rate_keys = await redis.keys("rate_limit:*")
        if rate_keys:
            await redis.delete(*rate_keys)
        # Delete all user cache keys
        cache_keys = await redis.keys("user_cache:*")
        if cache_keys:
            await redis.delete(*cache_keys)
        # Delete all concept cache keys
        concept_keys = await redis.keys("concepts:*")
        if concept_keys:
            await redis.delete(*concept_keys)
    except Exception:
        # Ignore errors if Redis is not available
        pass
    yield
    # Also clear cache after test to ensure clean state for next test
    try:
        redis = await get_redis()
        cache_keys = await redis.keys("user_cache:*")
        if cache_keys:
            await redis.delete(*cache_keys)
        concept_keys = await redis.keys("concepts:*")
        if concept_keys:
            await redis.delete(*concept_keys)
    except Exception:
        pass


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
    # httpx 0.28+ requires ASGITransport instead of app parameter
    from httpx import ASGITransport
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def async_client(client: AsyncClient) -> AsyncGenerator[AsyncClient, None]:
    """Alias for client fixture - some tests use async_client instead of client."""
    yield client


# ============================================================================
# Database Fixtures
# ============================================================================

# Event loop fixture for pytest-asyncio 0.21.x compatibility
# Required for session-scoped async fixtures like test_engine
@pytest.fixture(scope="session")
def event_loop():
    """
    Create a session-scoped event loop for async fixtures.

    pytest-asyncio 0.21.x requires an explicit event_loop fixture for
    session-scoped async fixtures. This will be automatically managed
    in pytest-asyncio 0.23+.
    """
    import asyncio
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
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

    Each test gets a fresh session with database cleanup after the test.

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

        # Clean up all tables after each test to ensure isolation
        # This handles nested transactions that commit independently
        # Order matters due to foreign key constraints
        await session.rollback()
        await session.execute(Base.metadata.tables['questions'].delete())
        if 'enrollments' in Base.metadata.tables:
            await session.execute(Base.metadata.tables['enrollments'].delete())
        if 'concept_prerequisites' in Base.metadata.tables:
            await session.execute(Base.metadata.tables['concept_prerequisites'].delete())
        if 'concepts' in Base.metadata.tables:
            await session.execute(Base.metadata.tables['concepts'].delete())
        await session.execute(Base.metadata.tables['users'].delete())
        await session.execute(Base.metadata.tables['password_reset_tokens'].delete())
        if 'courses' in Base.metadata.tables:
            await session.execute(Base.metadata.tables['courses'].delete())
        await session.commit()


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


@pytest.fixture(scope="session", autouse=True)
def reset_qdrant_client():
    """
    Reset Qdrant client singleton to use test environment settings.
    This ensures tests use localhost:6333 instead of cloud URL from .env
    """
    import src.db.qdrant_client as qdrant_module
    from src.config import settings

    # Force settings to use test QDRANT_URL (env var was set at module load time)
    # This is needed because settings may have been initialized before env var was set
    settings.QDRANT_URL = "http://localhost:6333"
    settings.QDRANT_API_KEY = None

    # Reset singleton so it picks up the updated settings
    qdrant_module.qdrant_client = None
    yield
    # Cleanup after all tests
    qdrant_module.qdrant_client = None


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


@pytest.fixture
def sample_course_data():
    """Sample course data for testing."""
    return {
        "slug": "cbap",
        "name": "CBAP Certification Prep",
        "description": "Comprehensive preparation course for CBAP certification.",
        "corpus_name": "BABOK v3",
        "knowledge_areas": [
            {"id": "ba-planning", "name": "Business Analysis Planning and Monitoring", "short_name": "BA Planning", "display_order": 1, "color": "#3B82F6"},
            {"id": "elicitation", "name": "Elicitation and Collaboration", "short_name": "Elicitation", "display_order": 2, "color": "#10B981"},
            {"id": "rlcm", "name": "Requirements Life Cycle Management", "short_name": "RLCM", "display_order": 3, "color": "#F59E0B"},
            {"id": "strategy", "name": "Strategy Analysis", "short_name": "Strategy", "display_order": 4, "color": "#EF4444"},
            {"id": "radd", "name": "Requirements Analysis and Design Definition", "short_name": "RADD", "display_order": 5, "color": "#8B5CF6"},
            {"id": "solution-eval", "name": "Solution Evaluation", "short_name": "Solution Eval", "display_order": 6, "color": "#EC4899"}
        ],
        "is_active": True,
        "is_public": True
    }


@pytest.fixture
def sample_concept_data():
    """Sample concept data for testing."""
    return {
        "name": "Stakeholder Identification",
        "description": "The process of identifying all individuals and groups affected by a solution.",
        "corpus_section_ref": "3.2.1",
        "knowledge_area_id": "ba-planning",
        "difficulty_estimate": 0.3,
        "prerequisite_depth": 0
    }


# ============================================================================
# Authentication Fixtures
# ============================================================================

@pytest.fixture
async def test_user(db_session: AsyncSession):
    """
    Create a test user in the database for authentication testing.

    Returns:
        User object with hashed password
    """
    from src.models.user import User
    from src.utils.auth import hash_password

    user = User(
        email="testuser@example.com",
        hashed_password=hash_password("testpass123"),
        is_admin=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user):
    """
    Generate authentication headers for testing protected endpoints.

    Example:
        async def test_protected_endpoint(client, auth_headers):
            response = await client.get("/api/me", headers=auth_headers)
            assert response.status_code == 200
    """
    # Generate real JWT token using actual test user ID
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def admin_test_user(db_session: AsyncSession):
    """Create an admin test user in the database."""
    from src.models.user import User
    from src.utils.auth import hash_password

    user = User(
        email="admin@example.com",
        hashed_password=hash_password("adminpass123"),
        is_admin=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def admin_auth_headers(admin_test_user):
    """Authentication headers for admin user."""
    # Generate real JWT token for admin using actual admin user ID
    token = create_access_token(data={"sub": str(admin_test_user.id)})
    return {"Authorization": f"Bearer {token}"}


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
