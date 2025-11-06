"""Matching exercise prompt strategy.

Generates prompts for matching pair activities.
"""

from components.prompts.base import SimplePromptStrategy


class MatchingPromptStrategy(SimplePromptStrategy):
    """Strategy for generating matching exercise prompts.

    Uses SimplePromptStrategy since matching doesn't need variety tracking.
    Creates exercises with 4 pairs to match.
    """

    def _build_prompt(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        style_guard: str
    ) -> str:
        """Build matching exercise prompt.

        Args:
            theme: Current theme
            difficulty: Not used for matching
            page_number: Current page number
            style_guard: Common style requirements

        Returns:
            Complete prompt string
        """
        prompt = style_guard + f"""Create a matching exercise for preschoolers.
Theme: {theme}

Create EXACTLY 4 pairs using variety.

Return ONLY valid JSON:
{{
  "title": "Match the Pairs!",
  "instruction": "Draw lines to connect matching items",
  "pairs": [
    [{{"type": "shape", "shape": "circle"}}, {{"type": "shape", "shape": "circle"}}],
    [{{"type": "shape", "shape": "star"}}, {{"type": "shape", "shape": "star"}}],
    [{{"type": "shape", "shape": "heart"}}, {{"type": "shape", "shape": "heart"}}],
    [{{"type": "shape", "shape": "square"}}, {{"type": "shape", "shape": "square"}}]
  ],
  "theme": "{theme}"
}}"""

        return prompt
