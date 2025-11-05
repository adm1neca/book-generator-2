from langflow.custom import Component
from langflow.io import Output
from langflow.schema import Data
from typing import List

class PageGenerator(Component):
    display_name = "Page Generator"
    description = "Generates 30 page configurations for the booklet"
    icon = "file-text"

    outputs = [
        Output(display_name="Pages", name="pages", method="generate_pages"),
    ]

    def generate_pages(self) -> List[Data]:
        themes = ['peppa-pig', 'paw-patrol', 'shapes', 'colors', 'animals']
        activities = [
            {'type': 'coloring', 'count': 8},
            {'type': 'tracing', 'count': 6},
            {'type': 'dot-to-dot', 'count': 4},
            {'type': 'maze', 'count': 4},
            {'type': 'matching', 'count': 4},
            {'type': 'counting', 'count': 4}
        ]
        
        pages = []
        page_num = 1
        theme_index = 0
        
        for activity in activities:
            for i in range(activity['count']):
                theme = themes[theme_index % len(themes)]
                page_data = {
                    'pageNumber': page_num,
                    'type': activity['type'],
                    'theme': theme,
                    'themeName': theme.replace('-', ' ').upper()
                }
                pages.append(Data(data=page_data))
                page_num += 1
                theme_index += 1
        
        self.status = f"Generated {len(pages)} pages"
        return pages