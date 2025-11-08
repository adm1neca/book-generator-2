"""Factory for creating AI backend instances.

This module provides the BackendFactory for creating AI backend instances
based on backend type and configuration.

The factory pattern allows centralized backend creation, configuration
validation, and easy extension to support new backends.

Usage:
    # Create Claude backend
    backend = BackendFactory.create(
        backend_type="claude",
        api_key="your-key",
        model="claude-3-5-sonnet-20241022"
    )

    # Get available backends
    backends = BackendFactory.get_available_backends()

    # Validate configuration
    is_valid = BackendFactory.validate_config(
        backend_type="claude",
        api_key="test",
        model="claude-3-5-sonnet-20241022"
    )
"""

from typing import Dict, List, Any
from .base import AIBackend
from .claude_backend import ClaudeBackend


class BackendFactory:
    """Factory for creating AI backend instances.

    This class provides static methods for:
    - Creating backend instances
    - Listing available backends
    - Validating backend configuration
    """

    @staticmethod
    def create(backend_type: str, **config) -> AIBackend:
        """Create AI backend instance.

        Args:
            backend_type: Type of backend ("claude", "openai", etc.)
            **config: Backend-specific configuration

        Returns:
            AIBackend instance

        Raises:
            ValueError: If backend type is unknown

        Example:
            backend = BackendFactory.create(
                backend_type="claude",
                api_key="sk-...",
                model="claude-3-5-sonnet-20241022"
            )
        """
        if backend_type == "claude":
            return ClaudeBackend(**config)
        else:
            raise ValueError(
                f"Unknown backend type: {backend_type}. "
                f"Available: {', '.join(BackendFactory.get_available_backends())}"
            )

    @staticmethod
    def get_available_backends() -> List[str]:
        """Get list of available backend types.

        Returns:
            List of backend type strings

        Example:
            >>> BackendFactory.get_available_backends()
            ['claude']
        """
        return ["claude"]

    @staticmethod
    def validate_config(backend_type: str, **config) -> bool:
        """Validate backend configuration.

        Args:
            backend_type: Type of backend
            **config: Configuration to validate

        Returns:
            True if valid, False otherwise

        Example:
            is_valid = BackendFactory.validate_config(
                backend_type="claude",
                api_key="sk-...",
                model="claude-3-5-sonnet-20241022"
            )
        """
        if backend_type == "claude":
            return BackendFactory._validate_claude_config(**config)
        else:
            return False

    @staticmethod
    def _validate_claude_config(**config) -> bool:
        """Validate Claude backend configuration.

        Args:
            **config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if "api_key" not in config or not config["api_key"]:
            return False

        if "model" not in config or not config["model"]:
            return False

        # Check API key format (basic validation)
        api_key = config["api_key"]
        if len(api_key) < 5:  # Minimum reasonable length
            return False

        return True
