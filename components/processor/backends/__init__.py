"""AI Backend Plugin System.

This package provides a plugin architecture for supporting multiple AI providers
through a common interface.

Available backends:
- ClaudeBackend: Anthropic Claude models
- (Future) OpenAI, Google, Local models

Usage:
    from components.processor.backends import BackendFactory

    backend = BackendFactory.create(
        backend_type="claude",
        api_key="your-key",
        model="claude-3-5-sonnet-20241022"
    )

    parsed, raw = await backend.send_message("Hello, world!")
"""

from .base import AIBackend
from .claude_backend import ClaudeBackend
from .factory import BackendFactory

__all__ = [
    "AIBackend",
    "ClaudeBackend",
    "BackendFactory",
]
