"""
Logging Module

Provides structured logging and output capabilities for Claude processor:
- Session logging with detailed API call tracking
- JSON output dumping for testing and debugging
- Formatted log file generation

Design Pattern: Observer Pattern (simplified)
Collects events and provides formatted output.

Example Usage:
    from components.logging import SessionLogger, OutputDumper

    # Initialize logger
    logger = SessionLogger()
    logger.log("Starting process")

    # Log API calls
    logger.log_api_call(1, "prompt text", "response text")

    # Save logs to file
    logger.save(variety_summary={'coloring': ['cat', 'dog']})

    # Dump output to JSON
    from pathlib import Path
    dumper = OutputDumper()
    dumper.dump(pages, logs, Path("./output"))
"""

from .session_logger import SessionLogger
from .output_dumper import OutputDumper

__all__ = ['SessionLogger', 'OutputDumper']

# Version info
__version__ = '1.0.0'
__author__ = 'Book Generator Team'
__description__ = 'Structured logging and output dumping for Claude processor'
