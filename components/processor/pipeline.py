"""Processing Pipeline Module

Orchestrates the complete page processing workflow.

This module is the main orchestrator that coordinates all services
(PageProcessor, PageLimiter, LoggerFacade) to process a batch of pages.

Example:
    >>> from components.processor import ProcessingPipeline, PipelineConfig
    >>>
    >>> config = PipelineConfig(...)
    >>> pipeline = ProcessingPipeline(
    ...     page_processor=processor,
    ...     limiter=limiter,
    ...     logger=logger,
    ...     config=config
    ... )
    >>>
    >>> result = pipeline.run(pages)
    >>> print(f"Processed {result.total_processed} pages")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime
import time

# Import Data class (handle cases where langflow may not be available)
try:
    from langflow.schema import Data
except ImportError:
    # Mock Data class for testing environments
    class Data:
        """Mock Data class for environments without Langflow."""
        def __init__(self, data):
            self.data = data

from .page_processor import PageProcessor, ProcessedPage
from .limiter import PageLimiter
from .logger_facade import LoggerFacade


@dataclass
class PipelineConfig:
    """Configuration for ProcessingPipeline.

    Attributes:
        output_dir: Optional directory for output dumps
        random_seed: Optional random seed for reproducibility
        variety_summary: Optional pre-existing variety summary

    Example:
        >>> config = PipelineConfig(
        ...     output_dir=Path("/tmp/output"),
        ...     random_seed=42
        ... )
    """

    output_dir: Optional[Path] = None
    random_seed: Optional[int] = None
    variety_summary: Optional[Dict[str, List[str]]] = None


@dataclass
class PipelineResult:
    """Result of processing pipeline.

    Attributes:
        processed_pages: List of successfully processed pages
        total_processed: Total number of pages processed
        total_skipped: Total number of pages skipped
        duration_seconds: Processing duration in seconds
        variety_summary: Summary of variety items used
        limit_summary: Summary of limit enforcement
        error_pages: List of pages that had errors

    Example:
        >>> result = PipelineResult(
        ...     processed_pages=[...],
        ...     total_processed=20,
        ...     total_skipped=5,
        ...     duration_seconds=45.2,
        ...     variety_summary={...},
        ...     limit_summary={...},
        ...     error_pages=[]
        ... )
    """

    processed_pages: List[Data]
    total_processed: int
    total_skipped: int
    duration_seconds: float
    variety_summary: Dict[str, List[str]]
    limit_summary: Dict[str, Any]
    error_pages: List[Data] = field(default_factory=list)

    def to_langflow_data(self) -> List[Data]:
        """Convert result to Langflow Data format.

        Returns:
            List of Data objects for Langflow output
        """
        return self.processed_pages


class ProcessingPipeline:
    """Orchestrates the complete page processing workflow.

    The pipeline coordinates all services to process a batch of pages:
    - Validates input
    - Checks limits before processing
    - Processes each page
    - Tracks progress and variety
    - Generates final summary

    All dependencies are injected for testability.

    Attributes:
        page_processor: PageProcessor instance
        limiter: PageLimiter instance
        logger: LoggerFacade instance
        config: Pipeline configuration

    Design Pattern:
        - Orchestrator pattern: Coordinates multiple services
        - Template Method: run() defines the workflow
        - Dependency Injection: All services injected

    Example:
        >>> pipeline = ProcessingPipeline(
        ...     page_processor=processor,
        ...     limiter=limiter,
        ...     logger=logger,
        ...     config=config
        ... )
        >>>
        >>> pages = [Data(data={"type": "coloring", ...}), ...]
        >>> result = pipeline.run(pages)
        >>> print(f"Success! Processed {result.total_processed} pages")
    """

    def __init__(
        self,
        page_processor: PageProcessor,
        limiter: PageLimiter,
        logger: LoggerFacade,
        config: PipelineConfig,
    ):
        """Initialize the processing pipeline.

        Args:
            page_processor: PageProcessor instance
            limiter: PageLimiter instance
            logger: LoggerFacade instance
            config: Pipeline configuration
        """
        self.page_processor = page_processor
        self.limiter = limiter
        self.logger = logger
        self.config = config

    def run(self, pages: List[Data]) -> PipelineResult:
        """Execute the complete processing pipeline.

        Processing Flow:
        1. Initialize: Reset state, log start
        2. Validate: Check input is valid
        3. Process Loop: For each page:
           a. Check limits
           b. Process page
           c. Track results
        4. Finalize: Generate summary and return result

        Args:
            pages: List of Data objects with page configurations

        Returns:
            PipelineResult with all processed pages and metadata

        Raises:
            ValueError: If input is invalid (empty, None)

        Example:
            >>> pages = [
            ...     Data(data={"type": "coloring", "theme": "animals", "pageNumber": 1}),
            ...     Data(data={"type": "maze", "theme": "space", "pageNumber": 2}),
            ... ]
            >>> result = pipeline.run(pages)
            >>> assert result.total_processed == 2
        """
        start_time = time.time()

        # Phase 1: Initialize
        self._initialize()

        # Phase 2: Validate
        self._validate_input(pages)

        # Phase 3: Process
        processed = self._process_pages(pages)

        # Phase 4: Finalize
        result = self._finalize(processed, start_time)

        return result

    def _initialize(self) -> None:
        """Initialize pipeline state and logging."""
        self.logger.section_header("CLAUDE ACTIVITY PROCESSOR INITIALIZED")
        self.logger.info("Starting Claude Activity Generation...")

    def _validate_input(self, pages: List[Data]) -> None:
        """Validate input pages.

        Args:
            pages: Input pages to validate

        Raises:
            ValueError: If pages is None, empty, or invalid
        """
        if pages is None:
            self.logger.error("Pages is None!")
            raise ValueError("Pages input is None")

        if not pages:
            self.logger.warning("Received 0 pages to process!")
            raise ValueError("Pages input is empty")

        self.logger.info(f"Total pages to process: {len(pages)}")
        self.logger.info(f"Pages input type: {type(pages)}")

        if len(pages) > 0:
            preview = pages[0].data
            self.logger.debug(f"First page preview: {preview}")

    def _process_pages(self, pages: List[Data]) -> List[Data]:
        """Process all pages through the pipeline.

        Args:
            pages: List of pages to process

        Returns:
            List of processed Data objects
        """
        processed = []
        total = len(pages)

        for idx, page_data_obj in enumerate(pages):
            page = page_data_obj.data

            # Check if we should process this page
            result_data = self._process_single_page(page, idx, total)

            if result_data is not None:
                processed.append(result_data)

        # Sort by page number
        processed.sort(key=lambda x: x.data.get("pageNumber", 0))

        return processed

    def _process_single_page(
        self, page: Dict[str, Any], idx: int, total: int
    ) -> Optional[Data]:
        """Process a single page with limit checks.

        Args:
            page: Page data dictionary
            idx: Index in the pages list
            total: Total number of pages

        Returns:
            Data object with result, or None if skipped
        """
        page_type = page.get("type", "")
        theme = page.get("theme", "")
        page_number = page.get("pageNumber", 0)

        # Check limits
        should_process, skip_reason = self.limiter.should_process(page_type)

        if not should_process:
            self.logger.warning(f"Page {page_number}: {skip_reason}")
            self.limiter.track_skip(skip_reason)
            return None

        # Log progress
        self.logger.progress(idx + 1, total, f"{page_type} ({theme})")

        # Process the page
        result = self.page_processor.process(page)

        # Handle result
        if result.success:
            self.limiter.mark_processed(page_type)
            return Data(data=result.page_data)
        else:
            self.logger.error(
                f"Page {page_number}: Processing failed - {result.error}"
            )
            # Still return the error page (fail-safe)
            return Data(data=result.page_data)

    def _finalize(self, processed: List[Data], start_time: float) -> PipelineResult:
        """Generate final result and summary.

        Args:
            processed: List of processed pages
            start_time: Pipeline start time

        Returns:
            Complete PipelineResult
        """
        duration = time.time() - start_time

        # Get summaries
        limit_summary = self.limiter.get_summary()
        variety_summary = self.config.variety_summary or {}

        # Log final summary
        self.logger.section_header("GENERATION COMPLETE - SUMMARY")
        self.logger.info(f"Total pages generated: {len(processed)}")
        self.logger.info(f"Session duration: {duration:.2f} seconds")

        if limit_summary["per_topic_counts"]:
            self.logger.info("\nPages generated per topic/type:")
            for topic, count in sorted(limit_summary["per_topic_counts"].items()):
                self.logger.info(f"  {topic}: {count}")

        skipped_messages = self.limiter.get_skipped_messages()
        if skipped_messages:
            self.logger.info(f"\nSkipped {len(skipped_messages)} page(s) due to limits")

        if variety_summary:
            self.logger.info("\nVariety used per activity type:")
            for activity_type, items in variety_summary.items():
                if items:
                    self.logger.info(f"  {activity_type}: {', '.join(items)}")

        return PipelineResult(
            processed_pages=processed,
            total_processed=limit_summary["total_processed"],
            total_skipped=len(skipped_messages),
            duration_seconds=duration,
            variety_summary=variety_summary,
            limit_summary=limit_summary,
        )
