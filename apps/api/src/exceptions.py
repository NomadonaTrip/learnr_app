"""
Custom exception classes for the LearnR API.
"""


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


class ConflictError(AppException):
    """Raised when resource conflict occurs (409)."""
    pass


class ValidationError(AppException):
    """Raised when validation fails (400)."""
    pass


class DatabaseError(AppException):
    """Raised when database operation fails (500)."""
    pass


class AuthenticationError(AppException):
    """Raised when authentication fails (401)."""
    pass


class AuthorizationError(AppException):
    """Raised when authorization fails (403)."""
    pass


class NotFoundError(AppException):
    """Raised when resource is not found (404)."""
    pass


class RateLimitError(AppException):
    """Raised when rate limit is exceeded (429)."""

    def __init__(self, message: str, retry_after_seconds: int):
        super().__init__(message, {"retry_after_seconds": retry_after_seconds})
        self.retry_after_seconds = retry_after_seconds


class TokenExpiredError(AppException):
    """Raised when token has expired (400)."""
    pass


class TokenInvalidError(AppException):
    """Raised when token is invalid (400)."""
    pass


class TokenAlreadyUsedError(AppException):
    """Raised when token has already been used (400)."""
    pass


class BeliefInitializationError(AppException):
    """Raised when belief state initialization fails (500)."""
    pass


# Story 4.3: Answer Submission and Immediate Feedback


class InvalidSessionError(AppException):
    """Raised when session is invalid, expired, or not found (404)."""
    pass


class InvalidQuestionError(AppException):
    """Raised when question is not found or inactive (404)."""
    pass


class AlreadyAnsweredError(AppException):
    """Raised when question has already been answered in this session (409)."""
    pass
