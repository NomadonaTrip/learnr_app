"""
Sample Unit Test: Email Service

This demonstrates unit testing patterns for services:
- Mocking external dependencies
- Testing service logic
- Verifying method calls
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock


@pytest.mark.unit
@pytest.mark.email
class TestEmailService:
    """Test email service functionality."""

    @pytest.mark.asyncio
    async def test_send_password_reset_email_success(self, mock_email_service):
        """Test sending password reset email."""
        result = await mock_email_service.send_password_reset_email(
            to_email="test@example.com",
            reset_token="fake-token-123",
            user_name="Test User"
        )

        assert result is True

        # Verify email was recorded
        sent_emails = mock_email_service.get_sent_emails()
        assert len(sent_emails) == 1

        email = sent_emails[0]
        assert email["to"] == "test@example.com"
        assert "reset" in email["subject"].lower()
        assert "fake-token-123" in email["html"]

    @pytest.mark.asyncio
    async def test_send_password_reset_email_generates_correct_url(
        self,
        mock_email_service
    ):
        """Test that password reset email contains correct reset URL."""
        reset_token = "test-token-xyz"

        await mock_email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token=reset_token
        )

        sent_emails = mock_email_service.get_sent_emails()
        email = sent_emails[0]

        # Reset URL should contain the token
        assert reset_token in email["html"]

    @pytest.mark.asyncio
    async def test_send_welcome_email_to_new_user(self, mock_email_service):
        """Test sending welcome email to newly registered user."""
        result = await mock_email_service.send_email(
            to_email="newuser@example.com",
            subject="Welcome to LearnR!",
            html_content="<h1>Welcome!</h1>",
            text_content="Welcome!"
        )

        assert result is True

        sent_emails = mock_email_service.get_sent_emails()
        assert len(sent_emails) == 1

        email = sent_emails[0]
        assert email["to"] == "newuser@example.com"
        assert "welcome" in email["subject"].lower()

    @pytest.mark.asyncio
    async def test_email_service_handles_invalid_email(self, mock_email_service):
        """Test email service handles invalid email addresses."""
        # In a real implementation, this might raise an exception
        # For now, we'll test that the mock allows it
        result = await mock_email_service.send_email(
            to_email="not-an-email",
            subject="Test",
            html_content="Test"
        )

        # Mock service allows any email (real service would validate)
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_emails_sent_correctly(self, mock_email_service):
        """Test sending multiple emails."""
        emails_to_send = [
            "user1@example.com",
            "user2@example.com",
            "user3@example.com"
        ]

        for email in emails_to_send:
            await mock_email_service.send_email(
                to_email=email,
                subject="Test",
                html_content="Test content"
            )

        sent_emails = mock_email_service.get_sent_emails()
        assert len(sent_emails) == 3

        sent_addresses = [email["to"] for email in sent_emails]
        assert sent_addresses == emails_to_send

    @pytest.mark.asyncio
    async def test_email_service_clear_functionality(self, mock_email_service):
        """Test clearing sent emails list."""
        # Send an email
        await mock_email_service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="Test"
        )

        assert len(mock_email_service.get_sent_emails()) == 1

        # Clear
        mock_email_service.clear()

        assert len(mock_email_service.get_sent_emails()) == 0


@pytest.mark.unit
@pytest.mark.email
class TestEmailTemplateRendering:
    """Test email template rendering."""

    def test_password_reset_template_renders_username(self):
        """Test that password reset template includes username."""
        # Mock template rendering function
        def render_template(template: str, **kwargs):
            for key, value in kwargs.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            return template

        template = "Hello {{user_name}}, reset your password using this link: {{reset_url}}"

        rendered = render_template(
            template,
            user_name="John Doe",
            reset_url="https://learnr.com/reset?token=abc123"
        )

        assert "John Doe" in rendered
        assert "https://learnr.com/reset?token=abc123" in rendered
        assert "{{" not in rendered  # No unrendered variables

    def test_template_handles_missing_variables_gracefully(self):
        """Test template rendering with missing variables."""
        def render_template(template: str, **kwargs):
            for key, value in kwargs.items():
                template = template.replace(f"{{{{{key}}}}}", str(value))
            return template

        template = "Hello {{user_name}}, your code is {{code}}"

        # Only provide user_name, not code
        rendered = render_template(template, user_name="Jane")

        assert "Jane" in rendered
        # {{code}} remains unrendered (in real implementation, might want to handle this differently)
        assert "{{code}}" in rendered
