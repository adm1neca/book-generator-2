from langflow.custom import Component
from langflow.io import Output, MessageTextInput
from langflow.schema import Data
from typing import List

class PageGenerator(Component):
    display_name = "Page Generator"
    description = "Generates 30 page configurations for the booklet"
    icon = "file-text"

    # NEW: let user type a theme in the UI
    inputs = [
        MessageTextInput(
            name="theme",
            display_name="Theme",
            info="Theme slug, e.g. 'forest-friends', 'under-the-sea'",
            value="forest-friends"  # default for now
        ),
    ]

    outputs = [
        Output(display_name="Pages", name="pages", method="generate_pages"),
    ]

    def generate_pages(self) -> List[Data]:
        theme = (self.theme or "forest-friends").strip().lower()

        activities = [
            {'type': 'coloring', 'count': 8},
            {'type': 'tracing', 'count': 6},
            {'type': 'dot-to-dot', 'count': 4},
            {'type': 'maze', 'count': 4},
            {'type': 'matching', 'count': 4},
            {'type': 'counting', 'count': 4},
        ]

        pages = []
        page_num = 1

        for activity in activities:
            for _ in range(activity['count']):
                pages.append(Data(data={
                    'pageNumber': page_num,
                    'type': activity['type'],
                    'theme': theme,
                    'themeName': theme.replace('-', ' ').upper()
                }))
                page_num += 1

        self.status = f"Generated {len(pages)} pages with theme '{theme}'"
        return pages
