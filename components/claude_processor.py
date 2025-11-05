from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DataInput
from langflow.schema import Data
from typing import List
import json
import re
import requests
import time

class ClaudeProcessor(Component):
    display_name = "Claude Activity Processor"
    description = "Processes pages through Claude API with variety tracking"
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
            info="Your Claude API key",
            required=True
        ),
    ]

    outputs = [
        Output(display_name="Processed Pages", name="processed_pages", method="process_pages"),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Track what has been used for each page type
        self.used_items = {
            'coloring': [],
            'tracing': [],
            'counting': [],
            'dot-to-dot': []
        }

    def call_claude(self, prompt: str, api_key: str) -> str:
        """Call Claude API directly via HTTP"""
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result['content'][0]['text']

    def get_prompt_for_type(self, page_type: str, theme: str, page_number: int) -> str:
        
        if page_type == 'coloring':
            theme_subjects = {
                'peppa-pig': ['pig', 'house', 'flower', 'heart'],
                'paw-patrol': ['star', 'flower', 'heart', 'pig'],
                'shapes': ['star', 'heart', 'flower', 'pig'],
                'colors': ['star', 'heart', 'flower', 'pig'],
                'animals': ['pig', 'star', 'heart', 'flower']
            }
            subjects = theme_subjects.get(theme, ['star', 'heart', 'flower', 'pig'])
            
            # Get what's already been used
            used = self.used_items.get('coloring', [])
            available = [s for s in subjects if s not in used]
            
            # If we've used everything, reset
            if not available:
                self.used_items['coloring'] = []
                available = subjects
            
            return f"""Create specifications for a simple coloring page for a 3-4 year old child.
Theme: {theme}
Page Number: {page_number}

CRITICAL REQUIREMENT: You MUST choose from these available options only: {', '.join(available)}
Already used (DO NOT REPEAT): {', '.join(used) if used else 'none yet'}

Pick EXACTLY ONE subject from the available list. Choose the FIRST available option.

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "title": "Color the [subject]",
  "instruction": "Use your crayons to color me in!",
  "subject": "[EXACTLY ONE WORD from available list]",
  "description": "[2-3 word description]",
  "theme": "{theme}"
}}

Example: {{"title": "Color the Star", "instruction": "Use your crayons to color me in!", "subject": "star", "description": "Big yellow star", "theme": "{theme}"}}"""

        elif page_type == 'tracing':
            options = ['A', 'B', 'C', 'P', '1', '2', '3', '4', '5']
            used = self.used_items.get('tracing', [])
            available = [s for s in options if s not in used]
            
            if not available:
                self.used_items['tracing'] = []
                available = options
            
            return f"""Create a tracing worksheet for preschoolers.
Theme: {theme}
Page: {page_number}

CRITICAL: Choose from AVAILABLE options: {', '.join(available)}
Already used (DO NOT REPEAT): {', '.join(used) if used else 'none'}

Pick the FIRST available option from the list above.

Return ONLY valid JSON:
{{
  "title": "Trace the [Letter/Number]",
  "content": "[single character from available list]",
  "instruction": "Trace over the dotted lines",
  "repetitions": 12,
  "theme": "{theme}"
}}

Example: {{"title": "Trace the Letter B", "content": "B", "instruction": "Trace over the dotted lines", "repetitions": 12, "theme": "{theme}"}}"""

        elif page_type == 'counting':
            count_options = [3, 4, 5, 6, 7]
            item_options = ['circle', 'star', 'heart']
            
            used = self.used_items.get('counting', [])
            
            # Create combinations and filter used ones
            all_combinations = [f"{count}-{item}" for count in count_options for item in item_options]
            available = [c for c in all_combinations if c not in used]
            
            if not available:
                self.used_items['counting'] = []
                available = all_combinations
            
            # Pick first available
            choice = available[0]
            count_str, item = choice.split('-')
            
            return f"""Create a counting exercise for preschoolers.
Theme: {theme}

YOU MUST USE: {count_str} {item}s

Return ONLY valid JSON:
{{
  "title": "Count the {item.title()}s",
  "count": {count_str},
  "item": "{item}",
  "instruction": "Count how many you see",
  "theme": "{theme}"
}}"""

        elif page_type == 'maze':
            return f"""Create a maze title for preschoolers.
Theme: {theme}

Return ONLY valid JSON:
{{
  "title": "Fun Maze",
  "instruction": "Help find the way!",
  "difficulty": "easy",
  "theme": "{theme}"
}}"""

        elif page_type == 'matching':
            return f"""Create a matching exercise for preschoolers.
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

        elif page_type == 'dot-to-dot':
            shape_options = ['star', 'circle', 'heart']
            used = self.used_items.get('dot-to-dot', [])
            available = [s for s in shape_options if s not in used]
            
            if not available:
                self.used_items['dot-to-dot'] = []
                available = shape_options
            
            return f"""Create a dot-to-dot exercise.
Theme: {theme}

AVAILABLE shapes: {', '.join(available)}
Already used: {', '.join(used) if used else 'none'}

Pick the FIRST available shape.

Return ONLY valid JSON:
{{
  "title": "Connect the Dots",
  "instruction": "Connect 1 to 12",
  "dots": 12,
  "shape": "[first available shape]",
  "theme": "{theme}"
}}"""

        return ""

    def process_pages(self) -> List[Data]:
        processed = []
        total = len(self.pages)
        
        # Reset tracking for new run
        self.used_items = {
            'coloring': [],
            'tracing': [],
            'counting': [],
            'dot-to-dot': []
        }
        
        for idx, page_data_obj in enumerate(self.pages):
            page = page_data_obj.data
            page_type = page['type']
            theme = page['theme']
            page_number = page['pageNumber']
            
            self.status = f"Processing page {idx + 1}/{total} - {page_type} ({theme})"
            
            prompt = self.get_prompt_for_type(page_type, theme, page_number)
            
            try:
                content = self.call_claude(prompt, self.anthropic_api_key)
                
                # Remove markdown code blocks if present
                content = re.sub(r'```json\s*', '', content)
                content = re.sub(r'```\s*', '', content)
                
                # Extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    parsed = json.loads(json_match.group(0))
                    
                    # Track what we used
                    if page_type == 'coloring':
                        subject = parsed.get('subject', '')
                        if subject:
                            self.used_items['coloring'].append(subject)
                            self.log(f"✓ Page {page_number}: {subject} coloring")
                    elif page_type == 'tracing':
                        content_char = parsed.get('content', '')
                        if content_char:
                            self.used_items['tracing'].append(content_char)
                            self.log(f"✓ Page {page_number}: Trace {content_char}")
                    elif page_type == 'counting':
                        count = parsed.get('count', 0)
                        item = parsed.get('item', '')
                        if count and item:
                            self.used_items['counting'].append(f"{count}-{item}")
                            self.log(f"✓ Page {page_number}: Count {count} {item}s")
                    elif page_type == 'dot-to-dot':
                        shape = parsed.get('shape', '')
                        if shape:
                            self.used_items['dot-to-dot'].append(shape)
                            self.log(f"✓ Page {page_number}: {shape} dot-to-dot")
                    
                    # Ensure required fields exist
                    merged = {
                        'pageNumber': page_number,
                        'type': page_type,
                        'theme': theme,
                        **parsed
                    }
                    
                    processed.append(Data(data=merged))
                else:
                    self.log(f"ERROR Page {page_number}: No JSON found")
                    processed.append(Data(data={
                        **page,
                        'error': 'No JSON found',
                        'raw_response': content[:200]
                    }))
                    
                # Small delay to avoid rate limits
                time.sleep(0.3)
                
            except Exception as e:
                self.status = f"Error on page {page_number}: {str(e)}"
                self.log(f"ERROR on page {page_number}: {str(e)}")
                processed.append(Data(data={
                    **page,
                    'error': str(e)
                }))
        
        # Sort by page number
        processed.sort(key=lambda x: x.data.get('pageNumber', 0))
        self.status = f"✓ Completed {len(processed)} pages with variety!"
        return processed