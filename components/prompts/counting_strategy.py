"""Counting exercise prompt strategy.

Generates prompts for counting exercises with various items.
"""

from components.prompts.base import PromptStrategy
from typing import List


class CountingPromptStrategy(PromptStrategy):
    """Strategy for generating counting exercise prompts.

    Combines count (2-10) with items to create counting exercises.
    Uses combination tracking for variety.
    """

    COUNT_OPTIONS = [2, 3, 4, 5, 6, 7, 8, 9, 10]
    ITEM_OPTIONS = [
        'circle', 'star', 'heart', 'square', 'triangle',
        'apple', 'flower', 'car', 'ball', 'balloon',
        'butterfly', 'fish'
    ]

    def get_available_options(self, theme: str, difficulty: str) -> List[str]:
        """Get all count-item combinations.

        Args:
            theme: Not used for counting
            difficulty: Not used for option selection

        Returns:
            List of "count-item" combination strings
        """
        return [
            f"{count}-{item}"
            for count in self.COUNT_OPTIONS
            for item in self.ITEM_OPTIONS
        ]

    def build(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        used_items: List[str],
        style_guard: str
    ) -> tuple[str, str]:
        """Build counting exercise prompt.

        Args:
            theme: Current theme
            difficulty: Not used for counting
            page_number: Current page number
            used_items: Combinations already used
            style_guard: Common style requirements

        Returns:
            Tuple of (prompt, selected_combination)
        """
        # Get all combinations
        all_combinations = self.get_available_options(theme, difficulty)

        # Select unused combination
        selected = self.select_item(all_combinations, used_items)

        # Parse combination
        count_str, item = selected.split('-')

        # Show available options (limited to first 10 for readability)
        available_display = [c for c in all_combinations if c not in used_items][:10]
        more_indicator = '...' if len(available_display) < len([c for c in all_combinations if c not in used_items]) else ''

        # Build prompt
        prompt = style_guard + f"""Create a counting exercise for preschoolers.
Theme: {theme}
Page: {page_number}

CRITICAL: YOU MUST USE EXACTLY: {count_str} {item}s
Available combinations were: {', '.join(available_display)}{more_indicator}
Already used: {', '.join(used_items) if used_items else 'none'}

You must use EXACTLY: {count_str} {item}s

Return ONLY valid JSON:
{{
  "title": "Count the {item.title()}s",
  "count": {count_str},
  "item": "{item}",
  "instruction": "Count how many you see and write your answer",
  "theme": "{theme}"
}}"""

        return prompt, selected
