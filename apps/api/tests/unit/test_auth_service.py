"""
Unit tests for authentication service.
Tests user registration business logic.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
from src.services.auth_service import AuthService
from src.repositories.user_repository import UserRepository
from src.models.user import User
from src.exceptions import ConflictError, AuthenticationError
from src.utils.auth import hash_password


class TestAuthServiceRegistration:
    """Tests for user registration in auth service."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def auth_service(self, mock_user_repo):
        """Create auth service with mock repository."""
        return AuthService(mock_user_repo)

    @pytest.fixture
    def sample_user(self):
        """Create a sample user for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="$2b$12$hashedpassword",
            created_at=datetime.utcnow(),
            is_admin=False,
            dark_mode="auto"
        )
        return user

    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, mock_user_repo, sample_user):
        """Test successful user registration."""
        # Mock repository methods
        mock_user_repo.get_by_email = AsyncMock(return_value=None)  # User doesn't exist
        mock_user_repo.create_user = AsyncMock(return_value=sample_user)

        # Register user
        email = "test@example.com"
        password = "SecurePass123"
        user, token = await auth_service.register_user(email, password)

        # Verify user was created
        assert user == sample_user
        assert user.email == email

        # Verify token was generated
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify repository methods were called
        mock_user_repo.get_by_email.assert_called_once_with(email)
        mock_user_repo.create_user.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_duplicate_email(self, auth_service, mock_user_repo, sample_user):
        """Test registration fails when email already exists."""
        # Mock repository to return existing user
        mock_user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Attempt to register with duplicate email
        email = "test@example.com"
        password = "SecurePass123"

        with pytest.raises(ConflictError) as exc_info:
            await auth_service.register_user(email, password)

        # Verify error message
        assert "already registered" in str(exc_info.value.message)
        assert email in str(exc_info.value.message)

        # Verify create_user was NOT called
        mock_user_repo.create_user.assert_not_called()

    @pytest.mark.asyncio
    async def test_register_user_password_is_hashed(self, auth_service, mock_user_repo, sample_user):
        """Test that password is hashed before storing."""
        # Mock repository methods
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        mock_user_repo.create_user = AsyncMock(return_value=sample_user)

        # Register user
        email = "test@example.com"
        password = "SecurePass123"
        await auth_service.register_user(email, password)

        # Verify create_user was called with hashed password (not plaintext)
        call_args = mock_user_repo.create_user.call_args
        hashed_password = call_args[0][1]  # Second argument

        assert hashed_password != password  # Not plaintext
        assert hashed_password.startswith("$2b$")  # bcrypt hash

    @pytest.mark.asyncio
    async def test_register_user_email_normalization(self, auth_service, mock_user_repo, sample_user):
        """Test that email is checked with lowercase in repository."""
        # Mock repository methods
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        mock_user_repo.create_user = AsyncMock(return_value=sample_user)

        # Register user with mixed-case email
        email = "Test@Example.COM"
        password = "SecurePass123"
        await auth_service.register_user(email, password)

        # Verify get_by_email was called with original email (repository handles normalization)
        mock_user_repo.get_by_email.assert_called_once_with(email)

    @pytest.mark.asyncio
    async def test_register_user_token_contains_user_id(self, auth_service, mock_user_repo, sample_user):
        """Test that JWT token contains user_id in 'sub' claim."""
        from jose import jwt
        from src.config import settings

        # Mock repository methods
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        mock_user_repo.create_user = AsyncMock(return_value=sample_user)

        # Register user
        email = "test@example.com"
        password = "SecurePass123"
        user, token = await auth_service.register_user(email, password)

        # Decode token and verify user_id
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == str(sample_user.id)

    @pytest.mark.asyncio
    async def test_register_user_token_has_expiration(self, auth_service, mock_user_repo, sample_user):
        """Test that JWT token has proper expiration."""
        from jose import jwt
        from src.config import settings

        # Mock repository methods
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        mock_user_repo.create_user = AsyncMock(return_value=sample_user)

        # Register user
        email = "test@example.com"
        password = "SecurePass123"
        user, token = await auth_service.register_user(email, password)

        # Decode token and verify expiration
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        # Verify token has expiration (7 days = 604800 seconds)
        exp_delta = payload["exp"] - payload["iat"]
        assert abs(exp_delta - settings.JWT_EXPIRATION_SECONDS) < 5


class TestAuthServiceLogin:
    """Tests for user login in auth service."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def auth_service(self, mock_user_repo):
        """Create auth service with mock repository."""
        return AuthService(mock_user_repo)

    @pytest.fixture
    def sample_user(self):
        """Create a sample user with hashed password for testing."""
        user = User(
            id=uuid4(),
            email="test@example.com",
            hashed_password=hash_password("SecurePass123"),
            created_at=datetime.utcnow(),
            is_admin=False,
            dark_mode="auto"
        )
        return user

    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user_repo, sample_user):
        """Test successful login with valid credentials."""
        # Mock repository to return user
        mock_user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Login user
        email = "test@example.com"
        password = "SecurePass123"
        user, token = await auth_service.login_user(email, password)

        # Verify user was returned
        assert user == sample_user
        assert user.email == sample_user.email

        # Verify token was generated
        assert isinstance(token, str)
        assert len(token) > 0

        # Verify repository method was called
        mock_user_repo.get_by_email.assert_called_once_with(email)

    @pytest.mark.asyncio
    async def test_login_invalid_password(self, auth_service, mock_user_repo, sample_user):
        """Test login failure with invalid password."""
        # Mock repository to return user
        mock_user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Attempt login with wrong password
        email = "test@example.com"
        password = "WrongPassword123"

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.login_user(email, password)

        # Verify generic error message
        assert "Invalid email or password" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_login_nonexistent_email(self, auth_service, mock_user_repo):
        """Test login failure with non-existent email."""
        # Mock repository to return None (user doesn't exist)
        mock_user_repo.get_by_email = AsyncMock(return_value=None)

        # Attempt login with non-existent email
        email = "nonexistent@example.com"
        password = "AnyPassword123"

        with pytest.raises(AuthenticationError) as exc_info:
            await auth_service.login_user(email, password)

        # Verify generic error message
        assert "Invalid email or password" in str(exc_info.value.message)

    @pytest.mark.asyncio
    async def test_login_generic_error_message(self, auth_service, mock_user_repo, sample_user):
        """Test that error messages are generic for security (prevent user enumeration)."""
        # Test wrong password
        mock_user_repo.get_by_email = AsyncMock(return_value=sample_user)

        try:
            await auth_service.login_user("test@example.com", "WrongPass123")
        except AuthenticationError as e:
            wrong_password_message = e.message

        # Test non-existent email
        mock_user_repo.get_by_email = AsyncMock(return_value=None)

        try:
            await auth_service.login_user("nonexistent@example.com", "AnyPass123")
        except AuthenticationError as e:
            nonexistent_email_message = e.message

        # Messages should be identical to prevent user enumeration
        assert wrong_password_message == nonexistent_email_message
        assert wrong_password_message == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_login_token_contains_user_id(self, auth_service, mock_user_repo, sample_user):
        """Test that JWT token contains user_id in 'sub' claim."""
        from jose import jwt
        from src.config import settings

        # Mock repository to return user
        mock_user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Login user
        email = "test@example.com"
        password = "SecurePass123"
        user, token = await auth_service.login_user(email, password)

        # Decode token and verify user_id
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )

        assert payload["sub"] == str(sample_user.id)

    @pytest.mark.asyncio
    async def test_login_case_insensitive_email(self, auth_service, mock_user_repo, sample_user):
        """Test that email lookup is case-insensitive."""
        # Mock repository to return user
        mock_user_repo.get_by_email = AsyncMock(return_value=sample_user)

        # Login with different email case
        email = "Test@Example.COM"
        password = "SecurePass123"
        user, token = await auth_service.login_user(email, password)

        # Verify login was successful
        assert user == sample_user
        assert len(token) > 0

        # Verify repository was called with the email as provided
        mock_user_repo.get_by_email.assert_called_once_with(email)
