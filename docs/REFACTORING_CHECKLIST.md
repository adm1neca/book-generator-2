# Refactoring Implementation Checklist

## Phase 1: Create New Modules (No Breaking Changes)

### 1.1 Setup Directory Structure

- [ ] Create `components/processor/` directory
- [ ] Create `components/processor/__init__.py`
- [ ] Create `components/processor/tests/` directory
- [ ] Create `components/processor/tests/__init__.py`

### 1.2 Implement LoggerFacade

**File**: `components/processor/logger_facade.py`

- [ ] Create `LoggerFacade` class
  - [ ] `__init__(session_logger, cli_enabled=True)`
  - [ ] `info(message, show_cli=True)` - Info messages
  - [ ] `error(message, show_cli=True)` - Error messages
  - [ ] `warning(message, show_cli=True)` - Warning messages
  - [ ] `section_header(title, char="=", width=60)` - Section dividers
  - [ ] `progress(current, total, message)` - Progress indicators
  - [ ] `summary(stats)` - Final summary output
  - [ ] `_format_message(message)` - Internal formatter
  - [ ] `_print(message)` - Internal CLI printer

**Tests**: `components/processor/tests/test_logger_facade.py`

- [ ] Test info logging (both CLI and session)
- [ ] Test error logging
- [ ] Test warning logging
- [ ] Test section headers
- [ ] Test progress indicators
- [ ] Test summary output
- [ ] Test CLI disabled mode
- [ ] Test message formatting
- [ ] Mock SessionLogger and verify calls
- [ ] Test thread safety (if needed)

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] 95%+ code coverage
- [ ] Can disable CLI output
- [ ] Session logger receives all messages

---

### 1.3 Implement PageLimiter

**File**: `components/processor/limiter.py`

- [ ] Create `LimiterConfig` dataclass
  - [ ] `max_total: Optional[int]`
  - [ ] `per_topic_limits: Dict[str, int]`

- [ ] Create `PageLimiter` class
  - [ ] `__init__(config: LimiterConfig)`
  - [ ] `should_process(page_type: str) -> Tuple[bool, Optional[str]]`
  - [ ] `mark_processed(page_type: str) -> None`
  - [ ] `get_total_processed() -> int`
  - [ ] `get_topic_count(topic: str) -> int`
  - [ ] `get_summary() -> Dict[str, Any]`
  - [ ] `get_skipped_messages() -> List[str]`
  - [ ] `reset() -> None`
  - [ ] `_normalize_topic(topic: str) -> str` - Internal normalizer

**Tests**: `components/processor/tests/test_limiter.py`

- [ ] Test no limits (all pages allowed)
- [ ] Test max_total limit enforcement
- [ ] Test per_topic limit enforcement
- [ ] Test combined limits (total + per-topic)
- [ ] Test topic normalization (case insensitive)
- [ ] Test unknown topics
- [ ] Test mark_processed updates counters
- [ ] Test skip reason messages
- [ ] Test summary generation
- [ ] Test reset clears state
- [ ] Test edge cases (0 limit, negative limit)

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] 95%+ code coverage
- [ ] Thread-safe state management
- [ ] Clear skip reason messages

---

### 1.4 Implement PageProcessor

**File**: `components/processor/page_processor.py`

- [ ] Create `ProcessorConfig` dataclass
  - [ ] `theme: str`
  - [ ] `difficulty: str`
  - [ ] `model: str`
  - [ ] `api_key: str`
  - [ ] `retry_attempts: int`

- [ ] Create `ProcessedPage` dataclass
  - [ ] `success: bool`
  - [ ] `page_data: Dict[str, Any]`
  - [ ] `error: Optional[str]`
  - [ ] `selected_item: Optional[str]`

- [ ] Create `PageProcessor` class
  - [ ] `__init__(config, api_client, retry_handler, prompt_factory, variety_tracker, logger)`
  - [ ] `process(page: Dict) -> ProcessedPage`
  - [ ] `_build_prompt(page_type, theme, page_num) -> Tuple[str, Optional[str]]`
  - [ ] `_call_api(prompt, page_num) -> Tuple[Optional[dict], str]`
  - [ ] `_merge_result(page, parsed, selected_item) -> Dict`
  - [ ] `_handle_error(page, error) -> ProcessedPage`

**Tests**: `components/processor/tests/test_page_processor.py`

- [ ] Test successful page processing
- [ ] Test API call failure
- [ ] Test parse error handling
- [ ] Test variety tracking
- [ ] Test result merging
- [ ] Test error page creation
- [ ] Mock all dependencies (API client, retry handler, etc.)
- [ ] Test different page types
- [ ] Test selected_item tracking
- [ ] Test configuration propagation

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] 95%+ code coverage
- [ ] No Langflow dependencies
- [ ] Clean dependency injection

---

### 1.5 Implement ProcessingPipeline

**File**: `components/processor/pipeline.py`

- [ ] Create `PipelineConfig` dataclass
  - [ ] `processor_config: ProcessorConfig`
  - [ ] `limiter_config: LimiterConfig`
  - [ ] `output_dir: Optional[Path]`
  - [ ] `random_seed: Optional[int]`

- [ ] Create `PipelineResult` dataclass
  - [ ] `processed_pages: List[Data]`
  - [ ] `total_processed: int`
  - [ ] `total_skipped: int`
  - [ ] `duration_seconds: float`
  - [ ] `variety_summary: Dict[str, List[str]]`
  - [ ] `limit_summary: Dict[str, int]`
  - [ ] `to_langflow_data() -> List[Data]` - Converter method

- [ ] Create `ProcessingPipeline` class
  - [ ] `__init__(page_processor, limiter, logger, config)`
  - [ ] `run(pages: List[Data]) -> PipelineResult`
  - [ ] `_initialize() -> None`
  - [ ] `_validate_input(pages) -> None`
  - [ ] `_process_pages(pages) -> List[Data]`
  - [ ] `_process_single_page(page, idx, total) -> Optional[Data]`
  - [ ] `_finalize(processed) -> PipelineResult`
  - [ ] `_dump_output(processed) -> Optional[Path]`
  - [ ] `_generate_summary(processed, start_time) -> PipelineResult`

**Tests**: `components/processor/tests/test_pipeline.py`

- [ ] Test successful pipeline run
- [ ] Test empty input validation
- [ ] Test None input validation
- [ ] Test limit enforcement during processing
- [ ] Test partial success (some pages error)
- [ ] Test complete failure (all pages error)
- [ ] Test result sorting by page number
- [ ] Test summary generation
- [ ] Test output dumping
- [ ] Test random seed application
- [ ] Mock all dependencies
- [ ] Test pipeline phases independently

**Acceptance Criteria**:
- [ ] All tests pass
- [ ] 95%+ code coverage
- [ ] Clear orchestration flow
- [ ] No Langflow dependencies

---

### 1.6 Update Module Exports

**File**: `components/processor/__init__.py`

```python
from .logger_facade import LoggerFacade
from .limiter import PageLimiter, LimiterConfig
from .page_processor import PageProcessor, ProcessorConfig, ProcessedPage
from .pipeline import ProcessingPipeline, PipelineConfig, PipelineResult

__all__ = [
    'LoggerFacade',
    'PageLimiter',
    'LimiterConfig',
    'PageProcessor',
    'ProcessorConfig',
    'ProcessedPage',
    'ProcessingPipeline',
    'PipelineConfig',
    'PipelineResult',
]
```

- [ ] Create `__init__.py` with exports
- [ ] Verify imports work
- [ ] Add module docstring

---

## Phase 2: Refactor ClaudeProcessor

### 2.1 Create Helper Methods

**File**: `components/claude_processor.py`

- [ ] Add `_build_processor_config() -> ProcessorConfig`
  - [ ] Extract theme from inputs
  - [ ] Extract difficulty
  - [ ] Extract model name
  - [ ] Extract API key
  - [ ] Set retry attempts

- [ ] Add `_build_limiter_config() -> LimiterConfig`
  - [ ] Parse max_total_pages
  - [ ] Parse pages_per_topic
  - [ ] Create LimiterConfig

- [ ] Add `_build_pipeline_config() -> PipelineConfig`
  - [ ] Build processor config
  - [ ] Build limiter config
  - [ ] Extract output directory
  - [ ] Extract random seed
  - [ ] Create PipelineConfig

- [ ] Add `_build_pipeline(config: PipelineConfig) -> ProcessingPipeline`
  - [ ] Create LoggerFacade
  - [ ] Create API client
  - [ ] Create RetryHandler
  - [ ] Create PromptFactory
  - [ ] Create VarietyTracker
  - [ ] Create PageProcessor
  - [ ] Create PageLimiter
  - [ ] Create ProcessingPipeline
  - [ ] Return configured pipeline

### 2.2 Refactor process_pages()

**Before** (570 lines total, 200 in process_pages):
```python
def process_pages(self) -> List[Data]:
    # 50 lines initialization
    # 100 lines limit parsing
    # 200 lines processing loop
    # 50 lines finalization
    return processed
```

**After** (~20 lines):
```python
def process_pages(self) -> List[Data]:
    """Langflow entry point - delegates to pipeline."""
    # 1. Build configuration
    config = self._build_pipeline_config()

    # 2. Build pipeline with dependencies
    pipeline = self._build_pipeline(config)

    # 3. Run pipeline
    result = pipeline.run(self.pages)

    # 4. Convert to Langflow format
    return result.to_langflow_data()
```

- [ ] Refactor process_pages to use pipeline
- [ ] Remove old initialization code
- [ ] Remove old limit parsing code
- [ ] Remove old processing loop
- [ ] Remove old finalization code

### 2.3 Remove Deprecated Methods

**Methods to Remove**:
- [ ] Remove `_call_with_retry()` (moved to PageProcessor)
- [ ] Remove `get_prompt_for_type()` (moved to PageProcessor)
- [ ] Remove `_dump_processed_output()` (moved to Pipeline)
- [ ] Remove `save_detailed_logs()` (moved to Pipeline)

**Methods to Keep** (still used by config builders):
- [ ] Keep `_sanitize_theme()` (delegates to ThemeConfig)
- [ ] Keep `_difficulty()` (delegates to DifficultyConfig)
- [ ] Keep `_max_total_pages()` (used in _build_limiter_config)
- [ ] Keep `_pages_per_topic()` (used in _build_limiter_config)
- [ ] Keep `_dummy_output_directory()` (used in _build_pipeline_config)

### 2.4 Update Imports

- [ ] Add `from components.processor import *`
- [ ] Remove unused imports
- [ ] Organize imports by category

### 2.5 Update Documentation

- [ ] Update class docstring
- [ ] Update method docstrings
- [ ] Update architecture section
- [ ] Add migration notes

---

## Phase 3: Testing & Validation

### 3.1 Unit Tests

- [ ] Run all new unit tests
  ```bash
  pytest components/processor/tests/ -v --cov=components/processor
  ```
- [ ] Verify 95%+ coverage
- [ ] Fix any failing tests

### 3.2 Integration Tests

**File**: `components/tests/integration/test_pipeline_integration.py`

- [ ] Test full pipeline with mock API
- [ ] Test with real config objects
- [ ] Test all page types
- [ ] Test error scenarios
- [ ] Test limit enforcement end-to-end

**File**: `components/tests/integration/test_langflow_component.py`

- [ ] Test ClaudeProcessor with mock pipeline
- [ ] Test input parsing
- [ ] Test config building
- [ ] Test result conversion

### 3.3 Regression Tests

- [ ] Run existing Langflow component tests
- [ ] Verify same output format
- [ ] Verify same logging behavior
- [ ] Verify same error handling
- [ ] Test with real Claude API (manual)

---

## Phase 4: Documentation & Cleanup

### 4.1 Code Documentation

- [ ] Add docstrings to all new classes
- [ ] Add docstrings to all new methods
- [ ] Add type hints everywhere
- [ ] Add usage examples in docstrings

### 4.2 Architecture Documentation

- [ ] Update README.md
- [ ] Update architecture diagram
- [ ] Create migration guide
- [ ] Document breaking changes (if any)

### 4.3 Developer Guide

**File**: `docs/DEVELOPER_GUIDE.md`

- [ ] How to add a new processor service
- [ ] How to test the pipeline
- [ ] How to mock dependencies
- [ ] How to extend the limiter
- [ ] How to add new logging features

### 4.4 Code Cleanup

- [ ] Remove commented-out code
- [ ] Remove debug print statements
- [ ] Fix linting issues
- [ ] Format with Black/autopep8
- [ ] Run type checker (mypy)

---

## Phase 5: Performance & Optimization

### 5.1 Performance Testing

- [ ] Benchmark old vs new implementation
- [ ] Profile memory usage
- [ ] Profile execution time
- [ ] Identify bottlenecks

### 5.2 Optimization Opportunities

- [ ] Add caching to theme sanitization
- [ ] Add caching to prompt building
- [ ] Consider lazy initialization
- [ ] Consider batch API calls (future)
- [ ] Consider async/await (future)

---

## Final Checklist

### Code Quality

- [ ] All tests pass
- [ ] 95%+ code coverage
- [ ] No linting errors
- [ ] No type checker errors
- [ ] Code formatted

### Functionality

- [ ] Same output as before
- [ ] Same logging behavior
- [ ] Same error handling
- [ ] All features working
- [ ] No regressions

### Documentation

- [ ] All classes documented
- [ ] All methods documented
- [ ] Architecture docs updated
- [ ] Migration guide created
- [ ] README updated

### Deployment

- [ ] Create feature branch
- [ ] Commit changes with clear messages
- [ ] Push to remote
- [ ] Create pull request
- [ ] Request code review
- [ ] Merge to main

---

## Rollback Plan

If issues arise during refactoring:

1. **Partial Rollback**:
   - Keep new modules in `components/processor/`
   - Revert `claude_processor.py` to original
   - Mark new modules as experimental

2. **Full Rollback**:
   - Delete `components/processor/` directory
   - Revert all changes to `claude_processor.py`
   - Document issues for future retry

---

## Success Metrics

### Before Refactoring
- `claude_processor.py`: 570 lines
- `process_pages()`: 200 lines
- Unit test coverage: ~40%
- Testable without Langflow: No

### After Refactoring Targets
- `claude_processor.py`: <200 lines
- `ProcessingPipeline.run()`: <80 lines
- Unit test coverage: >95%
- Testable without Langflow: Yes

### Quality Metrics
- [ ] Cyclomatic complexity: <10 per method
- [ ] Max method length: <50 lines
- [ ] Max class length: <300 lines
- [ ] Test execution time: <5s (unit tests)

---

## Timeline Estimate

| Phase | Tasks | Estimated Time |
|-------|-------|----------------|
| Phase 1.1 | Setup | 15 min |
| Phase 1.2 | LoggerFacade | 2 hours |
| Phase 1.3 | PageLimiter | 3 hours |
| Phase 1.4 | PageProcessor | 4 hours |
| Phase 1.5 | ProcessingPipeline | 4 hours |
| Phase 1.6 | Module exports | 15 min |
| Phase 2 | Refactor component | 3 hours |
| Phase 3 | Testing | 4 hours |
| Phase 4 | Documentation | 2 hours |
| Phase 5 | Performance | 2 hours |
| **Total** | | **~24 hours** |

Suggested approach: **2-3 days** with testing breaks

---

## Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Breaking changes | Medium | High | Comprehensive integration tests |
| Performance regression | Low | Medium | Benchmark before/after |
| Langflow compatibility | Low | High | Test with real Langflow |
| Testing complexity | Medium | Low | Clear test fixtures |
| Merge conflicts | Low | Low | Frequent commits |

---

## Notes

- Keep commits small and focused
- Run tests after each module
- Don't refactor everything at once
- Document as you go
- Ask for help if stuck
