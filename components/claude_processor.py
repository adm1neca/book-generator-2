from langflow.custom import Component
from langflow.io import MessageTextInput, Output, SecretStrInput, DataInput
from langflow.schema import Data
from typing import List, Optional
import random
from pathlib import Path

# Configuration modules (Phase 1 refactoring)
from components.config import (
    ThemeConfig,
    DifficultyConfig,
    PageLimitsConfig
)

# API client modules (Phase 3 refactoring)
from components.api import ClaudeAPIClient, RetryHandler

# Variety tracking module (Phase 4 refactoring)
from components.tracking import VarietyTracker

# Logging modules (Phase 5 refactoring)
from components.logging import SessionLogger, OutputDumper

# Prompt building (Phase 2 refactoring)
from components.prompts import PromptBuilderFactory

# NEW: Processor modules (Phase 6 refactoring)
from components.processor import (
    LoggerFacade,
    PageLimiter,
    LimiterConfig,
    PageProcessor,
    ProcessorConfig,
    ProcessingPipeline,
    PipelineConfig,
)


class ClaudeProcessor(Component):
    """Claude Activity Processor - Thin Langflow Adapter.

    This component is now a thin adapter that delegates all processing logic
    to the ProcessingPipeline. It focuses solely on:
    1. Parsing Langflow inputs into configuration objects
    2. Building and injecting dependencies
    3. Running the pipeline
    4. Returning Langflow-formatted results

    All business logic has been moved to testable, focused modules in
    components/processor/.

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
            info="Claude model to use",
            value="claude-haiku-4-5-20251001",
            required=False
        ),
        MessageTextInput(
            name="random_seed",
            display_name="Random Seed",
            info="Optional integer for reproducible variety",
            value=""
        ),
        MessageTextInput(
            name="difficulty",
            display_name="Difficulty",
            info="easy | medium | hard",
            value="easy"
        ),
        MessageTextInput(
            name="max_total_pages",
            display_name="Max Total Pages",
            info="Optional integer cap on total pages",
            value=""
        ),
        MessageTextInput(
            name="pages_per_topic",
            display_name="Pages Per Topic",
            info="Optional limits per page type (JSON or comma-separated)",
            value=""
        ),
        MessageTextInput(
            name="dummy_output_dir",
            display_name="Dummy Output Directory",
            info="Optional folder for test JSON dumps",
            value="/tmp/claude_runs"
        ),
    ]

    outputs = [
        Output(display_name="Processed Pages", name="processed_pages", method="process_pages"),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialize services
        self.variety_tracker = VarietyTracker()
        self.session_logger = SessionLogger()
        self.status = "ClaudeProcessor initialized"

    # ==================== LANGFLOW ENTRY POINT ====================

    def process_pages(self) -> List[Data]:
        """Main entry point - delegates to ProcessingPipeline.

        This is now a thin orchestrator that:
        1. Builds configuration from Langflow inputs
        2. Constructs the processing pipeline with dependencies
        3. Runs the pipeline
        4. Saves logs and returns results

        All business logic is in the ProcessingPipeline and supporting modules.
        """
        # Reset state
        self.variety_tracker.reset()
        self.session_logger.clear()

        # Apply random seed if provided
        self._apply_random_seed()

        # Build configuration
        pipeline_config = self._build_pipeline_config()

        # Build and run pipeline
        pipeline = self._build_pipeline(pipeline_config)

        try:
            result = pipeline.run(self.pages)
        except ValueError as e:
            # Input validation errors
            self.session_logger.log(f"ERROR: {e}")
            self.save_detailed_logs()
            return []

        # Save logs
        self.save_detailed_logs()

        # Dump output if configured
        self._dump_output(result.processed_pages)

        # Update status
        self.status = f"Completed {result.total_processed} pages in {result.duration_seconds:.2f}s"

        return result.to_langflow_data()

    # ==================== CONFIGURATION BUILDERS ====================

    def _apply_random_seed(self) -> None:
        """Apply random seed if configured."""
        try:
            seed_raw = str(getattr(self, "random_seed", "")).strip()
            if seed_raw:
                random.seed(int(seed_raw))
                self.session_logger.log(f"Random seed set to {seed_raw}")
        except Exception:
            self.session_logger.log("Random seed not applied (non-integer)")

    def _build_pipeline_config(self) -> PipelineConfig:
        """Build pipeline configuration from Langflow inputs."""
        return PipelineConfig(
            output_dir=self._dummy_output_directory(),
            random_seed=self._parse_random_seed(),
            variety_summary=None,  # Will be populated after processing
        )

    def _build_processor_config(self) -> ProcessorConfig:
        """Build processor configuration."""
        return ProcessorConfig(
            difficulty=self._difficulty(),
            model=getattr(self, 'model_name', 'claude-3-5-sonnet') or 'claude-3-5-sonnet',
            api_key=self.anthropic_api_key,
            retry_attempts=2
        )

    def _build_limiter_config(self) -> LimiterConfig:
        """Build limiter configuration."""
        return LimiterConfig(
            max_total=self._max_total_pages(),
            per_topic_limits=self._pages_per_topic()
        )

    def _build_pipeline(self, pipeline_config: PipelineConfig) -> ProcessingPipeline:
        """Build processing pipeline with all dependencies.

        This method constructs the complete dependency graph:
        - LoggerFacade (wraps SessionLogger)
        - PageLimiter (enforces limits)
        - PageProcessor (processes individual pages)
          - ClaudeAPIClient
          - RetryHandler
          - VarietyTracker
        - ProcessingPipeline (orchestrates everything)
        """
        # Create logger facade
        logger = LoggerFacade(self.session_logger, cli_enabled=True)

        # Create limiter
        limiter_config = self._build_limiter_config()
        limiter = PageLimiter(limiter_config)

        # Create API client and retry handler
        processor_config = self._build_processor_config()
        api_client = ClaudeAPIClient(
            api_key=processor_config.api_key,
            model=processor_config.model,
            max_tokens=768
        )
        retry_handler = RetryHandler(base_delay=0.4)

        # Create page processor
        page_processor = PageProcessor(
            config=processor_config,
            api_client=api_client,
            retry_handler=retry_handler,
            variety_tracker=self.variety_tracker,
            logger=logger
        )

        # Create pipeline
        pipeline = ProcessingPipeline(
            page_processor=page_processor,
            limiter=limiter,
            logger=logger,
            config=pipeline_config
        )

        # Update pipeline config with variety summary reference
        pipeline.config.variety_summary = self.variety_tracker.get_summary()

        return pipeline

    # ==================== HELPER METHODS ====================

    def _difficulty(self) -> str:
        """Get normalized difficulty level."""
        raw_difficulty = getattr(self, "difficulty", "easy")
        return DifficultyConfig.normalize(raw_difficulty)

    def _parse_random_seed(self) -> Optional[int]:
        """Parse random seed from input."""
        try:
            seed_raw = str(getattr(self, "random_seed", "")).strip()
            if seed_raw:
                return int(seed_raw)
        except Exception:
            pass
        return None

    def _max_total_pages(self) -> Optional[int]:
        """Get maximum total pages limit."""
        raw_value = getattr(self, "max_total_pages", None)
        return PageLimitsConfig.parse_max_total(raw_value)

    def _pages_per_topic(self) -> dict:
        """Get per-topic page limits."""
        raw = getattr(self, "pages_per_topic", None)
        try:
            return PageLimitsConfig.parse_pages_per_topic(raw)
        except Exception as exc:
            self.session_logger.log(f"Could not parse pages_per_topic: {exc}")
            return {}

    def _dummy_output_directory(self) -> Optional[Path]:
        """Get dummy output directory path."""
        dump_dir = (getattr(self, "dummy_output_dir", "") or "").strip()
        if not dump_dir:
            return None

        base_path = Path(dump_dir).expanduser()
        if not base_path.is_absolute():
            base_path = Path.cwd() / base_path

        try:
            base_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            self.session_logger.log(f"Failed to create output directory: {exc}")
            return None

        return base_path

    def _dump_output(self, processed_pages: List[Data]) -> None:
        """Dump processed output to JSON file."""
        directory = self._dummy_output_directory()
        if directory is None:
            return

        metadata = {
            "model": getattr(self, "model_name", ""),
            "difficulty": self._difficulty()
        }

        file_path = OutputDumper.dump(
            processed_pages=[item.data for item in processed_pages],
            logs=self.session_logger.get_detailed_logs(),
            output_dir=directory,
            metadata=metadata
        )

        if file_path:
            self.session_logger.log(f"Saved output to {file_path}")

    def save_detailed_logs(self) -> Optional[str]:
        """Save detailed logs to file."""
        variety_summary = self.variety_tracker.get_summary()
        filename = self.session_logger.save(variety_summary=variety_summary)
        if filename:
            self.session_logger.log(f"✅ Detailed logs saved to: {filename}")
        return filename

    # Backward compatibility methods (kept for legacy code)
    def log(self, message: str):
        """Legacy logging method - delegates to session_logger."""
        self.session_logger.log(message)
