"""
API Module

Provides clean interfaces for Claude API interaction with:
- Structured API communication (ClaudeAPIClient)
- Response parsing and validation (ResponseParser)
- Retry logic with exponential backoff (RetryHandler)
- Custom exceptions for error handling

Design Patterns:
- Adapter Pattern: ClaudeAPIClient adapts Anthropic SDK
- Strategy Pattern: Flexible retry strategies
- Single Responsibility: Each class has one clear purpose

Example Usage:
    from components.api import ClaudeAPIClient, ResponseParser, RetryHandler

    # Create client
    client = ClaudeAPIClient(api_key="your-key")
    client.set_logger(print)

    # Create retry handler
    retry_handler = RetryHandler(base_delay=0.5)

    # Make API call with retry
    api_call = lambda: client.send_message("Hello!", page_number=1)
    parsed, raw = retry_handler.call_with_retry(api_call, retries=3)

    if parsed:
        print("Success:", parsed)
    else:
        print("Failed after retries")
"""

from .claude_client import ClaudeAPIClient
from .response_parser import ResponseParser
from .retry_handler import RetryHandler
from .exceptions import (
    ClaudeAPIError,
    ClaudeAPIConnectionError,
    ClaudeAPIResponseError,
    ClaudeAPIParseError,
    ClaudeAPIModelNotFoundError,
    ClaudeAPIRetryExhaustedError
)

__all__ = [
    # Main classes
    'ClaudeAPIClient',
    'ResponseParser',
    'RetryHandler',

    # Exceptions
    'ClaudeAPIError',
    'ClaudeAPIConnectionError',
    'ClaudeAPIResponseError',
    'ClaudeAPIParseError',
    'ClaudeAPIModelNotFoundError',
    'ClaudeAPIRetryExhaustedError',
]

# Version info
__version__ = '1.0.0'
__author__ = 'Book Generator Team'
__description__ = 'Claude API client with retry and parsing capabilities'
