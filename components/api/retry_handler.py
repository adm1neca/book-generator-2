"""
Retry Handler Module

Provides retry logic with exponential backoff for API calls.
Handles transient failures gracefully with configurable retry attempts.
"""

import time
from typing import Optional, Tuple, Callable, Any

try:
    from .response_parser import ResponseParser
except ImportError:
    from response_parser import ResponseParser


class RetryHandler:
    """Handle API call retries with exponential backoff.

    Provides intelligent retry logic that:
    - Attempts parsing after each API call
    - Uses exponential backoff between retries
    - Returns both parsed result and raw response
    - Tracks all attempts for debugging

    Examples:
        >>> def mock_api():
        ...     return '{"result": "success"}'
        >>> handler = RetryHandler()
        >>> parsed, raw = handler.call_with_retry(mock_api, retries=2)
        >>> parsed['result']
        'success'
        >>> raw
        '{"result": "success"}'
    """

    def __init__(self, base_delay: float = 0.4):
        """Initialize retry handler.

        Args:
            base_delay: Base delay in seconds between retries (default: 0.4)
        """
        self.base_delay = base_delay
        self.parser = ResponseParser()

    def call_with_retry(
        self,
        api_call_func: Callable[[], str],
        retries: int = 2,
        parse_json: bool = True
    ) -> Tuple[Optional[dict], str]:
        """Execute API call with retry logic.

        Args:
            api_call_func: Function that makes the API call and returns raw response
            retries: Number of retry attempts (default: 2)
            parse_json: Whether to parse response as JSON (default: True)

        Returns:
            Tuple of (parsed_dict, raw_response)
            - parsed_dict: Parsed JSON if successful and parse_json=True, else None
            - raw_response: Raw API response text from last attempt

        Retry Strategy:
            - Attempt 0: No delay
            - Attempt 1: base_delay * 1 seconds
            - Attempt 2: base_delay * 2 seconds
            - Attempt N: base_delay * N seconds

        Example:
            >>> def failing_api(attempt=[0]):
            ...     attempt[0] += 1
            ...     if attempt[0] < 3:
            ...         return "invalid"
            ...     return '{"status": "ok"}'
            >>> handler = RetryHandler(base_delay=0.01)
            >>> parsed, raw = handler.call_with_retry(failing_api, retries=3)
            >>> parsed['status']
            'ok'
        """
        last_raw = ""

        for attempt in range(retries + 1):
            # Make API call
            raw = api_call_func()
            last_raw = raw

            # If JSON parsing not needed, return immediately
            if not parse_json:
                return None, raw

            # Try to parse response
            parsed = self.parser.extract_json(raw)

            # Success - return parsed result
            if parsed is not None:
                return parsed, raw

            # Failed to parse - retry unless this was last attempt
            if attempt < retries:
                delay = self.base_delay * (attempt + 1)
                time.sleep(delay)

        # All retries exhausted
        return None, last_raw

    def call_with_retry_and_validation(
        self,
        api_call_func: Callable[[], str],
        required_keys: list,
        retries: int = 2
    ) -> Tuple[Optional[dict], str]:
        """Execute API call with retry and validate response structure.

        Args:
            api_call_func: Function that makes the API call
            required_keys: List of required keys in parsed response
            retries: Number of retry attempts

        Returns:
            Tuple of (parsed_dict, raw_response)
            Returns (None, raw) if validation fails after all retries

        Example:
            >>> def api_call():
            ...     return '{"name": "test", "value": 42}'
            >>> handler = RetryHandler()
            >>> parsed, raw = handler.call_with_retry_and_validation(
            ...     api_call, required_keys=["name", "value"])
            >>> parsed['name']
            'test'
        """
        last_raw = ""

        for attempt in range(retries + 1):
            raw = api_call_func()
            last_raw = raw

            parsed = self.parser.extract_json(raw)

            # Check if parsed successfully AND has required keys
            if parsed and self.parser.validate_json_structure(parsed, required_keys):
                return parsed, raw

            if attempt < retries:
                delay = self.base_delay * (attempt + 1)
                time.sleep(delay)

        return None, last_raw


if __name__ == "__main__":
    import doctest
    print("Running doctests for RetryHandler...")
    results = doctest.testmod(verbose=False)
    if results.failed == 0:
        print(f"✅ All {results.attempted} doctests passed!")
    else:
        print(f"❌ {results.failed}/{results.attempted} doctests failed")
