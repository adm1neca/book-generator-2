"""Dot-to-dot exercise prompt strategy.

Generates prompts for dot-to-dot activities with various shapes.
"""

from components.prompts.base import PromptStrategy
from typing import List


class DotToDotPromptStrategy(PromptStrategy):
    """Strategy for generating dot-to-dot exercise prompts.

    Uses shape selection with variety tracking.
    """

    SHAPE_OPTIONS = [
        'star', 'circle', 'heart', 'square', 'triangle',
        'diamond', 'house', 'tree', 'flower', 'butterfly',
        'fish', 'apple'
    ]

    def get_available_options(self, theme: str, difficulty: str) -> List[str]:
        """Get shape options for dot-to-dot.

        Args:
            theme: Not used for dot-to-dot
            difficulty: Not used for option selection

        Returns:
            List of shape names
        """
        return self.SHAPE_OPTIONS

    def build(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        used_items: List[str],
        style_guard: str
    ) -> tuple[str, str]:
        """Build dot-to-dot exercise prompt.

        Args:
            theme: Current theme
            difficulty: Not used for dot-to-dot
            page_number: Current page number
            used_items: Shapes already used
            style_guard: Common style requirements

        Returns:
            Tuple of (prompt, selected_shape)
        """
        # Select unused shape
        selected = self.select_item(self.SHAPE_OPTIONS, used_items)

        # Show available shapes
        available_display = [s for s in self.SHAPE_OPTIONS if s not in used_items]

        # Build prompt
        prompt = style_guard + f"""Create a dot-to-dot exercise.
Theme: {theme}
Page: {page_number}

CRITICAL: You MUST use THIS EXACT shape: "{selected}"
Available shapes were: {', '.join(available_display)}
Already used: {', '.join(used_items) if used_items else 'none'}

You must use EXACTLY: "{selected}"

Return ONLY valid JSON:
{{
  "title": "Connect the Dots",
  "instruction": "Connect 1 to 12 to reveal a {selected}",
  "dots": 12,
  "shape": "{selected}",
  "theme": "{theme}"
}}"""

        return prompt, selected
