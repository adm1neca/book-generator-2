"""Abstract base class for AI backends.

This module defines the interface that all AI backend implementations must follow,
enabling a plugin architecture for multiple AI providers.

The AIBackend abstract class ensures all backends implement:
- send_message: Async method for sending prompts and receiving responses
- get_model_info: Method for retrieving model metadata

This allows seamless swapping between different AI providers without changing
application code.
"""

from abc import ABC, abstractmethod
from typing import Dict, Tuple, Optional, Any


class AIBackend(ABC):
    """Abstract base class for AI backends.

    All AI backend implementations must inherit from this class and implement
    the required abstract methods.

    This enables a plugin architecture where different AI providers can be
    used interchangeably through a common interface.

    Example:
        class MyBackend(AIBackend):
            async def send_message(self, prompt: str, **kwargs):
                # Implementation
                return (parsed_dict, raw_string)

            def get_model_info(self):
                return {"name": "my-model", "provider": "my-provider"}
    """

    @abstractmethod
    async def send_message(
        self, prompt: str, **kwargs
    ) -> Tuple[Optional[Dict[str, Any]], str]:
        """Send message to AI service and get response.

        This method must be implemented by all backend implementations.
        It should send the prompt to the AI service and return both parsed
        and raw responses.

        Args:
            prompt: The prompt/message to send
            **kwargs: Additional backend-specific parameters (e.g., temperature,
                     max_tokens, etc.)

        Returns:
            Tuple of (parsed_dict_or_none, raw_response_string)
            - parsed_dict: Parsed JSON response if available, None if parsing failed
            - raw_response: Raw string response from the AI service

        Raises:
            Exception: If the API call fails or times out
        """
        pass

    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the model/backend.

        This method must be implemented by all backend implementations.
        It should return metadata about the model and provider.

        Returns:
            Dictionary with model information, must include:
            - name: Model name (e.g., "claude-3-5-sonnet-20241022")
            - provider: Provider name (e.g., "anthropic", "openai")
            - version: Optional version string

        Example:
            {
                "name": "claude-3-5-sonnet-20241022",
                "provider": "anthropic",
                "version": "3.5"
            }
        """
        pass
