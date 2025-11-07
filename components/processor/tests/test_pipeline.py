"""Tests for ProcessingPipeline.

This test suite ensures ProcessingPipeline correctly orchestrates
the complete processing workflow.
"""

import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

# Mock Data class for testing (to avoid langflow dependency in unit tests)
try:
    from langflow.schema import Data
except ImportError:
    class Data:
        """Mock Data class for testing."""
        def __init__(self, data):
            self.data = data

from components.processor.pipeline import (
    ProcessingPipeline,
    PipelineConfig,
    PipelineResult,
)
from components.processor.page_processor import ProcessedPage


@pytest.fixture
def config():
    """Create a test pipeline configuration."""
    return PipelineConfig(
        output_dir=Path("/tmp/test"), random_seed=42, variety_summary={}
    )


@pytest.fixture
def mock_processor():
    """Create a mock PageProcessor."""
    return Mock()


@pytest.fixture
def mock_limiter():
    """Create a mock PageLimiter."""
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
    """Create a mock LoggerFacade."""
    return Mock()


@pytest.fixture
def pipeline(config, mock_processor, mock_limiter, mock_logger):
    """Create a ProcessingPipeline with mocked dependencies."""
    return ProcessingPipeline(
        page_processor=mock_processor,
        limiter=mock_limiter,
        logger=mock_logger,
        config=config,
    )


class TestPipelineConfig:
    """Test PipelineConfig dataclass."""

    def test_default_config(self):
        """Test configuration with defaults."""
        config = PipelineConfig()

        assert config.output_dir is None
        assert config.random_seed is None
        assert config.variety_summary is None

    def test_config_with_values(self):
        """Test configuration with all values set."""
        config = PipelineConfig(
            output_dir=Path("/tmp/test"),
            random_seed=42,
            variety_summary={"coloring": ["elephant"]},
        )

        assert config.output_dir == Path("/tmp/test")
        assert config.random_seed == 42
        assert config.variety_summary == {"coloring": ["elephant"]}


class TestPipelineResult:
    """Test PipelineResult dataclass."""

    def test_result_structure(self):
        """Test PipelineResult structure."""
        result = PipelineResult(
            processed_pages=[Data(data={"page": 1})],
            total_processed=5,
            total_skipped=2,
            duration_seconds=10.5,
            variety_summary={},
            limit_summary={},
            error_pages=[],
        )

        assert len(result.processed_pages) == 1
        assert result.total_processed == 5
        assert result.total_skipped == 2
        assert result.duration_seconds == 10.5
        assert result.error_pages == []

    def test_to_langflow_data(self):
        """Test conversion to Langflow data format."""
        pages = [Data(data={"page": 1}), Data(data={"page": 2})]

        result = PipelineResult(
            processed_pages=pages,
            total_processed=2,
            total_skipped=0,
            duration_seconds=1.0,
            variety_summary={},
            limit_summary={},
        )

        langflow_data = result.to_langflow_data()

        assert langflow_data == pages
        assert len(langflow_data) == 2


class TestPipelineValidation:
    """Test input validation."""

    def test_rejects_none_input(self, pipeline, mock_logger):
        """Test that None input raises ValueError."""
        with pytest.raises(ValueError, match="None"):
            pipeline.run(None)

        mock_logger.error.assert_called()

    def test_rejects_empty_input(self, pipeline, mock_logger):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="empty"):
            pipeline.run([])

        mock_logger.warning.assert_called()

    def test_accepts_valid_input(self, pipeline, mock_processor, mock_limiter):
        """Test that valid input is accepted."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "test", "theme": "test", "pageNumber": 1})]

        result = pipeline.run(pages)

        assert isinstance(result, PipelineResult)

    def test_logs_input_details(self, pipeline, mock_logger, mock_processor, mock_limiter):
        """Test that input details are logged."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "test", "theme": "test", "pageNumber": 1})]

        pipeline.run(pages)

        # Check that logging happened
        assert mock_logger.info.call_count > 0


class TestPipelineProcessing:
    """Test page processing workflow."""

    def test_processes_single_page(
        self, pipeline, mock_processor, mock_limiter, mock_logger
    ):
        """Test processing a single page successfully."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"pageNumber": 1, "type": "coloring"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {"coloring": 1},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "coloring", "theme": "animals", "pageNumber": 1})
        ]

        result = pipeline.run(pages)

        assert len(result.processed_pages) == 1
        mock_processor.process.assert_called_once()
        mock_limiter.mark_processed.assert_called_once_with("coloring")

    def test_processes_multiple_pages(
        self, pipeline, mock_processor, mock_limiter
    ):
        """Test processing multiple pages."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 3,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "coloring", "theme": "animals", "pageNumber": 1}),
            Data(data={"type": "maze", "theme": "space", "pageNumber": 2}),
            Data(data={"type": "tracing", "theme": "letters", "pageNumber": 3}),
        ]

        result = pipeline.run(pages)

        assert len(result.processed_pages) == 3
        assert mock_processor.process.call_count == 3

    def test_sorts_pages_by_number(self, pipeline, mock_processor, mock_limiter):
        """Test that pages are sorted by page number."""
        # Return different page numbers
        mock_processor.process.side_effect = [
            ProcessedPage(success=True, page_data={"pageNumber": 5}),
            ProcessedPage(success=True, page_data={"pageNumber": 2}),
            ProcessedPage(success=True, page_data={"pageNumber": 8}),
        ]
        mock_limiter.get_summary.return_value = {
            "total_processed": 3,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": 5}),
            Data(data={"type": "test", "theme": "test", "pageNumber": 2}),
            Data(data={"type": "test", "theme": "test", "pageNumber": 8}),
        ]

        result = pipeline.run(pages)

        # Check order
        page_numbers = [p.data["pageNumber"] for p in result.processed_pages]
        assert page_numbers == [2, 5, 8]

    def test_shows_progress_indicators(
        self, pipeline, mock_processor, mock_limiter, mock_logger
    ):
        """Test that progress indicators are shown."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 2,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "coloring", "theme": "animals", "pageNumber": 1}),
            Data(data={"type": "maze", "theme": "space", "pageNumber": 2}),
        ]

        pipeline.run(pages)

        # Check progress was logged
        mock_logger.progress.assert_called()


class TestPipelineLimitEnforcement:
    """Test limit enforcement during processing."""

    def test_skips_page_when_limit_reached(
        self, pipeline, mock_processor, mock_limiter, mock_logger
    ):
        """Test that pages are skipped when limits are reached."""
        # First page OK, second page blocked
        mock_limiter.should_process.side_effect = [
            (True, None),
            (False, "Limit reached"),
        ]
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 1,
        }
        mock_limiter.get_skipped_messages.return_value = ["Limit reached"]

        pages = [
            Data(data={"type": "coloring", "theme": "animals", "pageNumber": 1}),
            Data(data={"type": "coloring", "theme": "animals", "pageNumber": 2}),
        ]

        result = pipeline.run(pages)

        # Only first page processed
        assert len(result.processed_pages) == 1
        assert mock_processor.process.call_count == 1
        mock_limiter.track_skip.assert_called_once_with("Limit reached")

    def test_logs_skip_reason(self, pipeline, mock_limiter, mock_logger):
        """Test that skip reasons are logged."""
        mock_limiter.should_process.return_value = (False, "Total limit 10 reached")
        mock_limiter.get_summary.return_value = {
            "total_processed": 0,
            "per_topic_counts": {},
            "skipped_count": 1,
        }
        mock_limiter.get_skipped_messages.return_value = ["Total limit 10 reached"]

        pages = [Data(data={"type": "test", "theme": "test", "pageNumber": 1})]

        result = pipeline.run(pages)

        mock_logger.warning.assert_called()
        # Check skip was tracked
        assert result.total_skipped == 1

    def test_marks_processed_after_success(
        self, pipeline, mock_processor, mock_limiter
    ):
        """Test that limiter is updated after successful processing."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "coloring", "theme": "test", "pageNumber": 1})]

        pipeline.run(pages)

        mock_limiter.mark_processed.assert_called_once_with("coloring")


class TestPipelineErrorHandling:
    """Test error handling during processing."""

    def test_continues_after_page_error(
        self, pipeline, mock_processor, mock_limiter, mock_logger
    ):
        """Test that pipeline continues after individual page errors."""
        # First page fails, second succeeds
        mock_processor.process.side_effect = [
            ProcessedPage(success=False, page_data={"error": "failed"}, error="Test error"),
            ProcessedPage(success=True, page_data={"success": True}),
        ]
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": 1}),
            Data(data={"type": "test", "theme": "test", "pageNumber": 2}),
        ]

        result = pipeline.run(pages)

        # Both pages should be in result (fail-safe)
        assert len(result.processed_pages) == 2
        mock_logger.error.assert_called()

    def test_includes_error_pages_in_result(
        self, pipeline, mock_processor, mock_limiter
    ):
        """Test that error pages are included in results."""
        mock_processor.process.return_value = ProcessedPage(
            success=False, page_data={"error": "failed"}, error="API error"
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 0,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "test", "theme": "test", "pageNumber": 1})]

        result = pipeline.run(pages)

        # Error page should still be in results
        assert len(result.processed_pages) == 1
        assert "error" in result.processed_pages[0].data


class TestPipelineSummary:
    """Test summary generation."""

    def test_includes_processing_stats(self, pipeline, mock_processor, mock_limiter):
        """Test that summary includes all statistics."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 3,
            "per_topic_counts": {"coloring": 2, "maze": 1},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "coloring", "theme": "test", "pageNumber": i})
            for i in range(3)
        ]

        result = pipeline.run(pages)

        assert result.total_processed == 3
        assert result.total_skipped == 0
        assert isinstance(result.duration_seconds, float)
        assert result.duration_seconds > 0

    def test_includes_variety_summary(self, pipeline, mock_processor, mock_limiter):
        """Test that variety summary is included."""
        variety = {"coloring": ["elephant", "lion"], "maze": ["castle"]}
        config_with_variety = PipelineConfig(variety_summary=variety)

        pipeline_with_variety = ProcessingPipeline(
            page_processor=mock_processor,
            limiter=mock_limiter,
            logger=Mock(),
            config=config_with_variety,
        )

        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "test", "theme": "test", "pageNumber": 1})]

        result = pipeline_with_variety.run(pages)

        assert result.variety_summary == variety

    def test_logs_final_summary(self, pipeline, mock_processor, mock_limiter, mock_logger):
        """Test that final summary is logged."""
        mock_processor.process.return_value = ProcessedPage(
            success=True, page_data={"test": "data"}
        )
        mock_limiter.get_summary.return_value = {
            "total_processed": 1,
            "per_topic_counts": {"coloring": 1},
            "skipped_count": 0,
        }

        pages = [Data(data={"type": "test", "theme": "test", "pageNumber": 1})]

        pipeline.run(pages)

        # Check summary section was logged
        assert mock_logger.section_header.call_count >= 1
        assert mock_logger.info.call_count > 0


class TestPipelineIntegration:
    """Integration tests for complete workflows."""

    def test_complete_successful_workflow(
        self, pipeline, mock_processor, mock_limiter
    ):
        """Test a complete successful processing workflow."""
        # Setup
        mock_processor.process.side_effect = [
            ProcessedPage(success=True, page_data={"pageNumber": 1, "type": "coloring"}),
            ProcessedPage(success=True, page_data={"pageNumber": 2, "type": "maze"}),
            ProcessedPage(success=True, page_data={"pageNumber": 3, "type": "tracing"}),
        ]
        mock_limiter.get_summary.return_value = {
            "total_processed": 3,
            "per_topic_counts": {"coloring": 1, "maze": 1, "tracing": 1},
            "skipped_count": 0,
        }

        pages = [
            Data(data={"type": "coloring", "theme": "animals", "pageNumber": 1}),
            Data(data={"type": "maze", "theme": "space", "pageNumber": 2}),
            Data(data={"type": "tracing", "theme": "letters", "pageNumber": 3}),
        ]

        # Execute
        result = pipeline.run(pages)

        # Verify
        assert result.total_processed == 3
        assert result.total_skipped == 0
        assert len(result.processed_pages) == 3
        assert result.duration_seconds > 0

    def test_workflow_with_limits_and_errors(
        self, pipeline, mock_processor, mock_limiter
    ):
        """Test workflow with both limits and errors."""
        # Page 1: Success
        # Page 2: Skipped (limit)
        # Page 3: Error
        # Page 4: Success

        mock_limiter.should_process.side_effect = [
            (True, None),
            (False, "Limit reached"),
            (True, None),
            (True, None),
        ]

        mock_processor.process.side_effect = [
            ProcessedPage(success=True, page_data={"pageNumber": 1}),
            ProcessedPage(
                success=False, page_data={"pageNumber": 3, "error": "failed"}, error="API error"
            ),
            ProcessedPage(success=True, page_data={"pageNumber": 4}),
        ]

        mock_limiter.get_summary.return_value = {
            "total_processed": 2,
            "per_topic_counts": {},
            "skipped_count": 1,
        }
        mock_limiter.get_skipped_messages.return_value = ["Limit reached"]

        pages = [
            Data(data={"type": "test", "theme": "test", "pageNumber": i})
            for i in range(1, 5)
        ]

        result = pipeline.run(pages)

        # 3 pages processed (1 success, 1 error, 1 success), 1 skipped
        assert len(result.processed_pages) == 3
        assert result.total_skipped == 1
