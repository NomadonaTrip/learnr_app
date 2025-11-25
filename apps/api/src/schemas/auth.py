"""
Authentication-related Pydantic schemas.
Schemas for request/response data structures for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr
from src.schemas.user import UserResponse


class RegisterResponse(BaseModel):
    """Response schema for user registration."""
    user: UserResponse
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "created_at": "2025-11-21T10:30:00Z",
                    "exam_date": None,
                    "target_score": None,
                    "daily_study_time": None,
                    "knowledge_level": None,
                    "motivation": None,
                    "referral_source": None,
                    "is_admin": False,
                    "dark_mode": "auto"
                },
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }


class TokenData(BaseModel):
    """JWT token payload structure."""
    sub: str  # user_id
    exp: int  # expiration timestamp
    iat: int  # issued at timestamp


class LoginRequest(BaseModel):
    """Request schema for user login."""
    email: EmailStr
    password: str

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class LoginResponse(BaseModel):
    """Response schema for user login."""
    user: UserResponse
    token: str

    class Config:
        json_schema_extra = {
            "example": {
                "user": {
                    "id": "123e4567-e89b-12d3-a456-426614174000",
                    "email": "user@example.com",
                    "created_at": "2025-11-21T10:30:00Z",
                    "exam_date": None,
                    "target_score": None,
                    "daily_study_time": None,
                    "knowledge_level": None,
                    "motivation": None,
                    "referral_source": None,
                    "is_admin": False,
                    "dark_mode": "auto"
                },
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
