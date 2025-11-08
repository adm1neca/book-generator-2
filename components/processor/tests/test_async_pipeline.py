"""Tests for AsyncProcessingPipeline (TDD - Red Phase).

These tests are written BEFORE implementation to follow Test-Driven Development.
They should initially fail, then pass once AsyncProcessingPipeline is implemented.

Test Coverage:
- Async pipeline orchestration
- Concurrency control with semaphores
- Limit enforcement in async context
- Error handling with partial failures
- Progress tracking
- Performance characteristics
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

# Import will fail initially - this is expected in TDD Red phase
try:
    from components.processor.async_pipeline import (
        AsyncProcessingPipeline,
        AsyncPipelineConfig,
        AsyncPipelineResult,
    )
    from components.processor.page_processor import ProcessedPage
except ImportError:
    # Expected to fail in Red phase
    AsyncProcessingPipeline = None
    AsyncPipelineConfig = None
    AsyncPipelineResult = None
    ProcessedPage = None


# Mock Data class for testing
class Data:
    """Mock Data class."""

    def __init__(self, data):
        self.data = data


@pytest.fixture
def config():
    """Create test pipeline configuration."""
    if AsyncPipelineConfig is None:
        pytest.skip("AsyncProcessingPipeline not yet implemented (TDD Red phase)")
    return AsyncPipelineConfig(
        output_dir=Path("/tmp/test"),
        random_seed=42,
        variety_summary={},
        max_concurrency=5,
    )


@pytest.fixture
def mock_async_processor():
    """Create mock async page processor."""
    processor = Mock()

    async def mock_process(page):
        if ProcessedPage is None:
            # Create simple result dict for testing
            return Mock(
                success=True,
                page_data={"pageNumber": page["pageNumber"], "type": page["type"]},
                error=None,
            )
        return ProcessedPage(
            success=True,
            page_data={"pageNumber": page["pageNumber"], "type": page["type"]},
            error=None,
        )

    processor.process = AsyncMock(side_effect=mock_process)
    return processor


@pytest.fixture
def mock_limiter():
    """Create mock page limiter."""
    limiter = Mock()
    limiter.should_process.return_value = (True, None)
    limiter.get_summary.return_value = {
        "total_processed": 0,
        "per_topic_counts": {},
        "skipped_count": 0,
    }
    limiter.get_skipped_messages.return_value = []
    return limiter


@pytest.fixture
def mock_logger():
    """Create mock logger."""
    return Mock()


@pytest.fixture
def async_pipeline(config, mock_async_processor, mock_limiter, mock_logger):
    """Create AsyncProcessingPipeline with mocked dependencies."""
    if AsyncProcessingPipeline is None:
        pytest.skip("AsyncProcessingPipeline not yet implemented (TDD Red phase)")

    return AsyncProcessingPipeline(
        page_processor=mock_async_processor,
        limiter=mock_limiter,
        logger=mock_logger,
        config=config,
    )


class TestAsyncPipelineConfig:
    """Test async pipeline configuration."""

    def test_config_with_concurrency_limit(self):
        """Test configuration with concurrency limit."""
        if AsyncPipelineConfig is None:
            pytest.skip("AsyncPipelineConfig not yet implemented")

        config = AsyncPipelineConfig(max_concurrency=10)
        assert config.max_concurrency == 10

    def test_default_concurrency_limit(self):
        """Test default concurrency limit."""
        if AsyncPipelineConfig is None:
            pytest.skip("AsyncPipelineConfig not yet implemented")

        config = AsyncPipelineConfig()
        assert config.max_concurrency == 5  # Expected default


class TestAsyncPipelineBasics:
    """Test basic async pipeline functionality."""

    @pytest.mark.asyncio
    async def test_run_returns_awaitable(self, async_pipeline):
        """Test that run() returns an awaitable."""
        pages = [Data(data={"type": "coloring", "theme": "test", "pageNumber": 1})]

        result = async_pipeline.run(pages)

        assert asyncio.iscoroutine(result)
        await result  # Clean up

    @pytest.mark.asyncio
    async def test_successful_pipeline_run(
        self, async_pipeline, mock_async_processor, mock_limiter
    ):
        """Test successful async pipeline run."""
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {"coloring": 1},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "coloring", "theme": "animals", "pageNumber": 1})]

        result = await async_pipeline.run(pages)

        assert result.total_processed == 1
        assert len(result.processed_pages) == 1
        assert result.total_skipped == 0

    @pytest.mark.asyncio
    async def test_processes_multiple_pages(self, async_pipeline, mock_limiter):
        """Test processing multiple pages."""
        mock_limiter.get_summary.return_value = {
            "total_processed": 3,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "coloring", "theme": "animals", "pageNumber": i})
            for i in range(1, 4)
        ]

        result = await async_pipeline.run(pages)

        assert result.total_processed == 3
        assert len(result.processed_pages) == 3


class TestAsyncPipelineConcurrency:
    """Test concurrency control in pipeline."""

    @pytest.mark.asyncio
    async def test_respects_concurrency_limit(
        self, mock_async_processor, mock_limiter, mock_logger
    ):
        """Test that concurrency limit is respected."""
        if AsyncProcessingPipeline is None:
            pytest.skip("AsyncProcessingPipeline not yet implemented")

        # Track active concurrent tasks
        active_tasks = []
        max_concurrent = 0

        async def track_concurrency(page):
            active_tasks.append(1)
            nonlocal max_concurrent
            max_concurrent = max(max_concurrent, len(active_tasks))
            await asyncio.sleep(0.1)
            active_tasks.pop()
            return Mock(
                success=True, page_data={"pageNumber": page["pageNumber"]}, error=None
            )

        mock_async_processor.process = AsyncMock(side_effect=track_concurrency)
        mock_limiter.get_summary.return_value = {
            "total_processed": 10,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        config = AsyncPipelineConfig(max_concurrency=3)
        pipeline = AsyncProcessingPipeline(
            page_processor=mock_async_processor,
            limiter=mock_limiter,
            logger=mock_logger,
            config=config,
        )

        pages = [
            Data(data={"type": "coloring", "theme": "test", "pageNumber": i})
            for i in range(10)
        ]

        await pipeline.run(pages)

        # Should never exceed concurrency limit
        assert max_concurrent <= 3

    @pytest.mark.asyncio
    async def test_concurrent_processing_is_faster(
        self, mock_async_processor, mock_limiter, mock_logger
    ):
        """Test that concurrent processing is faster than sequential."""
        if AsyncProcessingPipeline is None:
            pytest.skip("AsyncProcessingPipeline not yet implemented")

        async def mock_process(page):
            await asyncio.sleep(0.1)  # 100ms per page
            return Mock(
                success=True, page_data={"pageNumber": page["pageNumber"]}, error=None
            )

        mock_async_processor.process = AsyncMock(side_effect=mock_process)
        mock_limiter.get_summary.return_value = {
            "total_processed": 5,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        config = AsyncPipelineConfig(max_concurrency=5)
        pipeline = AsyncProcessingPipeline(
            page_processor=mock_async_processor,
            limiter=mock_limiter,
            logger=mock_logger,
            config=config,
        )

        pages = [
            Data(data={"type": "coloring", "theme": "test", "pageNumber": i})
            for i in range(5)
        ]

        import time

        start = time.time()
        await pipeline.run(pages)
        duration = time.time() - start

        # 5 pages at 0.1s each, concurrent should be ~0.1s total
        # Allow overhead, but should be < 0.3s
        assert duration < 0.3  # Much faster than 0.5s sequential

    @pytest.mark.asyncio
    async def test_processes_pages_concurrently_not_sequentially(
        self, mock_async_processor, mock_limiter, mock_logger
    ):
        """Test that pages are actually processed concurrently."""
        if AsyncProcessingPipeline is None:
            pytest.skip("AsyncProcessingPipeline not yet implemented")

        processing_times = []

        async def track_timing(page):
            start = asyncio.get_event_loop().time()
            await asyncio.sleep(0.05)
            processing_times.append(start)
            return Mock(
                success=True, page_data={"pageNumber": page["pageNumber"]}, error=None
            )

        mock_async_processor.process = AsyncMock(side_effect=track_timing)
        mock_limiter.get_summary.return_value = {
            "total_processed": 3,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        config = AsyncPipelineConfig(max_concurrency=3)
        pipeline = AsyncProcessingPipeline(
            page_processor=mock_async_processor,
            limiter=mock_limiter,
            logger=mock_logger,
            config=config,
        )

        pages = [
            Data(data={"type": "coloring", "theme": "test", "pageNumber": i})
            for i in range(3)
        ]

        await pipeline.run(pages)

        # All should start nearly simultaneously
        time_spread = max(processing_times) - min(processing_times)
        assert time_spread < 0.1  # Started within 100ms


class TestAsyncPipelineLimitEnforcement:
    """Test limit enforcement in async pipeline."""

    @pytest.mark.asyncio
    async def test_skips_pages_when_limit_reached(
        self, async_pipeline, mock_limiter, mock_logger
    ):
        """Test that pages are skipped when limits reached."""
        # First 2 OK, third blocked
        mock_limiter.should_process.side_effect = [
            (True, None),
            (True, None),
            (False, "Limit reached"),
        ]
        mock_limiter.get_summary.return_value = {
            "total_processed": 2,
            "per_topic_counts": {},
            "skipped_count": 1,
        }
        mock_limiter.get_skipped_messages.return_value = ["Limit reached"]

        pages = [
            Data(data={"type": "coloring", "theme": "test", "pageNumber": i})
            for i in range(3)
        ]

        result = await async_pipeline.run(pages)

        assert result.total_processed == 2
        assert result.total_skipped == 1
        mock_limiter.track_skip.assert_called_once_with("Limit reached")

    @pytest.mark.asyncio
    async def test_marks_processed_after_success(
        self, async_pipeline, mock_limiter
    ):
        """Test that limiter is updated after successful processing."""
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "coloring", "theme": "test", "pageNumber": 1})]

        await async_pipeline.run(pages)

        mock_limiter.mark_processed.assert_called_once_with("coloring")


class TestAsyncPipelineErrorHandling:
    """Test error handling in async pipeline."""

    @pytest.mark.asyncio
    async def test_continues_after_page_error(
        self, async_pipeline, mock_async_processor, mock_limiter
    ):
        """Test that pipeline continues after individual page errors."""
        call_count = 0

        async def mock_process(page):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                return Mock(
                    success=False,
                    page_data={"error": "failed"},
                    error="Test error"
                )
            return Mock(
                success=True,
                page_data={"pageNumber": page["pageNumber"]},
                error=None
            )

        mock_async_processor.process = AsyncMock(side_effect=mock_process)
        mock_limiter.get_summary.return_value = {
            "total_processed": 2,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": i})
            for i in range(3)
        ]

        result = await async_pipeline.run(pages)

        # All 3 pages should be in result (fail-safe)
        assert len(result.processed_pages) == 3

    @pytest.mark.asyncio
    async def test_handles_validation_errors(self, async_pipeline):
        """Test handling of input validation errors."""
        # Empty pages should raise ValueError
        with pytest.raises(ValueError):
            await async_pipeline.run([])

    @pytest.mark.asyncio
    async def test_handles_none_input(self, async_pipeline):
        """Test handling of None input."""
        with pytest.raises(ValueError):
            await async_pipeline.run(None)

    @pytest.mark.asyncio
    async def test_partial_failure_returns_partial_results(
        self, async_pipeline, mock_async_processor, mock_limiter
    ):
        """Test that partial failures return partial results."""
        async def mock_process(page):
            if page["pageNumber"] == 2:
                raise Exception("Processing error")
            return Mock(
                success=True,
                page_data={"pageNumber": page["pageNumber"]},
                error=None
            )

        mock_async_processor.process = AsyncMock(side_effect=mock_process)
        mock_limiter.get_summary.return_value = {
            "total_processed": 2,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": i})
            for i in range(1, 4)
        ]

        result = await async_pipeline.run(pages)

        # Should still have some results
        assert len(result.processed_pages) > 0


class TestAsyncPipelineResult:
    """Test async pipeline result structure."""

    @pytest.mark.asyncio
    async def test_result_includes_metadata(self, async_pipeline, mock_limiter):
        """Test that result includes all metadata."""
        mock_limiter.get_summary.return_value = {
            "total_processed": 2,
            "per_topic_counts": {"coloring": 2},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "coloring", "theme": "test", "pageNumber": i})
            for i in range(2)
        ]

        result = await async_pipeline.run(pages)

        assert hasattr(result, "total_processed")
        assert hasattr(result, "total_skipped")
        assert hasattr(result, "duration_seconds")
        assert hasattr(result, "variety_summary")
        assert hasattr(result, "limit_summary")
        assert result.duration_seconds > 0

    @pytest.mark.asyncio
    async def test_result_to_langflow_data(self, async_pipeline, mock_limiter):
        """Test conversion to Langflow data format."""
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "test", "theme": "test", "pageNumber": 1})]

        result = await async_pipeline.run(pages)

        langflow_data = result.to_langflow_data()
        assert isinstance(langflow_data, list)
        assert len(langflow_data) == 1


class TestAsyncPipelinePageSorting:
    """Test page sorting in async pipeline."""

    @pytest.mark.asyncio
    async def test_sorts_pages_by_number(
        self, async_pipeline, mock_async_processor, mock_limiter
    ):
        """Test that pages are sorted by page number."""
        async def mock_process(page):
            return Mock(
                success=True,
                page_data={"pageNumber": page["pageNumber"]},
                error=None
            )

        mock_async_processor.process = AsyncMock(side_effect=mock_process)
        mock_limiter.get_summary.return_value = {
            "total_processed": 3,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        # Pages out of order
        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": 5}),
            Data(data={"type": "test", "theme": "test", "pageNumber": 2}),
            Data(data={"type": "test", "theme": "test", "pageNumber": 8}),
        ]

        result = await async_pipeline.run(pages)

        # Check order
        page_numbers = [p.data["pageNumber"] for p in result.processed_pages]
        assert page_numbers == [2, 5, 8]


class TestAsyncPipelineProgressTracking:
    """Test progress tracking in async pipeline."""

    @pytest.mark.asyncio
    async def test_logs_progress(self, async_pipeline, mock_logger, mock_limiter):
        """Test that progress is logged."""
        mock_limiter.get_summary.return_value = {
            "total_processed": 2,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": i})
            for i in range(2)
        ]

        await async_pipeline.run(pages)

        # Should log progress
        assert mock_logger.progress.called or mock_logger.info.called


class TestAsyncPipelinePerformance:
    """Test performance characteristics."""

    @pytest.mark.asyncio
    async def test_performance_improvement_over_sync(
        self, mock_async_processor, mock_limiter, mock_logger
    ):
        """Test that async pipeline is faster than sync would be."""
        if AsyncProcessingPipeline is None:
            pytest.skip("AsyncProcessingPipeline not yet implemented")

        async def mock_process(page):
            await asyncio.sleep(0.1)  # Simulate API call
            return Mock(
                success=True,
                page_data={"pageNumber": page["pageNumber"]},
                error=None
            )

        mock_async_processor.process = AsyncMock(side_effect=mock_process)
        mock_limiter.get_summary.return_value = {
            "total_processed": 10,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        config = AsyncPipelineConfig(max_concurrency=5)
        pipeline = AsyncProcessingPipeline(
            page_processor=mock_async_processor,
            limiter=mock_limiter,
            logger=mock_logger,
            config=config,
        )

        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": i})
            for i in range(10)
        ]

        import time
        start = time.time()
        result = await pipeline.run(pages)
        duration = time.time() - start

        # Sequential would be 10 * 0.1 = 1.0s
        # With concurrency=5, should be ~0.2s (2 batches)
        # Allow overhead, should be < 0.5s
        assert duration < 0.5
        assert result.total_processed == 10


# Marker for async tests
pytestmark = pytest.mark.asyncio
