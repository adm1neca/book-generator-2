"""Page Processor Module

Handles single page processing with clean dependency injection.

This module encapsulates all the logic for processing a single page through
the Claude API pipeline, including prompt building, API calls, variety tracking,
and result merging.

Example:
    >>> from components.processor import PageProcessor, ProcessorConfig
    >>> from components.api import ClaudeAPIClient, RetryHandler
    >>> from components.prompts import PromptBuilderFactory
    >>> from components.tracking import VarietyTracker
    >>> from components.processor import LoggerFacade
    >>>
    >>> config = ProcessorConfig(
    ...     difficulty="easy",
    ...     model="claude-3-5-sonnet",
    ...     api_key="...",
    ...     retry_attempts=2
    ... )
    >>>
    >>> processor = PageProcessor(
    ...     config=config,
    ...     api_client=api_client,
    ...     retry_handler=retry_handler,
    ...     variety_tracker=variety_tracker,
    ...     logger=logger
    ... )
    >>>
    >>> page = {"type": "coloring", "theme": "animals", "pageNumber": 1}
    >>> result = processor.process(page)
    >>> if result.success:
    ...     print(f"Page processed: {result.page_data}")
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple

from components.api import ClaudeAPIClient, RetryHandler
from components.tracking import VarietyTracker
from components.prompts import PromptBuilderFactory
from components.config import ThemeConfig
from .logger_facade import LoggerFacade


@dataclass
class ProcessorConfig:
    """Configuration for PageProcessor.

    Attributes:
        difficulty: Difficulty level (easy, medium, hard)
        model: Claude model name
        api_key: Anthropic API key
        retry_attempts: Number of retry attempts for API calls

    Example:
        >>> config = ProcessorConfig(
        ...     difficulty="easy",
        ...     model="claude-haiku-4-5-20251001",
        ...     api_key="sk-...",
        ...     retry_attempts=2
        ... )
    """

    difficulty: str
    model: str
    api_key: str
    retry_attempts: int = 2


@dataclass
class ProcessedPage:
    """Result of processing a single page.

    Attributes:
        success: Whether processing succeeded
        page_data: The processed page data (merged with API response)
        error: Error message if processing failed
        selected_item: Selected variety item (for tracking)

    Example:
        >>> result = ProcessedPage(
        ...     success=True,
        ...     page_data={"pageNumber": 1, "type": "coloring", ...},
        ...     error=None,
        ...     selected_item="elephant"
        ... )
    """

    success: bool
    page_data: Dict[str, Any]
    error: Optional[str] = None
    selected_item: Optional[str] = None


class PageProcessor:
    """Processes a single page through the Claude API pipeline.

    Encapsulates all logic for processing one page: prompt building,
    API calls with retry, variety tracking, and result merging.

    All dependencies are injected via constructor for testability.

    Attributes:
        config: Processor configuration
        api_client: Claude API client
        retry_handler: Retry logic handler
        variety_tracker: Variety tracking state
        logger: Logging facade

    Design Pattern:
        - Dependency Injection: All dependencies via constructor
        - Single Responsibility: Only processes single pages
        - Template Method: process() orchestrates the steps

    Example:
        >>> processor = PageProcessor(
        ...     config=config,
        ...     api_client=api_client,
        ...     retry_handler=retry_handler,
        ...     variety_tracker=variety_tracker,
        ...     logger=logger
        ... )
        >>>
        >>> page = {"type": "coloring", "theme": "animals", "pageNumber": 1}
        >>> result = processor.process(page)
        >>> assert result.success
    """

    def __init__(
        self,
        config: ProcessorConfig,
        api_client: ClaudeAPIClient,
        retry_handler: RetryHandler,
        variety_tracker: VarietyTracker,
        logger: LoggerFacade,
    ):
        """Initialize the page processor.

        Args:
            config: Processor configuration
            api_client: Claude API client instance
            retry_handler: Retry handler instance
            variety_tracker: Variety tracker instance
            logger: Logger facade instance
        """
        self.config = config
        self.api_client = api_client
        self.retry_handler = retry_handler
        self.variety_tracker = variety_tracker
        self.logger = logger

    def process(self, page: Dict[str, Any]) -> ProcessedPage:
        """Process a single page through the pipeline.

        Orchestrates the complete processing flow:
        1. Extract page information
        2. Build prompt using strategy
        3. Call API with retry
        4. Track variety
        5. Merge results

        Args:
            page: Page data dict with type, theme, pageNumber

        Returns:
            ProcessedPage with success status and data

        Example:
            >>> page = {"type": "coloring", "theme": "animals", "pageNumber": 1}
            >>> result = processor.process(page)
            >>> if result.success:
            ...     print("Success!")
            ... else:
            ...     print(f"Error: {result.error}")
        """
        page_type = page.get("type", "")
        theme = page.get("theme", "")
        page_number = page.get("pageNumber", 0)

        try:
            # Build prompt using strategy
            prompt, selected_item = self._build_prompt(page_type, theme, page_number)

            if not prompt:
                return ProcessedPage(
                    success=False,
                    page_data=page,
                    error=f"Unknown page type: {page_type}",
                )

            # Call API with retry
            parsed, raw = self._call_api(prompt, page_number)

            if parsed:
                # Track variety
                if selected_item:
                    self.variety_tracker.mark_used(page_type, selected_item)
                    self.logger.debug(
                        f"Page {page_number}: {page_type} - {selected_item}"
                    )

                # Merge results
                merged = self._merge_result(page, parsed, theme)

                return ProcessedPage(
                    success=True,
                    page_data=merged,
                    selected_item=selected_item,
                )
            else:
                # No JSON found after retries
                return ProcessedPage(
                    success=False,
                    page_data={
                        **page,
                        "error": "No JSON found",
                        "raw_response": (raw or "")[:400],
                    },
                    error="No JSON found in API response",
                )

        except Exception as e:
            # Catch-all error handler
            self.logger.error(f"Error processing page {page_number}: {e}")
            return ProcessedPage(
                success=False, page_data={**page, "error": str(e)}, error=str(e)
            )

    def _build_prompt(
        self, page_type: str, theme: str, page_number: int
    ) -> Tuple[str, Optional[str]]:
        """Build prompt using appropriate strategy.

        Args:
            page_type: Type of page (coloring, maze, etc.)
            theme: Theme for the page
            page_number: Page number for logging

        Returns:
            Tuple of (prompt, selected_item) or ("", None) if unknown type
        """
        # Sanitize theme
        theme = ThemeConfig.sanitize(theme)

        # Style guard common to all page types
        style_guard = f"""
GLOBAL STYLE REQUIREMENTS:
- Target age: 2–3 years old
- Illustration style: thick black outlines, simple cute shapes, no shading
- Lots of white space; minimal clutter
- Friendly 1-sentence instructions
- Difficulty: {self.config.difficulty}
- No copyrighted characters or brands
- Keep the theme consistent across pages: '{theme}'
"""

        # Get appropriate strategy from factory
        try:
            strategy = PromptBuilderFactory.get_builder(page_type)
        except ValueError:
            # Unknown page type
            self.logger.warning(f"Unknown page type: {page_type}")
            return "", None

        # Get used items for variety
        used_items = self.variety_tracker.get_used(page_type)

        # Build prompt using strategy
        prompt, selected_item = strategy.build(
            theme=theme,
            difficulty=self.config.difficulty,
            page_number=page_number,
            used_items=used_items,
            style_guard=style_guard,
        )

        return prompt, selected_item

    def _call_api(self, prompt: str, page_number: int) -> Tuple[Optional[dict], str]:
        """Call Claude API with retry logic.

        Args:
            prompt: The prompt to send
            page_number: Page number for logging

        Returns:
            Tuple of (parsed_json, raw_response)
        """
        # Make API call with retry
        api_call = lambda: self.api_client.send_message(prompt, page_number=page_number)
        parsed, raw = self.retry_handler.call_with_retry(
            api_call, retries=self.config.retry_attempts
        )

        return parsed, raw

    def _merge_result(
        self, original_page: Dict[str, Any], parsed: Dict[str, Any], theme: str
    ) -> Dict[str, Any]:
        """Merge original page data with API response.

        Args:
            original_page: Original page data
            parsed: Parsed API response
            theme: Sanitized theme

        Returns:
            Merged page data dictionary
        """
        return {
            "pageNumber": original_page.get("pageNumber", 0),
            "type": original_page.get("type", ""),
            "theme": ThemeConfig.sanitize(theme),
            **parsed,
        }
