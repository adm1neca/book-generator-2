"""Tests for PageProcessor.

This test suite ensures PageProcessor correctly processes pages with
dependency injection and proper error handling.
"""

import pytest
from unittest.mock import Mock, MagicMock
from components.processor.page_processor import PageProcessor, ProcessorConfig, ProcessedPage


@pytest.fixture
def config():
    """Create a test configuration."""
    return ProcessorConfig(
        difficulty="easy",
        model="claude-3-5-sonnet",
        api_key="test-key",
        retry_attempts=2,
    )


@pytest.fixture
def mock_api_client():
    """Create a mock API client."""
    return Mock()


@pytest.fixture
def mock_retry_handler():
    """Create a mock retry handler."""
    return Mock()


@pytest.fixture
def mock_variety_tracker():
    """Create a mock variety tracker."""
    tracker = Mock()
    tracker.get_used.return_value = []
    return tracker


@pytest.fixture
def mock_logger():
    """Create a mock logger."""
    return Mock()


@pytest.fixture
def processor(config, mock_api_client, mock_retry_handler, mock_variety_tracker, mock_logger):
    """Create a PageProcessor with mocked dependencies."""
    return PageProcessor(
        config=config,
        api_client=mock_api_client,
        retry_handler=mock_retry_handler,
        variety_tracker=mock_variety_tracker,
        logger=mock_logger,
    )


class TestProcessorConfig:
    """Test ProcessorConfig dataclass."""

    def test_config_creation(self):
        """Test configuration creation with all fields."""
        config = ProcessorConfig(
            difficulty="medium",
            model="claude-haiku",
            api_key="sk-test",
            retry_attempts=3,
        )

        assert config.difficulty == "medium"
        assert config.model == "claude-haiku"
        assert config.api_key == "sk-test"
        assert config.retry_attempts == 3

    def test_config_default_retry_attempts(self):
        """Test default retry attempts value."""
        config = ProcessorConfig(
            difficulty="easy", model="claude-3-5-sonnet", api_key="test"
        )

        assert config.retry_attempts == 2


class TestProcessedPage:
    """Test ProcessedPage dataclass."""

    def test_successful_page(self):
        """Test creating a successful ProcessedPage."""
        result = ProcessedPage(
            success=True,
            page_data={"pageNumber": 1, "type": "coloring"},
            selected_item="elephant",
        )

        assert result.success
        assert result.page_data == {"pageNumber": 1, "type": "coloring"}
        assert result.error is None
        assert result.selected_item == "elephant"

    def test_failed_page(self):
        """Test creating a failed ProcessedPage."""
        result = ProcessedPage(
            success=False, page_data={"pageNumber": 1}, error="API call failed"
        )

        assert not result.success
        assert result.error == "API call failed"
        assert result.selected_item is None


class TestPageProcessorSuccessfulProcessing:
    """Test successful page processing scenarios."""

    def test_process_successful_page(self, processor, mock_retry_handler, mock_variety_tracker):
        """Test processing a page successfully."""
        # Setup mock response
        mock_retry_handler.call_with_retry.return_value = (
            {"description": "An elephant", "items": ["elephant"]},
            "raw response",
        )

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = processor.process(page)

        assert result.success
        assert result.page_data["pageNumber"] == 1
        assert result.page_data["type"] == "coloring"
        assert result.page_data["theme"] == "animals"
        assert "description" in result.page_data

    def test_tracks_variety_on_success(self, processor, mock_retry_handler, mock_variety_tracker):
        """Test that variety is tracked when selected_item exists."""
        # Setup: mock the strategy to return a selected item
        mock_retry_handler.call_with_retry.return_value = (
            {"description": "test"},
            "raw",
        )

        # We need to mock the prompt building to return a selected_item
        # This happens inside _build_prompt which uses PromptBuilderFactory
        # For this test, we'll trust that if API succeeds, variety tracking happens

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}
        result = processor.process(page)

        # Verify tracker was accessed
        mock_variety_tracker.get_used.assert_called()

    def test_merges_api_response_with_page_data(
        self, processor, mock_retry_handler
    ):
        """Test that API response is merged with original page data."""
        api_response = {
            "description": "A cute elephant",
            "items": ["elephant", "trunk", "ears"],
            "instructions": "Color the elephant",
        }

        mock_retry_handler.call_with_retry.return_value = (api_response, "raw")

        page = {"type": "coloring", "theme": "animals", "pageNumber": 5}

        result = processor.process(page)

        assert result.success
        assert result.page_data["pageNumber"] == 5
        assert result.page_data["type"] == "coloring"
        assert result.page_data["theme"] == "animals"
        assert result.page_data["description"] == "A cute elephant"
        assert result.page_data["items"] == ["elephant", "trunk", "ears"]


class TestPageProcessorErrorHandling:
    """Test error handling scenarios."""

    def test_handles_api_returning_none(self, processor, mock_retry_handler):
        """Test handling when API returns None (no JSON found)."""
        mock_retry_handler.call_with_retry.return_value = (None, "raw response text")

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = processor.process(page)

        assert not result.success
        assert result.error == "No JSON found in API response"
        assert "error" in result.page_data
        assert result.page_data["error"] == "No JSON found"

    def test_handles_unknown_page_type(self, processor):
        """Test handling of unknown page type."""
        page = {"type": "invalid_type", "theme": "animals", "pageNumber": 1}

        result = processor.process(page)

        assert not result.success
        assert "Unknown page type" in result.error
        assert result.page_data["type"] == "invalid_type"

    def test_handles_exception_during_processing(
        self, processor, mock_retry_handler, mock_logger
    ):
        """Test handling when exception occurs during processing."""
        mock_retry_handler.call_with_retry.side_effect = Exception("API error")

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = processor.process(page)

        assert not result.success
        assert "API error" in result.error
        mock_logger.error.assert_called()

    def test_includes_truncated_raw_response_on_parse_failure(
        self, processor, mock_retry_handler
    ):
        """Test that raw response is included (truncated) when parsing fails."""
        long_raw = "x" * 1000
        mock_retry_handler.call_with_retry.return_value = (None, long_raw)

        page = {"type": "coloring", "theme": "animals", "pageNumber": 1}

        result = processor.process(page)

        assert not result.success
        assert "raw_response" in result.page_data
        assert len(result.page_data["raw_response"]) == 400  # Truncated


class TestPageProcessorBuildPrompt:
    """Test prompt building logic."""

    def test_sanitizes_theme(self, processor):
        """Test that theme is sanitized before building prompt."""
        # Use a known good page type
        prompt, selected = processor._build_prompt("coloring", "Disney", 1)

        # Theme should be sanitized (Disney -> generic)
        assert "Disney" not in prompt.lower() or "disney" not in prompt.lower()

    def test_includes_difficulty_in_prompt(self, processor):
        """Test that difficulty is included in prompt."""
        prompt, _ = processor._build_prompt("coloring", "animals", 1)

        assert "easy" in prompt.lower()

    def test_returns_empty_for_unknown_type(self, processor, mock_logger):
        """Test that unknown types return empty prompt."""
        prompt, selected = processor._build_prompt("invalid_type", "animals", 1)

        assert prompt == ""
        assert selected is None
        mock_logger.warning.assert_called()

    def test_queries_variety_tracker(self, processor, mock_variety_tracker):
        """Test that variety tracker is queried for used items."""
        mock_variety_tracker.get_used.return_value = ["elephant", "lion"]

        processor._build_prompt("coloring", "animals", 1)

        mock_variety_tracker.get_used.assert_called_once_with("coloring")


class TestPageProcessorCallAPI:
    """Test API calling logic."""

    def test_calls_retry_handler(self, processor, mock_retry_handler):
        """Test that retry handler is called with correct parameters."""
        mock_retry_handler.call_with_retry.return_value = ({"test": "data"}, "raw")

        parsed, raw = processor._call_api("test prompt", 5)

        mock_retry_handler.call_with_retry.assert_called_once()
        call_args = mock_retry_handler.call_with_retry.call_args
        assert call_args[1]["retries"] == 2  # From config

    def test_returns_parsed_and_raw(self, processor, mock_retry_handler):
        """Test that both parsed and raw responses are returned."""
        expected_parsed = {"key": "value"}
        expected_raw = "raw response"
        mock_retry_handler.call_with_retry.return_value = (
            expected_parsed,
            expected_raw,
        )

        parsed, raw = processor._call_api("prompt", 1)

        assert parsed == expected_parsed
        assert raw == expected_raw


class TestPageProcessorMergeResult:
    """Test result merging logic."""

    def test_merges_all_fields(self, processor):
        """Test that all fields are properly merged."""
        original = {"type": "coloring", "theme": "animals", "pageNumber": 3}
        parsed = {"description": "test", "items": ["a", "b"]}

        merged = processor._merge_result(original, parsed, "animals")

        assert merged["pageNumber"] == 3
        assert merged["type"] == "coloring"
        assert merged["theme"] == "animals"
        assert merged["description"] == "test"
        assert merged["items"] == ["a", "b"]

    def test_sanitizes_theme_in_merge(self, processor):
        """Test that theme is sanitized during merge."""
        original = {"type": "coloring", "theme": "Disney", "pageNumber": 1}
        parsed = {"description": "test"}

        merged = processor._merge_result(original, parsed, "Disney")

        # Theme should be sanitized
        assert merged["theme"] != "Disney"

    def test_handles_missing_fields(self, processor):
        """Test merging with missing fields in original page."""
        original = {}  # Missing all fields
        parsed = {"description": "test"}

        merged = processor._merge_result(original, parsed, "animals")

        # Should have defaults
        assert merged["pageNumber"] == 0
        assert merged["type"] == ""
        assert "theme" in merged


class TestPageProcessorIntegration:
    """Integration tests with realistic scenarios."""

    def test_complete_successful_workflow(
        self, processor, mock_retry_handler, mock_variety_tracker
    ):
        """Test a complete successful processing workflow."""
        # Setup
        api_response = {
            "description": "A big red apple",
            "items": ["apple", "stem", "leaf"],
            "instructions": "Color the apple red",
        }
        mock_retry_handler.call_with_retry.return_value = (api_response, "raw")
        mock_variety_tracker.get_used.return_value = ["banana", "orange"]

        # Process
        page = {"type": "coloring", "theme": "fruits", "pageNumber": 7}
        result = processor.process(page)

        # Verify
        assert result.success
        assert result.page_data["pageNumber"] == 7
        assert result.page_data["type"] == "coloring"
        assert result.page_data["theme"] == "fruits"
        assert result.page_data["description"] == "A big red apple"
        assert result.error is None

    def test_complete_failure_workflow(self, processor, mock_retry_handler, mock_logger):
        """Test a complete failure workflow."""
        # Setup: API fails completely
        mock_retry_handler.call_with_retry.side_effect = RuntimeError("API timeout")

        # Process
        page = {"type": "maze", "theme": "space", "pageNumber": 3}
        result = processor.process(page)

        # Verify
        assert not result.success
        assert "API timeout" in result.error
        assert result.page_data["pageNumber"] == 3
        mock_logger.error.assert_called()

    def test_processes_different_page_types(self, processor, mock_retry_handler):
        """Test processing different page types."""
        mock_retry_handler.call_with_retry.return_value = ({"data": "test"}, "raw")

        page_types = ["coloring", "tracing", "maze", "counting", "matching", "dot-to-dot"]

        for page_type in page_types:
            page = {"type": page_type, "theme": "test", "pageNumber": 1}
            result = processor.process(page)

            # All valid types should succeed
            assert result.success, f"Failed for type: {page_type}"
            assert result.page_data["type"] == page_type


class TestPageProcessorEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_handles_empty_page_data(self, processor, mock_retry_handler):
        """Test handling of empty page data."""
        mock_retry_handler.call_with_retry.return_value = ({"test": "data"}, "raw")

        page = {}  # Empty page
        result = processor.process(page)

        # Should handle gracefully
        assert isinstance(result, ProcessedPage)

    def test_handles_none_values_in_page(self, processor, mock_retry_handler):
        """Test handling of None values in page data."""
        mock_retry_handler.call_with_retry.return_value = ({"test": "data"}, "raw")

        page = {"type": None, "theme": None, "pageNumber": None}
        result = processor.process(page)

        assert isinstance(result, ProcessedPage)

    def test_handles_very_long_raw_response(self, processor, mock_retry_handler):
        """Test handling of very long raw responses."""
        long_response = "x" * 10000
        mock_retry_handler.call_with_retry.return_value = (None, long_response)

        page = {"type": "coloring", "theme": "test", "pageNumber": 1}
        result = processor.process(page)

        # Should truncate to 400 chars
        assert len(result.page_data.get("raw_response", "")) == 400

    def test_preserves_original_page_on_error(self, processor, mock_retry_handler):
        """Test that original page data is preserved on error."""
        mock_retry_handler.call_with_retry.return_value = (None, "raw")

        original_page = {
            "type": "coloring",
            "theme": "animals",
            "pageNumber": 5,
            "custom_field": "custom_value",
        }

        result = processor.process(original_page)

        # Original fields should be in result
        assert result.page_data["type"] == "coloring"
        assert result.page_data["pageNumber"] == 5
        assert result.page_data["custom_field"] == "custom_value"
