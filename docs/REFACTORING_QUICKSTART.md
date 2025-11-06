# Refactoring Quick Start Guide

## Getting Started in 5 Minutes

This guide will help you start the refactoring by implementing the first module: **LoggerFacade**.

---

## Why Start with LoggerFacade?

1. **Simplest module** - No complex dependencies
2. **High impact** - Used everywhere in the codebase
3. **Easy to test** - Pure functionality, easy mocking
4. **Quick win** - Can complete in 2 hours
5. **Foundation** - Other modules will use it

---

## Step 1: Create Directory Structure (2 minutes)

```bash
# Create the processor module directory
mkdir -p components/processor/tests

# Create __init__ files
touch components/processor/__init__.py
touch components/processor/tests/__init__.py
```

---

## Step 2: Implement LoggerFacade (30 minutes)

Create `components/processor/logger_facade.py`:

```python
"""Unified logging facade for Claude Processor.

Provides a consistent interface for both CLI output and structured session logging.
"""

from typing import Dict, Any, Optional
from components.logging import SessionLogger


class LoggerFacade:
    """Unified logging interface combining CLI and structured logging.

    Example:
        >>> logger = LoggerFacade(session_logger, cli_enabled=True)
        >>> logger.info("Processing started")
        >>> logger.section_header("VALIDATION")
        >>> logger.progress(5, 10, "Processing pages")
    """

    def __init__(self, session_logger: SessionLogger, cli_enabled: bool = True):
        """Initialize the logger facade.

        Args:
            session_logger: The SessionLogger instance for structured logging
            cli_enabled: Whether to output to CLI (default True)
        """
        self.session = session_logger
        self.cli_enabled = cli_enabled

    def info(self, message: str, show_cli: bool = True) -> None:
        """Log an info message.

        Args:
            message: The message to log
            show_cli: Whether to also print to CLI (default True)
        """
        # Always log to session
        self.session.log(message)

        # Optionally print to CLI
        if self.cli_enabled and show_cli:
            print(message)

    def error(self, message: str, show_cli: bool = True) -> None:
        """Log an error message.

        Args:
            message: The error message to log
            show_cli: Whether to also print to CLI (default True)
        """
        error_msg = f"ERROR: {message}"
        self.session.log(error_msg)

        if self.cli_enabled and show_cli:
            print(error_msg)

    def warning(self, message: str, show_cli: bool = True) -> None:
        """Log a warning message.

        Args:
            message: The warning message to log
            show_cli: Whether to also print to CLI (default True)
        """
        warning_msg = f"WARNING: {message}"
        self.session.log(warning_msg)

        if self.cli_enabled and show_cli:
            print(warning_msg)

    def section_header(self, title: str, char: str = "=", width: int = 60) -> None:
        """Print a formatted section header.

        Args:
            title: The section title
            char: Character to use for the border (default "=")
            width: Width of the header (default 60)

        Example:
            >>> logger.section_header("PROCESSING")
            ============================================================
            PROCESSING
            ============================================================
        """
        border = char * width
        self.info(border)
        self.info(title)
        self.info(border)

    def progress(self, current: int, total: int, message: str = "") -> None:
        """Show progress indicator.

        Args:
            current: Current item number (1-indexed)
            total: Total number of items
            message: Optional message to display

        Example:
            >>> logger.progress(5, 10, "Processing pages")
            [5/10] Processing pages
        """
        progress_msg = f"[{current}/{total}]"
        if message:
            progress_msg += f" {message}"

        self.info(progress_msg)

    def summary(self, stats: Dict[str, Any]) -> None:
        """Print a formatted summary.

        Args:
            stats: Dictionary of statistics to display

        Example:
            >>> logger.summary({
            ...     "Total pages": 20,
            ...     "Duration": "45.2s",
            ...     "Errors": 0
            ... })
        """
        self.section_header("SUMMARY")
        for key, value in stats.items():
            self.info(f"{key}: {value}")
        self.info("=" * 60)
```

**Validation**: File should be ~150 lines, well-documented

---

## Step 3: Write Tests (45 minutes)

Create `components/processor/tests/test_logger_facade.py`:

```python
"""Tests for LoggerFacade."""

import pytest
from unittest.mock import Mock, call
from io import StringIO
import sys

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


class TestLoggerFacade:
    """Test suite for LoggerFacade."""

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

    def test_info_respects_show_cli_parameter(self, logger, capsys):
        """Test that show_cli=False suppresses CLI output."""
        logger.info("Hidden message", show_cli=False)
        captured = capsys.readouterr()
        assert captured.out == ""

    def test_error_adds_prefix(self, logger, mock_session_logger):
        """Test that error messages get ERROR prefix."""
        logger.error("Something failed")
        mock_session_logger.log.assert_called_once_with("ERROR: Something failed")

    def test_error_prints_to_cli(self, logger, capsys):
        """Test that error messages print to CLI."""
        logger.error("Test error")
        captured = capsys.readouterr()
        assert "ERROR: Test error" in captured.out

    def test_warning_adds_prefix(self, logger, mock_session_logger):
        """Test that warning messages get WARNING prefix."""
        logger.warning("Be careful")
        mock_session_logger.log.assert_called_once_with("WARNING: Be careful")

    def test_warning_prints_to_cli(self, logger, capsys):
        """Test that warning messages print to CLI."""
        logger.warning("Test warning")
        captured = capsys.readouterr()
        assert "WARNING: Test warning" in captured.out

    def test_section_header_format(self, logger, capsys):
        """Test section header formatting."""
        logger.section_header("TEST SECTION")
        captured = capsys.readouterr()
        lines = captured.out.strip().split('\n')

        assert len(lines) == 3
        assert lines[0] == "=" * 60
        assert lines[1] == "TEST SECTION"
        assert lines[2] == "=" * 60

    def test_section_header_custom_char(self, logger, capsys):
        """Test section header with custom character."""
        logger.section_header("CUSTOM", char="-", width=20)
        captured = capsys.readouterr()
        lines = captured.out.strip().split('\n')

        assert lines[0] == "-" * 20
        assert lines[1] == "CUSTOM"
        assert lines[2] == "-" * 20

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

    def test_summary_format(self, logger, capsys):
        """Test summary formatting."""
        stats = {
            "Total pages": 20,
            "Duration": "45.2s",
            "Errors": 0
        }
        logger.summary(stats)
        captured = capsys.readouterr()

        assert "SUMMARY" in captured.out
        assert "Total pages: 20" in captured.out
        assert "Duration: 45.2s" in captured.out
        assert "Errors: 0" in captured.out

    def test_summary_logs_to_session(self, logger, mock_session_logger):
        """Test that summary items are logged to session."""
        stats = {"Test": "value"}
        logger.summary(stats)

        # Should log: border + SUMMARY + border + Test: value + border
        assert mock_session_logger.log.call_count >= 5


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
        logs = session.get_logs()
        assert len(logs) == 3
        assert any("Integration test" in log for log in logs)
```

**Validation**: Run tests with `pytest components/processor/tests/test_logger_facade.py -v`

---

## Step 4: Update Module Exports (2 minutes)

Update `components/processor/__init__.py`:

```python
"""Processor module for Claude activity generation.

This module contains the refactored processing pipeline components.
"""

from .logger_facade import LoggerFacade

__all__ = [
    'LoggerFacade',
]

__version__ = '1.0.0'
```

---

## Step 5: Run Tests (5 minutes)

```bash
# Run the tests with coverage
pytest components/processor/tests/test_logger_facade.py -v --cov=components/processor

# Expected output:
# ============================= test session starts ==============================
# collected 15 items
#
# components/processor/tests/test_logger_facade.py::TestLoggerFacade::test_info_logs_to_session PASSED
# ... (all tests should pass)
#
# ----------- coverage: platform linux, python 3.x -----------
# Name                                    Stmts   Miss  Cover
# -----------------------------------------------------------
# components/processor/logger_facade.py      45      0   100%
# -----------------------------------------------------------
# TOTAL                                       45      0   100%
```

---

## Step 6: Try It Out (10 minutes)

Create a test script `test_logger_demo.py`:

```python
"""Demo script for LoggerFacade."""

from components.logging import SessionLogger
from components.processor import LoggerFacade


def main():
    # Initialize logger
    session = SessionLogger()
    logger = LoggerFacade(session, cli_enabled=True)

    # Test different log types
    logger.section_header("LOGGER FACADE DEMO")

    logger.info("This is an info message")
    logger.warning("This is a warning")
    logger.error("This is an error")

    logger.section_header("PROGRESS DEMO", char="-")

    for i in range(1, 6):
        logger.progress(i, 5, f"Processing item {i}")

    logger.section_header("SUMMARY DEMO")

    logger.summary({
        "Items processed": 5,
        "Errors": 0,
        "Warnings": 1,
        "Duration": "2.5s"
    })

    # Test CLI disabled
    print("\n--- Testing with CLI disabled ---")
    silent_logger = LoggerFacade(session, cli_enabled=False)
    silent_logger.info("This should only go to session, not CLI")

    # Show session logs
    print("\n--- Session Logs ---")
    for i, log in enumerate(session.get_logs(), 1):
        print(f"{i}. {log}")


if __name__ == "__main__":
    main()
```

Run it:
```bash
python test_logger_demo.py
```

Expected output:
```
============================================================
LOGGER FACADE DEMO
============================================================
This is an info message
WARNING: This is a warning
ERROR: This is an error
------------------------------------------------------------
PROGRESS DEMO
------------------------------------------------------------
[1/5] Processing item 1
[2/5] Processing item 2
[3/5] Processing item 3
[4/5] Processing item 4
[5/5] Processing item 5
============================================================
SUMMARY DEMO
============================================================
Items processed: 5
Errors: 0
Warnings: 1
Duration: 2.5s
============================================================

--- Testing with CLI disabled ---

--- Session Logs ---
1. ============================================================
2. LOGGER FACADE DEMO
3. ============================================================
...
```

---

## Step 7: Commit Your Work (5 minutes)

```bash
# Stage the files
git add components/processor/
git add docs/REFACTORING_*.md
git add docs/ARCHITECTURE_DIAGRAM.md

# Commit with a clear message
git commit -m "feat(processor): Add LoggerFacade module

- Implement LoggerFacade with unified logging interface
- Add comprehensive test suite (100% coverage)
- Support CLI and session logging
- Add section headers, progress indicators, and summaries
- Part of Phase 6 refactoring initiative

Related: #<issue-number>"
```

---

## Next Steps

Now that you have LoggerFacade working:

1. **Review the implementation** with team
2. **Get feedback** on the approach
3. **Proceed to PageLimiter** (next simplest module)
4. **Follow the checklist** in REFACTORING_CHECKLIST.md

---

## Troubleshooting

### Tests fail with import errors

```bash
# Make sure you're in the project root
cd /home/user/book-generator-2

# Install any missing dependencies
pip install pytest pytest-cov

# Try running again
pytest components/processor/tests/test_logger_facade.py -v
```

### SessionLogger not found

```bash
# Check that components/logging/session_logger.py exists
ls components/logging/

# If missing, check the import path
# You may need to adjust the import in logger_facade.py
```

### Coverage too low

- Check for untested edge cases
- Add tests for error conditions
- Test with different parameter combinations

---

## Success Criteria

✅ LoggerFacade module created
✅ All tests passing (15+ tests)
✅ 100% code coverage
✅ Demo script works
✅ Code committed to git

**Time to complete**: ~1-2 hours
**Confidence**: High (simple module, low risk)
**Next module**: PageLimiter (see REFACTORING_CHECKLIST.md)

---

## Questions?

- Check `docs/REFACTORING_PLAN.md` for architecture details
- Check `docs/REFACTORING_CHECKLIST.md` for complete task list
- Check `docs/ARCHITECTURE_DIAGRAM.md` for visual diagrams

**Ready to proceed?** Start with Step 1 above!
