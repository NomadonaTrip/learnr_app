"""
LearnR Backend API
FastAPI application entry point
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from src.config import settings
from src.db import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    Tests database connection on startup and cleans up on shutdown.
    """
    # Startup: Test database connection
    try:
        async with engine.begin() as conn:
            await conn.execute(text("SELECT 1"))
        print("✓ Database connection successful")
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        raise

    yield

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

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


# TODO: Import and include routers here as they are created
# Example:
# from src.routes import auth, users, sessions
# app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
# app.include_router(users.router, prefix="/api/users", tags=["users"])
# app.include_router(sessions.router, prefix="/api/sessions", tags=["sessions"])
