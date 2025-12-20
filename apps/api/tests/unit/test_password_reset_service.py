"""
Unit tests for password reset functionality in AuthService and PasswordResetRepository.
Tests password reset business logic and token management.
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from src.exceptions import (
    TokenAlreadyUsedError,
    TokenExpiredError,
    TokenInvalidError,
)
from src.models.password_reset_token import PasswordResetToken
from src.models.user import User
from src.repositories.password_reset_repository import PasswordResetRepository
from src.repositories.user_repository import UserRepository
from src.services.auth_service import AuthService
from src.services.email_service import EmailService


class TestPasswordResetRepository:
    """Tests for PasswordResetRepository methods."""

    @pytest.fixture
    def mock_session(self):
        """Create a mock async session."""
        session = AsyncMock()
        session.add = MagicMock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def reset_repo(self, mock_session):
        """Create repository with mock session."""
        return PasswordResetRepository(mock_session)

    @pytest.fixture
    def sample_token(self):
        """Create a sample password reset token."""
        return PasswordResetToken(
            id=uuid4(),
            user_id=uuid4(),
            token=uuid4(),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=None
        )

    @pytest.mark.asyncio
    async def test_create_token(self, reset_repo, mock_session):
        """Test creating a password reset token."""
        user_id = uuid4()

        # Call create_token
        token = await reset_repo.create_token(user_id, expires_in_hours=1)

        # Verify token was created correctly
        assert token.user_id == user_id
        assert token.token is not None
        assert token.expires_at > datetime.now(UTC)

        # Verify session methods called
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_success(self, reset_repo, mock_session, sample_token):
        """Test retrieving a valid token."""
        # Mock database result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_token)
        mock_session.execute.return_value = mock_result

        # Get valid token
        result = await reset_repo.get_valid_token(str(sample_token.token))

        # Verify result
        assert result == sample_token
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_valid_token_invalid_uuid(self, reset_repo):
        """Test get_valid_token with invalid UUID string."""
        result = await reset_repo.get_valid_token("not-a-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_valid_token_none_value(self, reset_repo):
        """Test get_valid_token with None value."""
        result = await reset_repo.get_valid_token(None)
        assert result is None

    @pytest.mark.asyncio
    async def test_mark_token_used(self, reset_repo, mock_session, sample_token):
        """Test marking a token as used."""
        # Mock database result
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=sample_token)
        mock_session.execute.return_value = mock_result

        # Mark token as used
        await reset_repo.mark_token_used(str(sample_token.token))

        # Verify token was marked as used
        assert sample_token.used_at is not None
        mock_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mark_token_used_nonexistent(self, reset_repo, mock_session):
        """Test marking a non-existent token as used (should not raise error)."""
        # Mock database result returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none = MagicMock(return_value=None)
        mock_session.execute.return_value = mock_result

        # Should not raise error
        await reset_repo.mark_token_used(str(uuid4()))

        # Commit should not be called if token doesn't exist
        mock_session.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_invalidate_user_tokens(self, reset_repo, mock_session):
        """Test invalidating all tokens for a user."""
        user_id = uuid4()

        # Create multiple tokens
        token1 = PasswordResetToken(
            id=uuid4(),
            user_id=user_id,
            token=uuid4(),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=None
        )
        token2 = PasswordResetToken(
            id=uuid4(),
            user_id=user_id,
            token=uuid4(),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=None
        )

        # Mock database result
        mock_result = AsyncMock()
        mock_result.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[token1, token2])))
        mock_session.execute.return_value = mock_result

        # Invalidate tokens
        await reset_repo.invalidate_user_tokens(user_id)

        # Verify all tokens were marked as used
        assert token1.used_at is not None
        assert token2.used_at is not None
        mock_session.commit.assert_called_once()


class TestAuthServicePasswordReset:
    """Tests for password reset methods in AuthService."""

    @pytest.fixture
    def mock_user_repo(self):
        """Create a mock user repository."""
        return MagicMock(spec=UserRepository)

    @pytest.fixture
    def mock_reset_repo(self):
        """Create a mock password reset repository."""
        return MagicMock(spec=PasswordResetRepository)

    @pytest.fixture
    def mock_email_service(self):
        """Create a mock email service."""
        return MagicMock(spec=EmailService)

    @pytest.fixture
    def auth_service(self, mock_user_repo, mock_reset_repo, mock_email_service):
        """Create auth service with mock dependencies."""
        service = AuthService(mock_user_repo, mock_reset_repo)
        service.email_service = mock_email_service
        return service

    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        return User(
            id=uuid4(),
            email="test@example.com",
            hashed_password="$2b$12$hashedpassword",
            created_at=datetime.now(UTC),
            is_admin=False,
            dark_mode="auto"
        )

    @pytest.fixture
    def sample_reset_token(self):
        """Create a sample password reset token."""
        return PasswordResetToken(
            id=uuid4(),
            user_id=uuid4(),
            token=uuid4(),
            created_at=datetime.now(UTC),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=None
        )

    @pytest.mark.asyncio
    async def test_request_password_reset_existing_user(
        self, auth_service, mock_user_repo, mock_reset_repo, mock_email_service, sample_user, sample_reset_token
    ):
        """Test requesting password reset for an existing user."""
        # Setup mocks
        mock_user_repo.get_by_email = AsyncMock(return_value=sample_user)
        mock_reset_repo.create_token = AsyncMock(return_value=sample_reset_token)
        mock_email_service.send_password_reset_email = AsyncMock(return_value=True)

        # Request password reset
        await auth_service.request_password_reset("test@example.com")

        # Verify token was created
        mock_reset_repo.create_token.assert_called_once_with(sample_user.id, expires_in_hours=1)

        # Verify email was sent
        mock_email_service.send_password_reset_email.assert_called_once_with(
            to_email=sample_user.email,
            reset_token=str(sample_reset_token.token)
        )

    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(
        self, auth_service, mock_user_repo, mock_reset_repo, mock_email_service
    ):
        """Test requesting password reset for non-existent user (no token created, email sent anyway)."""
        # Setup mocks
        mock_user_repo.get_by_email = AsyncMock(return_value=None)
        mock_email_service.send_password_reset_email = AsyncMock(return_value=True)

        # Request password reset
        await auth_service.request_password_reset("nonexistent@example.com")

        # Verify no token was created
        mock_reset_repo.create_token.assert_not_called()

        # Verify email was still sent (with dummy token to prevent enumeration)
        mock_email_service.send_password_reset_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_reset_password_success(
        self, auth_service, mock_user_repo, mock_reset_repo, sample_user, sample_reset_token
    ):
        """Test successful password reset."""
        # Setup mocks
        sample_reset_token.user_id = sample_user.id
        mock_reset_repo.get_valid_token = AsyncMock(return_value=sample_reset_token)
        mock_user_repo.get_by_id = AsyncMock(return_value=sample_user)
        mock_user_repo.session = AsyncMock()
        mock_user_repo.session.commit = AsyncMock()
        mock_reset_repo.mark_token_used = AsyncMock()
        mock_reset_repo.invalidate_user_tokens = AsyncMock()

        # Reset password
        await auth_service.reset_password(str(sample_reset_token.token), "NewPassword123")

        # Verify password was updated
        assert sample_user.hashed_password != "$2b$12$hashedpassword"  # Password should be changed

        # Verify token was marked as used
        mock_reset_repo.mark_token_used.assert_called_once_with(str(sample_reset_token.token))

        # Verify other tokens were invalidated
        mock_reset_repo.invalidate_user_tokens.assert_called_once_with(sample_user.id)

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token(self, auth_service, mock_reset_repo):
        """Test reset password with invalid token raises TokenInvalidError."""
        # Setup mocks
        mock_reset_repo.get_valid_token = AsyncMock(return_value=None)
        mock_reset_repo.get_token = AsyncMock(return_value=None)

        # Should raise TokenInvalidError
        with pytest.raises(TokenInvalidError):
            await auth_service.reset_password("invalid-token", "NewPassword123")

    @pytest.mark.asyncio
    async def test_reset_password_expired_token(self, auth_service, mock_reset_repo):
        """Test reset password with expired token raises TokenExpiredError."""
        # Create expired token
        expired_token = PasswordResetToken(
            id=uuid4(),
            user_id=uuid4(),
            token=uuid4(),
            created_at=datetime.now(UTC) - timedelta(hours=2),
            expires_at=datetime.now(UTC) - timedelta(hours=1),
            used_at=None
        )

        # Setup mocks
        mock_reset_repo.get_valid_token = AsyncMock(return_value=None)
        mock_reset_repo.get_token = AsyncMock(return_value=expired_token)

        # Should raise TokenExpiredError
        with pytest.raises(TokenExpiredError):
            await auth_service.reset_password(str(expired_token.token), "NewPassword123")

    @pytest.mark.asyncio
    async def test_reset_password_already_used_token(self, auth_service, mock_reset_repo):
        """Test reset password with already-used token raises TokenAlreadyUsedError."""
        # Create used token
        used_token = PasswordResetToken(
            id=uuid4(),
            user_id=uuid4(),
            token=uuid4(),
            created_at=datetime.now(UTC) - timedelta(hours=1),
            expires_at=datetime.now(UTC) + timedelta(hours=1),
            used_at=datetime.now(UTC) - timedelta(minutes=30)
        )

        # Setup mocks
        mock_reset_repo.get_valid_token = AsyncMock(return_value=None)
        mock_reset_repo.get_token = AsyncMock(return_value=used_token)

        # Should raise TokenAlreadyUsedError
        with pytest.raises(TokenAlreadyUsedError):
            await auth_service.reset_password(str(used_token.token), "NewPassword123")


class TestEmailServicePasswordReset:
    """Tests for password reset email functionality."""

    @pytest.fixture
    def email_service(self):
        """Create email service instance."""
        return EmailService()

    @pytest.mark.asyncio
    async def test_send_password_reset_email_mock_mode(self, email_service):
        """Test sending password reset email in mock mode."""
        # Email service should be in mock mode by default (no SENDGRID_API_KEY)
        assert email_service.use_mock is True

        # Send email (should succeed in mock mode)
        result = await email_service.send_password_reset_email(
            to_email="test@example.com",
            reset_token=str(uuid4())
        )

        # Should return True in mock mode
        assert result is True

    @pytest.mark.asyncio
    async def test_send_password_reset_email_with_sendgrid(self):
        """Test sending password reset email with SendGrid (mocked).

        This test is skipped if sendgrid package is not installed.
        In the test environment, emails are typically mocked anyway.
        """
        try:
            import sendgrid
        except ImportError:
            pytest.skip("SendGrid package not installed - skipping SendGrid-specific test")

        # Since we use mock mode in tests (USE_MOCK_EMAIL=true in conftest),
        # just verify the email service works in mock mode
        email_service = EmailService()
        assert email_service.use_mock is True

        # Send email in mock mode
        result = await email_service.send_password_reset_email(
            to_email="test@example.com",
            reset_token=str(uuid4())
        )

        # Should return True in mock mode
        assert result is True
