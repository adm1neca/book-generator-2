from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DataInput
from langflow.schema import Data
from typing import List, Tuple, Optional, Dict
import time
import random
from datetime import datetime
from pathlib import Path

# Configuration modules (Phase 1 refactoring)
from components.config import (
    ThemeConfig,
    DifficultyConfig,
    PageLimitsConfig
)

# Prompt building strategies (Phase 2 refactoring)
from components.prompts import PromptBuilderFactory

# API client modules (Phase 3 refactoring)
from components.api import (
    ClaudeAPIClient,
    ResponseParser,
    RetryHandler
)

# Variety tracking module (Phase 4 refactoring)
from components.tracking import VarietyTracker

# Logging modules (Phase 5 refactoring)
from components.logging import SessionLogger, OutputDumper

class ClaudeProcessor(Component):
    """Claude Activity Processor - Main Orchestrator.

    A Langflow component that generates children's activity book pages using Claude AI.
    This is the main orchestrator that coordinates between specialized subsystems.

    Architecture (Post-Refactoring):
    --------------------------------
    This component follows a modular architecture with clear separation of concerns:

    1. Configuration Management (components/config/)
       - ThemeConfig: Theme sanitization and validation
       - DifficultyConfig: Difficulty normalization
       - PageLimitsConfig: Page limit parsing and enforcement

    2. Prompt Building (components/prompts/)
       - PromptBuilderFactory: Strategy factory for activity types
       - 6 Strategy classes: coloring, tracing, counting, maze, matching, dot-to-dot
       - Each strategy encapsulates prompt generation logic

    3. API Communication (components/api/)
       - ClaudeAPIClient: Adapter for Anthropic SDK
       - ResponseParser: JSON extraction and validation
       - RetryHandler: Exponential backoff retry logic

    4. Variety Tracking (components/tracking/)
       - VarietyTracker: State management for content diversity
       - Automatic reset when all options exhausted

    5. Logging System (components/logging/)
       - SessionLogger: Structured session and API call logging
       - OutputDumper: JSON output for testing and debugging

    Design Patterns Applied:
    -----------------------
    - Strategy Pattern: Prompt building strategies
    - Factory Pattern: Strategy creation
    - Adapter Pattern: Claude API client
    - State Pattern: Variety tracking
    - Observer Pattern (simplified): Logging
    - Template Method: Base strategy classes
    - Value Object: Configuration objects
    - Single Responsibility: Each module has one purpose
    - Open/Closed: Easy to extend without modification

    Inputs:
    -------
    - pages: List of page configurations to process
    - anthropic_api_key: Claude API key
    - model_name: Claude model (default: claude-haiku-4-5-20251001)
    - random_seed: Optional seed for reproducible variety
    - difficulty: easy|medium|hard (affects repetitions)
    - max_total_pages: Optional cap on total pages
    - pages_per_topic: Optional limits per activity type
    - dummy_output_dir: Optional directory for test JSON dumps

    Outputs:
    --------
    - processed_pages: List of Data objects with generated page specifications
    """
    display_name = "Claude Activity Processor 2"
    description = "Processes pages through Claude API with variety tracking"
    icon = "brain"

    MAX_CONSECUTIVE_API_FAILURES = 2

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
        MessageTextInput(
            name="use_latest_dummy_run",
            display_name="Use Latest Dummy Run",
            info="Set to true to replay the most recent dummy JSON and skip live Claude calls.",
            value="false"
        ),
    ]

    outputs = [
        Output(display_name="Processed Pages", name="processed_pages", method="process_pages"),
    ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # REFACTORED: Phase 4 - Use VarietyTracker for state management
        self.variety_tracker = VarietyTracker()
        # REFACTORED: Phase 5 - Use SessionLogger for logging
        self.session_logger = SessionLogger()

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

    def _use_latest_dummy_run(self) -> bool:
        raw_value = getattr(self, "use_latest_dummy_run", "")
        if raw_value is None:
            return False

        normalized = str(raw_value).strip().lower()
        return normalized in {"true", "1", "yes", "y", "on"}

    def _load_latest_dummy_run(self) -> Tuple[List[Data], Optional[Path]]:
        """Load the most recent dummy JSON file, returning processed pages."""

        directory = self._dummy_output_directory()
        if directory is None:
            self.log("Dummy playback requested but no dummy_output_dir is configured.")
            return [], None

        latest = OutputDumper.get_latest_dump(directory)
        if latest is None:
            self.log(f"Dummy playback requested but no files found in {directory}.")
            return [], None

        payload = OutputDumper.read_dump(latest)
        if not payload or "pages" not in payload:
            self.log(f"Dummy playback failed - '{latest}' is missing a 'pages' list.")
            return [], None

        pages = payload.get("pages", [])
        processed = [Data(data=item) for item in pages]

        self.log(f"Dummy playback mode active. Loaded {len(processed)} page(s) from {latest}.")
        print(f"📁 Using dummy run from {latest}")

        return processed, latest

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

    # REFACTORED: Phase 5 - Use OutputDumper for JSON output
    def _dump_processed_output(self, processed: List[Data]) -> Optional[Path]:
        """Dump processed output to JSON file using OutputDumper."""
        directory = self._dummy_output_directory()
        if directory is None:
            return None

        # Prepare metadata
        metadata = {
            "model": getattr(self, "model_name", ""),
            "difficulty": self._difficulty()
        }

        # Dump using OutputDumper
        file_path = OutputDumper.dump(
            processed_pages=[item.data for item in processed],
            logs=self.session_logger.get_detailed_logs(),
            output_dir=directory,
            metadata=metadata
        )

        if file_path:
            self.log(f"Saved Claude dummy data to {file_path}")
        else:
            self.log(f"Failed to dump Claude dummy data")

        return file_path

    # ---------- API Communication ----------
    # REFACTORED: Phase 3 - Uses ClaudeAPIClient + RetryHandler
    def _call_with_retry(self, prompt: str, api_key: str, page_number: int, retries: int = 2) -> Tuple[Optional[dict], str]:
        """Call Claude API with retry logic.

        Args:
            prompt: The prompt to send to Claude
            api_key: Anthropic API key
            page_number: Page number for logging
            retries: Number of retry attempts

        Returns:
            Tuple of (parsed_json, raw_response)
        """
        # Initialize API client
        model = getattr(self, 'model_name', 'claude-3-5-sonnet') or 'claude-3-5-sonnet'
        client = ClaudeAPIClient(api_key=api_key, model=model, max_tokens=768)
        client.set_logger(self.log)

        # Create retry handler
        retry_handler = RetryHandler(base_delay=0.4)

        # Make API call with retry
        api_call = lambda: client.send_message(prompt, page_number=page_number)
        parsed, raw = retry_handler.call_with_retry(api_call, retries=retries)

        # REFACTORED: Phase 5 - Merge client logs into session_logger
        for log_entry in client.get_detailed_logs():
            self.session_logger.log_api_call(
                page_number=log_entry.get('page_number', 0),
                prompt=log_entry.get('prompt', ''),
                response=log_entry.get('response', ''),
                model=log_entry.get('model'),
                usage=log_entry.get('usage')
            )

        return parsed, raw

    # ---------- Prompt builder ----------
    # REFACTORED: Phase 2 - Uses Strategy Pattern for prompt building
    def get_prompt_for_type(self, page_type: str, theme: str, page_number: int) -> Tuple[str, Optional[str]]:
        """Build prompt using appropriate strategy.

        Returns:
            Tuple of (prompt, selected_item) where selected_item is used for variety tracking
        """
        theme = self._sanitize_theme(theme)
        diff = self._difficulty()

        # Common style requirements for all page types
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

        # Get appropriate strategy from factory
        try:
            strategy = PromptBuilderFactory.get_builder(page_type)
        except ValueError:
            # Unknown page type, return empty
            return "", None

        # REFACTORED: Phase 4 - Use VarietyTracker for state
        used_items = self.variety_tracker.get_used(page_type)

        # Build prompt using strategy
        prompt, selected_item = strategy.build(
            theme=theme,
            difficulty=diff,
            page_number=page_number,
            used_items=used_items,
            style_guard=style_guard
        )

        return prompt, selected_item

    # REFACTORED: Phase 5 - Use SessionLogger for saving logs
    def save_detailed_logs(self):
        """Save detailed logs using SessionLogger."""
        variety_summary = self.variety_tracker.get_summary()
        filename = self.session_logger.save(variety_summary=variety_summary)
        if filename:
            self.log(f"\n✅ Detailed logs saved to: {filename}")
        return filename



    def process_pages(self) -> List[Data]:
        """Main orchestration method - processes activity pages through Claude API.

        Processing Flow:
        ---------------
        1. Initialize/Reset: Clear trackers and loggers
        2. Validate Input: Check pages input is valid
        3. Parse Limits: Apply max_total_pages and pages_per_topic constraints
        4. Process Loop: For each page:
           a. Check limits
           b. Build prompt using strategy
           c. Call Claude API with retry
           d. Track variety
           e. Merge results
        5. Finalize: Save logs and dump output

        Returns:
            List of Data objects with generated page specifications
        """
        # ========== PHASE 1: INITIALIZE ==========
        processed: List[Data] = []
        self.variety_tracker.reset()
        self.session_logger.clear()

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

        # ========== PHASE 2: VALIDATE INPUT ==========
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

        if self._use_latest_dummy_run():
            processed, source_path = self._load_latest_dummy_run()
            if processed:
                return self._finalize_run(
                    processed=processed,
                    per_topic_counts={},
                    per_topic_labels={},
                    skipped_due_to_limits=[],
                    dump_results=False,
                    existing_dummy_path=source_path
                )

            self.log("Proceeding with live Claude calls because dummy playback data was unavailable.")

        # ========== PHASE 3: PARSE LIMITS ==========
        total_limit = self._max_total_pages()
        if total_limit:
            self.log("Max total pages limit active: {}".format(total_limit))

        per_topic_limits = self._pages_per_topic()
        per_topic_counts = {}
        per_topic_labels = {}
        skipped_due_to_limits = []
        total_processed = 0
        consecutive_failures = 0

        # ========== PHASE 4: PROCESS LOOP ==========
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

            status_msg = "Processing page {}/{} - {} ({})".format(idx + 1, total, page_type, theme)
            print("\n" + "=" * 50)
            print("=> {}".format(status_msg))
            print("=" * 50)
            self.status = status_msg

            # REFACTORED: Phase 2 - get_prompt_for_type now returns (prompt, selected_item)
            prompt, selected_item = self.get_prompt_for_type(page_type, theme, page_number)

            success = False
            try:
                parsed, raw = self._call_with_retry(prompt, self.anthropic_api_key, page_number, retries=2)

                if parsed:
                    # REFACTORED: Phase 4 - Use VarietyTracker to mark items as used
                    if selected_item:
                        self.variety_tracker.mark_used(page_type, selected_item)
                        self.log("> Page {}: {} - {}".format(page_number, page_type, selected_item))

                    merged = {
                        'pageNumber': page_number,
                        'type': page_type,
                        'theme': self._sanitize_theme(theme),
                        **parsed
                    }
                    processed.append(Data(data=merged))
                    per_topic_counts[normalized_type] = current_count + 1
                    total_processed += 1
                    consecutive_failures = 0
                    success = True
                else:
                    self.log("ERROR Page {}: No JSON found after retries".format(page_number))
                    processed.append(Data(data={
                        **page,
                        'error': 'No JSON found',
                        'raw_response': (raw or '')[:400]
                    }))
                    consecutive_failures += 1

                time.sleep(0.3)

            except Exception as e:
                self.status = "Error on page {}: {}".format(page_number, e)
                self.log("ERROR on page {}: {}".format(page_number, e))
                processed.append(Data(data={**page, 'error': str(e)}))
                consecutive_failures += 1

            if not success and consecutive_failures >= self.MAX_CONSECUTIVE_API_FAILURES:
                abort_msg = (
                    f"Aborting Claude API calls after {consecutive_failures} consecutive failure(s)."
                )
                self.log(abort_msg)
                print(abort_msg)

                for remaining in self.pages[idx + 1:]:
                    remaining_page = remaining.data
                    processed.append(Data(data={
                        **remaining_page,
                        'error': 'Skipped due to consecutive Claude API failures'
                    }))

                break

        return self._finalize_run(
            processed=processed,
            per_topic_counts=per_topic_counts,
            per_topic_labels=per_topic_labels,
            skipped_due_to_limits=skipped_due_to_limits,
            dump_results=True
        )

    def _finalize_run(
        self,
        processed: List[Data],
        per_topic_counts: Dict[str, int],
        per_topic_labels: Dict[str, str],
        skipped_due_to_limits: List[str],
        dump_results: bool = True,
        existing_dummy_path: Optional[Path] = None
    ) -> List[Data]:
        """Shared finalization logic for both live and dummy playback runs."""

        processed.sort(key=lambda x: x.data.get('pageNumber', 0))

        dummy_path = existing_dummy_path
        if dump_results:
            generated_path = self._dump_processed_output(processed)
            if generated_path:
                dummy_path = generated_path
                self.log("Dummy JSON saved to {}".format(generated_path))
        elif dummy_path:
            self.log(f"Replayed output from existing dummy JSON: {dummy_path}")

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
        summary = self.session_logger.get_summary()
        self.log("Session duration: {:.2f} seconds".format(summary['duration_seconds']))
        self.log("\nVariety used per activity type:")
        for activity_type, items in self.variety_tracker.get_summary().items():
            if items:
                self.log("  {}: {}".format(activity_type, ', '.join(items)))
        self.log("=" * 60 + "\n")

        log_file = self.save_detailed_logs()

        final_msg = "Completed {} pages with variety! Logs: {}".format(len(processed), log_file)
        if dump_results and dummy_path:
            final_msg += " | Dummy JSON: {}".format(dummy_path)
        elif not dump_results and dummy_path:
            final_msg += " | Dummy Source: {}".format(dummy_path)
        if skipped_due_to_limits:
            final_msg += " | Skipped {} due to limits".format(len(skipped_due_to_limits))
        print("\n" + "=" * 60)
        print("* {}".format(final_msg))
        print("=" * 60 + "\n")
        self.status = final_msg
        return processed
