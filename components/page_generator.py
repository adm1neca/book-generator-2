from langflow.custom import Component
from langflow.io import Output, MessageTextInput
from langflow.schema import Data
from typing import List

class PageGenerator(Component):
    display_name = "Page Generator"
    description = "Generates 30 page configurations for the booklet"
    icon = "file-text"

    # New user-facing controls so they sit next to each other in the UI
    inputs = [
        MessageTextInput(
            name="theme",
            display_name="Theme",
            info="Theme slug, e.g. 'forest-friends', 'under-the-sea', 'farm-day', 'space-explorer'",
            value="forest-friends"
        ),
        MessageTextInput(
            name="difficulty",
            display_name="Difficulty",
            info="easy | medium | hard",
            value="easy"
        ),
        MessageTextInput(
            name="random_seed",
            display_name="Random Seed",
            info="Optional integer. Set to reproduce subject choices downstream.",
            value=""
        ),
    ]

    outputs = [
        Output(display_name="Pages", name="pages", method="generate_pages"),
    ]

    def generate_pages(self) -> List[Data]:
        theme = (getattr(self, "theme", "forest-friends") or "forest-friends").strip().lower()
        difficulty = (getattr(self, "difficulty", "easy") or "easy").strip().lower()
        random_seed = (getattr(self, "random_seed", "") or "").strip()

        # Activity mix (kept from your original flow)
        activities = [
            {"type": "coloring",  "count": 8},
            {"type": "tracing",   "count": 6},
            {"type": "dot-to-dot","count": 4},
            {"type": "maze",      "count": 4},
            {"type": "matching",  "count": 4},
            {"type": "counting",  "count": 4},
        ]

        pages: List[Data] = []
        page_num = 1

        for activity in activities:
            for _ in range(activity["count"]):
                pages.append(
                    Data(
                        data={
                            "pageNumber": page_num,
                            "type": activity["type"],
                            "theme": theme,
                            "themeName": theme.replace("-", " ").upper(),
                            # Pass-through so downstream nodes can read them if desired
                            "difficulty": difficulty,
                            "randomSeed": random_seed,
                        }
                    )
                )
                page_num += 1

        self.status = f"Generated {len(pages)} pages | theme='{theme}', difficulty='{difficulty}', seed='{random_seed or '∅'}'"
        return pages
