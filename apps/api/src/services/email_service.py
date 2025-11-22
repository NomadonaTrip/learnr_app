"""
Email service for sending transactional emails via SendGrid.

This service handles all email sending functionality including:
- Password reset emails
- Welcome emails
- Email template rendering
- Error handling and logging
"""

import logging
import os
from pathlib import Path
from typing import Optional

# SendGrid SDK (will be installed via requirements.txt)
try:
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Content, Email, Mail, To
    SENDGRID_AVAILABLE = True
except ImportError:
    SENDGRID_AVAILABLE = False
    logging.warning("SendGrid SDK not installed. Email sending will be mocked.")


logger = logging.getLogger(__name__)


class EmailService:
    """
    Email service for sending transactional emails.

    In development mode (USE_MOCK_EMAIL=true), emails are logged instead of sent.
    """

    def __init__(self):
        self.api_key = os.getenv("SENDGRID_API_KEY")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@learnr.com")
        self.use_mock = os.getenv("USE_MOCK_EMAIL", "false").lower() == "true"

        if not self.use_mock and not SENDGRID_AVAILABLE:
            logger.warning("SendGrid SDK not available. Falling back to mock mode.")
            self.use_mock = True

        if not self.use_mock and not self.api_key:
            logger.error("SENDGRID_API_KEY not set. Email sending will fail.")

        self.client = SendGridAPIClient(self.api_key) if not self.use_mock and SENDGRID_AVAILABLE else None
        self.template_dir = Path(__file__).parent.parent / "templates"

    def _load_template(self, template_name: str) -> str:
        """Load email template from file."""
        template_path = self.template_dir / template_name
        if not template_path.exists():
            logger.error(f"Template not found: {template_path}")
            return ""

        with open(template_path, encoding='utf-8') as f:
            return f.read()

    def _render_template(self, template: str, **kwargs) -> str:
        """Simple template rendering (replace {{variable}} with values)."""
        for key, value in kwargs.items():
            template = template.replace(f"{{{{{key}}}}}", str(value))
        return template

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send an email via SendGrid.

        Args:
            to_email: Recipient email address
            subject: Email subject line
            html_content: HTML email body
            text_content: Plain text fallback (optional)

        Returns:
            bool: True if email sent successfully, False otherwise
        """
        # Mock mode (development/testing)
        if self.use_mock:
            logger.info(f"[MOCK EMAIL] To: {to_email}")
            logger.info(f"[MOCK EMAIL] Subject: {subject}")
            logger.info(f"[MOCK EMAIL] HTML: {html_content[:200]}...")
            return True

        try:
            message = Mail(
                from_email=Email(self.from_email),
                to_emails=To(to_email),
                subject=subject,
                html_content=Content("text/html", html_content)
            )

            if text_content:
                message.add_content(Content("text/plain", text_content))

            response = self.client.send(message)

            if response.status_code in [200, 201, 202]:
                logger.info(f"Email sent successfully to {to_email}")
                return True
            else:
                logger.error(f"Failed to send email to {to_email}. Status: {response.status_code}")
                return False

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            # In production, you might want to:
            # - Send to Sentry
            # - Retry with exponential backoff
            # - Queue for later retry
            return False

    async def send_password_reset_email(
        self,
        to_email: str,
        reset_token: str,
        user_name: Optional[str] = None
    ) -> bool:
        """
        Send password reset email with reset link.

        Args:
            to_email: User's email address
            reset_token: JWT token for password reset (1-hour expiration)
            user_name: User's name (optional, defaults to email)

        Returns:
            bool: True if email sent successfully
        """
        # Generate reset URL
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")
        reset_url = f"{frontend_url}/reset-password?token={reset_token}"

        # Load and render HTML template
        html_template = self._load_template("password_reset.html")
        html_content = self._render_template(
            html_template,
            user_name=user_name or to_email.split('@')[0],
            reset_url=reset_url,
            expiration_hours=1
        )

        # Load and render plain text template
        text_template = self._load_template("password_reset.txt")
        text_content = self._render_template(
            text_template,
            user_name=user_name or to_email.split('@')[0],
            reset_url=reset_url,
            expiration_hours=1
        )

        return await self.send_email(
            to_email=to_email,
            subject="Reset Your LearnR Password",
            html_content=html_content,
            text_content=text_content
        )

    async def send_welcome_email(
        self,
        to_email: str,
        user_name: str
    ) -> bool:
        """
        Send welcome email to new users (optional for MVP).

        Args:
            to_email: User's email address
            user_name: User's name

        Returns:
            bool: True if email sent successfully
        """
        frontend_url = os.getenv("FRONTEND_URL", "http://localhost:5173")

        html_content = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h1 style="color: #0066CC;">Welcome to LearnR!</h1>
                <p>Hi {user_name},</p>
                <p>Thank you for joining LearnR, your AI-powered adaptive learning platform for CBAP exam preparation.</p>
                <h2>What's Next?</h2>
                <ol>
                    <li><strong>Complete Your Diagnostic Assessment</strong> - Get your baseline competency scores</li>
                    <li><strong>Start Your First Quiz Session</strong> - Begin your adaptive learning journey</li>
                    <li><strong>Review Your Progress</strong> - Track your competency growth across all knowledge areas</li>
                </ol>
                <p>
                    <a href="{frontend_url}/dashboard"
                       style="display: inline-block; padding: 12px 24px; background-color: #0066CC; color: white; text-decoration: none; border-radius: 4px;">
                        Go to Dashboard
                    </a>
                </p>
                <p>Good luck with your exam preparation!</p>
                <p>The LearnR Team</p>
            </div>
        </body>
        </html>
        """

        text_content = f"""
        Welcome to LearnR!

        Hi {user_name},

        Thank you for joining LearnR, your AI-powered adaptive learning platform for CBAP exam preparation.

        What's Next?
        1. Complete Your Diagnostic Assessment - Get your baseline competency scores
        2. Start Your First Quiz Session - Begin your adaptive learning journey
        3. Review Your Progress - Track your competency growth across all knowledge areas

        Go to Dashboard: {frontend_url}/dashboard

        Good luck with your exam preparation!

        The LearnR Team
        """

        return await self.send_email(
            to_email=to_email,
            subject="Welcome to LearnR - Start Your CBAP Prep Journey!",
            html_content=html_content,
            text_content=text_content
        )


# Singleton instance
email_service = EmailService()


# Example usage (for testing)
if __name__ == "__main__":
    import asyncio

    async def test():
        # Test password reset email
        success = await email_service.send_password_reset_email(
            to_email="test@example.com",
            reset_token="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            user_name="John Doe"
        )
        print(f"Password reset email sent: {success}")

    asyncio.run(test())
