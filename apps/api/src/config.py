"""
Configuration management using Pydantic settings
Loads environment variables from .env file
"""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000

    # CORS
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000"
    ]

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_dev"
    TEST_DATABASE_URL: str = "postgresql+asyncpg://learnr:learnr123@localhost:5432/learnr_test"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
    DB_ECHO: bool = False  # Set True for SQL query logging

    # Redis
    REDIS_URL: str = "redis://:learnr123@localhost:6379/0"  # Default for local Docker Redis
    REDIS_PASSWORD: str | None = "learnr123"  # Password for local Docker Redis

    # JWT
    SECRET_KEY: str = "your-secret-key-for-jwt-signing-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 604800  # 7 days

    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    PASSWORD_RESET_RATE_LIMIT: int = 5
    REGISTRATION_RATE_LIMIT: str = "5/minute"  # Max 5 registration attempts per minute per IP

    # Logging
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
