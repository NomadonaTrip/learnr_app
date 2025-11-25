"""
LearnR Backend API
FastAPI application entry point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from src.config import settings
from src.db import engine
from src.db.redis_client import get_redis, close_redis, test_redis_connection
from src.routes import auth
from src.utils.rate_limiter import limiter
from src.middleware.error_handler import (
    conflict_error_handler,
    validation_error_handler,
    database_error_handler,
    authentication_error_handler,
    authorization_error_handler,
    not_found_error_handler,
    rate_limit_error_handler
)
from src.exceptions import (
    ConflictError,
    ValidationError,
    DatabaseError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    RateLimitError
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

    yield

    # Shutdown: Close Redis connection
    await close_redis()
    print("✓ Redis connection closed")

    # Shutdown: Dispose of database connections
    await engine.dispose()
    print("✓ Database connections closed")


# Initialize FastAPI app
app = FastAPI(
    title="LearnR API",
    description="AI-Powered Adaptive Learning Platform for Professional Certification Exam Preparation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

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

# Include routers
app.include_router(auth.router, prefix="/v1")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "message": "LearnR API is running",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Detailed health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG
    }
