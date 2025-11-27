"""
Pydantic schemas for User model.
Handles request/response validation and serialization.
"""
from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator


class UserCreate(BaseModel):
    """
    Schema for user registration.
    Validates email format and password strength.
    """
    email: EmailStr
    password: str

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """
        Password must be 8+ chars with at least one letter and one number.
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    class Config:
        """Pydantic config with example."""
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "SecurePass123"
            }
        }


class UserUpdate(BaseModel):
    """
    Schema for updating user profile/onboarding data.
    All fields optional to support partial updates.
    """
    exam_date: Optional[date] = None
    target_score: Optional[int] = None
    daily_study_time: Optional[int] = None
    knowledge_level: Optional[str] = None
    motivation: Optional[str] = None
    referral_source: Optional[str] = None
    dark_mode: Optional[str] = None

    @field_validator('target_score')
    @classmethod
    def validate_target_score(cls, v: Optional[int]) -> Optional[int]:
        """Target score must be between 0 and 100."""
        if v is not None and not (0 <= v <= 100):
            raise ValueError('Target score must be between 0 and 100')
        return v

    @field_validator('knowledge_level')
    @classmethod
    def validate_knowledge_level(cls, v: Optional[str]) -> Optional[str]:
        """Knowledge level must be one of: Beginner, Intermediate, Advanced."""
        if v is not None and v not in ('Beginner', 'Intermediate', 'Advanced'):
            raise ValueError('Knowledge level must be Beginner, Intermediate, or Advanced')
        return v

    @field_validator('referral_source')
    @classmethod
    def validate_referral_source(cls, v: Optional[str]) -> Optional[str]:
        """Referral source must be one of: Search, Friend, Social, Other."""
        if v is not None and v not in ('Search', 'Friend', 'Social', 'Other'):
            raise ValueError('Referral source must be Search, Friend, Social, or Other')
        return v

    @field_validator('dark_mode')
    @classmethod
    def validate_dark_mode(cls, v: Optional[str]) -> Optional[str]:
        """Dark mode must be one of: light, dark, auto."""
        if v is not None and v not in ('light', 'dark', 'auto'):
            raise ValueError('Dark mode must be light, dark, or auto')
        return v

    class Config:
        """Pydantic config with example."""
        json_schema_extra = {
            "example": {
                "exam_date": "2025-06-15",
                "target_score": 85,
                "daily_study_time": 60,
                "knowledge_level": "Intermediate",
                "motivation": "Career advancement",
                "referral_source": "Search",
                "dark_mode": "auto"
            }
        }


class UserResponse(BaseModel):
    """
    Schema for user data returned to frontend.
    Excludes password_hash for security.
    """
    id: UUID
    email: str
    exam_date: Optional[date] = None
    target_score: Optional[int] = None
    daily_study_time: Optional[int] = None
    knowledge_level: Optional[str] = None
    motivation: Optional[str] = None
    referral_source: Optional[str] = None
    is_admin: bool
    dark_mode: str
    created_at: datetime

    class Config:
        """Pydantic config to enable SQLAlchemy model compatibility."""
        from_attributes = True  # Pydantic v2 (replaces orm_mode in v1)
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "email": "user@example.com",
                "exam_date": "2025-06-15",
                "target_score": 85,
                "daily_study_time": 60,
                "knowledge_level": "Intermediate",
                "motivation": "Career advancement",
                "referral_source": "Search",
                "is_admin": False,
                "dark_mode": "auto",
                "created_at": "2025-11-21T10:30:00Z"
            }
        }
