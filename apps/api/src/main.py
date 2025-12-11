"""
LearnR Backend API
FastAPI application entry point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.db import engine
from src.db.redis_client import get_redis, close_redis, test_redis_connection
from src.db.qdrant_client import get_qdrant, close_qdrant, test_qdrant_connection
from src.routes import auth, concepts, courses, health, questions, reading, users
from src.utils.rate_limiter import limiter
from src.middleware.error_handler import (
    conflict_error_handler,
    validation_error_handler,
    database_error_handler,
    authentication_error_handler,
    authorization_error_handler,
    not_found_error_handler,
    rate_limit_error_handler,
    token_invalid_error_handler,
    token_expired_error_handler,
    token_already_used_error_handler
)
from src.exceptions import (
    ConflictError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError,
    TokenInvalidError,
    TokenExpiredError,
    TokenAlreadyUsedError
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Tests database and Redis connections on startup and cleans up on shutdown.
    """
    # Startup: Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise

    # Startup: Test Redis connection
    try:
        redis_ok = await test_redis_connection()
        if redis_ok:
            print("✓ Redis connection successful")
        else:
            print("✗ Redis connection failed")
            raise Exception("Redis connection test failed")
    except Exception as e:
        print(f"✗ Redis connection failed: {e}")
        raise

    # Startup: Test Qdrant connection
    try:
        qdrant_ok = await test_qdrant_connection()
        if qdrant_ok:
            print("✓ Qdrant connection successful")
        else:
            print("✗ Qdrant connection failed")
            raise Exception("Qdrant connection test failed")
    except Exception as e:
        print(f"✗ Qdrant connection failed: {e}")
        raise

    yield

    # Shutdown: Close Redis connection
    await close_redis()
    print("✓ Redis connection closed")

    # Shutdown: Close Qdrant connection
    await close_qdrant()
    print("✓ Qdrant connection closed")

    # Shutdown: Dispose of database connections
    await engine.dispose()
    print("✓ Database connections closed")


# Initialize FastAPI app
app = FastAPI(
    title="LearnR API",
    description="""
    # LearnR API - CBAP Certification Preparation Platform

    The LearnR API provides endpoints for user authentication, adaptive quiz sessions,
    competency tracking, and personalized reading recommendations for CBAP exam preparation.

    ## Features

    - **User Authentication**: Registration, login, password reset with JWT tokens
    - **User Profile Management**: Update exam date, target score, study preferences
    - **Adaptive Quiz Engine**: IRT-based question selection (future)
    - **Competency Tracking**: Real-time competency scores per knowledge area (future)
    - **Reading Library**: Personalized BABOK content recommendations (future)
    - **Spaced Repetition**: SM-2 algorithm for optimal review scheduling (future)

    ## Authentication

    Most endpoints require JWT authentication. Include the token in the Authorization header:

    ```
    Authorization: Bearer <your_jwt_token>
    ```

    Get a token by calling `/v1/auth/register` or `/v1/auth/login`.

    ## Base URL

    - **Development**: http://localhost:8000
    - **Production**: https://api.learnr.com

    ## Support

    For API support, contact: support@learnr.com
    """,
    version="1.0.0",
    contact={
        "name": "LearnR Support",
        "email": "support@learnr.com",
        "url": "https://learnr.com"
    },
    license_info={
        "name": "Proprietary",
        "url": "https://learnr.com/terms"
    },
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# Configure JWT Bearer authentication for OpenAPI
def custom_openapi():
    """Customize OpenAPI schema with security scheme."""
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )

    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "LearnR Support",
        "email": "support@learnr.com",
        "url": "https://learnr.com"
    }
    openapi_schema["info"]["license"] = {
        "name": "Proprietary",
        "url": "https://learnr.com/terms"
    }

    # Add JWT Bearer security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your JWT token from /v1/auth/login or /v1/auth/register"
        }
    }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register exception handlers
app.add_exception_handler(ConflictError, conflict_error_handler)
app.add_exception_handler(ValidationError, validation_error_handler)
app.add_exception_handler(DatabaseError, database_error_handler)
app.add_exception_handler(AuthenticationError, authentication_error_handler)
app.add_exception_handler(AuthorizationError, authorization_error_handler)
app.add_exception_handler(NotFoundError, not_found_error_handler)
app.add_exception_handler(RateLimitError, rate_limit_error_handler)
app.add_exception_handler(TokenInvalidError, token_invalid_error_handler)
app.add_exception_handler(TokenExpiredError, token_expired_error_handler)
app.add_exception_handler(TokenAlreadyUsedError, token_already_used_error_handler)

# Include routers
app.include_router(health.router)  # Health check (no prefix - root level)
app.include_router(auth.router, prefix="/v1")
app.include_router(users.router, prefix="/v1")
app.include_router(courses.router, prefix="/v1")
app.include_router(concepts.router, prefix="/v1")
app.include_router(questions.router, prefix="/v1")
app.include_router(reading.router, prefix="/v1")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "healthy",
        "message": "LearnR API is running",
        "version": "1.0.0"
    }
