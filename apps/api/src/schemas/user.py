"""
Pydantic schemas for User model.
Handles request/response validation and serialization.
"""
from datetime import date, datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, EmailStr, field_validator

# Valid familiarity levels from onboarding Q3
FamiliarityLevel = Literal["new", "basics", "intermediate", "expert"]


class OnboardingData(BaseModel):
    """
    Schema for onboarding data collected during registration.
    Maps user's declared familiarity to initial belief prior.
    """
    course: str  # e.g., 'business-analysis'
    motivation: str  # e.g., 'certification', 'career', etc.
    familiarity: FamiliarityLevel  # 'new', 'basics', 'intermediate', 'expert'
    initial_belief_prior: float  # 0.1, 0.3, 0.5, or 0.7

    @field_validator('initial_belief_prior')
    @classmethod
    def validate_prior(cls, v: float) -> float:
        """Initial belief prior must be in [0.0, 1.0]."""
        if not (0.0 <= v <= 1.0):
            raise ValueError('initial_belief_prior must be between 0.0 and 1.0')
        return v

    class Config:
        """Pydantic config with example."""
        json_schema_extra = {
            "example": {
                "course": "business-analysis",
                "motivation": "certification",
                "familiarity": "basics",
                "initial_belief_prior": 0.3
            }
        }


class UserCreate(BaseModel):
    """
    Schema for user registration.
    Validates email format and password strength.
    Optional onboarding_data sets initial belief priors based on familiarity.
    """
    email: EmailStr
    password: str
    onboarding_data: OnboardingData | None = None

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
                "password": "SecurePass123",
                "onboarding_data": {
                    "course": "business-analysis",
                    "motivation": "certification",
                    "familiarity": "basics",
                    "initial_belief_prior": 0.3
                }
            }
        }


class UserUpdate(BaseModel):
    """
    Schema for updating user profile/onboarding data.
    All fields optional to support partial updates.
    """
    exam_date: date | None = None
    target_score: int | None = None
    daily_study_time: int | None = None
    knowledge_level: str | None = None
    motivation: str | None = None
    referral_source: str | None = None
    dark_mode: str | None = None

    @field_validator('target_score')
    @classmethod
    def validate_target_score(cls, v: int | None) -> int | None:
        """Target score must be between 0 and 100."""
        if v is not None and not (0 <= v <= 100):
            raise ValueError('Target score must be between 0 and 100')
        return v

    @field_validator('knowledge_level')
    @classmethod
    def validate_knowledge_level(cls, v: str | None) -> str | None:
        """Knowledge level must be one of: Beginner, Intermediate, Advanced."""
        if v is not None and v not in ('Beginner', 'Intermediate', 'Advanced'):
            raise ValueError('Knowledge level must be Beginner, Intermediate, or Advanced')
        return v

    @field_validator('referral_source')
    @classmethod
    def validate_referral_source(cls, v: str | None) -> str | None:
        """Referral source must be one of: Search, Friend, Social, Other."""
        if v is not None and v not in ('Search', 'Friend', 'Social', 'Other'):
            raise ValueError('Referral source must be Search, Friend, Social, or Other')
        return v

    @field_validator('dark_mode')
    @classmethod
    def validate_dark_mode(cls, v: str | None) -> str | None:
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
    exam_date: date | None = None
    target_score: int | None = None
    daily_study_time: int | None = None
    knowledge_level: str | None = None
    motivation: str | None = None
    referral_source: str | None = None
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
