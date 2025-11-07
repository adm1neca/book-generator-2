"""Tests for LoggerFacade.

This test suite ensures that LoggerFacade correctly routes messages to both
CLI output and session logging, and that CLI output can be disabled for testing.
"""

import pytest
from unittest.mock import Mock, call

from components.logging import SessionLogger
from components.processor.logger_facade import LoggerFacade


@pytest.fixture
def mock_session_logger():
    """Create a mock SessionLogger."""
    return Mock(spec=SessionLogger)


@pytest.fixture
def logger(mock_session_logger):
    """Create a LoggerFacade with CLI enabled."""
    return LoggerFacade(mock_session_logger, cli_enabled=True)


@pytest.fixture
def silent_logger(mock_session_logger):
    """Create a LoggerFacade with CLI disabled."""
    return LoggerFacade(mock_session_logger, cli_enabled=False)


class TestLoggerFacadeInfo:
    """Test suite for info logging."""

    def test_info_logs_to_session(self, logger, mock_session_logger):
        """Test that info messages are logged to session."""
        logger.info("Test message")
        mock_session_logger.log.assert_called_once_with("Test message")

    def test_info_prints_to_cli_when_enabled(self, logger, capsys):
        """Test that info messages print to CLI when enabled."""
        logger.info("CLI message")
        captured = capsys.readouterr()
        assert "CLI message" in captured.out

    def test_info_does_not_print_when_cli_disabled(self, silent_logger, capsys):
        """Test that info messages don't print when CLI disabled."""
        silent_logger.info("Should not print")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_info_still_logs_to_session_when_cli_disabled(
        self, silent_logger, mock_session_logger
    ):
        """Test that session logging works even when CLI is disabled."""
        silent_logger.info("Session only")
        mock_session_logger.log.assert_called_once_with("Session only")

    def test_info_respects_show_cli_parameter(self, logger, capsys):
        """Test that show_cli=False suppresses CLI output."""
        logger.info("Hidden message", show_cli=False)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_info_with_show_cli_false_still_logs_to_session(
        self, logger, mock_session_logger
    ):
        """Test that session logging works when show_cli=False."""
        logger.info("Session message", show_cli=False)
        mock_session_logger.log.assert_called_once_with("Session message")


class TestLoggerFacadeError:
    """Test suite for error logging."""

    def test_error_adds_prefix(self, logger, mock_session_logger):
        """Test that error messages get ERROR prefix."""
        logger.error("Something failed")
        mock_session_logger.log.assert_called_once_with("ERROR: Something failed")

    def test_error_prints_to_cli(self, logger, capsys):
        """Test that error messages print to CLI."""
        logger.error("Test error")
        captured = capsys.readouterr()
        assert "ERROR: Test error" in captured.out

    def test_error_respects_cli_disabled(self, silent_logger, capsys):
        """Test that errors don't print when CLI is disabled."""
        silent_logger.error("Silent error")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_error_respects_show_cli_parameter(self, logger, capsys):
        """Test that show_cli=False suppresses error CLI output."""
        logger.error("Hidden error", show_cli=False)
        captured = capsys.readouterr()
        assert captured.out == ""


class TestLoggerFacadeWarning:
    """Test suite for warning logging."""

    def test_warning_adds_prefix(self, logger, mock_session_logger):
        """Test that warning messages get WARNING prefix."""
        logger.warning("Be careful")
        mock_session_logger.log.assert_called_once_with("WARNING: Be careful")

    def test_warning_prints_to_cli(self, logger, capsys):
        """Test that warning messages print to CLI."""
        logger.warning("Test warning")
        captured = capsys.readouterr()
        assert "WARNING: Test warning" in captured.out

    def test_warning_respects_cli_disabled(self, silent_logger, capsys):
        """Test that warnings don't print when CLI is disabled."""
        silent_logger.warning("Silent warning")
        captured = capsys.readouterr()
        assert captured.out == ""


class TestLoggerFacadeDebug:
    """Test suite for debug logging."""

    def test_debug_adds_prefix(self, logger, mock_session_logger):
        """Test that debug messages get DEBUG prefix."""
        logger.debug("Debug info")
        mock_session_logger.log.assert_called_once_with("DEBUG: Debug info")

    def test_debug_does_not_print_by_default(self, logger, capsys):
        """Test that debug messages don't print to CLI by default."""
        logger.debug("Debug message")
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_debug_prints_when_show_cli_true(self, logger, capsys):
        """Test that debug messages print when explicitly requested."""
        logger.debug("Debug message", show_cli=True)
        captured = capsys.readouterr()
        assert "DEBUG: Debug message" in captured.out


class TestLoggerFacadeSectionHeader:
    """Test suite for section headers."""

    def test_section_header_format(self, logger, capsys):
        """Test section header formatting."""
        logger.section_header("TEST SECTION")
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert len(lines) == 3
        assert lines[0] == "=" * 60
        assert lines[1] == "TEST SECTION"
        assert lines[2] == "=" * 60

    def test_section_header_custom_char(self, logger, capsys):
        """Test section header with custom character."""
        logger.section_header("CUSTOM", char="-", width=20)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert lines[0] == "-" * 20
        assert lines[1] == "CUSTOM"
        assert lines[2] == "-" * 20

    def test_section_header_custom_width(self, logger, capsys):
        """Test section header with custom width."""
        logger.section_header("WIDE", char="#", width=80)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")

        assert lines[0] == "#" * 80
        assert lines[2] == "#" * 80

    def test_section_header_logs_to_session(self, logger, mock_session_logger):
        """Test that section headers are logged to session."""
        logger.section_header("SECTION")
        # Should log: border + title + border = 3 calls
        assert mock_session_logger.log.call_count == 3


class TestLoggerFacadeProgress:
    """Test suite for progress indicators."""

    def test_progress_format(self, logger, capsys):
        """Test progress indicator format."""
        logger.progress(5, 10, "Processing pages")
        captured = capsys.readouterr()
        assert "[5/10] Processing pages" in captured.out

    def test_progress_without_message(self, logger, capsys):
        """Test progress indicator without message."""
        logger.progress(3, 7)
        captured = capsys.readouterr()
        assert "[3/7]" in captured.out
        # Should not have extra space after bracket
        assert captured.out.strip() == "[3/7]"

    def test_progress_with_empty_message(self, logger, capsys):
        """Test progress indicator with empty string message."""
        logger.progress(1, 5, "")
        captured = capsys.readouterr()
        assert captured.out.strip() == "[1/5]"

    def test_progress_logs_to_session(self, logger, mock_session_logger):
        """Test that progress is logged to session."""
        logger.progress(5, 10, "Test")
        mock_session_logger.log.assert_called_once_with("[5/10] Test")


class TestLoggerFacadeSummary:
    """Test suite for summary formatting."""

    def test_summary_format(self, logger, capsys):
        """Test summary formatting."""
        stats = {"Total pages": 20, "Duration": "45.2s", "Errors": 0}
        logger.summary(stats)
        captured = capsys.readouterr()

        assert "SUMMARY" in captured.out
        assert "Total pages: 20" in captured.out
        assert "Duration: 45.2s" in captured.out
        assert "Errors: 0" in captured.out

    def test_summary_with_empty_dict(self, logger, capsys):
        """Test summary with no stats."""
        logger.summary({})
        captured = capsys.readouterr()

        # Should still have headers
        assert "SUMMARY" in captured.out
        lines = captured.out.strip().split("\n")
        # Header border + SUMMARY + Header border + Footer border = 4 lines
        assert len(lines) == 4

    def test_summary_logs_to_session(self, logger, mock_session_logger):
        """Test that summary items are logged to session."""
        stats = {"Test": "value"}
        logger.summary(stats)

        # Should log: border + SUMMARY + border + stat line + border = 5 calls
        assert mock_session_logger.log.call_count == 5

    def test_summary_with_various_value_types(self, logger, capsys):
        """Test summary with different value types."""
        stats = {
            "String": "test",
            "Integer": 42,
            "Float": 3.14,
            "Boolean": True,
            "None": None,
        }
        logger.summary(stats)
        captured = capsys.readouterr()

        assert "String: test" in captured.out
        assert "Integer: 42" in captured.out
        assert "Float: 3.14" in captured.out
        assert "Boolean: True" in captured.out
        assert "None: None" in captured.out


class TestLoggerFacadeIntegration:
    """Integration tests with real SessionLogger."""

    def test_with_real_session_logger(self, capsys):
        """Test LoggerFacade with real SessionLogger."""
        session = SessionLogger()
        logger = LoggerFacade(session, cli_enabled=True)

        logger.info("Integration test")
        logger.error("Test error")
        logger.warning("Test warning")

        # Verify CLI output
        captured = capsys.readouterr()
        assert "Integration test" in captured.out
        assert "ERROR: Test error" in captured.out
        assert "WARNING: Test warning" in captured.out

        # Verify session logs
        logs = session.messages
        assert len(logs) == 3
        assert any("Integration test" in log for log in logs)
        assert any("ERROR: Test error" in log for log in logs)
        assert any("WARNING: Test warning" in log for log in logs)

    def test_complete_workflow(self, capsys):
        """Test a complete logging workflow."""
        session = SessionLogger()
        logger = LoggerFacade(session, cli_enabled=True)

        # Simulate a processing workflow
        logger.section_header("PROCESSING WORKFLOW")
        logger.info("Starting processing...")

        for i in range(1, 4):
            logger.progress(i, 3, f"Processing item {i}")

        logger.warning("Skipped one item")
        logger.error("Failed to process one item")

        logger.summary(
            {"Total": 3, "Success": 1, "Skipped": 1, "Failed": 1, "Duration": "5.2s"}
        )

        # Verify all messages appear in CLI
        captured = capsys.readouterr()
        assert "PROCESSING WORKFLOW" in captured.out
        assert "Starting processing..." in captured.out
        assert "[1/3]" in captured.out
        assert "[2/3]" in captured.out
        assert "[3/3]" in captured.out
        assert "WARNING: Skipped one item" in captured.out
        assert "ERROR: Failed to process one item" in captured.out
        assert "SUMMARY" in captured.out
        assert "Total: 3" in captured.out

        # Verify session captured everything
        logs = session.messages
        assert len(logs) > 10  # Multiple log entries


class TestLoggerFacadeEdgeCases:
    """Test edge cases and error conditions."""

    def test_multiline_message(self, logger, capsys):
        """Test logging multiline messages."""
        message = "Line 1\nLine 2\nLine 3"
        logger.info(message)
        captured = capsys.readouterr()
        assert "Line 1" in captured.out
        assert "Line 2" in captured.out
        assert "Line 3" in captured.out

    def test_empty_message(self, logger, mock_session_logger, capsys):
        """Test logging empty message."""
        logger.info("")
        mock_session_logger.log.assert_called_once_with("")
        captured = capsys.readouterr()
        # Should produce an empty line
        assert captured.out == "\n"

    def test_message_with_special_characters(self, logger, capsys):
        """Test logging messages with special characters."""
        message = "Test: 100% complete! @user #tag $value & more"
        logger.info(message)
        captured = capsys.readouterr()
        assert message in captured.out

    def test_unicode_message(self, logger, capsys):
        """Test logging Unicode characters."""
        message = "Unicode test: 🎉 ✓ → ← ↑ ↓"
        logger.info(message)
        captured = capsys.readouterr()
        assert "Unicode test:" in captured.out

    def test_very_long_message(self, logger, capsys):
        """Test logging very long messages."""
        message = "A" * 1000
        logger.info(message)
        captured = capsys.readouterr()
        assert len(captured.out.strip()) == 1000
