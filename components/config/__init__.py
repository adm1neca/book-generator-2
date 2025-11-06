"""Configuration management for Claude processor.

Design Pattern: Facade Pattern
- Provides clean public API for config subsystem
- Hides internal module structure
- Makes imports simple and consistent

Usage:
    from components.config import ThemeConfig, THEME_SUBJECTS

Instead of:
    from components.config.theme_config import ThemeConfig
    from components.config.constants import THEME_SUBJECTS
"""

from components.config.constants import (
    THEME_FALLBACKS,
    BLOCKED_THEMES,
    DEFAULT_THEME,
    VALID_DIFFICULTIES,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_REPETITIONS,
    THEME_SUBJECTS,
    TARGET_AGE_MIN,
    TARGET_AGE_MAX,
    STYLE_DESCRIPTION
)

from components.config.validation import (
    coerce_positive_int,
    validate_string_not_empty
)

from components.config.theme_config import ThemeConfig
from components.config.difficulty_config import DifficultyConfig
from components.config.limits_config import PageLimitsConfig

__all__ = [
    # Constants
    'THEME_FALLBACKS',
    'BLOCKED_THEMES',
    'DEFAULT_THEME',
    'VALID_DIFFICULTIES',
    'DEFAULT_DIFFICULTY',
    'DIFFICULTY_REPETITIONS',
    'THEME_SUBJECTS',
    'TARGET_AGE_MIN',
    'TARGET_AGE_MAX',
    'STYLE_DESCRIPTION',

    # Validation
    'coerce_positive_int',
    'validate_string_not_empty',

    # Config classes
    'ThemeConfig',
    'DifficultyConfig',
    'PageLimitsConfig',
]
