"""Difficulty configuration management.

Design Pattern: Value Object Pattern
- Validates difficulty levels
- Maps difficulty to game parameters (repetitions)
- Encapsulates difficulty-related business rules
"""

from typing import Optional
from components.config.constants import (
    VALID_DIFFICULTIES,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_REPETITIONS
)


class DifficultyConfig:
    """Handles difficulty level validation and settings.

    Value Object Pattern: Ensures valid difficulty levels.
    Single Responsibility: Only handles difficulty logic.
    """

    @staticmethod
    def normalize(difficulty: Optional[str]) -> str:
        """
        Normalize difficulty to valid value.

        Guarantees return value is one of: easy, medium, hard.

        Args:
            difficulty: Raw difficulty string

        Returns:
            Valid difficulty level (easy, medium, or hard)

        Examples:
            >>> DifficultyConfig.normalize("EASY")
            'easy'
            >>> DifficultyConfig.normalize("Medium")
            'medium'
            >>> DifficultyConfig.normalize("invalid")
            'easy'
            >>> DifficultyConfig.normalize(None)
            'easy'
        """
        d = (difficulty or "").strip().lower()
        if d not in VALID_DIFFICULTIES:
            return DEFAULT_DIFFICULTY
        return d

    @staticmethod
    def get_repetitions(difficulty: str) -> int:
        """
        Get number of repetitions for difficulty level.

        Business Rule: Maps difficulty to tracing repetition count.

        Args:
            difficulty: Difficulty level

        Returns:
            Number of repetitions for tracing activities

        Examples:
            >>> DifficultyConfig.get_repetitions("easy")
            8
            >>> DifficultyConfig.get_repetitions("medium")
            12
            >>> DifficultyConfig.get_repetitions("hard")
            16
        """
        normalized = DifficultyConfig.normalize(difficulty)
        return DIFFICULTY_REPETITIONS[normalized]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
