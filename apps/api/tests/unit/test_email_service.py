"""
Unit tests for Email Service.

Tests the EmailService class including:
- Mock mode email sending
- Template loading and rendering
- Password reset emails
- Welcome emails
"""

import os
from unittest.mock import AsyncMock, patch

import pytest


class TestEmailServiceInit:
    """Tests for EmailService initialization."""

    def test_init_with_mock_mode_enabled(self):
        """Test EmailService initializes in mock mode when USE_MOCK_EMAIL=true."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()
            assert service.use_mock is True
            assert service.client is None

    def test_init_uses_default_from_email(self):
        """Test EmailService uses default from_email when not set."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true", "FROM_EMAIL": ""}, clear=False):
            # Clear FROM_EMAIL to test default
            env = os.environ.copy()
            env.pop("FROM_EMAIL", None)
            with patch.dict(os.environ, env, clear=True):
                with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
                    from src.services.email_service import EmailService
                    service = EmailService()
                    assert service.from_email == "noreply@learnr.com"

    def test_init_uses_custom_from_email(self):
        """Test EmailService uses custom FROM_EMAIL when set."""
        with patch.dict(os.environ, {
            "USE_MOCK_EMAIL": "true",
            "FROM_EMAIL": "custom@learnr.com"
        }):
            from src.services.email_service import EmailService
            service = EmailService()
            assert service.from_email == "custom@learnr.com"


class TestEmailServiceTemplates:
    """Tests for template loading and rendering."""

    def test_render_template_replaces_variables(self):
        """Test _render_template replaces {{variable}} placeholders."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            template = "Hello {{name}}, your token is {{token}}."
            result = service._render_template(template, name="John", token="abc123")

            assert result == "Hello John, your token is abc123."

    def test_render_template_handles_missing_variables(self):
        """Test _render_template leaves unmatched placeholders."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            template = "Hello {{name}}, your code is {{code}}."
            result = service._render_template(template, name="Jane")

            assert "Jane" in result
            assert "{{code}}" in result

    def test_render_template_converts_non_string_values(self):
        """Test _render_template converts non-string values to strings."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            template = "Count: {{count}}, Active: {{active}}"
            result = service._render_template(template, count=42, active=True)

            assert "42" in result
            assert "True" in result

    def test_load_template_returns_empty_for_missing_file(self):
        """Test _load_template returns empty string for missing template."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            result = service._load_template("nonexistent_template.html")
            assert result == ""

    def test_load_template_reads_existing_file(self):
        """Test _load_template reads existing template file."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            # Create a temporary template
            template_dir = service.template_dir
            template_dir.mkdir(parents=True, exist_ok=True)
            test_template = template_dir / "test_template.html"
            test_template.write_text("<html>Test Content</html>")

            try:
                result = service._load_template("test_template.html")
                assert result == "<html>Test Content</html>"
            finally:
                test_template.unlink()


@pytest.mark.asyncio
class TestEmailServiceSendEmail:
    """Tests for send_email method."""

    async def test_send_email_mock_mode_returns_true(self):
        """Test send_email returns True in mock mode."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            result = await service.send_email(
                to_email="test@example.com",
                subject="Test Subject",
                html_content="<p>Test</p>"
            )

            assert result is True

    async def test_send_email_mock_mode_logs_email(self):
        """Test send_email logs email details in mock mode."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            with patch("src.services.email_service.logger") as mock_logger:
                await service.send_email(
                    to_email="user@example.com",
                    subject="Test Subject",
                    html_content="<p>Content</p>"
                )

                # Verify logging was called
                assert mock_logger.info.call_count >= 1


@pytest.mark.asyncio
class TestEmailServicePasswordReset:
    """Tests for password reset email functionality."""

    async def test_send_password_reset_email_success(self):
        """Test sending password reset email in mock mode."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true", "FRONTEND_URL": "http://localhost:5173"}):
            from src.services.email_service import EmailService
            service = EmailService()

            # Mock template loading
            with patch.object(service, '_load_template', return_value="Reset: {{reset_url}}"):
                result = await service.send_password_reset_email(
                    to_email="user@example.com",
                    reset_token="test-token-123",
                    user_name="Test User"
                )

                assert result is True

    async def test_send_password_reset_email_generates_correct_url(self):
        """Test password reset email contains correct reset URL."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true", "FRONTEND_URL": "https://app.learnr.com"}):
            from src.services.email_service import EmailService
            service = EmailService()

            reset_token = "my-secret-token"

            with patch.object(service, '_load_template', return_value="{{reset_url}}"):
                with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
                    mock_send.return_value = True

                    await service.send_password_reset_email(
                        to_email="user@example.com",
                        reset_token=reset_token
                    )

                    # Check that send_email was called with URL containing token
                    call_args = mock_send.call_args
                    html_content = call_args.kwargs.get('html_content', call_args[1].get('html_content', ''))
                    assert reset_token in html_content

    async def test_send_password_reset_uses_email_prefix_when_no_name(self):
        """Test password reset uses email prefix when user_name is None."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            with patch.object(service, '_load_template', return_value="Hello {{user_name}}"):
                with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
                    mock_send.return_value = True

                    await service.send_password_reset_email(
                        to_email="johndoe@example.com",
                        reset_token="token123",
                        user_name=None  # No name provided
                    )

                    call_args = mock_send.call_args
                    html_content = call_args.kwargs.get('html_content', call_args[1].get('html_content', ''))
                    assert "johndoe" in html_content


@pytest.mark.asyncio
class TestEmailServiceWelcomeEmail:
    """Tests for welcome email functionality."""

    async def test_send_welcome_email_success(self):
        """Test sending welcome email in mock mode."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true", "FRONTEND_URL": "http://localhost:5173"}):
            from src.services.email_service import EmailService
            service = EmailService()

            result = await service.send_welcome_email(
                to_email="newuser@example.com",
                user_name="New User"
            )

            assert result is True

    async def test_send_welcome_email_contains_user_name(self):
        """Test welcome email contains user's name."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true", "FRONTEND_URL": "http://localhost:5173"}):
            from src.services.email_service import EmailService
            service = EmailService()

            with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = True

                await service.send_welcome_email(
                    to_email="jane@example.com",
                    user_name="Jane Doe"
                )

                call_args = mock_send.call_args
                html_content = call_args.kwargs.get('html_content', call_args[1].get('html_content', ''))
                text_content = call_args.kwargs.get('text_content', call_args[1].get('text_content', ''))

                assert "Jane Doe" in html_content
                assert "Jane Doe" in text_content

    async def test_send_welcome_email_contains_dashboard_link(self):
        """Test welcome email contains dashboard link."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true", "FRONTEND_URL": "https://app.learnr.com"}):
            from src.services.email_service import EmailService
            service = EmailService()

            with patch.object(service, 'send_email', new_callable=AsyncMock) as mock_send:
                mock_send.return_value = True

                await service.send_welcome_email(
                    to_email="user@example.com",
                    user_name="User"
                )

                call_args = mock_send.call_args
                html_content = call_args.kwargs.get('html_content', call_args[1].get('html_content', ''))

                assert "https://app.learnr.com/dashboard" in html_content


@pytest.mark.unit
@pytest.mark.email
class TestMockEmailServiceFixture:
    """Test the mock_email_service fixture functionality."""

    @pytest.mark.asyncio
    async def test_mock_service_send_email(self, mock_email_service):
        """Test mock service records sent emails."""
        result = await mock_email_service.send_email(
            to_email="test@example.com",
            subject="Test Subject",
            html_content="<p>Test</p>",
            text_content="Test"
        )

        assert result is True
        sent = mock_email_service.get_sent_emails()
        assert len(sent) == 1
        assert sent[0]["to"] == "test@example.com"

    @pytest.mark.asyncio
    async def test_mock_service_password_reset(self, mock_email_service):
        """Test mock service handles password reset email."""
        result = await mock_email_service.send_password_reset_email(
            to_email="user@example.com",
            reset_token="token123",
            user_name="Test User"
        )

        assert result is True
        sent = mock_email_service.get_sent_emails()
        assert len(sent) == 1
        assert "token123" in sent[0]["html"]

    @pytest.mark.asyncio
    async def test_mock_service_clear(self, mock_email_service):
        """Test mock service clear functionality."""
        await mock_email_service.send_email(
            to_email="test@example.com",
            subject="Test",
            html_content="Test"
        )

        assert len(mock_email_service.get_sent_emails()) == 1

        mock_email_service.clear()

        assert len(mock_email_service.get_sent_emails()) == 0

    @pytest.mark.asyncio
    async def test_mock_service_multiple_emails(self, mock_email_service):
        """Test mock service tracks multiple emails."""
        emails = ["a@test.com", "b@test.com", "c@test.com"]

        for email in emails:
            await mock_email_service.send_email(
                to_email=email,
                subject="Test",
                html_content="Content"
            )

        sent = mock_email_service.get_sent_emails()
        assert len(sent) == 3
        assert [e["to"] for e in sent] == emails


@pytest.mark.unit
@pytest.mark.email
class TestEmailTemplateRendering:
    """Test email template rendering patterns."""

    def test_password_reset_template_renders_all_variables(self):
        """Test password reset template rendering."""
        with patch.dict(os.environ, {"USE_MOCK_EMAIL": "true"}):
            from src.services.email_service import EmailService
            service = EmailService()

            template = "Hello {{user_name}}, click {{reset_url}} (expires in {{expiration_hours}} hours)"

            rendered = service._render_template(
                template,
                user_name="John Doe",
                reset_url="https://example.com/reset?token=abc",
                expiration_hours=1
            )

            assert "John Doe" in rendered
            assert "https://example.com/reset?token=abc" in rendered
            assert "1 hours" in rendered
            assert "{{" not in rendered
