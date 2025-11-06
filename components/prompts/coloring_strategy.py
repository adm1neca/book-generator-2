"""Coloring page prompt strategy.

Generates prompts for simple coloring pages using theme-based subjects.
"""

from components.prompts.base import PromptStrategy
from components.config import THEME_SUBJECTS
from typing import List


class ColoringPromptStrategy(PromptStrategy):
    """Strategy for generating coloring page prompts.

    Uses theme-based subjects with variety tracking to avoid repetition.
    """

    def get_available_options(self, theme: str, difficulty: str) -> List[str]:
        """Get subject options for the given theme.

        Args:
            theme: Theme name (e.g., 'animals', 'forest-friends')
            difficulty: Not used for coloring (included for interface compatibility)

        Returns:
            List of subjects for the theme
        """
        return THEME_SUBJECTS.get(theme, THEME_SUBJECTS['animals'])

    def build(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        used_items: List[str],
        style_guard: str
    ) -> tuple[str, str]:
        """Build coloring page prompt.

        Args:
            theme: Sanitized theme string
            difficulty: Normalized difficulty (not used for coloring)
            page_number: Current page number
            used_items: List of subjects already used
            style_guard: Common style requirements

        Returns:
            Tuple of (prompt, selected_subject)
        """
        # Get available subjects for theme
        subjects = self.get_available_options(theme, difficulty)

        # Select unused subject
        selected = self.select_item(subjects, used_items)

        # Build prompt
        prompt = style_guard + f"""Create specifications for a simple coloring page for a 45 year old child.
Theme: {theme}
Page Number: {page_number}

CRITICAL REQUIREMENT: You MUST use THIS EXACT subject: "{selected}"
Available options were: {', '.join([s for s in subjects if s not in used_items][:10])}
Already used (DO NOT REPEAT): {', '.join(used_items) if used_items else 'none yet'}

You must use EXACTLY: "{selected}"

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "title": "Color the {selected.title()}",
  "instruction": "Use your crayons to color me in!",
  "subject": "{selected}",
  "description": "[2-3 word fun description of the {selected}]",
  "theme": "{theme}"
}}"""

        return prompt, selected
