"""Structured logging with correlation IDs for request tracing.

This module provides structured logging capabilities with correlation ID tracking,
enabling better debugging, log aggregation, and request tracing.

Key Features:
- Structured JSON log format
- Correlation ID tracking across operations
- Multiple log levels (info, warning, error)
- Specialized logging methods for common operations
- Child logger creation with inherited correlation ID
- Log storage and filtering

Usage:
    logger = StructuredLogger(correlation_id="req-123")

    logger.info("Processing started", page_count=10)
    logger.log_page_start(page_number=1, page_type="coloring")
    logger.log_api_call(endpoint="messages", duration=1.5, tokens=100)
    logger.log_page_complete(page_number=1, duration=2.0, success=True)

    # Export logs
    json_logs = logger.export_json()
    all_logs = logger.get_logs()
    errors = logger.get_logs(level="error")
"""

import json
import uuid
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict


@dataclass
class LogEntry:
    """Structured log entry.

    Attributes:
        timestamp: ISO format timestamp
        correlation_id: Request correlation ID
        level: Log level (info, warning, error)
        message: Log message
        metadata: Additional metadata
    """

    timestamp: str
    correlation_id: str
    level: str
    message: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary.

        Returns:
            Dictionary representation
        """
        result = {
            "timestamp": self.timestamp,
            "correlation_id": self.correlation_id,
            "level": self.level,
            "message": self.message,
        }
        result.update(self.metadata)
        return result


class StructuredLogger:
    """Structured logging with correlation IDs.

    This class provides structured logging with automatic correlation ID
    tracking, JSON formatting, and specialized methods for common operations.

    Attributes:
        correlation_id: Unique ID for this request/session
        logs: List of log entries
        logger: Python logger instance
    """

    def __init__(self, correlation_id: Optional[str] = None):
        """Initialize structured logger.

        Args:
            correlation_id: Optional correlation ID (generated if not provided)
        """
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.logs: List[LogEntry] = []
        self.logger = logging.getLogger(__name__)
        self._default_metadata: Dict[str, Any] = {}

    def log(self, level: str, message: str, **kwargs) -> None:
        """Log structured message.

        Args:
            level: Log level (info, warning, error)
            message: Log message
            **kwargs: Additional metadata
        """
        # Merge default metadata with kwargs
        metadata = {**self._default_metadata, **kwargs}

        log_entry = LogEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            correlation_id=self.correlation_id,
            level=level,
            message=message,
            metadata=metadata,
        )

        self.logs.append(log_entry)
        self._write_log(log_entry.to_dict())

    def _write_log(self, log_dict: Dict[str, Any]) -> None:
        """Write log to Python logger.

        Args:
            log_dict: Log entry dictionary
        """
        level = log_dict.get("level", "info")
        json_str = json.dumps(log_dict)

        if level == "error":
            self.logger.error(json_str)
        elif level == "warning":
            self.logger.warning(json_str)
        else:
            self.logger.info(json_str)

    def info(self, message: str, **kwargs) -> None:
        """Log info level message.

        Args:
            message: Log message
            **kwargs: Additional metadata
        """
        self.log("info", message, **kwargs)

    def warning(self, message: str, **kwargs) -> None:
        """Log warning level message.

        Args:
            message: Log message
            **kwargs: Additional metadata
        """
        self.log("warning", message, **kwargs)

    def error(self, message: str, **kwargs) -> None:
        """Log error level message.

        Args:
            message: Log message
            **kwargs: Additional metadata
        """
        self.log("error", message, **kwargs)

    def log_page_start(self, page_number: int, page_type: str) -> None:
        """Log page processing start.

        Args:
            page_number: Page number
            page_type: Type of page (coloring, puzzle, etc.)
        """
        self.log(
            "info",
            "page_processing_start",
            page_number=page_number,
            page_type=page_type,
        )

    def log_page_complete(
        self, page_number: int, duration: float, success: bool
    ) -> None:
        """Log page processing completion.

        Args:
            page_number: Page number
            duration: Processing duration (seconds)
            success: Whether processing succeeded
        """
        self.log(
            "info",
            "page_processing_complete",
            page_number=page_number,
            duration=duration,
            success=success,
        )

    def log_api_call(
        self, endpoint: str, duration: float, tokens: Optional[int] = None
    ) -> None:
        """Log API call.

        Args:
            endpoint: API endpoint
            duration: Call duration (seconds)
            tokens: Number of tokens (optional)
        """
        metadata = {
            "endpoint": endpoint,
            "duration": duration,
        }
        if tokens is not None:
            metadata["tokens"] = tokens

        self.log("info", "api_call", **metadata)

    def log_exception(self, exception: Exception, **kwargs) -> None:
        """Log exception with details.

        Args:
            exception: Exception instance
            **kwargs: Additional context
        """
        self.log(
            "error",
            f"Exception: {type(exception).__name__}: {str(exception)}",
            exception_type=type(exception).__name__,
            exception_message=str(exception),
            **kwargs,
        )

    def create_child(self, **kwargs) -> "StructuredLogger":
        """Create child logger with same correlation ID.

        Args:
            **kwargs: Additional metadata to include in all child logs

        Returns:
            New StructuredLogger with same correlation ID
        """
        child = StructuredLogger(correlation_id=self.correlation_id)
        # Store default metadata for child
        child._default_metadata = kwargs
        return child

    def get_logs(self, level: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get log entries.

        Args:
            level: Optional level filter

        Returns:
            List of log entry dictionaries
        """
        if level is None:
            return [log.to_dict() for log in self.logs]

        return [log.to_dict() for log in self.logs if log.level == level]

    def clear(self) -> None:
        """Clear all log entries."""
        self.logs = []

    def export_json(self) -> str:
        """Export logs as JSON.

        Returns:
            JSON string of all logs
        """
        return json.dumps(self.get_logs(), indent=2)
