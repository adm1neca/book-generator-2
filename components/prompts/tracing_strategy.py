"""Tracing worksheet prompt strategy.

Generates prompts for letter/number/shape tracing worksheets.
"""

from components.prompts.base import PromptStrategy
from components.config import DifficultyConfig
from typing import List


class TracingPromptStrategy(PromptStrategy):
    """Strategy for generating tracing worksheet prompts.

    Uses letters, numbers, and basic shapes with variety tracking.
    """

    # Fixed set of tracing options
    OPTIONS = [
        'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M',
        'N', 'O', 'P',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
        'Ë', '³', '¡', '', 'e'
    ]

    def get_available_options(self, theme: str, difficulty: str) -> List[str]:
        """Get tracing options (letters/numbers/shapes).

        Args:
            theme: Not used for tracing
            difficulty: Not used for option selection

        Returns:
            List of traceable characters
        """
        return self.OPTIONS

    def build(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        used_items: List[str],
        style_guard: str
    ) -> tuple[str, str]:
        """Build tracing worksheet prompt.

        Args:
            theme: Current theme
            difficulty: Determines repetition count
            page_number: Current page number
            used_items: Characters already used
            style_guard: Common style requirements

        Returns:
            Tuple of (prompt, selected_character)
        """
        # Get repetitions based on difficulty
        reps = DifficultyConfig.get_repetitions(difficulty)

        # Select unused character
        selected = self.select_item(self.OPTIONS, used_items)

        # Determine type for title
        if selected.isalpha():
            title_kind = "Letter"
        elif selected.isdigit():
            title_kind = "Number"
        else:
            title_kind = "Shape"

        # Build prompt
        prompt = style_guard + f"""Create a tracing worksheet for preschoolers.
Theme: {theme}
Page: {page_number}

CRITICAL: You MUST use THIS EXACT character: "{selected}"
Available options were: {', '.join([opt for opt in self.OPTIONS if opt not in used_items][:15])}
Already used (DO NOT REPEAT): {', '.join(used_items) if used_items else 'none'}

You must use EXACTLY: "{selected}"

Return ONLY valid JSON:
{{
  "title": "Trace the {title_kind} {selected}",
  "content": "{selected}",
  "instruction": "Trace over the dotted lines",
  "repetitions": {reps},
  "theme": "{theme}"
}}"""

        return prompt, selected
