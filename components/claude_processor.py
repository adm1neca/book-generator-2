from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DataInput
from langflow.schema import Data
from typing import List
import json
import re
import requests
import time
import random
from datetime import datetime

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
        # Store detailed logs for debugging
        self.detailed_logs = []
        self.session_start = datetime.now()

    def call_claude(self, prompt: str, api_key: str, page_number: int = 0) -> str:
        """Call Claude API directly via HTTP with detailed logging"""
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

        # Log the prompt
        self.log(f"\n{'='*60}")
        self.log(f"📤 SENDING TO CLAUDE (Page {page_number})")
        self.log(f"{'='*60}")
        self.log(f"PROMPT:\n{prompt}")
        self.log(f"{'='*60}\n")

        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        response_text = result['content'][0]['text']

        # Log the response
        self.log(f"\n{'='*60}")
        self.log(f"📥 RECEIVED FROM CLAUDE (Page {page_number})")
        self.log(f"{'='*60}")
        self.log(f"RESPONSE:\n{response_text}")
        self.log(f"{'='*60}\n")

        # Store in detailed logs
        self.detailed_logs.append({
            'timestamp': datetime.now().isoformat(),
            'page_number': page_number,
            'prompt': prompt,
            'response': response_text
        })

        return response_text

    def get_prompt_for_type(self, page_type: str, theme: str, page_number: int) -> str:
        
        if page_type == 'coloring':
            # Greatly expanded subject options for variety
            theme_subjects = {
                'peppa-pig': ['pig', 'house', 'flower', 'heart', 'sun', 'car', 'tree', 'butterfly', 'apple', 'balloon', 'teddy bear', 'ball'],
                'paw-patrol': ['dog', 'star', 'fire truck', 'bone', 'paw print', 'badge', 'helicopter', 'truck', 'mountain', 'sun', 'cloud', 'tree'],
                'shapes': ['circle', 'square', 'triangle', 'star', 'heart', 'diamond', 'oval', 'rectangle', 'hexagon', 'pentagon'],
                'colors': ['rainbow', 'sun', 'flower', 'butterfly', 'apple', 'balloon', 'car', 'house', 'tree', 'heart', 'star', 'bird'],
                'animals': ['cat', 'dog', 'rabbit', 'bird', 'fish', 'elephant', 'giraffe', 'lion', 'bear', 'monkey', 'butterfly', 'bee', 'duck', 'frog']
            }
            subjects = theme_subjects.get(theme, ['star', 'heart', 'flower', 'sun', 'tree', 'house', 'car', 'balloon', 'butterfly', 'apple'])

            # Get what's already been used
            used = self.used_items.get('coloring', [])
            available = [s for s in subjects if s not in used]

            # If we've used everything, reset
            if not available:
                self.used_items['coloring'] = []
                available = subjects

            # Randomly select from available options
            selected = random.choice(available)

            return f"""Create specifications for a simple coloring page for a 3-4 year old child.
Theme: {theme}
Page Number: {page_number}

CRITICAL REQUIREMENT: You MUST use THIS EXACT subject: "{selected}"
Available options were: {', '.join(available)}
Already used (DO NOT REPEAT): {', '.join(used) if used else 'none yet'}

You must use EXACTLY: "{selected}"

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "title": "Color the {selected.title()}",
  "instruction": "Use your crayons to color me in!",
  "subject": "{selected}",
  "description": "[2-3 word fun description of the {selected}]",
  "theme": "{theme}"
}}

Example: {{"title": "Color the {selected.title()}", "instruction": "Use your crayons to color me in!", "subject": "{selected}", "description": "Happy little {selected}", "theme": "{theme}"}}"""

        elif page_type == 'tracing':
            # Expanded tracing options - letters, numbers, and simple shapes
            options = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P',
                      '1', '2', '3', '4', '5', '6', '7', '8', '9', '0',
                      '○', '△', '□', '★', '♥']
            used = self.used_items.get('tracing', [])
            available = [s for s in options if s not in used]

            if not available:
                self.used_items['tracing'] = []
                available = options

            # Randomly select from available
            selected = random.choice(available)

            return f"""Create a tracing worksheet for preschoolers.
Theme: {theme}
Page: {page_number}

CRITICAL: You MUST use THIS EXACT character: "{selected}"
Available options were: {', '.join(available)}
Already used (DO NOT REPEAT): {', '.join(used) if used else 'none'}

You must use EXACTLY: "{selected}"

Return ONLY valid JSON:
{{
  "title": "Trace the {'Letter' if selected.isalpha() else 'Number' if selected.isdigit() else 'Shape'} {selected}",
  "content": "{selected}",
  "instruction": "Trace over the dotted lines",
  "repetitions": 12,
  "theme": "{theme}"
}}

Example: {{"title": "Trace the {'Letter' if selected.isalpha() else 'Number' if selected.isdigit() else 'Shape'} {selected}", "content": "{selected}", "instruction": "Trace over the dotted lines", "repetitions": 12, "theme": "{theme}"}}"""

        elif page_type == 'counting':
            # Expanded counting options
            count_options = [2, 3, 4, 5, 6, 7, 8, 9, 10]
            item_options = ['circle', 'star', 'heart', 'square', 'triangle', 'apple', 'flower', 'car', 'ball', 'balloon', 'butterfly', 'fish']

            used = self.used_items.get('counting', [])

            # Create combinations and filter used ones
            all_combinations = [f"{count}-{item}" for count in count_options for item in item_options]
            available = [c for c in all_combinations if c not in used]

            if not available:
                self.used_items['counting'] = []
                available = all_combinations

            # Randomly pick from available
            choice = random.choice(available)
            count_str, item = choice.split('-')

            return f"""Create a counting exercise for preschoolers.
Theme: {theme}
Page: {page_number}

CRITICAL: YOU MUST USE EXACTLY: {count_str} {item}s
Available combinations were: {', '.join(available[:10])}{'...' if len(available) > 10 else ''}
Already used: {', '.join(used) if used else 'none'}

You must use EXACTLY: {count_str} {item}s

Return ONLY valid JSON:
{{
  "title": "Count the {item.title()}s",
  "count": {count_str},
  "item": "{item}",
  "instruction": "Count how many you see and write your answer",
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
            # Expanded dot-to-dot shapes with variety
            shape_options = ['star', 'circle', 'heart', 'square', 'triangle', 'diamond', 'house', 'tree', 'flower', 'butterfly', 'fish', 'apple']
            used = self.used_items.get('dot-to-dot', [])
            available = [s for s in shape_options if s not in used]

            if not available:
                self.used_items['dot-to-dot'] = []
                available = shape_options

            # Randomly select from available
            selected = random.choice(available)

            return f"""Create a dot-to-dot exercise.
Theme: {theme}
Page: {page_number}

CRITICAL: You MUST use THIS EXACT shape: "{selected}"
Available shapes were: {', '.join(available)}
Already used: {', '.join(used) if used else 'none'}

You must use EXACTLY: "{selected}"

Return ONLY valid JSON:
{{
  "title": "Connect the Dots",
  "instruction": "Connect 1 to 12 to reveal a {selected}",
  "dots": 12,
  "shape": "{selected}",
  "theme": "{theme}"
}}"""

        return ""

    def save_detailed_logs(self):
        """Save detailed logs to a file for debugging"""
        try:
            timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
            log_filename = f"claude_logs_{timestamp}.txt"

            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write("CLAUDE ACTIVITY GENERATOR - DETAILED LOG\n")
                f.write("="*80 + "\n")
                f.write(f"Session Start: {self.session_start.isoformat()}\n")
                f.write(f"Total Pages Processed: {len(self.detailed_logs)}\n")
                f.write("="*80 + "\n\n")

                for idx, log_entry in enumerate(self.detailed_logs, 1):
                    f.write(f"\n{'#'*80}\n")
                    f.write(f"PAGE {log_entry['page_number']} - Entry {idx}/{len(self.detailed_logs)}\n")
                    f.write(f"Timestamp: {log_entry['timestamp']}\n")
                    f.write(f"{'#'*80}\n\n")

                    f.write("PROMPT SENT TO CLAUDE:\n")
                    f.write("-"*80 + "\n")
                    f.write(log_entry['prompt'])
                    f.write("\n" + "-"*80 + "\n\n")

                    f.write("CLAUDE RESPONSE:\n")
                    f.write("-"*80 + "\n")
                    f.write(log_entry['response'])
                    f.write("\n" + "-"*80 + "\n\n")

                # Summary section
                f.write("\n" + "="*80 + "\n")
                f.write("SUMMARY\n")
                f.write("="*80 + "\n")
                f.write(f"Total API calls: {len(self.detailed_logs)}\n")
                f.write(f"Session duration: {(datetime.now() - self.session_start).total_seconds():.2f} seconds\n")
                f.write("\nItems used per activity type:\n")
                for activity_type, items in self.used_items.items():
                    f.write(f"  {activity_type}: {', '.join(items) if items else 'none'}\n")
                f.write("="*80 + "\n")

            self.log(f"\n✅ Detailed logs saved to: {log_filename}")
            return log_filename
        except Exception as e:
            self.log(f"⚠️ Failed to save detailed logs: {str(e)}")
            return None

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
        self.detailed_logs = []
        self.session_start = datetime.now()

        self.log("\n🚀 Starting Claude Activity Generation")
        self.log(f"Total pages to process: {total}\n")

        for idx, page_data_obj in enumerate(self.pages):
            page = page_data_obj.data
            page_type = page['type']
            theme = page['theme']
            page_number = page['pageNumber']

            self.status = f"Processing page {idx + 1}/{total} - {page_type} ({theme})"

            prompt = self.get_prompt_for_type(page_type, theme, page_number)

            try:
                content = self.call_claude(prompt, self.anthropic_api_key, page_number)
                
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

        # Save detailed logs
        self.log("\n" + "="*60)
        self.log("📊 GENERATION COMPLETE - SUMMARY")
        self.log("="*60)
        self.log(f"Total pages generated: {len(processed)}")
        self.log(f"Session duration: {(datetime.now() - self.session_start).total_seconds():.2f} seconds")
        self.log("\nVariety used per activity type:")
        for activity_type, items in self.used_items.items():
            if items:
                self.log(f"  {activity_type}: {', '.join(items)}")
        self.log("="*60 + "\n")

        # Save detailed logs to file
        log_file = self.save_detailed_logs()

        self.status = f"✓ Completed {len(processed)} pages with variety! Logs: {log_file}"
        return processed