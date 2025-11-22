"""
Database utility functions.
Provides helper functions for database operations and health checks.
"""
from sqlalchemy import text

from .session import engine


async def check_database_health() -> dict:
    """
    Check database health and connectivity.

    Returns:
        dict: Database health status with connection info

    Example:
        health = await check_database_health()
        if health["status"] == "healthy":
            print("Database is operational")
    """
    try:
        async with engine.begin() as conn:
            # Execute simple query to test connection
            result = await conn.execute(text("SELECT 1 as health_check"))
            result.scalar()

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "database": "PostgreSQL"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "database": "PostgreSQL"
        }
