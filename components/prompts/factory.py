"""Factory for creating prompt building strategies.

Design Pattern: Factory Pattern + Registry Pattern
- Centralized strategy creation
- Easy to add new activity types
- Decouples client from concrete strategy classes
"""

from typing import Dict, Type
from components.prompts.base import PromptStrategy


# Import all concrete strategies
# (These will be created next)
from components.prompts.coloring_strategy import ColoringPromptStrategy
from components.prompts.tracing_strategy import TracingPromptStrategy
from components.prompts.counting_strategy import CountingPromptStrategy
from components.prompts.maze_strategy import MazePromptStrategy
from components.prompts.matching_strategy import MatchingPromptStrategy
from components.prompts.dot_to_dot_strategy import DotToDotPromptStrategy


class PromptBuilderFactory:
    """Factory for creating prompt strategies by page type.

    Factory Pattern: Centralized object creation
    Registry Pattern: Strategies registered in _strategies dict

    SOLID Principles:
    - Open/Closed: Add new types by registering, not modifying
    - Dependency Inversion: Client depends on factory, not concrete classes
    """

    # Registry of available strategies
    _strategies: Dict[str, Type[PromptStrategy]] = {
        'coloring': ColoringPromptStrategy,
        'tracing': TracingPromptStrategy,
        'counting': CountingPromptStrategy,
        'maze': MazePromptStrategy,
        'matching': MatchingPromptStrategy,
        'dot-to-dot': DotToDotPromptStrategy,
    }

    @classmethod
    def get_builder(cls, page_type: str) -> PromptStrategy:
        """Get appropriate prompt strategy for page type.

        Args:
            page_type: Type of activity page (coloring, tracing, etc.)

        Returns:
            Instance of appropriate PromptStrategy

        Raises:
            ValueError: If page_type is unknown

        Examples:
            >>> factory = PromptBuilderFactory()
            >>> builder = factory.get_builder('coloring')
            >>> assert isinstance(builder, ColoringPromptStrategy)

            >>> builder = factory.get_builder('invalid')  # doctest: +SKIP
            Traceback (most recent call last):
                ...
            ValueError: Unknown page type: invalid
        """
        strategy_class = cls._strategies.get(page_type)

        if not strategy_class:
            available = ', '.join(cls._strategies.keys())
            raise ValueError(
                f"Unknown page type: '{page_type}'. "
                f"Available types: {available}"
            )

        return strategy_class()

    @classmethod
    def register_strategy(cls, page_type: str, strategy_class: Type[PromptStrategy]):
        """Register a new strategy type.

        Allows dynamic registration of new activity types at runtime.

        Args:
            page_type: Name of the activity type
            strategy_class: Strategy class to use for this type

        Examples:
            >>> class CustomStrategy(PromptStrategy):
            ...     def build(self, *args): return "custom prompt", None
            >>> PromptBuilderFactory.register_strategy('custom', CustomStrategy)
            >>> builder = PromptBuilderFactory.get_builder('custom')
            >>> assert isinstance(builder, CustomStrategy)
        """
        cls._strategies[page_type] = strategy_class

    @classmethod
    def get_available_types(cls) -> list[str]:
        """Get list of all registered activity types.

        Returns:
            List of page type strings

        Examples:
            >>> types = PromptBuilderFactory.get_available_types()
            >>> assert 'coloring' in types
            >>> assert 'tracing' in types
        """
        return list(cls._strategies.keys())
