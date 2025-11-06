"""Prompt building strategies for activity pages.

Design Pattern: Strategy Pattern + Factory Pattern
- Each activity type has its own strategy class
- PromptBuilderFactory creates appropriate strategy
- All strategies share common PromptStrategy interface

Usage:
    from components.prompts import PromptBuilderFactory

    # Get strategy for activity type
    builder = PromptBuilderFactory.get_builder('coloring')

    # Build prompt
    prompt, selected_item = builder.build(
        theme='animals',
        difficulty='easy',
        page_number=1,
        used_items=[],
        style_guard="..."
    )
"""

from components.prompts.base import PromptStrategy, SimplePromptStrategy
from components.prompts.factory import PromptBuilderFactory

# Import all concrete strategies for registration
from components.prompts.coloring_strategy import ColoringPromptStrategy
from components.prompts.tracing_strategy import TracingPromptStrategy
from components.prompts.counting_strategy import CountingPromptStrategy
from components.prompts.maze_strategy import MazePromptStrategy
from components.prompts.matching_strategy import MatchingPromptStrategy
from components.prompts.dot_to_dot_strategy import DotToDotPromptStrategy

__all__ = [
    # Main exports for client use
    'PromptBuilderFactory',
    'PromptStrategy',

    # For testing or advanced use
    'SimplePromptStrategy',

    # Concrete strategies (for testing)
    'ColoringPromptStrategy',
    'TracingPromptStrategy',
    'CountingPromptStrategy',
    'MazePromptStrategy',
    'MatchingPromptStrategy',
    'DotToDotPromptStrategy',
]
