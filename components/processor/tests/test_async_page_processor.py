"""Tests for AsyncPageProcessor (TDD - Red Phase).

These tests are written BEFORE implementation to follow Test-Driven Development.
They should initially fail, then pass once AsyncPageProcessor is implemented.

Test Coverage:
- Async single page processing
- Concurrent API calls
- Error handling in async context
- Timeout handling
- Proper async/await usage
- Resource cleanup
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import will fail initially - this is expected in TDD Red phase
try:
    from components.processor.async_page_processor import AsyncPageProcessor
    from components.processor.page_processor import ProcessorConfig, ProcessedPage
except ImportError:
    # Expected to fail in Red phase
    AsyncPageProcessor = None
    ProcessorConfig = None
    ProcessedPage = None


@pytest.fixture
def config():
    """Create test processor configuration."""
    if ProcessorConfig is None:
        pytest.skip("AsyncPageProcessor not yet implemented (TDD Red phase)")
    return ProcessorConfig(
        difficulty="easy",
        model="claude-3-5-sonnet",
        api_key="test-key",
        retry_attempts=2,
    )


@pytest.fixture
def mock_async_api_client():
    """Create mock async API client."""
    client = Mock()
    client.send_message_async = AsyncMock(
        return_value=({"description": "test", "items": []}, "raw response")
    )
    return client


@pytest.fixture
def mock_retry_handler():
    """Create mock retry handler."""
    handler = Mock()
    handler.call_with_retry_async = AsyncMock(
        return_value=({"description": "test", "items": []}, "raw response")
    )
    return handler


@pytest.fixture
def mock_variety_tracker():
    """Create mock variety tracker."""
    tracker = Mock()
    tracker.get_used.return_value = []
    return tracker


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    return Mock()


@pytest.fixture
def async_processor(
    config, mock_async_api_client, mock_retry_handler, mock_variety_tracker, mock_logger
):
    """Create AsyncPageProcessor with mocked dependencies."""
    if AsyncPageProcessor is None:
        pytest.skip("AsyncPageProcessor not yet implemented (TDD Red phase)")

    return AsyncPageProcessor(
        config=config,
        api_client=mock_async_api_client,
        retry_handler=mock_retry_handler,
        variety_tracker=mock_variety_tracker,
        logger=mock_logger,
    )


class TestAsyncPageProcessorBasics:
    """Test basic async page processing functionality."""

    @pytest.mark.asyncio
    async def test_process_returns_awaitable(self, async_processor):
        """Test that process() returns an awaitable."""
        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = async_processor.process(page)

        # Should be a coroutine
        assert asyncio.iscoroutine(result)
        await result  # Clean up

    @pytest.mark.asyncio
    async def test_successful_page_processing(self, async_processor, mock_retry_handler):
        """Test successful async page processing."""
        mock_retry_handler.call_with_retry_async.return_value = (
            {"description": "An elephant", "items": ["elephant"]},
            "raw",
        )

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = await async_processor.process(page)

        assert result.success
        assert result.page_data["pageNumber"] == 1
        assert result.page_data["type"] == "coloring"
        assert "description" in result.page_data

    @pytest.mark.asyncio
    async def test_process_calls_async_api(self, async_processor, mock_async_api_client):
        """Test that async API client is called."""
        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        await async_processor.process(page)

        # Verify async API was called
        assert mock_async_api_client.send_message_async.called

    @pytest.mark.asyncio
    async def test_handles_api_failure(self, async_processor, mock_retry_handler):
        """Test handling of API failures in async context."""
        mock_retry_handler.call_with_retry_async.return_value = (None, "error response")

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = await async_processor.process(page)

        assert not result.success
        assert result.error is not None


class TestAsyncPageProcessorConcurrency:
    """Test concurrent processing capabilities."""

    @pytest.mark.asyncio
    async def test_multiple_pages_concurrently(self, async_processor, mock_retry_handler):
        """Test processing multiple pages concurrently."""
        # Track call order
        call_times = []

        async def mock_api_call(*args, **kwargs):
            call_times.append(asyncio.get_event_loop().time())
            await asyncio.sleep(0.1)  # Simulate API delay
            return ({"description": "test"}, "raw")

        mock_retry_handler.call_with_retry_async.side_effect = mock_api_call

        pages = [
            {"type": "coloring", "theme": "animals", "pageNumber": i} for i in range(5)
        ]

        # Process all concurrently
        tasks = [async_processor.process(page) for page in pages]
        results = await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 5
        assert all(r.success for r in results)

        # Calls should happen concurrently (within short time window)
        time_spread = max(call_times) - min(call_times)
        assert time_spread < 0.2  # Should start nearly simultaneously

    @pytest.mark.asyncio
    async def test_concurrent_with_failures(self, async_processor, mock_retry_handler):
        """Test that failures in one page don't affect others."""
        call_count = 0

        async def mock_api_call(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return (None, "error")  # Second call fails
            return ({"description": "test"}, "raw")

        mock_retry_handler.call_with_retry_async.side_effect = mock_api_call

        pages = [{"type": "coloring", "theme": "animals", "pageNumber": i} for i in range(3)]

        tasks = [async_processor.process(page) for page in pages]
        results = await asyncio.gather(*tasks)

        # Should have 2 successes, 1 failure
        successes = [r for r in results if r.success]
        failures = [r for r in results if not r.success]

        assert len(successes) == 2
        assert len(failures) == 1


class TestAsyncPageProcessorErrorHandling:
    """Test error handling in async context."""

    @pytest.mark.asyncio
    async def test_handles_exception_during_processing(
        self, async_processor, mock_retry_handler, mock_logger
    ):
        """Test handling of exceptions in async processing."""
        mock_retry_handler.call_with_retry_async.side_effect = Exception("API error")

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = await async_processor.process(page)

        assert not result.success
        assert "API error" in result.error
        mock_logger.error.assert_called()

    @pytest.mark.asyncio
    async def test_handles_timeout(self, async_processor, mock_retry_handler):
        """Test handling of timeout errors."""
        async def slow_api_call(*args, **kwargs):
            await asyncio.sleep(10)  # Very slow
            return ({"test": "data"}, "raw")

        mock_retry_handler.call_with_retry_async.side_effect = slow_api_call

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        # Should timeout
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(async_processor.process(page), timeout=0.5)

    @pytest.mark.asyncio
    async def test_handles_cancellation(self, async_processor, mock_retry_handler):
        """Test handling of task cancellation."""
        async def long_api_call(*args, **kwargs):
            await asyncio.sleep(5)
            return ({"test": "data"}, "raw")

        mock_retry_handler.call_with_retry_async.side_effect = long_api_call

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        task = asyncio.create_task(async_processor.process(page))
        await asyncio.sleep(0.1)  # Let it start
        task.cancel()

        with pytest.raises(asyncio.CancelledError):
            await task


class TestAsyncPageProcessorPromptBuilding:
    """Test async prompt building."""

    @pytest.mark.asyncio
    async def test_build_prompt_async(self, async_processor):
        """Test async prompt building."""
        prompt, selected = await async_processor._build_prompt_async(
            "coloring", "animals", 1
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        # selected_item may be None or string
        assert selected is None or isinstance(selected, str)

    @pytest.mark.asyncio
    async def test_prompt_includes_difficulty(self, async_processor):
        """Test that prompt includes difficulty setting."""
        prompt, _ = await async_processor._build_prompt_async("coloring", "animals", 1)

        assert "easy" in prompt.lower()

    @pytest.mark.asyncio
    async def test_sanitizes_theme(self, async_processor):
        """Test that theme is sanitized in async context."""
        prompt, _ = await async_processor._build_prompt_async("coloring", "Disney", 1)

        # Disney should be sanitized out
        assert "disney" not in prompt.lower()


class TestAsyncPageProcessorVarietyTracking:
    """Test variety tracking in async context."""

    @pytest.mark.asyncio
    async def test_tracks_variety_on_success(
        self, async_processor, mock_variety_tracker, mock_retry_handler
    ):
        """Test that variety is tracked after successful processing."""
        mock_retry_handler.call_with_retry_async.return_value = (
            {"description": "test"}, "raw"
        )

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        await async_processor.process(page)

        # Variety tracker should be accessed
        mock_variety_tracker.get_used.assert_called()


class TestAsyncPageProcessorPerformance:
    """Test performance characteristics of async processing."""

    @pytest.mark.asyncio
    async def test_concurrent_faster_than_sequential(
        self, async_processor, mock_retry_handler
    ):
        """Test that concurrent processing is faster than sequential."""
        async def mock_api_call(*args, **kwargs):
            await asyncio.sleep(0.1)  # 100ms per call
            return ({"description": "test"}, "raw")

        mock_retry_handler.call_with_retry_async.side_effect = mock_api_call

        pages = [{"type": "coloring", "theme": "animals", "pageNumber": i} for i in range(5)]

        # Concurrent processing
        import time
        start = time.time()
        tasks = [async_processor.process(page) for page in pages]
        await asyncio.gather(*tasks)
        concurrent_time = time.time() - start

        # Should be much faster than 5 * 0.1 = 0.5s
        # Allow for overhead, but should be < 0.3s
        assert concurrent_time < 0.3

    @pytest.mark.asyncio
    async def test_processes_pages_in_parallel(self, async_processor, mock_retry_handler):
        """Test that pages are actually processed in parallel."""
        processing_times = []

        async def track_timing(*args, **kwargs):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.05)
            processing_times.append((start, asyncio.get_event_loop().time()))
            return ({"description": "test"}, "raw")

        mock_retry_handler.call_with_retry_async.side_effect = track_timing

        pages = [{"type": "coloring", "theme": "animals", "pageNumber": i} for i in range(3)]

        tasks = [async_processor.process(page) for page in pages]
        await asyncio.gather(*tasks)

        # Check that processing overlapped
        # If sequential, each would start after previous ends
        # If parallel, starts should be close together
        starts = [t[0] for t in processing_times]
        time_between_starts = max(starts) - min(starts)
        assert time_between_starts < 0.1  # Started nearly simultaneously


class TestAsyncPageProcessorResourceManagement:
    """Test proper resource management in async context."""

    @pytest.mark.asyncio
    async def test_cleans_up_on_error(self, async_processor, mock_retry_handler):
        """Test that resources are cleaned up on error."""
        mock_retry_handler.call_with_retry_async.side_effect = Exception("Error")

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = await async_processor.process(page)

        # Should handle error gracefully
        assert not result.success

    @pytest.mark.asyncio
    async def test_multiple_processors_concurrent(self, config, mock_async_api_client):
        """Test that multiple processor instances can run concurrently."""
        if AsyncPageProcessor is None:
            pytest.skip("AsyncPageProcessor not yet implemented")

        # Create multiple processors
        processors = []
        for i in range(3):
            proc = AsyncPageProcessor(
                config=config,
                api_client=mock_async_api_client,
                retry_handler=Mock(
                    call_with_retry_async=AsyncMock(
                        return_value=({"description": f"test{i}"}, "raw")
                    )
                ),
                variety_tracker=Mock(get_used=Mock(return_value=[])),
                logger=Mock(),
            )
            processors.append(proc)

        # Process with all processors concurrently
        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}
        tasks = [proc.process(page) for proc in processors]
        results = await asyncio.gather(*tasks)

        assert len(results) == 3
        assert all(r.success for r in results)


class TestAsyncPageProcessorEdgeCases:
    """Test edge cases in async processing."""

    @pytest.mark.asyncio
    async def test_handles_empty_page_data(self, async_processor, mock_retry_handler):
        """Test handling of empty page data."""
        mock_retry_handler.call_with_retry_async.return_value = (
            {"description": "test"}, "raw"
        )

        page = {}

        result = await async_processor.process(page)

        assert isinstance(result, ProcessedPage)

    @pytest.mark.asyncio
    async def test_handles_none_values(self, async_processor, mock_retry_handler):
        """Test handling of None values in page data."""
        mock_retry_handler.call_with_retry_async.return_value = (
            {"description": "test"}, "raw"
        )

        page = {"type": None, "theme": None, "pageNumber": None}

        result = await async_processor.process(page)

        assert isinstance(result, ProcessedPage)

    @pytest.mark.asyncio
    async def test_handles_unknown_page_type(self, async_processor):
        """Test handling of unknown page type."""
        page = {"type": "invalid_type", "theme": "animals", "pageNumber": 1}

        result = await async_processor.process(page)

        assert not result.success
        assert "Unknown page type" in result.error or result.error is not None


# Marker for async tests
pytestmark = pytest.mark.asyncio
