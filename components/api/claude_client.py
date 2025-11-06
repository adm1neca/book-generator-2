"""
Claude API Client Module

Provides a clean interface for interacting with the Claude API.
Handles logging, error handling, and token usage tracking.

Design Pattern: Adapter Pattern
Adapts the Anthropic SDK to our application's needs.
"""

from anthropic import Anthropic
from datetime import datetime
from typing import Optional, Callable, Dict, Any
try:
    from .exceptions import (
        ClaudeAPIError,
        ClaudeAPIModelNotFoundError,
        ClaudeAPIConnectionError
    )
except ImportError:
    from exceptions import (
        ClaudeAPIError,
        ClaudeAPIModelNotFoundError,
        ClaudeAPIConnectionError
    )


class ClaudeAPIClient:
    """Adapter for Claude API communication.

    Provides a clean interface to the Anthropic SDK with:
    - Structured logging
    - Error handling with custom exceptions
    - Token usage tracking
    - Console output for user feedback

    Example:
        >>> # Mock usage (actual API call requires API key)
        >>> client = ClaudeAPIClient("sk-ant-test-key", model="claude-3-5-sonnet")
        >>> client.set_logger(lambda msg: None)  # Silent logger
        >>> # response = client.send_message("Hello, Claude!", page_number=1)
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-sonnet",
        max_tokens: int = 768
    ):
        """Initialize Claude API client.

        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-3-5-sonnet)
            max_tokens: Maximum tokens in response (default: 768)
        """
        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self.client = Anthropic(api_key=api_key)
        self.logger: Optional[Callable[[str], None]] = None
        self.detailed_logs: list = []

    def set_logger(self, log_func: Callable[[str], None]):
        """Set logging function.

        Args:
            log_func: Function that takes a string and logs it
        """
        self.logger = log_func

    def send_message(
        self,
        prompt: str,
        page_number: int = 0,
        max_tokens: Optional[int] = None
    ) -> str:
        """Send message to Claude and return response.

        Args:
            prompt: The prompt to send to Claude
            page_number: Page number for logging (default: 0)
            max_tokens: Override default max_tokens (optional)

        Returns:
            Response text from Claude

        Raises:
            ClaudeAPIModelNotFoundError: If model not found or not accessible
            ClaudeAPIConnectionError: If connection to API fails
            ClaudeAPIError: For other API errors

        Side Effects:
            - Prints status to console
            - Logs to logger if set
            - Appends to detailed_logs
        """
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        # Console output
        print(f"\n📤 Calling Claude API for page {page_number}...")

        # Structured logging - Request
        if self.logger:
            self._log_request(prompt, page_number)

        try:
            # API call
            print(f"🤖 Using model: {self.model}")
            message = self.client.messages.create(
                model=self.model,
                max_tokens=tokens,
                messages=[{"role": "user", "content": prompt}]
            )

            # Extract response
            response_text = message.content[0].text
            print(f"✅ Claude API response received for page {page_number}")

            # Token usage tracking
            usage = getattr(message, "usage", None)
            if usage and self.logger:
                input_tokens = getattr(usage, 'input_tokens', 'n/a')
                output_tokens = getattr(usage, 'output_tokens', 'n/a')
                self.logger(f"Token usage - input:{input_tokens} output:{output_tokens}")

            # Structured logging - Response
            if self.logger:
                self._log_response(response_text, page_number)

            # Detailed logs
            self.detailed_logs.append({
                'timestamp': datetime.now().isoformat(),
                'page_number': page_number,
                'prompt': prompt,
                'response': response_text,
                'model': self.model,
                'usage': {
                    'input_tokens': getattr(usage, 'input_tokens', None) if usage else None,
                    'output_tokens': getattr(usage, 'output_tokens', None) if usage else None
                } if usage else None
            })

            return response_text

        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            print(f"❌ ERROR calling Claude API for page {page_number}: {error_msg}")

            # Provide helpful tip for model not found errors
            if "404" in str(e) or "not_found" in str(e):
                print("💡 TIP: Model not found. Try: claude-3-5-sonnet, claude-sonnet-4, or check API key access")
                self._log_error(error_msg, page_number)
                self.detailed_logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'page_number': page_number,
                    'prompt': prompt,
                    'response': f"ERROR: {error_msg}",
                    'error_type': 'model_not_found'
                })
                raise ClaudeAPIModelNotFoundError(error_msg) from e

            # Connection errors
            if "connection" in str(e).lower() or "timeout" in str(e).lower():
                self._log_error(error_msg, page_number)
                self.detailed_logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'page_number': page_number,
                    'prompt': prompt,
                    'response': f"ERROR: {error_msg}",
                    'error_type': 'connection'
                })
                raise ClaudeAPIConnectionError(error_msg) from e

            # Generic API error
            self._log_error(error_msg, page_number)
            self.detailed_logs.append({
                'timestamp': datetime.now().isoformat(),
                'page_number': page_number,
                'prompt': prompt,
                'response': f"ERROR: {error_msg}",
                'error_type': 'generic'
            })
            raise ClaudeAPIError(error_msg) from e

    def _log_request(self, prompt: str, page_number: int):
        """Log API request."""
        if self.logger:
            self.logger(f"\n{'='*60}")
            self.logger(f"📤 SENDING TO CLAUDE (Page {page_number})")
            self.logger(f"{'='*60}")
            self.logger(f"PROMPT:\n{prompt}")
            self.logger(f"{'='*60}\n")

    def _log_response(self, response: str, page_number: int):
        """Log API response."""
        if self.logger:
            self.logger(f"\n{'='*60}")
            self.logger(f"📥 RECEIVED FROM CLAUDE (Page {page_number})")
            self.logger(f"{'='*60}")
            self.logger(f"RESPONSE:\n{response}")
            self.logger(f"{'='*60}\n")

    def _log_error(self, error_msg: str, page_number: int):
        """Log API error."""
        if self.logger:
            self.logger(f"\n{'='*60}")
            self.logger(f"❌ ERROR calling Claude (Page {page_number})")
            self.logger(f"{'='*60}")
            self.logger(f"Error: {error_msg}")
            self.logger(f"{'='*60}\n")

    def get_detailed_logs(self) -> list:
        """Get detailed logs of all API calls.

        Returns:
            List of log entries with timestamp, prompt, response, etc.
        """
        return self.detailed_logs.copy()

    def clear_logs(self):
        """Clear detailed logs."""
        self.detailed_logs.clear()


if __name__ == "__main__":
    print("✅ ClaudeAPIClient module loaded successfully!")
    print("\nTo test with real API:")
    print('  client = ClaudeAPIClient("your-api-key")')
    print('  response = client.send_message("Hello!")')
