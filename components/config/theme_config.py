"""Theme configuration and sanitization.

Design Pattern: Value Object Pattern
- Encapsulates theme validation rules
- Makes invalid states unrepresentable
- Always returns valid theme (never raises exception)
- Business logic in ONE place
"""

from typing import Optional
from components.config.constants import (
    THEME_FALLBACKS,
    BLOCKED_THEMES,
    DEFAULT_THEME
)


class ThemeConfig:
    """Handles theme validation and normalization.

    Value Object Pattern: Ensures all themes are valid.
    Single Responsibility: Only handles theme validation.
    """

    @staticmethod
    def sanitize(theme: Optional[str]) -> str:
        """
        Normalize and block branded themes to keep content safe.

        This method guarantees a valid theme is returned.
        Invalid states are impossible.

        Args:
            theme: Raw theme string from input

        Returns:
            Sanitized theme string (always valid)

        Examples:
            >>> ThemeConfig.sanitize("Forest")
            'forest-friends'
            >>> ThemeConfig.sanitize("OCEAN")
            'under-the-sea'
            >>> ThemeConfig.sanitize("peppa pig")
            'animals'
            >>> ThemeConfig.sanitize(None)
            'animals'
        """
        # Normalize to lowercase
        t = (theme or "").strip().lower()

        # Apply friendly remaps
        for key, value in THEME_FALLBACKS.items():
            if key in t:
                t = value
                break

        # Block copyrighted/brand themes
        if any(blocked in t for blocked in BLOCKED_THEMES):
            return DEFAULT_THEME

        # Return sanitized or default
        return t or DEFAULT_THEME

    @staticmethod
    def is_valid_theme(theme: str) -> bool:
        """
        Check if theme is valid (not blocked).

        Args:
            theme: Theme to check

        Returns:
            True if valid, False if blocked
        """
        t = theme.lower().strip()
        return not any(blocked in t for blocked in BLOCKED_THEMES)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
