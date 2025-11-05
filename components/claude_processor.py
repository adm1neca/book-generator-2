from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DataInput
from langflow.schema import Data
from typing import List, Tuple, Optional
import json
import re
import time
import random
from datetime import datetime
from anthropic import Anthropic

class ClaudeProcessor(Component):
    display_name = "Claude Activity Processor 2"
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
        MessageTextInput(
            name="model_name",
            display_name="Model Name",
            info="Claude model to use. Try: claude-haiku-4-5-20251001, claude-sonnet-4, or specific versions",
            value="claude-haiku-4-5-20251001",
            required=False
        ),
        # NEW: reproducible variety control
        MessageTextInput(
            name="random_seed",
            display_name="Random Seed",
            info="Optional integer. Set to reproduce page subject choices.",
            value=""
        ),
        # NEW: user-tunable difficulty
        MessageTextInput(
            name="difficulty",
            display_name="Difficulty",
            info="easy | medium | hard (affects repetitions, maze difficulty)",
            value="easy"
        ),
    ]

    outputs = [
        Output(display_name="Processed Pages", name="processed_pages", method="process_pages"),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.used_items = {
            'coloring': [],
            'tracing': [],
            'counting': [],
            'dot-to-dot': []
        }
        self.detailed_logs = []
        self.session_start = datetime.now()

        print("🔵 ClaudeProcessor.__init__() called")
        try:
            self.status = "ClaudeProcessor initialized"
            self.log("🔵 ClaudeProcessor component initialized")
        except Exception as e:
            print(f"⚠️ Error in __init__ logging: {e}")

    # ---------- Utility: theme safety + mapping ----------
    def _sanitize_theme(self, theme: str) -> str:
        """Normalize and block branded themes to keep content safe."""
        t = (theme or "").strip().lower()

        # Friendly remaps
        fallbacks = {
            'forest': 'forest-friends', 'woods': 'forest-friends', 'forest friends': 'forest-friends',
            'sea': 'under-the-sea', 'ocean': 'under-the-sea', 'under the sea': 'under-the-sea',
            'farm': 'farm-day', 'farm animals': 'farm-day',
            'space': 'space-explorer', 'galaxy': 'space-explorer'
        }
        for k, v in fallbacks.items():
            if k in t:
                t = v
                break

        # Block copyrighted/brand themes
        blocked_keywords = ["peppa", "paw patrol", "paw-patrol", "disney", "marvel", "pokemon", "barbie"]
        if any(b in t for b in blocked_keywords):
            return "animals"

        return t or "animals"

    # ---------- Utility: difficulty ----------
    def _difficulty(self) -> str:
        d = (getattr(self, "difficulty", "easy") or "easy").strip().lower()
        if d not in ("easy", "medium", "hard"):
            d = "easy"
        return d

    # ---------- Utility: JSON extraction + retry ----------
    def _extract_json(self, text: str) -> Optional[dict]:
        # Strip code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.replace("```", "")
        m = re.search(r"\{[\s\S]*\}", cleaned)
        if not m:
            return None
        blob = m.group(0)
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            # Gentle cleanup: trailing commas before } or ]
            blob2 = re.sub(r",\s*([}\]])", r"\1", blob)
            try:
                return json.loads(blob2)
            except Exception:
                return None

    def _call_with_retry(self, prompt: str, api_key: str, page_number: int, retries: int = 2) -> Tuple[Optional[dict], str]:
        last_raw = ""
        for i in range(retries + 1):
            raw = self.call_claude(prompt, api_key, page_number)
            parsed = self._extract_json(raw)
            if parsed is not None:
                return parsed, raw
            last_raw = raw
            time.sleep(0.4 * (i + 1))
        return None, last_raw

    # ---------- Anthropic call ----------
    def call_claude(self, prompt: str, api_key: str, page_number: int = 0) -> str:
        """Call Claude API using official Anthropic SDK with detailed logging"""
        print(f"\n📤 Calling Claude API for page {page_number}...")
        self.log(f"\n{'='*60}")
        self.log(f"📤 SENDING TO CLAUDE (Page {page_number})")
        self.log(f"{'='*60}")
        self.log(f"PROMPT:\n{prompt}")
        self.log(f"{'='*60}\n")

        try:
            client = Anthropic(api_key=api_key)
            model = getattr(self, 'model_name', 'claude-3-5-sonnet') or 'claude-3-5-sonnet'
            print(f"🤖 Using model: {model}")

            message = client.messages.create(
                model=model,
                max_tokens=768,   # leaner default
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = message.content[0].text
            print(f"✅ Claude API response received for page {page_number}")

            # Usage logging if available
            usage = getattr(message, "usage", None)
            if usage:
                self.log(f"Token usage - input:{getattr(usage,'input_tokens', 'n/a')} output:{getattr(usage,'output_tokens','n/a')}")

            self.log(f"\n{'='*60}")
            self.log(f"📥 RECEIVED FROM CLAUDE (Page {page_number})")
            self.log(f"{'='*60}")
            self.log(f"RESPONSE:\n{response_text}")
            self.log(f"{'='*60}\n")

            self.detailed_logs.append({
                'timestamp': datetime.now().isoformat(),
                'page_number': page_number,
                'prompt': prompt,
                'response': response_text
            })

            return response_text

        except Exception as e:
            error_msg = f"API Error: {str(e)}"
            print(f"❌ ERROR calling Claude API for page {page_number}: {error_msg}")

            if "404" in str(e) or "not_found" in str(e):
                print("💡 TIP: Model not found. Try: claude-3-5-sonnet, claude-sonnet-4, or check API key access")

            self.log(f"\n{'='*60}")
            self.log(f"❌ ERROR calling Claude (Page {page_number})")
            self.log(f"{'='*60}")
            self.log(f"Error: {error_msg}")
            self.log(f"{'='*60}\n")

            self.detailed_logs.append({
                'timestamp': datetime.now().isoformat(),
                'page_number': page_number,
                'prompt': prompt,
                'response': f"ERROR: {error_msg}"
            })
            raise

    # ---------- Prompt builder ----------
    def get_prompt_for_type(self, page_type: str, theme: str, page_number: int) -> str:
        theme = self._sanitize_theme(theme)
        diff = self._difficulty()
        reps = 8 if diff == "easy" else 12 if diff == "medium" else 16

        style_guard = f"""
GLOBAL STYLE REQUIREMENTS:
- Target age: 4–5 years old
- Illustration style: thick black outlines, simple cute shapes, no shading
- Lots of white space; minimal clutter
- Friendly 1-sentence instructions
- Difficulty: {diff}
- No copyrighted characters or brands
- Keep the theme consistent across pages: '{theme}'
"""

        if page_type == 'coloring':
            theme_subjects = {
                'forest-friends': ['fox','bear','owl','rabbit','hedgehog','deer','squirrel','raccoon','snail','mushroom','acorn','pine tree'],
                'under-the-sea': ['fish','dolphin','starfish','shell','turtle','seahorse','crab','octopus','bubble','coral'],
                'farm-day': ['cow','chicken','sheep','pig','barn','tractor','duck','horse','hay bale'],
                'space-explorer': ['rocket','planet','star','moon','astronaut','satellite','comet'],
                'shapes': ['circle','square','triangle','star','heart','diamond','oval','rectangle','hexagon','pentagon'],
                'animals': ['cat','dog','rabbit','bird','fish','elephant','giraffe','lion','bear','monkey','butterfly','bee','duck','frog']
            }
            subjects = theme_subjects.get(theme, theme_subjects['animals'])

            used = self.used_items.get('coloring', [])
            available = [s for s in subjects if s not in used]
            if not available:
                self.used_items['coloring'] = []
                available = subjects

            selected = random.choice(available)

            return style_guard + f"""Create specifications for a simple coloring page for a 4–5 year old child.
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
}}"""

        elif page_type == 'tracing':
            options = [
                'A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P',
                '1','2','3','4','5','6','7','8','9','0',
                '○','△','□','★','♥'
            ]
            used = self.used_items.get('tracing', [])
            available = [s for s in options if s not in used]
            if not available:
                self.used_items['tracing'] = []
                available = options

            selected = random.choice(available)
            title_kind = "Letter" if selected.isalpha() else ("Number" if selected.isdigit() else "Shape")

            return style_guard + f"""Create a tracing worksheet for preschoolers.
Theme: {theme}
Page: {page_number}

CRITICAL: You MUST use THIS EXACT character: "{selected}"
Available options were: {', '.join(available)}
Already used (DO NOT REPEAT): {', '.join(used) if used else 'none'}

You must use EXACTLY: "{selected}"

Return ONLY valid JSON:
{{
  "title": "Trace the {title_kind} {selected}",
  "content": "{selected}",
  "instruction": "Trace over the dotted lines",
  "repetitions": {reps},
  "theme": "{theme}"
}}"""

        elif page_type == 'counting':
            count_options = [2, 3, 4, 5, 6, 7, 8, 9, 10]
            item_options = ['circle','star','heart','square','triangle','apple','flower','car','ball','balloon','butterfly','fish']

            used = self.used_items.get('counting', [])
            all_combinations = [f"{count}-{item}" for count in count_options for item in item_options]
            available = [c for c in all_combinations if c not in used]
            if not available:
                self.used_items['counting'] = []
                available = all_combinations

            choice = random.choice(available)
            count_str, item = choice.split('-')

            return style_guard + f"""Create a counting exercise for preschoolers.
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
            # Difficulty comes through in JSON
            diff = self._difficulty()
            return style_guard + f"""Create a maze title for preschoolers.
Theme: {theme}

Return ONLY valid JSON:
{{
  "title": "Fun Maze",
  "instruction": "Help find the way!",
  "difficulty": "{diff}",
  "theme": "{theme}"
}}"""

        elif page_type == 'matching':
            return style_guard + f"""Create a matching exercise for preschoolers.
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
            shape_options = ['star','circle','heart','square','triangle','diamond','house','tree','flower','butterfly','fish','apple']
            used = self.used_items.get('dot-to-dot', [])
            available = [s for s in shape_options if s not in used]
            if not available:
                self.used_items['dot-to-dot'] = []
                available = shape_options

            selected = random.choice(available)

            return style_guard + f"""Create a dot-to-dot exercise.
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
        print("\n" + "="*60)
        print("🚀 PROCESS_PAGES CALLED - STARTING NOW")
        print("="*60)

        self.status = "Claude Activity Processor started!"
        self.log("="*60)
        self.log("🚀 CLAUDE ACTIVITY PROCESSOR INITIALIZED")
        self.log("="*60)

        # NEW: reproducible randomness if provided
        try:
            seed_raw = getattr(self, "random_seed", "").strip()
            if seed_raw:
                random.seed(int(seed_raw))
                self.log(f"🔢 Random seed set to {seed_raw}")
        except Exception:
            self.log("⚠️ Random seed not applied (non-integer)")

        processed = []

        # Reset tracking for new run
        self.used_items = { 'coloring': [], 'tracing': [], 'counting': [], 'dot-to-dot': [] }
        self.detailed_logs = []
        self.session_start = datetime.now()

        self.log("\n🚀 Starting Claude Activity Generation")
        print("🚀 Starting Claude Activity Generation")

        if not hasattr(self, 'pages'):
            error_msg = "❌ ERROR: 'pages' attribute not found!"
            print(error_msg); self.log(error_msg); self.log("This might be a Langflow input issue.")
            self.save_detailed_logs(); return []

        if self.pages is None:
            error_msg = "❌ ERROR: 'pages' is None!"
            print(error_msg); self.log(error_msg); self.log("No pages were passed to the component.")
            self.save_detailed_logs(); return []

        total = len(self.pages)
        print(f"📊 Received {total} pages to process")

        if total == 0:
            warning_msg = "⚠️ WARNING: Received 0 pages to process!"
            print(warning_msg); self.log(warning_msg); self.log("Check that the pages input is connected and providing data.")
            self.save_detailed_logs(); return []

        self.log(f"📋 Total pages to process: {total}")
        self.log(f"📋 Pages input type: {type(self.pages)}")
        self.log(f"📋 First page preview: {self.pages[0].data if total > 0 else 'N/A'}\n")
        print(f"📋 Pages type: {type(self.pages)}, First page: {self.pages[0].data if total > 0 else 'N/A'}")

        for idx, page_data_obj in enumerate(self.pages):
            page = page_data_obj.data
            page_type = page['type']
            theme = page['theme']
            page_number = page['pageNumber']

            status_msg = f"Processing page {idx + 1}/{total} - {page_type} ({theme})"
            print(f"\n{'='*50}")
            print(f"🔄 {status_msg}")
            print(f"{'='*50}")
            self.status = status_msg

            prompt = self.get_prompt_for_type(page_type, theme, page_number)

            try:
                parsed, raw = self._call_with_retry(prompt, self.anthropic_api_key, page_number, retries=2)

                if parsed:
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

                    merged = {
                        'pageNumber': page_number,
                        'type': page_type,
                        'theme': self._sanitize_theme(theme),
                        **parsed
                    }
                    processed.append(Data(data=merged))
                else:
                    self.log(f"ERROR Page {page_number}: No JSON found after retries")
                    processed.append(Data(data={
                        **page,
                        'error': 'No JSON found',
                        'raw_response': (raw or '')[:400]
                    }))

                time.sleep(0.3)  # Rate limit cushion

            except Exception as e:
                self.status = f"Error on page {page_number}: {str(e)}"
                self.log(f"ERROR on page {page_number}: {str(e)}")
                processed.append(Data(data={ **page, 'error': str(e) }))

        processed.sort(key=lambda x: x.data.get('pageNumber', 0))

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

        log_file = self.save_detailed_logs()

        final_msg = f"✓ Completed {len(processed)} pages with variety! Logs: {log_file}"
        print("\n" + "="*60)
        print(f"✅ {final_msg}")
        print("="*60 + "\n")
        self.status = final_msg
        return processed