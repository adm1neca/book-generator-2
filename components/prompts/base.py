"""Base strategy for prompt generation.

Design Pattern: Strategy Pattern
- Defines common interface for all prompt builders
- Each activity type implements this interface
- Enables polymorphism - all strategies interchangeable
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional


class PromptStrategy(ABC):
    """Abstract base class for prompt generation strategies.

    Strategy Pattern: Each activity type (coloring, tracing, etc.) implements
    this interface, allowing them to be used interchangeably.

    SOLID Principles:
    - Single Responsibility: Each strategy handles ONE activity type
    - Open/Closed: Add new types by creating new strategies
    - Liskov Substitution: All strategies are interchangeable
    - Interface Segregation: Minimal interface (only what's needed)
    """

    @abstractmethod
    def build(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        used_items: List[str],
        style_guard: str
    ) -> tuple[str, Optional[str]]:
        """Generate prompt for this activity type.

        Args:
            theme: Sanitized theme string
            difficulty: Normalized difficulty level (easy/medium/hard)
            page_number: Current page number
            used_items: List of items already used for variety tracking
            style_guard: Common style requirements string

        Returns:
            Tuple of (prompt_text, selected_item)
            - prompt_text: Complete prompt for Claude API
            - selected_item: Item that was selected (for variety tracking), or None

        Examples:
            >>> strategy = ColoringPromptStrategy()
            >>> prompt, item = strategy.build("animals", "easy", 1, [], style_guard)
            >>> assert "coloring" in prompt.lower()
            >>> assert item in ['cat', 'dog', 'rabbit', ...]
        """
        pass

    def get_available_options(self, theme: str, difficulty: str) -> List[str]:
        """Get all available options for this activity type.

        Some strategies use theme-based options (coloring), others don't (tracing).

        Args:
            theme: Current theme
            difficulty: Current difficulty level

        Returns:
            List of all available option strings

        Default implementation returns empty list (for strategies without options).
        """
        return []

    def select_item(
        self,
        available_options: List[str],
        used_items: List[str]
    ) -> str:
        """Select an unused item from available options.

        Common logic for variety tracking:
        1. Filter out used items
        2. If all used, reset and use full list
        3. Random selection

        Args:
            available_options: All possible options
            used_items: Items already used

        Returns:
            Selected item string
        """
        import random

        # Filter out used items
        available = [opt for opt in available_options if opt not in used_items]

        # Reset if all used
        if not available:
            available = available_options

        # Random selection
        return random.choice(available)


class SimplePromptStrategy(PromptStrategy):
    """Base class for simple strategies that don't track variety.

    Used for activity types like maze and matching that don't need
    to track used items.
    """

    def build(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        used_items: List[str],
        style_guard: str
    ) -> tuple[str, Optional[str]]:
        """Build prompt without variety tracking.

        Subclasses implement _build_prompt() to generate the actual prompt.
        """
        prompt = self._build_prompt(theme, difficulty, page_number, style_guard)
        return prompt, None  # No item selected for variety tracking

    @abstractmethod
    def _build_prompt(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        style_guard: str
    ) -> str:
        """Generate the prompt text.

        Implemented by subclasses.
        """
        pass
