"""Validation utilities for configuration values.

Design Pattern: Pure Functions / Utility Module
- Stateless validation functions
- No side effects
- Easy to test (input -> output)
- Reusable across application
"""

from typing import Optional


def coerce_positive_int(raw_value, label: str) -> Optional[int]:
    """
    Convert incoming values to a positive int, logging when invalid.

    Pure function: Same input always produces same output.

    Args:
        raw_value: Value to convert (can be int, float, str, or None)
        label: Descriptive label for logging

    Returns:
        Positive integer or None if invalid

    Examples:
        >>> coerce_positive_int(5, "test")
        5
        >>> coerce_positive_int("10", "test")
        10
        >>> coerce_positive_int(-5, "test")
        >>> coerce_positive_int("", "test")
    """
    if raw_value is None:
        return None

    if isinstance(raw_value, (int, float)):
        value = int(raw_value)
    else:
        text = str(raw_value).strip()
        if not text:
            return None
        try:
            value = int(text)
        except ValueError:
            return None

    if value <= 0:
        return None

    return value


def validate_string_not_empty(value: Optional[str], default: str = "") -> str:
    """
    Ensure string is not None or empty.

    Pure function: Predictable behavior.

    Args:
        value: String to validate
        default: Default value if invalid

    Returns:
        Valid string or default

    Examples:
        >>> validate_string_not_empty("test", "default")
        'test'
        >>> validate_string_not_empty(None, "default")
        'default'
        >>> validate_string_not_empty("", "default")
        'default'
    """
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


if __name__ == "__main__":
    import doctest
    doctest.testmod()
