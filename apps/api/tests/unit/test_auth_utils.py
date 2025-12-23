"""
Unit tests for authentication utilities.
Tests password hashing and JWT token generation.
"""

from datetime import UTC, datetime, timedelta

import pytest
from jose import JWTError, jwt

from src.config import settings
from src.utils.auth import create_access_token, decode_token, hash_password, verify_password


class TestPasswordHashing:
    """Tests for password hashing utilities."""

    def test_hash_password_produces_different_hashes(self):
        """Test that same password produces different hashes due to salt."""
        password = "TestPass123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        # Hashes should be different due to random salt
        assert hash1 != hash2
        # Both should be bcrypt hashes (start with $2b$)
        assert hash1.startswith("$2b$")
        assert hash2.startswith("$2b$")

    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        password = "TestPass123"
        hashed = hash_password(password)

        assert isinstance(hashed, str)
        assert len(hashed) == 60  # bcrypt hash length

    def test_verify_password_success(self):
        """Test password verification with correct password."""
        password = "TestPass123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_failure(self):
        """Test password verification with incorrect password."""
        password = "TestPass123"
        hashed = hash_password(password)

        assert verify_password("WrongPass456", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case-sensitive."""
        password = "TestPass123"
        hashed = hash_password(password)

        assert verify_password("testpass123", hashed) is False
        assert verify_password("TESTPASS123", hashed) is False

    def test_verify_password_with_special_characters(self):
        """Test password hashing and verification with special characters."""
        password = "Test@Pass#123!"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True
        assert verify_password("Test@Pass#123", hashed) is False


class TestJWTTokenGeneration:
    """Tests for JWT token generation."""

    def test_create_access_token_basic(self):
        """Test JWT token creation with correct payload."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(data={"sub": user_id})

        # Verify token is a string
        assert isinstance(token, str)
        assert len(token) > 0

        # Decode token and verify payload
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == user_id
        assert "exp" in payload
        assert "iat" in payload

    def test_create_access_token_default_expiration(self):
        """Test JWT token has correct default expiration."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(data={"sub": user_id})

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify expiration is approximately 7 days (604800 seconds)
        exp_delta = payload["exp"] - payload["iat"]
        assert abs(exp_delta - settings.JWT_EXPIRATION_SECONDS) < 5  # Allow 5 second variance

    def test_create_access_token_custom_expiration(self):
        """Test JWT token with custom expiration."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        custom_delta = timedelta(hours=1)
        token = create_access_token(
            data={"sub": user_id},
            expires_delta=custom_delta
        )

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify custom expiration (1 hour = 3600 seconds)
        exp_delta = payload["exp"] - payload["iat"]
        assert abs(exp_delta - 3600) < 5  # Allow 5 second variance

    def test_create_access_token_with_additional_claims(self):
        """Test JWT token creation with additional claims."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(
            data={
                "sub": user_id,
                "email": "test@example.com",
                "is_admin": False
            }
        )

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == user_id
        assert payload["email"] == "test@example.com"
        assert payload["is_admin"] is False

    def test_token_cannot_be_decoded_with_wrong_key(self):
        """Test that token cannot be decoded with wrong secret key."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(data={"sub": user_id})

        with pytest.raises(JWTError):
            jwt.decode(
                token,
                "wrong-secret-key",
                algorithms=[settings.JWT_ALGORITHM]
            )

    def test_token_cannot_be_decoded_with_wrong_algorithm(self):
        """Test that token cannot be decoded with wrong algorithm."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        token = create_access_token(data={"sub": user_id})

        with pytest.raises(JWTError):
            jwt.decode(
                token,
                settings.SECRET_KEY,
                algorithms=["HS512"]  # Wrong algorithm
            )


class TestJWTTokenDecoding:
    """Tests for JWT token decoding and validation."""

    def test_decode_valid_token(self):
        """Test decoding valid JWT token."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "sub": user_id,
            "exp": datetime.now(UTC) + timedelta(days=1),
            "iat": datetime.now(UTC)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        decoded = decode_token(token)

        assert decoded is not None
        assert decoded["sub"] == user_id
        assert "exp" in decoded
        assert "iat" in decoded

    def test_decode_expired_token(self):
        """Test decoding expired token returns None."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "sub": user_id,
            "exp": datetime.now(UTC) - timedelta(days=1),  # Expired yesterday
            "iat": datetime.now(UTC) - timedelta(days=2)
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        decoded = decode_token(token)

        assert decoded is None

    def test_decode_invalid_signature(self):
        """Test decoding token with invalid signature returns None."""
        user_id = "123e4567-e89b-12d3-a456-426614174000"
        payload = {
            "sub": user_id,
            "exp": datetime.now(UTC) + timedelta(days=1),
            "iat": datetime.now(UTC)
        }
        # Sign with wrong secret
        token = jwt.encode(payload, "wrong_secret_key", algorithm=settings.JWT_ALGORITHM)

        decoded = decode_token(token)

        assert decoded is None

    def test_decode_malformed_token(self):
        """Test decoding malformed token returns None."""
        decoded = decode_token("not.a.valid.token")

        assert decoded is None

    def test_decode_token_missing_sub_claim(self):
        """Test decoding token without required 'sub' claim returns None."""
        payload = {
            "exp": datetime.now(UTC) + timedelta(days=1),
            "iat": datetime.now(UTC)
            # Missing 'sub' claim
        }
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        decoded = decode_token(token)

        assert decoded is None
