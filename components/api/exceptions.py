"""
API Exceptions Module

Custom exception classes for Claude API interactions.
Provides specific exception types for different error scenarios.
"""


class ClaudeAPIError(Exception):
    """Base exception for Claude API errors."""
    pass


class ClaudeAPIConnectionError(ClaudeAPIError):
    """Raised when connection to Claude API fails."""
    pass


class ClaudeAPIResponseError(ClaudeAPIError):
    """Raised when Claude API returns an error response."""
    pass


class ClaudeAPIParseError(ClaudeAPIError):
    """Raised when response parsing fails after retries."""
    pass


class ClaudeAPIModelNotFoundError(ClaudeAPIError):
    """Raised when specified model is not found or not accessible."""
    pass


class ClaudeAPIRetryExhaustedError(ClaudeAPIError):
    """Raised when all retry attempts have been exhausted."""
    pass
