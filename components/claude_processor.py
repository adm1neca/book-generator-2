from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DataInput
from langflow.schema import Data
from typing import List, Tuple, Optional, Dict
import json
import re
import time
import random
from datetime import datetime
from pathlib import Path
from anthropic import Anthropic

# Configuration modules (Phase 1 refactoring)
from components.config import (
    ThemeConfig,
    DifficultyConfig,
    PageLimitsConfig,
    DIFFICULTY_REPETITIONS,
    THEME_SUBJECTS
)

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
        MessageTextInput(
            name="max_total_pages",
            display_name="Max Total Pages",
            info="Optional integer cap on how many pages this processor will generate. Leave blank for no total limit.",
            value=""
        ),
        MessageTextInput(
            name="pages_per_topic",
            display_name="Pages Per Topic",
            info="Optional limits per page topic/type. Accepts JSON (e.g. {\"coloring\":8}) or comma list like coloring=8,tracing=4.",
            value=""
        ),
        MessageTextInput(
            name="dummy_output_dir",
            display_name="Dummy Output Directory",
            info="Optional folder to store Claude JSON runs for Langflow tests. Leave blank to skip.",
            value="/tmp/claude_runs"
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
        """Normalize and block branded themes to keep content safe.

        REFACTORED: Delegates to ThemeConfig value object.
        Maintains backward compatibility - same signature, same behavior.
        """
        return ThemeConfig.sanitize(theme)

    # ---------- Utility: difficulty ----------
    def _difficulty(self) -> str:
        """Get normalized difficulty level.

        REFACTORED: Delegates to DifficultyConfig value object.
        """
        raw_difficulty = getattr(self, "difficulty", "easy")
        return DifficultyConfig.normalize(raw_difficulty)

    def _dummy_output_directory(self) -> Optional[Path]:
        dump_dir = (getattr(self, "dummy_output_dir", "") or "").strip()
        if not dump_dir:
            return None

        base_path = Path(dump_dir).expanduser()
        if not base_path.is_absolute():
            base_path = Path.cwd() / base_path

        try:
            base_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.log(f"Failed to ensure dummy output directory '{base_path}': {exc}")
            return None

        return base_path

    # ---------- Utility: page/topic limits ----------
    @staticmethod
    def _coerce_positive_int(raw_value, label: str) -> Optional[int]:
        """Convert incoming values to a positive int, logging when invalid.

        REFACTORED: Delegates to validation module.
        Method kept for backward compatibility.
        """
        from components.config import coerce_positive_int as validate_int
        return validate_int(raw_value, label)

    def _max_total_pages(self) -> Optional[int]:
        """Get maximum total pages limit.

        REFACTORED: Uses PageLimitsConfig parser.
        """
        raw_value = getattr(self, "max_total_pages", None)
        value = PageLimitsConfig.parse_max_total(raw_value)
        if value is None and raw_value not in (None, "", 0):
            self.log(f"Ignoring max_total_pages value '{raw_value}' (must be a positive integer).")
        return value

    def _pages_per_topic(self) -> Dict[str, int]:
        """Get per-topic page limits.

        REFACTORED: Delegates parsing to PageLimitsConfig.
        """
        raw = getattr(self, "pages_per_topic", None)

        try:
            limits = PageLimitsConfig.parse_pages_per_topic(raw)
        except Exception as exc:
            self.log(f"Could not parse pages_per_topic: {exc}")
            return {}

        if limits:
            pretty = ", ".join(f"{topic}={count}" for topic, count in limits.items())
            self.log(f"Pages-per-topic limits active: {pretty}")

        return limits

    def _dump_processed_output(self, processed: List[Data]) -> Optional[Path]:
        directory = self._dummy_output_directory()
        if directory is None:
            return None

        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"claude_run_{timestamp}.json"
        payload = {
            "meta": {
                "generated_at": datetime.utcnow().isoformat(),
                "model": getattr(self, "model_name", ""),
                "difficulty": self._difficulty(),
                "pages_count": len(processed)
            },
            "pages": [item.data for item in processed],
            "claude_logs": self.detailed_logs,
        }

        file_path = directory / filename

        try:
            with file_path.open("w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, indent=2)
            self.log(f"Saved Claude dummy data to {file_path}")
            return file_path
        except Exception as exc:
            self.log(f"Failed to dump Claude dummy data: {exc}")
            return None

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
        reps = DifficultyConfig.get_repetitions(diff)  # REFACTORED: Uses config

        style_guard = f"""
GLOBAL STYLE REQUIREMENTS:
- Target age: 2–3 years old
- Illustration style: thick black outlines, simple cute shapes, no shading
- Lots of white space; minimal clutter
- Friendly 1-sentence instructions
- Difficulty: {diff}
- No copyrighted characters or brands
- Keep the theme consistent across pages: '{theme}'
"""

        if page_type == 'coloring':
            # REFACTORED: Uses THEME_SUBJECTS from config
            subjects = THEME_SUBJECTS.get(theme, THEME_SUBJECTS['animals'])

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
        processed: List[Data] = []
        self.used_items = {
            'coloring': [],
            'tracing': [],
            'counting': [],
            'dot-to-dot': []
        }
        self.detailed_logs = []
        self.session_start = datetime.now()

        self.status = "Claude Activity Processor started!"
        self.log("=" * 60)
        self.log("CLAUDE ACTIVITY PROCESSOR INITIALIZED")
        self.log("=" * 60)

        try:
            seed_raw = str(getattr(self, "random_seed", "")).strip()
            if seed_raw:
                random.seed(int(seed_raw))
                self.log("Random seed set to {}".format(seed_raw))
        except Exception:
            self.log("Random seed not applied (non-integer)")

        self.log("\n--- Starting Claude Activity Generation ---")
        print("--- Starting Claude Activity Generation ---")

        if not hasattr(self, "pages"):
            error_msg = "ERROR: 'pages' attribute not found!"
            print(error_msg)
            self.log(error_msg)
            self.log("This might be a Langflow input issue.")
            self.save_detailed_logs()
            return []

        if self.pages is None:
            error_msg = "ERROR: 'pages' is None!"
            print(error_msg)
            self.log(error_msg)
            self.log("No pages were passed to the component.")
            self.save_detailed_logs()
            return []

        total = len(self.pages)
        print("-> Received {} pages to process".format(total))

        if total == 0:
            warning_msg = "WARNING: Received 0 pages to process!"
            print(warning_msg)
            self.log(warning_msg)
            self.log("Check that the pages input is connected and providing data.")
            self.save_detailed_logs()
            return []

        self.log("> Total pages to process: {}".format(total))
        self.log("> Pages input type: {}".format(type(self.pages)))
        preview = self.pages[0].data if total > 0 else 'N/A'
        self.log("> First page preview: {}\n".format(preview))
        print("> Pages type: {}, First page: {}".format(type(self.pages), preview))

        total_limit = self._max_total_pages()
        if total_limit:
            self.log("Max total pages limit active: {}".format(total_limit))

        per_topic_limits = self._pages_per_topic()
        per_topic_counts = {}
        per_topic_labels = {}
        skipped_due_to_limits = []
        total_processed = 0

        for idx, page_data_obj in enumerate(self.pages):
            if total_limit is not None and total_processed >= total_limit:
                remaining = total - idx
                limit_msg = "Reached max_total_pages limit ({}). Skipping remaining {} page(s).".format(total_limit, remaining)
                self.log(limit_msg)
                print(limit_msg)
                skipped_due_to_limits.append(limit_msg)
                break

            page = page_data_obj.data
            page_type = page['type']
            theme = page['theme']
            page_number = page['pageNumber']

            normalized_type = (page_type or "").strip().lower()
            if normalized_type:
                per_topic_labels.setdefault(normalized_type, page_type)
            else:
                normalized_type = "__unknown__"
                per_topic_labels.setdefault(normalized_type, page_type or "unknown")

            type_limit = per_topic_limits.get(normalized_type) if normalized_type != "__unknown__" else None
            current_count = per_topic_counts.get(normalized_type, 0)
            if type_limit is not None and current_count >= type_limit:
                skip_msg = "Skipping page {} ({}) - limit {} reached for topic '{}'.".format(page_number, page_type, type_limit, per_topic_labels[normalized_type])
                self.log(skip_msg)
                print(skip_msg)
                skipped_due_to_limits.append(skip_msg)
                continue

            per_topic_counts[normalized_type] = current_count + 1
            total_processed += 1

            status_msg = "Processing page {}/{} - {} ({})".format(idx + 1, total, page_type, theme)
            print("\n" + "=" * 50)
            print("=> {}".format(status_msg))
            print("=" * 50)
            self.status = status_msg

            prompt = self.get_prompt_for_type(page_type, theme, page_number)

            try:
                parsed, raw = self._call_with_retry(prompt, self.anthropic_api_key, page_number, retries=2)

                if parsed:
                    if page_type == 'coloring':
                        subject = parsed.get('subject', '')
                        if subject:
                            self.used_items['coloring'].append(subject)
                            self.log("> Page {}: {} coloring".format(page_number, subject))
                    elif page_type == 'tracing':
                        content_char = parsed.get('content', '')
                        if content_char:
                            self.used_items['tracing'].append(content_char)
                            self.log("> Page {}: Trace {}".format(page_number, content_char))
                    elif page_type == 'counting':
                        count = parsed.get('count', 0)
                        item = parsed.get('item', '')
                        if count and item:
                            self.used_items['counting'].append("{}-{}".format(count, item))
                            self.log("> Page {}: Count {} {}s".format(page_number, count, item))
                    elif page_type == 'dot-to-dot':
                        shape = parsed.get('shape', '')
                        if shape:
                            self.used_items['dot-to-dot'].append(shape)
                            self.log("> Page {}: {} dot-to-dot".format(page_number, shape))

                    merged = {
                        'pageNumber': page_number,
                        'type': page_type,
                        'theme': self._sanitize_theme(theme),
                        **parsed
                    }
                    processed.append(Data(data=merged))
                else:
                    self.log("ERROR Page {}: No JSON found after retries".format(page_number))
                    processed.append(Data(data={
                        **page,
                        'error': 'No JSON found',
                        'raw_response': (raw or '')[:400]
                    }))

                time.sleep(0.3)

            except Exception as e:
                self.status = "Error on page {}: {}".format(page_number, e)
                self.log("ERROR on page {}: {}".format(page_number, e))
                processed.append(Data(data={**page, 'error': str(e)}))

        processed.sort(key=lambda x: x.data.get('pageNumber', 0))

        dummy_path = self._dump_processed_output(processed)
        if dummy_path:
            self.log("Dummy JSON saved to {}".format(dummy_path))

        if per_topic_counts:
            self.log("Pages generated per topic/type:")
            for key, count in sorted(per_topic_counts.items()):
                label = per_topic_labels.get(key, key)
                if key == "__unknown__":
                    label = "unknown"
                self.log("  {}: {}".format(label, count))

        if skipped_due_to_limits:
            self.log("Skipped due to configured limits:")
            for entry in skipped_due_to_limits:
                self.log("  - {}".format(entry))

        self.log("\n" + "=" * 60)
        self.log("GENERATION COMPLETE - SUMMARY")
        self.log("=" * 60)
        self.log("Total pages generated: {}".format(len(processed)))
        duration = (datetime.now() - self.session_start).total_seconds()
        self.log("Session duration: {:.2f} seconds".format(duration))
        self.log("\nVariety used per activity type:")
        for activity_type, items in self.used_items.items():
            if items:
                self.log("  {}: {}".format(activity_type, ', '.join(items)))
        self.log("=" * 60 + "\n")

        log_file = self.save_detailed_logs()

        final_msg = "Completed {} pages with variety! Logs: {}".format(len(processed), log_file)
        if dummy_path:
            final_msg += " | Dummy JSON: {}".format(dummy_path)
        if skipped_due_to_limits:
            final_msg += " | Skipped {} due to limits".format(len(skipped_due_to_limits))
        print("\n" + "=" * 60)
        print("* {}".format(final_msg))
        print("=" * 60 + "\n")
        self.status = final_msg
        return processed
