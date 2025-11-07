"""Unified logging facade for Claude Processor.

Provides a consistent interface for both CLI output and structured session logging.

This module implements the Facade pattern to unify two logging outputs:
1. CLI output (print statements) for real-time user feedback
2. Session logging for structured log files and analysis

Example:
    >>> from components.logging import SessionLogger
    >>> from components.processor.logger_facade import LoggerFacade
    >>>
    >>> session = SessionLogger()
    >>> logger = LoggerFacade(session, cli_enabled=True)
    >>>
    >>> logger.info("Processing started")
    >>> logger.section_header("VALIDATION")
    >>> logger.progress(5, 10, "Processing pages")
    >>> logger.summary({"Total": 10, "Success": 8})
"""

from typing import Dict, Any, Optional
from components.logging import SessionLogger


class LoggerFacade:
    """Unified logging interface combining CLI and structured logging.

    This facade provides a consistent API for logging that outputs to both:
    - CLI (via print) for immediate user feedback
    - SessionLogger for structured logs and analysis

    The CLI output can be disabled for testing or when running in non-interactive mode.

    Attributes:
        session: The SessionLogger instance for structured logging
        cli_enabled: Whether CLI output is enabled (default True)

    Design Pattern:
        Facade pattern - simplifies interface to multiple logging systems
    """

    def __init__(self, session_logger: SessionLogger, cli_enabled: bool = True):
        """Initialize the logger facade.

        Args:
            session_logger: The SessionLogger instance for structured logging
            cli_enabled: Whether to output to CLI (default True)

        Example:
            >>> logger = LoggerFacade(session_logger, cli_enabled=True)
        """
        self.session = session_logger
        self.cli_enabled = cli_enabled

    def info(self, message: str, show_cli: bool = True) -> None:
        """Log an info message.

        The message is always logged to the session logger. It will also be
        printed to CLI if both cli_enabled and show_cli are True.

        Args:
            message: The message to log
            show_cli: Whether to also print to CLI (default True)

        Example:
            >>> logger.info("Processing page 5")
            >>> logger.info("Internal state update", show_cli=False)
        """
        # Always log to session
        self.session.log(message)

        # Optionally print to CLI
        if self.cli_enabled and show_cli:
            print(message)

    def error(self, message: str, show_cli: bool = True) -> None:
        """Log an error message.

        Automatically prefixes the message with "ERROR: " for visibility.

        Args:
            message: The error message to log
            show_cli: Whether to also print to CLI (default True)

        Example:
            >>> logger.error("Failed to parse JSON response")
        """
        error_msg = f"ERROR: {message}"
        self.session.log(error_msg)

        if self.cli_enabled and show_cli:
            print(error_msg)

    def warning(self, message: str, show_cli: bool = True) -> None:
        """Log a warning message.

        Automatically prefixes the message with "WARNING: " for visibility.

        Args:
            message: The warning message to log
            show_cli: Whether to also print to CLI (default True)

        Example:
            >>> logger.warning("Using default configuration")
        """
        warning_msg = f"WARNING: {message}"
        self.session.log(warning_msg)

        if self.cli_enabled and show_cli:
            print(warning_msg)

    def section_header(self, title: str, char: str = "=", width: int = 60) -> None:
        """Print a formatted section header.

        Creates a bordered header for organizing log output into sections.

        Args:
            title: The section title
            char: Character to use for the border (default "=")
            width: Width of the header (default 60)

        Example:
            >>> logger.section_header("PROCESSING")
            ============================================================
            PROCESSING
            ============================================================

            >>> logger.section_header("SUMMARY", char="-", width=40)
            ----------------------------------------
            SUMMARY
            ----------------------------------------
        """
        border = char * width
        self.info(border)
        self.info(title)
        self.info(border)

    def progress(self, current: int, total: int, message: str = "") -> None:
        """Show progress indicator.

        Displays progress in the format [current/total] with optional message.

        Args:
            current: Current item number (1-indexed)
            total: Total number of items
            message: Optional message to display

        Example:
            >>> logger.progress(5, 10)
            [5/10]

            >>> logger.progress(5, 10, "Processing pages")
            [5/10] Processing pages
        """
        progress_msg = f"[{current}/{total}]"
        if message:
            progress_msg += f" {message}"

        self.info(progress_msg)

    def summary(self, stats: Dict[str, Any]) -> None:
        """Print a formatted summary.

        Creates a bordered summary section with key-value pairs.

        Args:
            stats: Dictionary of statistics to display

        Example:
            >>> logger.summary({
            ...     "Total pages": 20,
            ...     "Duration": "45.2s",
            ...     "Errors": 0
            ... })
            ============================================================
            SUMMARY
            ============================================================
            Total pages: 20
            Duration: 45.2s
            Errors: 0
            ============================================================
        """
        self.section_header("SUMMARY")
        for key, value in stats.items():
            self.info(f"{key}: {value}")
        self.info("=" * 60)

    def debug(self, message: str, show_cli: bool = False) -> None:
        """Log a debug message.

        Debug messages are logged to session but not shown in CLI by default.

        Args:
            message: The debug message to log
            show_cli: Whether to also print to CLI (default False)

        Example:
            >>> logger.debug("Internal state: counter=5")
        """
        debug_msg = f"DEBUG: {message}"
        self.session.log(debug_msg)

        if self.cli_enabled and show_cli:
            print(debug_msg)
