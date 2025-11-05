from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DataInput
from langflow.schema import Data
from langchain_anthropic import ChatAnthropic
from typing import List
import json
import re

class ClaudeProcessor(Component):
    display_name = "Claude Activity Processor"
    description = "Processes pages through Claude API to generate activity specifications"
    icon = "brain"

    inputs = [
        DataInput(
            name="pages",
            display_name="Pages",
            info="List of page configurations",
            is_list=True
        ),
        SecretStrInput(
            name="anthropic_api_key",
            display_name="Anthropic API Key",
            info="Your Claude API key"
        ),
    ]

    outputs = [
        Output(display_name="Processed Pages", name="processed_pages", method="process_pages"),
    ]

    def get_prompt_for_type(self, page_type: str, theme: str, page_number: int) -> str:
        prompts = {
            'coloring': f"""Create specifications for a simple coloring page for a 3-4 year old child.
Theme: {theme}
Page Number: {page_number}

Requirements:
- Large, simple shapes suitable for preschoolers
- Subject appropriate for theme
- For Peppa Pig: pig-related items
- For Paw Patrol: dog/puppy items
- For Shapes: geometric shapes
- For Colors: colorful items
- For Animals: simple animals

Return ONLY valid JSON (no markdown, no explanation):
{{
  "title": "Color the [subject]",
  "instruction": "Use your crayons to color me in!",
  "subject": "[one word: pig, star, dog, heart, flower, house, etc]",
  "description": "[simple 2-3 words]",
  "theme": "{theme}"
}}""",

            'tracing': f"""Create a tracing worksheet for preschoolers (ages 3-4).
Theme: {theme}

Choose ONE letter (A-Z) or number (1-10) appropriate for the theme.

Return ONLY valid JSON:
{{
  "title": "Trace the [Letter/Number]",
  "content": "[single letter or number]",
  "instruction": "Trace over the dotted lines",
  "repetitions": 12,
  "theme": "{theme}"
}}""",

            'counting': f"""Create a counting exercise for preschoolers (ages 3-4).
Theme: {theme}

Choose a number between 3-8 and a simple item to count.
For items use ONLY: circle, star, heart, or square

Return ONLY valid JSON:
{{
  "title": "Count the [items]",
  "count": [number 3-8],
  "item": "[circle, star, heart, or square]",
  "instruction": "Count how many you see",
  "theme": "{theme}"
}}""",

            'maze': f"""Create a simple maze title for preschoolers.
Theme: {theme}

Return ONLY valid JSON:
{{
  "title": "[Theme] Maze",
  "instruction": "Help find the way!",
  "difficulty": "easy",
  "theme": "{theme}"
}}""",

            'matching': f"""Create a matching exercise for preschoolers (ages 3-4).
Theme: {theme}

Create 4 pairs using shapes, numbers, or colors.
For shapes use: circle, square, triangle, star, heart
For colors use hex: #FF0000 (red), #0000FF (blue), #FFFF00 (yellow), #00FF00 (green)

Return ONLY valid JSON:
{{
  "title": "Match the Pairs!",
  "instruction": "Draw lines to connect matching items",
  "pairs": [
    [{{"type": "number", "value": 1}}, {{"type": "number", "value": 1}}],
    [{{"type": "shape", "shape": "circle"}}, {{"type": "shape", "shape": "circle"}}],
    [{{"type": "color", "color": "#FF0000"}}, {{"type": "color", "color": "#FF0000"}}],
    [{{"type": "shape", "shape": "star"}}, {{"type": "shape", "shape": "star"}}]
  ],
  "theme": "{theme}"
}}""",

            'dot-to-dot': f"""Create a dot-to-dot exercise for preschoolers.
Theme: {theme}

Use 12-15 dots. Choose shape: star, circle, or heart

Return ONLY valid JSON:
{{
  "title": "Connect the Dots",
  "instruction": "Connect the dots from 1 to [number]",
  "dots": [number 12-15],
  "shape": "[star, circle, or heart]",
  "theme": "{theme}"
}}"""
        }
        
        return prompts.get(page_type, prompts['coloring'])

    def process_pages(self) -> List[Data]:
        llm = ChatAnthropic(
            model="claude-3-5-sonnet-20241022",
            anthropic_api_key=self.anthropic_api_key,
            max_tokens=1024
        )
        
        processed = []
        total = len(self.pages)
        
        for idx, page_data_obj in enumerate(self.pages):
            page = page_data_obj.data
            page_type = page['type']
            theme = page['theme']
            page_number = page['pageNumber']
            
            self.status = f"Processing page {idx + 1}/{total} - {page_type}"
            
            prompt = self.get_prompt_for_type(page_type, theme, page_number)
            
            try:
                response = llm.invoke(prompt)
                content = response.content
                
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    merged = {
                        'pageNumber': page_number,
                        'type': page_type,
                        'theme': theme,
                        **parsed
                    }
                    processed.append(Data(data=merged))
                else:
                    processed.append(Data(data={
                        **page,
                        'error': 'No JSON found in response'
                    }))
            except Exception as e:
                processed.append(Data(data={
                    **page,
                    'error': str(e)
                }))
        
        # Sort by page number
        processed.sort(key=lambda x: x.data.get('pageNumber', 0))
        self.status = f"Completed processing {len(processed)} pages"
        return processed