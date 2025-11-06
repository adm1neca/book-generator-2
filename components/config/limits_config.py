"""Page limits configuration management.

Design Pattern: Parser Pattern + Value Object
- Parses multiple input formats (JSON, CSV, dict)
- Normalizes to internal representation
- Validates all values
- Encapsulates parsing complexity
"""

import json
from typing import Dict, Optional, Any
from components.config.validation import coerce_positive_int


class PageLimitsConfig:
    """Handles page limit configuration parsing and validation.

    Parser Pattern: Accepts multiple input formats.
    Value Object Pattern: Ensures valid limits.
    """

    def __init__(self, max_total: Optional[int] = None,
                 per_topic: Optional[Dict[str, int]] = None):
        """
        Initialize page limits configuration.

        Args:
            max_total: Maximum total pages to generate
            per_topic: Dictionary of topic -> max count
        """
        self.max_total = max_total
        self.per_topic = per_topic or {}

    @staticmethod
    def parse_max_total(raw_value: Any) -> Optional[int]:
        """
        Parse max_total_pages value.

        Flexible Parsing: Accepts int, float, or string.

        Args:
            raw_value: Raw input value

        Returns:
            Positive integer or None

        Examples:
            >>> PageLimitsConfig.parse_max_total("10")
            10
            >>> PageLimitsConfig.parse_max_total(5)
            5
            >>> PageLimitsConfig.parse_max_total("-1")
            >>> PageLimitsConfig.parse_max_total("")
        """
        return coerce_positive_int(raw_value, "max_total_pages")

    @staticmethod
    def parse_pages_per_topic(raw: Any) -> Dict[str, int]:
        """
        Parse pages_per_topic configuration.

        Flexible Parsing - Accepts multiple formats:
        - JSON dict: {"coloring": 8, "tracing": 4}
        - Comma list: "coloring=8,tracing=4"
        - Dict object: Already parsed

        Args:
            raw: Raw input value

        Returns:
            Dictionary of normalized topic -> count

        Examples:
            >>> PageLimitsConfig.parse_pages_per_topic('{"coloring":8}')
            {'coloring': 8}
            >>> PageLimitsConfig.parse_pages_per_topic("coloring=8,tracing=4")
            {'coloring': 8, 'tracing': 4}
            >>> PageLimitsConfig.parse_pages_per_topic("")
            {}
        """
        if raw is None:
            return {}

        # Already a dict
        if isinstance(raw, dict):
            source_items = raw.items()
        else:
            text = str(raw).strip()
            if not text:
                return {}

            # JSON format
            if text.startswith("{"):
                try:
                    decoded = json.loads(text)
                except json.JSONDecodeError:
                    return {}

                if not isinstance(decoded, dict):
                    return {}

                source_items = decoded.items()
            # Comma-separated format
            else:
                parts = [p.strip() for p in text.split(",") if p.strip()]
                parsed_pairs = []
                for part in parts:
                    if "=" not in part:
                        continue
                    key, value = part.split("=", 1)
                    parsed_pairs.append((key.strip(), value.strip()))
                source_items = parsed_pairs

        # Validate and normalize
        limits: Dict[str, int] = {}
        for key, value in source_items:
            topic = str(key).strip().lower()
            if not topic:
                continue

            count = coerce_positive_int(value, f"pages_per_topic[{topic}]")
            if count is None:
                continue

            limits[topic] = count

        return limits


if __name__ == "__main__":
    import doctest
    doctest.testmod()
