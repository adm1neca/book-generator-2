"""Metrics collection for page processing pipeline.

This module provides metrics collection and export functionality for monitoring
system performance, API usage, and processing statistics.

Key Features:
- Counters for pages processed, failed, skipped
- Timing metrics for API calls and processing
- Token usage tracking
- Prometheus export format
- JSON export format
- Low overhead collection

Usage:
    collector = MetricsCollector()

    # Record events
    collector.record_page_success(duration=1.5)
    collector.record_api_call(duration=0.8, tokens=100)

    # Export metrics
    prometheus = collector.export_prometheus()
    json_data = collector.export_json()
    summary = collector.get_summary()
"""

import time
import json
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional


@dataclass
class ProcessingMetrics:
    """Metrics for processing operations.

    This class tracks all relevant metrics for page processing including
    counters, timings, and API usage.

    Attributes:
        total_pages: Total number of pages processed (including failed)
        successful_pages: Number of successfully processed pages
        failed_pages: Number of failed pages
        skipped_pages: Number of skipped pages
        total_duration: Total processing duration
        api_call_times: List of API call durations
        prompt_build_times: List of prompt building durations
        total_tokens_used: Total tokens consumed by API
        total_api_calls: Total number of API calls made
        api_errors: Number of API errors encountered
        error_messages: List of error messages
    """

    # Counters
    total_pages: int = 0
    successful_pages: int = 0
    failed_pages: int = 0
    skipped_pages: int = 0

    # Timing
    total_duration: float = 0.0
    api_call_times: List[float] = field(default_factory=list)
    prompt_build_times: List[float] = field(default_factory=list)

    # API metrics
    total_tokens_used: int = 0
    total_api_calls: int = 0
    api_errors: int = 0

    # Error tracking
    error_messages: List[str] = field(default_factory=list)

    def record_page_success(self, duration: float) -> None:
        """Record successful page processing.

        Args:
            duration: Time taken to process page (seconds)
        """
        self.successful_pages += 1
        self.total_pages += 1
        self.total_duration += duration

    def record_page_failure(self, duration: float, error: str) -> None:
        """Record failed page processing.

        Args:
            duration: Time taken before failure (seconds)
            error: Error message
        """
        self.failed_pages += 1
        self.total_pages += 1
        self.total_duration += duration
        self.error_messages.append(error)

    def record_page_skip(self, reason: str) -> None:
        """Record skipped page.

        Args:
            reason: Reason for skipping
        """
        self.skipped_pages += 1
        self.total_pages += 1

    def record_api_call(self, duration: float, tokens: int) -> None:
        """Record API call metrics.

        Args:
            duration: API call duration (seconds)
            tokens: Number of tokens used
        """
        self.total_api_calls += 1
        self.api_call_times.append(duration)
        self.total_tokens_used += tokens

    def record_api_error(self, error: str) -> None:
        """Record API error.

        Args:
            error: Error message
        """
        self.api_errors += 1
        self.error_messages.append(error)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns:
            Dictionary with summary statistics
        """
        total_pages = max(1, self.total_pages)  # Avoid division by zero
        total_api_calls = max(1, len(self.api_call_times))

        return {
            "total_pages": self.total_pages,
            "successful_pages": self.successful_pages,
            "failed_pages": self.failed_pages,
            "skipped_pages": self.skipped_pages,
            "success_rate": self.successful_pages / total_pages if self.total_pages > 0 else 0.0,
            "avg_api_time": (
                sum(self.api_call_times) / total_api_calls
                if self.api_call_times
                else 0.0
            ),
            "total_tokens": self.total_tokens_used,
            "tokens_per_page": (
                self.total_tokens_used / total_pages
                if self.total_pages > 0
                else 0.0
            ),
            "api_errors": self.api_errors,
            "total_duration": self.total_duration,
        }


class MetricsCollector:
    """Collects and aggregates processing metrics.

    This class provides a service for collecting metrics throughout
    the processing pipeline and exporting them in various formats.

    Attributes:
        metrics: ProcessingMetrics instance
        start_time: Pipeline start timestamp
    """

    def __init__(self):
        """Initialize metrics collector."""
        self.metrics = ProcessingMetrics()
        self.start_time = time.time()

    def get_metrics(self) -> ProcessingMetrics:
        """Get current metrics.

        Returns:
            ProcessingMetrics instance
        """
        return self.metrics

    def record_page_success(self, duration: float) -> None:
        """Record successful page processing.

        Args:
            duration: Processing duration (seconds)
        """
        self.metrics.record_page_success(duration)

    def record_page_failure(self, duration: float, error: str) -> None:
        """Record failed page processing.

        Args:
            duration: Processing duration (seconds)
            error: Error message
        """
        self.metrics.record_page_failure(duration, error)

    def record_page_skip(self, reason: str) -> None:
        """Record skipped page.

        Args:
            reason: Skip reason
        """
        self.metrics.record_page_skip(reason)

    def record_api_call(self, duration: float, tokens: int) -> None:
        """Record API call.

        Args:
            duration: Call duration (seconds)
            tokens: Tokens used
        """
        self.metrics.record_api_call(duration, tokens)

    def record_api_error(self, error: str) -> None:
        """Record API error.

        Args:
            error: Error message
        """
        self.metrics.record_api_error(error)

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format.

        Returns:
            Prometheus-formatted metrics string
        """
        m = self.metrics

        return f"""# HELP claude_pages_processed Total pages processed
# TYPE claude_pages_processed counter
claude_pages_processed{{status="success"}} {m.successful_pages}
claude_pages_processed{{status="failed"}} {m.failed_pages}
claude_pages_processed{{status="skipped"}} {m.skipped_pages}

# HELP claude_api_calls_total Total API calls
# TYPE claude_api_calls_total counter
claude_api_calls_total {m.total_api_calls}

# HELP claude_api_errors_total Total API errors
# TYPE claude_api_errors_total counter
claude_api_errors_total {m.api_errors}

# HELP claude_tokens_used_total Total tokens used
# TYPE claude_tokens_used_total counter
claude_tokens_used_total {m.total_tokens_used}

# HELP claude_processing_duration_seconds Total processing duration
# TYPE claude_processing_duration_seconds gauge
claude_processing_duration_seconds {m.total_duration}

# HELP claude_api_call_duration_seconds Average API call duration
# TYPE claude_api_call_duration_seconds gauge
claude_api_call_duration_seconds {sum(m.api_call_times) / max(1, len(m.api_call_times)):.6f}
"""

    def export_json(self) -> str:
        """Export metrics in JSON format.

        Returns:
            JSON-formatted metrics string
        """
        summary = self.metrics.get_summary()
        summary["uptime_seconds"] = self.get_elapsed_time()

        return json.dumps(summary, indent=2)

    def get_summary(self) -> Dict[str, Any]:
        """Get metrics summary.

        Returns:
            Dictionary with all metrics
        """
        summary = self.metrics.get_summary()
        summary["uptime_seconds"] = self.get_elapsed_time()
        return summary

    def reset(self) -> None:
        """Reset all metrics to zero."""
        self.metrics = ProcessingMetrics()
        self.start_time = time.time()

    def get_elapsed_time(self) -> float:
        """Get elapsed time since collector creation.

        Returns:
            Elapsed time in seconds
        """
        return time.time() - self.start_time

    def get_throughput(self) -> float:
        """Get processing throughput (pages per second).

        Returns:
            Pages per second
        """
        elapsed = self.get_elapsed_time()
        if elapsed == 0:
            return 0.0

        return self.metrics.total_pages / elapsed
