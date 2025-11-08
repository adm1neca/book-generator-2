"""Tests for PageLimiter.

This test suite ensures PageLimiter correctly enforces limits and tracks state.
"""

import pytest
from components.processor.limiter import PageLimiter, LimiterConfig


class TestLimiterConfig:
    """Test suite for LimiterConfig dataclass."""

    def test_default_config(self):
        """Test default configuration with no limits."""
        config = LimiterConfig()
        assert config.max_total is None
        assert config.per_topic_limits == {}

    def test_config_with_total_limit(self):
        """Test configuration with total limit only."""
        config = LimiterConfig(max_total=10)
        assert config.max_total == 10
        assert config.per_topic_limits == {}

    def test_config_with_topic_limits(self):
        """Test configuration with per-topic limits."""
        config = LimiterConfig(per_topic_limits={"coloring": 5, "maze": 3})
        assert config.max_total is None
        assert config.per_topic_limits == {"coloring": 5, "maze": 3}

    def test_config_with_both_limits(self):
        """Test configuration with both total and per-topic limits."""
        config = LimiterConfig(max_total=20, per_topic_limits={"coloring": 8})
        assert config.max_total == 20
        assert config.per_topic_limits == {"coloring": 8}


class TestPageLimiterNoLimits:
    """Test PageLimiter with no limits configured."""

    def test_allows_unlimited_pages(self):
        """Test that limiter allows unlimited pages when no limits set."""
        limiter = PageLimiter(LimiterConfig())

        for i in range(100):
            should_process, reason = limiter.should_process("test")
            assert should_process
            assert reason is None
            limiter.mark_processed("test")

        assert limiter.total_processed == 100

    def test_tracks_multiple_topics(self):
        """Test tracking multiple topics without limits."""
        limiter = PageLimiter(LimiterConfig())

        for _ in range(5):
            limiter.mark_processed("coloring")
        for _ in range(3):
            limiter.mark_processed("maze")
        for _ in range(7):
            limiter.mark_processed("tracing")

        assert limiter.total_processed == 15
        assert limiter.get_topic_count("coloring") == 5
        assert limiter.get_topic_count("maze") == 3
        assert limiter.get_topic_count("tracing") == 7


class TestPageLimiterTotalLimit:
    """Test PageLimiter with total limit enforcement."""

    def test_enforces_total_limit(self):
        """Test that total limit is enforced."""
        limiter = PageLimiter(LimiterConfig(max_total=5))

        # Process up to limit
        for i in range(5):
            should_process, reason = limiter.should_process("test")
            assert should_process
            assert reason is None
            limiter.mark_processed("test")

        # Should reject after limit
        should_process, reason = limiter.should_process("test")
        assert not should_process
        assert "Total limit 5 reached" in reason

    def test_total_limit_with_multiple_topics(self):
        """Test total limit applies across all topics."""
        limiter = PageLimiter(LimiterConfig(max_total=10))

        limiter.mark_processed("coloring")  # 1
        limiter.mark_processed("maze")  # 2
        limiter.mark_processed("coloring")  # 3
        limiter.mark_processed("tracing")  # 4
        limiter.mark_processed("maze")  # 5
        limiter.mark_processed("coloring")  # 6
        limiter.mark_processed("coloring")  # 7
        limiter.mark_processed("maze")  # 8
        limiter.mark_processed("tracing")  # 9
        limiter.mark_processed("coloring")  # 10

        # Total limit reached
        should_process, reason = limiter.should_process("any_topic")
        assert not should_process
        assert "Total limit 10 reached" in reason

        assert limiter.total_processed == 10

    def test_total_limit_zero(self):
        """Test that zero total limit blocks all pages."""
        limiter = PageLimiter(LimiterConfig(max_total=0))

        should_process, reason = limiter.should_process("test")
        assert not should_process
        assert "Total limit 0 reached" in reason


class TestPageLimiterTopicLimit:
    """Test PageLimiter with per-topic limit enforcement."""

    def test_enforces_single_topic_limit(self):
        """Test that per-topic limit is enforced."""
        limiter = PageLimiter(LimiterConfig(per_topic_limits={"coloring": 3}))

        # Process up to limit
        for i in range(3):
            should_process, reason = limiter.should_process("coloring")
            assert should_process
            limiter.mark_processed("coloring")

        # Should reject after limit
        should_process, reason = limiter.should_process("coloring")
        assert not should_process
        assert "Topic limit 3 reached" in reason
        assert "coloring" in reason

    def test_different_topics_have_independent_limits(self):
        """Test that different topics have independent limits."""
        limiter = PageLimiter(
            LimiterConfig(per_topic_limits={"coloring": 2, "maze": 3, "tracing": 1})
        )

        # Process coloring up to limit
        for _ in range(2):
            should_process, _ = limiter.should_process("coloring")
            assert should_process
            limiter.mark_processed("coloring")

        # Coloring should be blocked
        should_process, reason = limiter.should_process("coloring")
        assert not should_process
        assert "Topic limit 2 reached" in reason

        # But maze should still be allowed
        for _ in range(3):
            should_process, _ = limiter.should_process("maze")
            assert should_process
            limiter.mark_processed("maze")

        # Maze now blocked
        should_process, reason = limiter.should_process("maze")
        assert not should_process

        # Tracing still allowed (limit 1)
        should_process, _ = limiter.should_process("tracing")
        assert should_process

    def test_topics_without_limit_are_unlimited(self):
        """Test that topics without explicit limits are unlimited."""
        limiter = PageLimiter(LimiterConfig(per_topic_limits={"coloring": 2}))

        # Coloring has limit
        for _ in range(2):
            limiter.mark_processed("coloring")

        should_process, _ = limiter.should_process("coloring")
        assert not should_process

        # But other topics are unlimited
        for _ in range(100):
            should_process, reason = limiter.should_process("maze")
            assert should_process
            assert reason is None
            limiter.mark_processed("maze")

        assert limiter.get_topic_count("maze") == 100


class TestPageLimiterCombinedLimits:
    """Test PageLimiter with both total and per-topic limits."""

    def test_respects_both_limits(self):
        """Test that both total and per-topic limits are enforced."""
        limiter = PageLimiter(
            LimiterConfig(max_total=10, per_topic_limits={"coloring": 3})
        )

        # Process coloring up to topic limit
        for _ in range(3):
            should_process, _ = limiter.should_process("coloring")
            assert should_process
            limiter.mark_processed("coloring")

        # Coloring blocked by topic limit
        should_process, reason = limiter.should_process("coloring")
        assert not should_process
        assert "Topic limit" in reason

        # Process other topics up to total limit
        for _ in range(7):  # 3 + 7 = 10
            should_process, _ = limiter.should_process("maze")
            assert should_process
            limiter.mark_processed("maze")

        # Now blocked by total limit
        should_process, reason = limiter.should_process("maze")
        assert not should_process
        assert "Total limit" in reason

    def test_total_limit_reached_before_topic_limit(self):
        """Test when total limit is reached before topic limit."""
        limiter = PageLimiter(
            LimiterConfig(max_total=5, per_topic_limits={"coloring": 10})
        )

        # Process mixed topics up to total limit
        limiter.mark_processed("coloring")  # 1
        limiter.mark_processed("maze")  # 2
        limiter.mark_processed("coloring")  # 3
        limiter.mark_processed("maze")  # 4
        limiter.mark_processed("coloring")  # 5

        # Total limit blocks both topics
        should_process, reason = limiter.should_process("coloring")
        assert not should_process
        assert "Total limit" in reason

        should_process, reason = limiter.should_process("maze")
        assert not should_process
        assert "Total limit" in reason


class TestPageLimiterTopicNormalization:
    """Test topic name normalization."""

    def test_case_insensitive_matching(self):
        """Test that topic names are case-insensitive."""
        limiter = PageLimiter(LimiterConfig(per_topic_limits={"coloring": 2}))

        limiter.mark_processed("Coloring")
        limiter.mark_processed("COLORING")

        # Should be at limit (2)
        should_process, reason = limiter.should_process("coloring")
        assert not should_process

        assert limiter.get_topic_count("Coloring") == 2
        assert limiter.get_topic_count("coloring") == 2
        assert limiter.get_topic_count("COLORING") == 2

    def test_whitespace_trimming(self):
        """Test that whitespace is trimmed from topic names."""
        limiter = PageLimiter(LimiterConfig())

        limiter.mark_processed("  coloring  ")
        limiter.mark_processed("coloring")

        assert limiter.get_topic_count("coloring") == 2
        assert limiter.get_topic_count("  coloring  ") == 2

    def test_empty_topic_normalized_to_unknown(self):
        """Test that empty topics are normalized to __unknown__."""
        limiter = PageLimiter(LimiterConfig())

        limiter.mark_processed("")
        limiter.mark_processed("  ")
        limiter.mark_processed(None)

        assert limiter.get_topic_count("__unknown__") == 3

    def test_preserves_original_label_for_reporting(self):
        """Test that original topic labels are preserved for display."""
        limiter = PageLimiter(LimiterConfig())

        limiter.mark_processed("Coloring")
        limiter.mark_processed("MAZE")

        summary = limiter.get_summary()
        # Should use original case in summary
        assert "Coloring" in summary["per_topic_counts"] or "coloring" in summary["per_topic_counts"]


class TestPageLimiterSummary:
    """Test summary generation."""

    def test_summary_structure(self):
        """Test that summary contains all expected fields."""
        limiter = PageLimiter(LimiterConfig(max_total=10, per_topic_limits={"coloring": 5}))

        limiter.mark_processed("coloring")
        limiter.mark_processed("maze")

        summary = limiter.get_summary()

        assert "total_processed" in summary
        assert "max_total" in summary
        assert "per_topic_counts" in summary
        assert "per_topic_limits" in summary
        assert "skipped_count" in summary

    def test_summary_values(self):
        """Test that summary values are correct."""
        limiter = PageLimiter(LimiterConfig(max_total=10))

        for _ in range(3):
            limiter.mark_processed("coloring")
        for _ in range(2):
            limiter.mark_processed("maze")

        summary = limiter.get_summary()

        assert summary["total_processed"] == 5
        assert summary["max_total"] == 10
        assert summary["per_topic_counts"]["coloring"] == 3
        assert summary["per_topic_counts"]["maze"] == 2
        assert summary["skipped_count"] == 0

    def test_summary_with_skipped(self):
        """Test summary includes skipped count."""
        limiter = PageLimiter(LimiterConfig())

        limiter.track_skip("Reason 1")
        limiter.track_skip("Reason 2")

        summary = limiter.get_summary()
        assert summary["skipped_count"] == 2


class TestPageLimiterSkipTracking:
    """Test skip message tracking."""

    def test_track_skip_message(self):
        """Test that skip messages are tracked."""
        limiter = PageLimiter(LimiterConfig())

        limiter.track_skip("Page skipped: limit reached")
        limiter.track_skip("Page skipped: invalid data")

        messages = limiter.get_skipped_messages()
        assert len(messages) == 2
        assert "Page skipped: limit reached" in messages
        assert "Page skipped: invalid data" in messages

    def test_skip_messages_return_copy(self):
        """Test that skip messages return a copy (no external modification)."""
        limiter = PageLimiter(LimiterConfig())

        limiter.track_skip("Test message")
        messages = limiter.get_skipped_messages()
        messages.append("External modification")

        # Original should be unchanged
        assert len(limiter.get_skipped_messages()) == 1


class TestPageLimiterReset:
    """Test reset functionality."""

    def test_reset_clears_all_state(self):
        """Test that reset clears all counters and messages."""
        limiter = PageLimiter(LimiterConfig(max_total=10))

        # Add some state
        for _ in range(5):
            limiter.mark_processed("coloring")
        limiter.track_skip("Test skip")

        assert limiter.total_processed == 5
        assert len(limiter.get_skipped_messages()) == 1

        # Reset
        limiter.reset()

        # Everything should be cleared
        assert limiter.total_processed == 0
        assert limiter.get_topic_count("coloring") == 0
        assert len(limiter.get_skipped_messages()) == 0
        assert len(limiter.per_topic_counts) == 0
        assert len(limiter.per_topic_labels) == 0

    def test_reset_preserves_config(self):
        """Test that reset preserves the configuration."""
        config = LimiterConfig(max_total=10, per_topic_limits={"coloring": 5})
        limiter = PageLimiter(config)

        limiter.mark_processed("coloring")
        limiter.reset()

        # Config should be unchanged
        assert limiter.config.max_total == 10
        assert limiter.config.per_topic_limits == {"coloring": 5}

    def test_can_process_after_reset(self):
        """Test that limiter works normally after reset."""
        limiter = PageLimiter(LimiterConfig(max_total=3))

        # Process to limit
        for _ in range(3):
            limiter.mark_processed("test")

        # Should be blocked
        should_process, _ = limiter.should_process("test")
        assert not should_process

        # Reset
        limiter.reset()

        # Should work again
        for _ in range(3):
            should_process, reason = limiter.should_process("test")
            assert should_process
            assert reason is None
            limiter.mark_processed("test")


class TestPageLimiterEdgeCases:
    """Test edge cases and error conditions."""

    def test_none_topic_name(self):
        """Test handling of None as topic name."""
        limiter = PageLimiter(LimiterConfig())

        should_process, reason = limiter.should_process(None)
        assert should_process
        limiter.mark_processed(None)

        assert limiter.get_topic_count("__unknown__") == 1

    def test_very_large_limits(self):
        """Test with very large limit values."""
        limiter = PageLimiter(LimiterConfig(max_total=1000000))

        for _ in range(1000):
            should_process, _ = limiter.should_process("test")
            assert should_process
            limiter.mark_processed("test")

        assert limiter.total_processed == 1000

    def test_multiple_topics_same_normalized_name(self):
        """Test that different casings count toward same limit."""
        limiter = PageLimiter(LimiterConfig(per_topic_limits={"coloring": 3}))

        limiter.mark_processed("Coloring")
        limiter.mark_processed("COLORING")
        limiter.mark_processed("coloring")

        # Should be at limit
        should_process, _ = limiter.should_process("CoLoRiNg")
        assert not should_process

    def test_topic_with_special_characters(self):
        """Test topics with special characters."""
        limiter = PageLimiter(LimiterConfig())

        limiter.mark_processed("color-ing")
        limiter.mark_processed("maze_type")
        limiter.mark_processed("dot.to.dot")

        assert limiter.get_topic_count("color-ing") == 1
        assert limiter.get_topic_count("maze_type") == 1
        assert limiter.get_topic_count("dot.to.dot") == 1


class TestPageLimiterIntegration:
    """Integration tests for complete workflows."""

    def test_realistic_workflow(self):
        """Test a realistic processing workflow with limits."""
        config = LimiterConfig(
            max_total=20, per_topic_limits={"coloring": 8, "maze": 4, "tracing": 4}
        )
        limiter = PageLimiter(config)

        topics = ["coloring", "maze", "tracing", "matching", "dot-to-dot"]
        processed = []
        skipped = []

        # Simulate processing 30 pages
        for i in range(30):
            topic = topics[i % len(topics)]

            should_process, reason = limiter.should_process(topic)
            if should_process:
                limiter.mark_processed(topic)
                processed.append(topic)
            else:
                limiter.track_skip(f"Page {i+1}: {reason}")
                skipped.append(topic)

        # Verify final state
        assert limiter.total_processed == 20
        assert len(skipped) == 10

        summary = limiter.get_summary()
        assert summary["total_processed"] == 20
        assert summary["max_total"] == 20
        assert summary["skipped_count"] == 10

        # Verify topic limits were respected
        assert limiter.get_topic_count("coloring") <= 8
        assert limiter.get_topic_count("maze") <= 4
        assert limiter.get_topic_count("tracing") <= 4
