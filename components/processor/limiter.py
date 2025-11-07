"""Page Limiter Module

Handles enforcement of total and per-topic page limits with clean state management.

This module provides centralized limit checking and counter management, replacing
the scattered limit logic that was previously spread across 100+ lines in the
main processing loop.

Example:
    >>> from components.processor.limiter import PageLimiter, LimiterConfig
    >>>
    >>> config = LimiterConfig(max_total=10, per_topic_limits={"coloring": 5})
    >>> limiter = PageLimiter(config)
    >>>
    >>> should_process, reason = limiter.should_process("coloring")
    >>> if should_process:
    ...     # ... process page ...
    ...     limiter.mark_processed("coloring")
    >>>
    >>> summary = limiter.get_summary()
    >>> print(f"Processed {summary['total_processed']} pages")
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple, List


@dataclass
class LimiterConfig:
    """Configuration for PageLimiter.

    Attributes:
        max_total: Maximum total pages to process (None = unlimited)
        per_topic_limits: Limits per topic/page type (empty = unlimited per topic)

    Example:
        >>> config = LimiterConfig(
        ...     max_total=20,
        ...     per_topic_limits={"coloring": 8, "tracing": 4}
        ... )
    """

    max_total: Optional[int] = None
    per_topic_limits: Dict[str, int] = field(default_factory=dict)


class PageLimiter:
    """Enforces total and per-topic page limits.

    Centralizes all limit checking and counter management logic. Tracks both
    total pages processed and per-topic counts, with support for skipped page
    tracking and summary generation.

    The limiter normalizes topic names to lowercase for consistent matching,
    so "Coloring", "coloring", and "COLORING" are all treated as the same topic.

    Attributes:
        config: The LimiterConfig with limit settings
        total_processed: Total number of pages processed
        per_topic_counts: Count of pages per topic
        skipped_messages: List of skip reason messages

    Design Pattern:
        State pattern - manages counters and limit state

    Example:
        >>> config = LimiterConfig(max_total=5)
        >>> limiter = PageLimiter(config)
        >>>
        >>> for i in range(10):
        ...     should_process, reason = limiter.should_process("test")
        ...     if should_process:
        ...         limiter.mark_processed("test")
        ...     else:
        ...         print(f"Skipped: {reason}")
        >>>
        >>> assert limiter.total_processed == 5
    """

    def __init__(self, config: LimiterConfig):
        """Initialize the page limiter.

        Args:
            config: Configuration with limit settings
        """
        self.config = config
        self.total_processed = 0
        self.per_topic_counts: Dict[str, int] = {}
        self.per_topic_labels: Dict[str, str] = {}  # normalized -> original
        self.skipped_messages: List[str] = []

    def should_process(self, page_type: str) -> Tuple[bool, Optional[str]]:
        """Check if a page should be processed based on limits.

        This method checks both total and per-topic limits. It returns False
        and a descriptive reason if any limit would be exceeded.

        Args:
            page_type: The type/topic of the page (e.g., "coloring", "maze")

        Returns:
            Tuple of (should_process, skip_reason):
            - (True, None) if page should be processed
            - (False, "reason") if page should be skipped

        Example:
            >>> limiter = PageLimiter(LimiterConfig(max_total=3))
            >>> for i in range(5):
            ...     should_process, reason = limiter.should_process("test")
            ...     if should_process:
            ...         limiter.mark_processed("test")
            ...         print(f"Processing page {i+1}")
            ...     else:
            ...         print(f"Skipping: {reason}")
            Processing page 1
            Processing page 2
            Processing page 3
            Skipping: Total limit 3 reached
            Skipping: Total limit 3 reached
        """
        # Check total limit
        if self.config.max_total is not None:
            if self.total_processed >= self.config.max_total:
                reason = f"Total limit {self.config.max_total} reached"
                return False, reason

        # Normalize topic name
        normalized = self._normalize_topic(page_type)

        # Store original label for reporting
        if normalized not in self.per_topic_labels:
            self.per_topic_labels[normalized] = page_type or "unknown"

        # Check per-topic limit
        if normalized in self.config.per_topic_limits:
            limit = self.config.per_topic_limits[normalized]
            current = self.per_topic_counts.get(normalized, 0)

            if current >= limit:
                original_label = self.per_topic_labels[normalized]
                reason = f"Topic limit {limit} reached for '{original_label}'"
                return False, reason

        return True, None

    def mark_processed(self, page_type: str) -> None:
        """Mark a page as successfully processed.

        Updates both total and per-topic counters. Should be called after
        successfully processing a page.

        Args:
            page_type: The type/topic of the page that was processed

        Example:
            >>> limiter = PageLimiter(LimiterConfig())
            >>> limiter.mark_processed("coloring")
            >>> limiter.mark_processed("maze")
            >>> limiter.mark_processed("coloring")
            >>> assert limiter.total_processed == 3
            >>> assert limiter.get_topic_count("coloring") == 2
            >>> assert limiter.get_topic_count("maze") == 1
        """
        # Increment total counter
        self.total_processed += 1

        # Increment per-topic counter
        normalized = self._normalize_topic(page_type)
        self.per_topic_counts[normalized] = self.per_topic_counts.get(normalized, 0) + 1

        # Store original label if not already stored
        if normalized not in self.per_topic_labels:
            self.per_topic_labels[normalized] = page_type or "unknown"

    def get_total_processed(self) -> int:
        """Get the total number of pages processed.

        Returns:
            Total count of processed pages
        """
        return self.total_processed

    def get_topic_count(self, topic: str) -> int:
        """Get the count for a specific topic.

        Args:
            topic: The topic name (case-insensitive)

        Returns:
            Count of pages processed for this topic

        Example:
            >>> limiter = PageLimiter(LimiterConfig())
            >>> limiter.mark_processed("Coloring")
            >>> assert limiter.get_topic_count("coloring") == 1
            >>> assert limiter.get_topic_count("COLORING") == 1
        """
        normalized = self._normalize_topic(topic)
        return self.per_topic_counts.get(normalized, 0)

    def get_summary(self) -> Dict[str, any]:
        """Get a summary of processed pages and limits.

        Returns a dictionary with:
        - total_processed: Total pages processed
        - max_total: Total limit (or None)
        - per_topic_counts: Dict of topic counts with original labels
        - per_topic_limits: Dict of topic limits
        - skipped_count: Number of skipped pages

        Returns:
            Dictionary with summary statistics

        Example:
            >>> config = LimiterConfig(
            ...     max_total=10,
            ...     per_topic_limits={"coloring": 5}
            ... )
            >>> limiter = PageLimiter(config)
            >>> limiter.mark_processed("coloring")
            >>> limiter.mark_processed("maze")
            >>>
            >>> summary = limiter.get_summary()
            >>> assert summary["total_processed"] == 2
            >>> assert summary["max_total"] == 10
            >>> assert "coloring" in summary["per_topic_counts"]
        """
        # Build per-topic counts with original labels
        topic_counts = {}
        for normalized, count in self.per_topic_counts.items():
            original_label = self.per_topic_labels.get(normalized, normalized)
            topic_counts[original_label] = count

        return {
            "total_processed": self.total_processed,
            "max_total": self.config.max_total,
            "per_topic_counts": topic_counts,
            "per_topic_limits": self.config.per_topic_limits.copy(),
            "skipped_count": len(self.skipped_messages),
        }

    def track_skip(self, message: str) -> None:
        """Track a skip message.

        Args:
            message: The skip reason message to track

        Example:
            >>> limiter = PageLimiter(LimiterConfig())
            >>> limiter.track_skip("Page skipped due to limit")
            >>> assert len(limiter.get_skipped_messages()) == 1
        """
        self.skipped_messages.append(message)

    def get_skipped_messages(self) -> List[str]:
        """Get all skip reason messages.

        Returns:
            List of skip messages

        Example:
            >>> limiter = PageLimiter(LimiterConfig(max_total=2))
            >>> for i in range(5):
            ...     should_process, reason = limiter.should_process("test")
            ...     if should_process:
            ...         limiter.mark_processed("test")
            ...     else:
            ...         limiter.track_skip(reason)
            >>>
            >>> assert len(limiter.get_skipped_messages()) == 3
        """
        return self.skipped_messages.copy()

    def reset(self) -> None:
        """Reset all counters and state.

        Clears all processed counts and skip messages. Useful for starting
        a new processing run with the same limiter.

        Example:
            >>> limiter = PageLimiter(LimiterConfig())
            >>> limiter.mark_processed("test")
            >>> assert limiter.total_processed == 1
            >>>
            >>> limiter.reset()
            >>> assert limiter.total_processed == 0
            >>> assert len(limiter.per_topic_counts) == 0
        """
        self.total_processed = 0
        self.per_topic_counts.clear()
        self.per_topic_labels.clear()
        self.skipped_messages.clear()

    def _normalize_topic(self, topic: str) -> str:
        """Normalize a topic name for consistent matching.

        Converts to lowercase and strips whitespace. Unknown/empty topics
        are normalized to "__unknown__".

        Args:
            topic: The raw topic name

        Returns:
            Normalized topic name

        Example:
            >>> limiter = PageLimiter(LimiterConfig())
            >>> assert limiter._normalize_topic("Coloring") == "coloring"
            >>> assert limiter._normalize_topic("  MAZE  ") == "maze"
            >>> assert limiter._normalize_topic("") == "__unknown__"
            >>> assert limiter._normalize_topic(None) == "__unknown__"
        """
        if not topic or not topic.strip():
            return "__unknown__"
        return topic.strip().lower()
