# Claude Processor Refactoring Plan - Phase 6

## Executive Summary

The `ClaudeProcessor` component is currently a 570-line orchestrator that blends multiple concerns:
- Configuration parsing and validation
- Retry logic and API communication
- Prompt dispatch
- Logging (both CLI and structured)
- Limit enforcement (total pages, per-topic)
- Pipeline orchestration
- Langflow component plumbing

**Goal**: Break this into thin, focused services that are independently testable while keeping the Langflow component as a minimal adapter.

---

## Current State Analysis

### Responsibilities in `claude_processor.py`

| Responsibility | Lines | Methods | Dependencies |
|---|---|---|---|
| **Langflow Component Setup** | ~150 | `__init__`, inputs, outputs | Langflow SDK |
| **Configuration Parsing** | ~100 | `_sanitize_theme`, `_difficulty`, `_max_total_pages`, `_pages_per_topic`, `_dummy_output_directory` | config modules |
| **API Communication** | ~40 | `_call_with_retry` | ClaudeAPIClient, RetryHandler |
| **Prompt Dispatch** | ~60 | `get_prompt_for_type` | PromptBuilderFactory, VarietyTracker |
| **Pipeline Orchestration** | ~200 | `process_pages` (massive method) | All of the above |
| **Logging** | Scattered | `self.log()`, `print()` everywhere | SessionLogger |

### Problems

1. **Testing Difficulty**: Can't test pipeline logic without Langflow SDK
2. **Mixed Concerns**: CLI output, business logic, and API calls intertwined
3. **Low Cohesion**: process_pages() does too much (5 phases in one method)
4. **Scattered Logic**: Limit enforcement logic spread across 100+ lines in process_pages
5. **Hard to Mock**: Direct coupling to logging and API makes unit testing hard

---

## Proposed Architecture

### New Module Structure

```
components/
├── claude_processor.py          # Thin Langflow adapter (~150 lines)
├── processor/                   # New: Core processing services
│   ├── __init__.py
│   ├── pipeline.py              # Orchestration flow
│   ├── page_processor.py        # Single page processing
│   ├── limiter.py               # Limit enforcement
│   └── logger_facade.py         # Unified logging interface
├── api/                         # Existing: API client
├── config/                      # Existing: Configuration
├── prompts/                     # Existing: Prompt strategies
├── tracking/                    # Existing: Variety tracking
└── logging/                     # Existing: Session logging
```

---

## Detailed Design

### 1. LoggerFacade (`processor/logger_facade.py`)

**Purpose**: Unified interface for all logging (CLI + structured)

**Responsibilities**:
- Provide consistent logging API
- Route to both console and SessionLogger
- Support progress indicators
- Handle log formatting

**Interface**:
```python
class LoggerFacade:
    def __init__(self, session_logger: SessionLogger, cli_enabled: bool = True):
        self.session = session_logger
        self.cli_enabled = cli_enabled

    def info(self, message: str, show_cli: bool = True) -> None:
        """Log info message to both session and CLI"""

    def error(self, message: str, show_cli: bool = True) -> None:
        """Log error message"""

    def progress(self, current: int, total: int, message: str) -> None:
        """Show progress indicator"""

    def section_header(self, title: str, char: str = "=") -> None:
        """Print formatted section header"""

    def summary(self, stats: Dict[str, Any]) -> None:
        """Print final summary"""
```

**Benefits**:
- Single place for all logging logic
- Easy to disable CLI output for tests
- Consistent formatting
- Can swap implementations (e.g., JSON logging)

---

### 2. PageLimiter (`processor/limiter.py`)

**Purpose**: Enforce total and per-topic page limits

**Responsibilities**:
- Track pages processed (total + per-topic)
- Check if next page should be processed
- Provide skip reasons
- Generate limit summary

**Interface**:
```python
class PageLimiter:
    def __init__(self,
                 max_total: Optional[int] = None,
                 per_topic_limits: Dict[str, int] = None):
        self.max_total = max_total
        self.per_topic_limits = per_topic_limits or {}
        self.total_processed = 0
        self.per_topic_counts: Dict[str, int] = {}
        self.skipped: List[str] = []

    def should_process(self, page_type: str) -> Tuple[bool, Optional[str]]:
        """Check if page should be processed.

        Returns:
            (should_process, skip_reason)
        """

    def mark_processed(self, page_type: str) -> None:
        """Mark a page as processed"""

    def get_summary(self) -> Dict[str, Any]:
        """Get statistics summary"""

    def get_skipped_messages(self) -> List[str]:
        """Get all skip messages"""
```

**Benefits**:
- Single responsibility
- Easy to test independently
- Clear state management
- Reusable across different contexts

---

### 3. PageProcessor (`processor/page_processor.py`)

**Purpose**: Process a single page through the pipeline

**Responsibilities**:
- Build prompt for page
- Call API with retry
- Parse response
- Track variety
- Merge results

**Interface**:
```python
class PageProcessor:
    def __init__(self,
                 api_client: ClaudeAPIClient,
                 retry_handler: RetryHandler,
                 prompt_factory: PromptBuilderFactory,
                 variety_tracker: VarietyTracker,
                 config: ProcessorConfig):
        self.api_client = api_client
        self.retry_handler = retry_handler
        self.prompt_factory = prompt_factory
        self.variety_tracker = variety_tracker
        self.config = config

    def process(self, page: Dict[str, Any]) -> ProcessedPage:
        """Process a single page.

        Returns:
            ProcessedPage with result or error
        """

    def _build_prompt(self, page_type: str, theme: str, page_num: int) -> Tuple[str, Optional[str]]:
        """Build prompt using strategy"""

    def _call_api(self, prompt: str, page_num: int) -> Tuple[Optional[dict], str]:
        """Call Claude API with retry"""
```

**Benefits**:
- Testable without Langflow
- Dependency injection for all dependencies
- Clean single-page processing
- Easy to mock for tests

---

### 4. ProcessingPipeline (`processor/pipeline.py`)

**Purpose**: Orchestrate the full processing flow

**Responsibilities**:
- Initialize subsystems
- Validate input
- Loop through pages
- Coordinate limiter, processor, logger
- Generate final summary

**Interface**:
```python
class ProcessingPipeline:
    def __init__(self,
                 processor: PageProcessor,
                 limiter: PageLimiter,
                 logger: LoggerFacade,
                 config: PipelineConfig):
        self.processor = processor
        self.limiter = limiter
        self.logger = logger
        self.config = config

    def run(self, pages: List[Data]) -> PipelineResult:
        """Execute the full processing pipeline.

        Returns:
            PipelineResult with processed pages and metadata
        """

    def _validate_input(self, pages: List[Data]) -> bool:
        """Validate input pages"""

    def _process_page(self, page: Data, idx: int, total: int) -> Optional[Data]:
        """Process single page with limit checks"""

    def _finalize(self, processed: List[Data]) -> PipelineResult:
        """Generate final result with metadata"""
```

**Benefits**:
- Clear orchestration flow
- Each phase is a method
- Easy to add pre/post hooks
- Testable without API calls

---

### 5. Thin Langflow Component (`claude_processor.py`)

**Purpose**: Minimal adapter between Langflow and business logic

**Responsibilities**:
- Define Langflow inputs/outputs
- Parse Langflow inputs → config objects
- Instantiate pipeline with dependencies
- Convert PipelineResult → Langflow Data

**New Structure** (~150 lines):
```python
class ClaudeProcessor(Component):
    """Thin Langflow adapter for Claude processing pipeline."""

    # Langflow metadata (inputs, outputs, display_name, etc.)

    def __init__(self):
        super().__init__()
        # Minimal initialization

    def process_pages(self) -> List[Data]:
        """Langflow entry point - delegates to pipeline."""

        # 1. Parse Langflow inputs → config objects
        config = self._build_config()

        # 2. Instantiate dependencies
        pipeline = self._build_pipeline(config)

        # 3. Run pipeline
        result = pipeline.run(self.pages)

        # 4. Convert result to Langflow format
        return result.to_langflow_data()

    def _build_config(self) -> PipelineConfig:
        """Parse Langflow inputs into config objects"""

    def _build_pipeline(self, config: PipelineConfig) -> ProcessingPipeline:
        """Instantiate pipeline with all dependencies"""
```

**Benefits**:
- Langflow concerns isolated
- Business logic 100% testable without Langflow
- Clear dependency construction
- Easy to swap implementations

---

## Migration Strategy

### Phase 1: Create New Modules (No Breaking Changes)

1. Create `components/processor/` directory
2. Implement `logger_facade.py` with tests
3. Implement `limiter.py` with tests
4. Implement `page_processor.py` with tests
5. Implement `pipeline.py` with tests

**Validation**: All tests pass, existing code unchanged

### Phase 2: Refactor Component (Maintain Interface)

1. Update `claude_processor.py` to use new pipeline
2. Keep same Langflow interface (inputs/outputs)
3. Delegate all logic to pipeline
4. Remove old methods

**Validation**: Integration tests pass, same Langflow behavior

### Phase 3: Clean Up (Safe)

1. Remove unused utility methods
2. Update documentation
3. Add migration guide

---

## Testing Strategy

### Unit Tests

Each new module gets comprehensive unit tests:

```
components/processor/tests/
├── test_logger_facade.py      # Mock SessionLogger, verify CLI output
├── test_limiter.py            # Test all limit scenarios
├── test_page_processor.py     # Mock API client, verify processing
└── test_pipeline.py           # Mock all dependencies, verify flow
```

**Coverage Target**: 95%+ for new modules

### Integration Tests

```
components/tests/integration/
└── test_full_pipeline.py      # End-to-end with real config, mock API
```

### Langflow Component Tests

```
components/tests/langflow/
└── test_claude_processor.py   # Test Langflow adapter only
```

---

## Metrics

### Before Refactoring
- `claude_processor.py`: 570 lines, 15 methods
- `process_pages()`: 200 lines (too complex)
- Unit test coverage: ~40% (hard to test)
- Langflow-coupled logic: ~80%

### After Refactoring
- `claude_processor.py`: ~150 lines, 5 methods
- `ProcessingPipeline.run()`: ~60 lines (readable)
- Unit test coverage: 95%+ (all testable)
- Langflow-coupled logic: ~20% (thin adapter)

---

## File Changes Summary

### New Files (5)
```
components/processor/__init__.py
components/processor/logger_facade.py      (~100 lines)
components/processor/limiter.py            (~120 lines)
components/processor/page_processor.py     (~150 lines)
components/processor/pipeline.py           (~200 lines)
```

### Modified Files (1)
```
components/claude_processor.py             (570 → 150 lines)
```

### New Test Files (4)
```
components/processor/tests/test_logger_facade.py
components/processor/tests/test_limiter.py
components/processor/tests/test_page_processor.py
components/processor/tests/test_pipeline.py
```

---

## Benefits Summary

### 1. Testability
- ✅ All business logic testable without Langflow SDK
- ✅ Easy to mock dependencies (dependency injection)
- ✅ Can test each concern independently
- ✅ Fast unit tests (no API calls, no Langflow)

### 2. Maintainability
- ✅ Single Responsibility Principle
- ✅ Clear module boundaries
- ✅ Easy to understand flow
- ✅ Self-documenting code structure

### 3. Extensibility
- ✅ Easy to add new features (e.g., rate limiting)
- ✅ Can swap implementations (e.g., different API clients)
- ✅ Plugin architecture possible
- ✅ Reusable components

### 4. Debugging
- ✅ Clear error propagation
- ✅ Easy to add logging at each layer
- ✅ Can run pipeline outside Langflow
- ✅ Better stack traces

### 5. Performance
- ✅ Can optimize each component independently
- ✅ Easy to add caching
- ✅ Can profile each service
- ✅ Parallel processing possible

---

## Next Steps

1. **Review this plan** - Get feedback on architecture
2. **Prototype LoggerFacade** - Validate logging approach
3. **Implement Phase 1** - Build new modules with tests
4. **Implement Phase 2** - Refactor component
5. **Implement Phase 3** - Clean up and document

---

## Questions to Consider

1. **Configuration**: Should we create a unified `ProcessorConfig` object?
2. **Error Handling**: Do we need a custom exception hierarchy?
3. **Async**: Should we design for async API calls from the start?
4. **Observability**: Do we need metrics/telemetry beyond logging?
5. **State**: Should variety tracker be stateful or passed around?

---

## Appendix: Code Examples

### Example: Before (Current State)

```python
def process_pages(self) -> List[Data]:
    """500-line monolith with everything mixed together"""
    processed = []
    # ... 50 lines of initialization
    # ... 100 lines of limit parsing
    # ... 200 lines of processing loop with embedded logic
    # ... 50 lines of finalization
    return processed
```

### Example: After (Proposed)

```python
def process_pages(self) -> List[Data]:
    """Thin adapter - delegates to pipeline"""
    config = self._build_config()
    pipeline = self._build_pipeline(config)
    result = pipeline.run(self.pages)
    return result.to_langflow_data()
```

### Example: Pipeline Run Method

```python
def run(self, pages: List[Data]) -> PipelineResult:
    """Clear, testable orchestration"""
    self._validate_input(pages)

    processed = []
    for idx, page_data in enumerate(pages):
        # Check limits
        should_process, reason = self.limiter.should_process(page_data.type)
        if not should_process:
            self.logger.info(reason, show_cli=True)
            continue

        # Process page
        result = self.processor.process(page_data)
        processed.append(result)

        # Track
        self.limiter.mark_processed(page_data.type)

    return self._finalize(processed)
```

---

## Conclusion

This refactoring will transform the Claude processor from a monolithic component into a clean, testable, maintainable system. The investment in separation of concerns will pay dividends in:

- **Faster development** (easier to add features)
- **Fewer bugs** (comprehensive unit tests)
- **Better onboarding** (clear architecture)
- **Production readiness** (observable, debuggable)

**Estimated Effort**: 2-3 days for full implementation + tests
**Risk**: Low (incremental approach, backward compatible)
**Impact**: High (2x testability, 3x maintainability)
