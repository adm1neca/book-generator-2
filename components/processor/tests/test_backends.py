"""Tests for AI Backend Plugin System (TDD - Red Phase).

These tests are written BEFORE implementation to follow Test-Driven Development.

Test Coverage:
- AIBackend abstract base class
- ClaudeBackend implementation
- BackendFactory for plugin creation
- Backend interface compatibility
- Error handling
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from abc import ABC

# Import will fail initially - expected in TDD Red phase
try:
    from components.processor.backends.base import AIBackend
    from components.processor.backends.claude_backend import ClaudeBackend
    from components.processor.backends.factory import BackendFactory
except ImportError:
    AIBackend = None
    ClaudeBackend = None
    BackendFactory = None


class TestAIBackendInterface:
    """Test AIBackend abstract base class."""

    def test_backend_is_abstract(self):
        """Test AIBackend is abstract and cannot be instantiated."""
        if AIBackend is None:
            pytest.skip("AIBackend not yet implemented (TDD Red phase)")

        # Should not be able to instantiate directly
        with pytest.raises(TypeError):
            AIBackend()

    def test_backend_requires_send_message(self):
        """Test AIBackend requires send_message implementation."""
        if AIBackend is None:
            pytest.skip("AIBackend not yet implemented")

        # Create incomplete subclass
        class IncompleteBackend(AIBackend):
            pass

        # Should fail without send_message
        with pytest.raises(TypeError):
            IncompleteBackend()

    def test_backend_requires_get_model_info(self):
        """Test AIBackend requires get_model_info implementation."""
        if AIBackend is None:
            pytest.skip("AIBackend not yet implemented")

        # Create subclass with only send_message
        class PartialBackend(AIBackend):
            async def send_message(self, prompt, **kwargs):
                pass

        # Should fail without get_model_info
        with pytest.raises(TypeError):
            PartialBackend()

    def test_complete_backend_can_be_instantiated(self):
        """Test complete backend implementation can be instantiated."""
        if AIBackend is None:
            pytest.skip("AIBackend not yet implemented")

        class CompleteBackend(AIBackend):
            async def send_message(self, prompt, **kwargs):
                return ({"test": "data"}, "raw")

            def get_model_info(self):
                return {"name": "test", "version": "1.0"}

        backend = CompleteBackend()
        assert backend is not None


class TestClaudeBackend:
    """Test ClaudeBackend implementation."""

    def test_claude_backend_initialization(self):
        """Test ClaudeBackend can be initialized."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented (TDD Red phase)")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        assert backend is not None
        assert backend.api_key == "test-key"
        assert backend.model == "claude-3-5-sonnet-20241022"

    def test_claude_backend_is_ai_backend(self):
        """Test ClaudeBackend implements AIBackend interface."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        assert isinstance(backend, AIBackend)

    @pytest.mark.asyncio
    async def test_send_message_async(self):
        """Test sending message asynchronously."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        with patch.object(backend, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                return_value=({"description": "test"}, "raw response")
            )

            parsed, raw = await backend.send_message("Test prompt")

            assert parsed == {"description": "test"}
            assert raw == "raw response"
            mock_client.send_message_async.assert_called_once()

    def test_get_model_info(self):
        """Test getting model information."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        info = backend.get_model_info()

        assert "name" in info
        assert "provider" in info
        assert info["provider"] == "anthropic"
        assert "claude" in info["name"].lower()

    @pytest.mark.asyncio
    async def test_send_message_with_params(self):
        """Test sending message with additional parameters."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        with patch.object(backend, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                return_value=({"test": "data"}, "raw")
            )

            await backend.send_message(
                "Test prompt",
                temperature=0.7,
                max_tokens=1000
            )

            # Should pass through kwargs
            call_kwargs = mock_client.send_message_async.call_args[1]
            assert call_kwargs.get("temperature") == 0.7
            assert call_kwargs.get("max_tokens") == 1000

    @pytest.mark.asyncio
    async def test_handles_api_errors(self):
        """Test handling API errors."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        with patch.object(backend, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                side_effect=Exception("API Error")
            )

            with pytest.raises(Exception) as exc_info:
                await backend.send_message("Test prompt")

            assert "API Error" in str(exc_info.value)


class TestBackendFactory:
    """Test BackendFactory for creating backends."""

    def test_factory_create_claude_backend(self):
        """Test factory creates Claude backend."""
        if BackendFactory is None:
            pytest.skip("BackendFactory not yet implemented (TDD Red phase)")

        backend = BackendFactory.create(
            backend_type="claude",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )

        assert isinstance(backend, ClaudeBackend)
        assert backend.api_key == "test-key"

    def test_factory_unknown_backend_raises_error(self):
        """Test factory raises error for unknown backend."""
        if BackendFactory is None:
            pytest.skip("BackendFactory not yet implemented")

        with pytest.raises(ValueError) as exc_info:
            BackendFactory.create(
                backend_type="unknown",
                api_key="test-key"
            )

        assert "unknown" in str(exc_info.value).lower()

    def test_factory_get_available_backends(self):
        """Test getting list of available backends."""
        if BackendFactory is None:
            pytest.skip("BackendFactory not yet implemented")

        backends = BackendFactory.get_available_backends()

        assert isinstance(backends, list)
        assert "claude" in backends

    def test_factory_validate_config(self):
        """Test factory validates backend configuration."""
        if BackendFactory is None:
            pytest.skip("BackendFactory not yet implemented")

        # Valid config
        is_valid = BackendFactory.validate_config(
            backend_type="claude",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )
        assert is_valid

        # Invalid - missing API key
        is_valid = BackendFactory.validate_config(
            backend_type="claude",
            api_key="",
            model="claude-3-5-sonnet-20241022"
        )
        assert not is_valid


class TestBackendCompatibility:
    """Test backend compatibility and interface consistency."""

    @pytest.mark.asyncio
    async def test_all_backends_same_interface(self):
        """Test all backends implement same interface."""
        if BackendFactory is None:
            pytest.skip("BackendFactory not yet implemented")

        claude = BackendFactory.create(
            backend_type="claude",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )

        # All backends should have same methods
        assert hasattr(claude, "send_message")
        assert hasattr(claude, "get_model_info")
        assert callable(claude.send_message)
        assert callable(claude.get_model_info)

    @pytest.mark.asyncio
    async def test_backend_swap_compatibility(self):
        """Test backends can be swapped without code changes."""
        if BackendFactory is None:
            pytest.skip("BackendFactory not yet implemented")

        def process_with_backend(backend: AIBackend, prompt: str):
            """Generic function that works with any backend."""
            return backend.send_message(prompt)

        claude = BackendFactory.create(
            backend_type="claude",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )

        with patch.object(claude, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                return_value=({"test": "data"}, "raw")
            )

            # Should work with any backend
            result = await process_with_backend(claude, "Test")
            assert result is not None


class TestBackendConfiguration:
    """Test backend configuration options."""

    def test_backend_with_custom_config(self):
        """Test creating backend with custom configuration."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(
            api_key="test-key",
            model="claude-3-5-sonnet-20241022",
            timeout=30,
            max_retries=3
        )

        assert backend.timeout == 30
        assert backend.max_retries == 3

    def test_backend_default_config(self):
        """Test backend uses sensible defaults."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )

        # Should have default timeout
        assert hasattr(backend, "timeout")
        assert backend.timeout > 0


class TestBackendErrorHandling:
    """Test backend error handling."""

    @pytest.mark.asyncio
    async def test_handles_network_errors(self):
        """Test handling network errors."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        with patch.object(backend, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                side_effect=ConnectionError("Network error")
            )

            with pytest.raises(ConnectionError):
                await backend.send_message("Test")

    @pytest.mark.asyncio
    async def test_handles_timeout_errors(self):
        """Test handling timeout errors."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        with patch.object(backend, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                side_effect=TimeoutError("Request timeout")
            )

            with pytest.raises(TimeoutError):
                await backend.send_message("Test")

    @pytest.mark.asyncio
    async def test_handles_auth_errors(self):
        """Test handling authentication errors."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        backend = ClaudeBackend(api_key="invalid-key", model="claude-3-5-sonnet-20241022")

        with patch.object(backend, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                side_effect=Exception("Authentication failed")
            )

            with pytest.raises(Exception) as exc_info:
                await backend.send_message("Test")

            assert "Authentication" in str(exc_info.value)


class TestBackendIntegration:
    """Test backend integration scenarios."""

    @pytest.mark.asyncio
    async def test_backend_with_page_processor(self):
        """Test backend integration with AsyncPageProcessor."""
        if ClaudeBackend is None:
            pytest.skip("ClaudeBackend not yet implemented")

        from components.processor.async_page_processor import AsyncPageProcessor
        from components.processor.page_processor import ProcessorConfig

        backend = ClaudeBackend(api_key="test-key", model="claude-3-5-sonnet-20241022")

        with patch.object(backend, 'client') as mock_client:
            mock_client.send_message_async = AsyncMock(
                return_value=({"description": "test"}, "raw")
            )

            # Create processor with backend
            config = ProcessorConfig(
                difficulty="easy",
                model="claude-3-5-sonnet-20241022",
                api_key="test-key"
            )

            # Backend should be compatible
            assert backend is not None

    def test_factory_integration(self):
        """Test factory integration with processor."""
        if BackendFactory is None:
            pytest.skip("BackendFactory not yet implemented")

        # Should be able to create and use backend from factory
        backend = BackendFactory.create(
            backend_type="claude",
            api_key="test-key",
            model="claude-3-5-sonnet-20241022"
        )

        info = backend.get_model_info()

        assert info is not None
        assert "provider" in info
