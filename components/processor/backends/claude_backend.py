"""Claude AI backend implementation.

This module provides the Claude backend for the AI backend plugin system,
using the Anthropic Claude API through ClaudeAPIClient.

Features:
- Async message sending
- Token tracking
- Error handling
- Model information

Usage:
    backend = ClaudeBackend(
        api_key="your-api-key",
        model="claude-3-5-sonnet-20241022"
    )

    parsed, raw = await backend.send_message("Hello!")
"""

from typing import Dict, Tuple, Optional, Any
from .base import AIBackend


class ClaudeBackend(AIBackend):
    """Claude AI backend implementation.

    This backend uses the Anthropic Claude API through ClaudeAPIClient
    to send messages and receive responses.

    Attributes:
        api_key: Anthropic API key
        model: Claude model name
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        client: ClaudeAPIClient instance
    """

    def __init__(
        self,
        api_key: str,
        model: str,
        timeout: int = 120,
        max_retries: int = 2,
    ):
        """Initialize Claude backend.

        Args:
            api_key: Anthropic API key
            model: Claude model name (e.g., "claude-3-5-sonnet-20241022")
            timeout: Request timeout in seconds (default: 120)
            max_retries: Maximum retry attempts (default: 2)
        """
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries

        # Import ClaudeAPIClient
        from components.api.claude_client import ClaudeAPIClient

        self.client = ClaudeAPIClient(api_key=api_key, model=model)

    async def send_message(
        self, prompt: str, **kwargs
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Send message to Claude API.

        Args:
            prompt: The prompt to send
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            Tuple of (parsed_dict, raw_response)

        Raises:
            Exception: If API call fails
        """
        # Check if client has async method, otherwise use async wrapper
        if hasattr(self.client, 'send_message_async'):
            parsed, raw = await self.client.send_message_async(prompt, **kwargs)
        else:
            # Use asyncio to run sync method in thread pool
            import asyncio
            import json
            import re

            # Run sync method in thread pool to avoid blocking
            raw = await asyncio.to_thread(
                self.client.send_message,
                prompt,
                page_number=kwargs.get("page_number", 0),
                max_tokens=kwargs.get("max_tokens")
            )

            # Parse JSON from response
            parsed = self._parse_json(raw)

        return parsed, raw

    def _parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Parse JSON from text response.

        Args:
            text: Response text

        Returns:
            Parsed JSON dict or None
        """
        import json
        import re

        # Try to find JSON in the response
        json_match = re.search(r'\{.*\}', text, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                return None

        return None

    def get_model_info(self) -> Dict[str, Any]:
        """Get Claude model information.

        Returns:
            Dictionary with model metadata
        """
        return {
            "name": self.model,
            "provider": "anthropic",
            "version": self._extract_version(self.model),
            "api_key_prefix": self.api_key[:10] + "..." if len(self.api_key) > 10 else "***",
        }

    def _extract_version(self, model: str) -> str:
        """Extract version from model name.

        Args:
            model: Model name

        Returns:
            Version string
        """
        # Extract version from model name like "claude-3-5-sonnet-20241022"
        if "claude-3-5" in model:
            return "3.5"
        elif "claude-3" in model:
            return "3.0"
        elif "claude-2" in model:
            return "2.0"
        else:
            return "unknown"
