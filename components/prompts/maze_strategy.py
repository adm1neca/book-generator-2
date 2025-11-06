"""Maze prompt strategy.

Generates prompts for maze activities.
"""

from components.prompts.base import SimplePromptStrategy


class MazePromptStrategy(SimplePromptStrategy):
    """Strategy for generating maze prompts.

    Uses SimplePromptStrategy since mazes don't need variety tracking.
    Difficulty is passed through to the JSON output.
    """

    def _build_prompt(
        self,
        theme: str,
        difficulty: str,
        page_number: int,
        style_guard: str
    ) -> str:
        """Build maze prompt.

        Args:
            theme: Current theme
            difficulty: Maze difficulty level
            page_number: Current page number
            style_guard: Common style requirements

        Returns:
            Complete prompt string
        """
        prompt = style_guard + f"""Create a maze title for preschoolers.
Theme: {theme}

Return ONLY valid JSON:
{{
  "title": "Fun Maze",
  "instruction": "Help find the way!",
  "difficulty": "{difficulty}",
  "theme": "{theme}"
}}"""

        return prompt
