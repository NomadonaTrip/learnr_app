"""
Authentication utilities for password hashing and JWT token generation.
"""

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt
from src.config import settings

# Password hashing context with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash password using bcrypt with cost factor 12.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify password against hashed version.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """
    Create JWT access token.

    Args:
        data: Payload data (must include 'sub' for user_id)
        expires_delta: Optional custom expiration delta

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)

    to_encode.update({
        "exp": expire,
        "iat": now
    })

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )

    return encoded_jwt
