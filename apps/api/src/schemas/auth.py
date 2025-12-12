"""
Authentication-related Pydantic schemas.
Schemas for request/response data structures for authentication endpoints.
"""

from pydantic import BaseModel, EmailStr, field_validator

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


class ForgotPasswordRequest(BaseModel):
    """Request schema for forgot password."""
    email: EmailStr

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com"
            }
        }


class ForgotPasswordResponse(BaseModel):
    """Response schema for forgot password."""
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "If your email is registered, you will receive a password reset link shortly."
            }
        }


class ResetPasswordRequest(BaseModel):
    """Request schema for reset password."""
    token: str
    new_password: str

    @field_validator('new_password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Password must be 8+ chars with letter and number (same as registration)."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isalpha() for c in v):
            raise ValueError('Password must contain at least one letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one number')
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "token": "550e8400-e29b-41d4-a716-446655440000",
                "new_password": "NewSecurePass123"
            }
        }


class ResetPasswordResponse(BaseModel):
    """Response schema for reset password."""
    message: str

    class Config:
        json_schema_extra = {
            "example": {
                "message": "Password reset successful. Please log in with your new password."
            }
        }
