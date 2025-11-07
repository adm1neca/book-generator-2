"""Counting exercise prompt strategy.

Generates prompts for counting exercises with various items.
"""

from components.prompts.base import PromptStrategy
from typing import List, Optional


class CountingPromptStrategy(PromptStrategy):
    """Strategy for generating counting exercise prompts.

    Combines count (0-15) with items to create counting exercises.
    Uses combination tracking for variety.
    """

    COUNT_OPTIONS = list(range(0, 16))
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

        # Track counts that have been used regardless of item variety
        used_counts = set()
        for used in used_items:
            try:
                count_part = int(used.split('-')[0])
            except (ValueError, IndexError):
                continue
            used_counts.add(count_part)

        # Prefer combinations that use counts not yet seen
        unused_counts = [count for count in self.COUNT_OPTIONS if count not in used_counts]
        if unused_counts:
            candidate_combinations = [
                combo
                for combo in all_combinations
                if self._extract_count(combo) in unused_counts
            ]
        else:
            candidate_combinations = all_combinations

        if not candidate_combinations:
            candidate_combinations = all_combinations

        # Select unused combination
        selected = self.select_item(candidate_combinations, used_items)

        # Parse combination
        count_str, item = selected.split('-')
        count_value = int(count_str)

        def format_count_phrase(count: int, noun: str) -> str:
            suffix = '' if count == 1 else 's'
            return f"{count} {noun}{suffix}"

        count_phrase = format_count_phrase(count_value, item)
        title_item = item.title() if count_value == 1 else f"{item.title()}s"

        # Show available options (limited to first 10 for readability)
        unused_combinations = [c for c in candidate_combinations if c not in used_items]
        available_display = unused_combinations[:10]
        more_indicator = '...' if len(available_display) < len(unused_combinations) else ''

        # Human-readable available combinations for prompt transparency
        formatted_available: List[str] = []
        for combo in available_display:
            count_option = self._extract_count(combo)
            if count_option is None:
                continue
            parts = combo.split('-', 1)
            if len(parts) != 2:
                continue
            formatted_available.append(format_count_phrase(count_option, parts[1]))

        # Build prompt
        prompt = style_guard + f"""Create a counting exercise for preschoolers.
Theme: {theme}
Page: {page_number}

CRITICAL: YOU MUST USE EXACTLY: {count_phrase}
Available combinations were: {', '.join(formatted_available) if formatted_available else 'various options'}{more_indicator}
Already used: {', '.join(used_items) if used_items else 'none'}

You must use EXACTLY: {count_phrase}

Return ONLY valid JSON:
{{
  "title": "Count the {title_item}",
  "count": {count_value},
  "item": "{item}",
  "instruction": "Count how many you see and write your answer",
  "theme": "{theme}"
}}"""

        return prompt, selected

    @staticmethod
    def _extract_count(combo: str) -> Optional[int]:
        """Extract the count integer from a combination string."""

        try:
            return int(combo.split('-')[0])
        except (ValueError, IndexError):
            return None
