# Complete Refactoring Plan: Claude Processor Decomposition

## Executive Summary

**Objective:** Transform `claude_processor.py` from a 781-line monolith with 14 responsibilities into a clean, maintainable system of focused modules.

**Current State:**
- Single file: 781 lines
- 14 distinct responsibilities
- God Object anti-pattern
- Hard to test, modify, extend
- High coupling, low cohesion

**Target State:**
- Main orchestrator: ~200 lines
- 10+ focused modules (each <150 lines)
- Clear separation of concerns
- High test coverage (80%+)
- SOLID principles followed

**Total Reduction:** ~525 lines from main file
**Risk Level:** LOW to MEDIUM (by phase)
**Total Duration:** 2-3 weeks
**Rollback Strategy:** Git branches with incremental commits

---

## Phase Overview

| Phase | Focus | Lines Saved | Risk | Duration | Priority |
|-------|-------|-------------|------|----------|----------|
| Phase 1 | Configuration Management | ~130 | LOW | 2-3 hrs | HIGH |
| Phase 2 | Prompt Building Strategy | ~165 | MEDIUM | 4-6 hrs | HIGH |
| Phase 3 | API Client | ~100 | LOW | 2-3 hrs | MEDIUM |
| Phase 4 | Variety Tracking | ~50 | LOW | 1-2 hrs | LOW |
| Phase 5 | Logging System | ~80 | LOW | 2-3 hrs | MEDIUM |
| Phase 6 | Main Orchestrator Refactor | N/A | MEDIUM | 3-4 hrs | HIGH |
| **Total** | | **~525** | | **15-21 hrs** | |

---

## Phase 1: Extract Configuration Management

### Goal
Extract theme, difficulty, and limits configuration into separate modules.

### What Gets Extracted
- `_sanitize_theme()` → `ThemeConfig.sanitize()`
- `_difficulty()` → `DifficultyConfig.normalize()`
- `_max_total_pages()` → `PageLimitsConfig.parse_max_total()`
- `_pages_per_topic()` → `PageLimitsConfig.parse_pages_per_topic()`
- Theme mappings, blocked keywords → `constants.py`
- Validation utilities → `validation.py`

### New Structure
```
components/config/
  __init__.py
  constants.py          # Theme mappings, difficulty levels, subjects
  validation.py         # Input validation utilities
  theme_config.py       # ThemeConfig class
  difficulty_config.py  # DifficultyConfig class
  limits_config.py      # PageLimitsConfig class
  test_config.py        # Integration tests
  test_behavior.py      # Behavioral equivalence tests
  README.md             # Documentation
```

### Success Metrics
- ✅ 130 lines reduced from main file
- ✅ 6 new modules created
- ✅ 20+ unit tests (doctests)
- ✅ Zero functionality changes

### Risk Mitigation
- Pure data transformation (low risk)
- Extensive testing (doctests + integration)
- Easy rollback (git branch)

### Dependencies
- None (foundation phase)

### Output
- Clean config module ready for import
- All tests passing
- Git commit: `refactor/extract-config`

**Detailed Plan:** See `REFACTORING_PLAN_PHASE1.md`

---

## Phase 2: Extract Prompt Building Strategy

### Goal
Eliminate 165 lines of duplicated prompt-building logic using Strategy Pattern.

### What Gets Extracted
- `get_prompt_for_type()` → `PromptBuilderFactory`
- 6 page type prompts → Individual strategy classes
- Variety selection logic → Strategy methods

### New Structure
```
components/prompts/
  __init__.py
  base.py                    # Abstract PromptStrategy base class
  factory.py                 # PromptBuilderFactory
  coloring_prompt.py         # ColoringPromptStrategy
  tracing_prompt.py          # TracingPromptStrategy
  counting_prompt.py         # CountingPromptStrategy
  maze_prompt.py             # MazePromptStrategy
  matching_prompt.py         # MatchingPromptStrategy
  dot_to_dot_prompt.py       # DotToDotPromptStrategy
  test_prompts.py            # Unit tests
  README.md                  # Documentation
```

### Design Pattern: Strategy Pattern

**Base Strategy:**
```python
from abc import ABC, abstractmethod
from typing import List

class PromptStrategy(ABC):
    """Abstract base class for prompt generation strategies."""

    @abstractmethod
    def build(self, theme: str, difficulty: str, page_number: int,
              used_items: List[str]) -> str:
        """Build prompt for specific page type."""
        pass

    @abstractmethod
    def extract_used_item(self, response: dict) -> str:
        """Extract the item used from Claude's response."""
        pass
```

**Factory:**
```python
class PromptBuilderFactory:
    """Factory for creating prompt builders by page type."""

    _strategies = {
        'coloring': ColoringPromptStrategy,
        'tracing': TracingPromptStrategy,
        'counting': CountingPromptStrategy,
        'maze': MazePromptStrategy,
        'matching': MatchingPromptStrategy,
        'dot-to-dot': DotToDotPromptStrategy,
    }

    @classmethod
    def get_builder(cls, page_type: str) -> PromptStrategy:
        """Get appropriate prompt builder for page type."""
        strategy_class = cls._strategies.get(page_type)
        if not strategy_class:
            raise ValueError(f"Unknown page type: {page_type}")
        return strategy_class()
```

**Usage in claude_processor.py:**
```python
# Old way (165 lines):
prompt = self.get_prompt_for_type(page_type, theme, page_number)

# New way (3 lines):
builder = PromptBuilderFactory.get_builder(page_type)
prompt = builder.build(theme, self._difficulty(), page_number,
                       self.used_items.get(page_type, []))
```

### Success Metrics
- ✅ 165 lines reduced from main file
- ✅ 8 new prompt modules created
- ✅ Each strategy independently testable
- ✅ Easy to add new activity types

### Risk Mitigation
- Test each strategy independently
- Validate prompt output matches original
- Keep old method until new code proven
- Parallel testing (old vs new outputs)

### Dependencies
- Phase 1 must be complete (uses config modules)

### Output
- Flexible, extensible prompt system
- Clean Strategy Pattern implementation
- Git commit: `refactor/extract-prompts`

---

## Phase 3: Extract API Client

### Goal
Isolate Claude API communication for better testability and reusability.

### What Gets Extracted
- `call_claude()` → `ClaudeAPIClient.send_message()`
- `_extract_json()` → `ResponseParser.extract_json()`
- `_call_with_retry()` → `RetryHandler.call_with_retry()`
- Error handling logic → Client methods
- Token usage tracking → Client methods

### New Structure
```
components/api/
  __init__.py
  claude_client.py      # ClaudeAPIClient class
  response_parser.py    # ResponseParser class
  retry_handler.py      # RetryHandler class
  exceptions.py         # Custom exceptions
  test_api.py           # Unit tests (with mocks)
  README.md             # Documentation
```

### Design Pattern: Adapter Pattern

**Claude Client:**
```python
from anthropic import Anthropic
from typing import Optional, Callable

class ClaudeAPIClient:
    """Adapter for Claude API communication."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger: Optional[Callable] = None

    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        """Send message to Claude and return response."""
        if self.logger:
            self.logger(f"Sending to Claude (model: {self.model})")
            self.logger(f"Prompt: {prompt}")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        if self.logger:
            self.logger(f"Response: {response_text}")
            if hasattr(message, 'usage'):
                self.logger(f"Token usage: {message.usage}")

        return response_text
```

**Response Parser:**
```python
import re
import json
from typing import Optional

class ResponseParser:
    """Parse JSON from Claude responses."""

    @staticmethod
    def extract_json(text: str) -> Optional[dict]:
        """Extract and parse JSON from response text."""
        # Strip code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.replace("```", "")

        # Find JSON object
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            return None

        blob = match.group(0)

        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            # Try fixing common issues (trailing commas)
            blob = re.sub(r",\s*([}\]])", r"\1", blob)
            try:
                return json.loads(blob)
            except Exception:
                return None
```

**Retry Handler:**
```python
import time
from typing import Optional, Tuple, Callable

class RetryHandler:
    """Handle retries with exponential backoff."""

    @staticmethod
    def call_with_retry(
        func: Callable[[], str],
        parser: Callable[[str], Optional[dict]],
        retries: int = 2,
        base_delay: float = 0.4
    ) -> Tuple[Optional[dict], str]:
        """Call function with retry logic."""
        last_raw = ""

        for attempt in range(retries + 1):
            raw = func()
            parsed = parser(raw)

            if parsed is not None:
                return parsed, raw

            last_raw = raw

            if attempt < retries:
                time.sleep(base_delay * (attempt + 1))

        return None, last_raw
```

**Usage in claude_processor.py:**
```python
# Old way (80 lines):
raw = self.call_claude(prompt, self.anthropic_api_key, page_number)
parsed = self._extract_json(raw)

# New way (5 lines):
client = ClaudeAPIClient(self.anthropic_api_key, self.model_name)
client.logger = self.log
raw = client.send_message(prompt)
parsed = ResponseParser.extract_json(raw)
```

### Success Metrics
- ✅ 100 lines reduced from main file
- ✅ API client fully mockable for testing
- ✅ Easy to swap API providers
- ✅ Retry logic reusable

### Risk Mitigation
- Mock API calls in tests (no real API usage)
- Validate error handling preserved
- Test token usage tracking
- Ensure logging still works

### Dependencies
- None (can run parallel to Phase 2)

### Output
- Clean API adapter
- Testable with mocks
- Git commit: `refactor/extract-api-client`

---

## Phase 4: Extract Variety Tracking

### Goal
Isolate variety tracking state management.

### What Gets Extracted
- `self.used_items` state → `VarietyTracker` class
- Item selection logic from prompts → Tracker methods
- Reset logic → Tracker methods

### New Structure
```
components/tracking/
  __init__.py
  variety_tracker.py    # VarietyTracker class
  test_tracking.py      # Unit tests
  README.md             # Documentation
```

### Design Pattern: State Pattern

**Variety Tracker:**
```python
from typing import Dict, List
import random

class VarietyTracker:
    """Track and manage variety across activity pages."""

    def __init__(self):
        self._used_items: Dict[str, List[str]] = {
            'coloring': [],
            'tracing': [],
            'counting': [],
            'dot-to-dot': []
        }

    def select_unused(self, activity_type: str,
                      available: List[str]) -> str:
        """Select an unused item from available options."""
        used = self._used_items.get(activity_type, [])
        unused = [item for item in available if item not in used]

        # Reset if all used
        if not unused:
            self._used_items[activity_type] = []
            unused = available

        selected = random.choice(unused)
        self._used_items[activity_type].append(selected)

        return selected

    def mark_used(self, activity_type: str, item: str):
        """Mark an item as used."""
        if activity_type not in self._used_items:
            self._used_items[activity_type] = []
        self._used_items[activity_type].append(item)

    def get_used(self, activity_type: str) -> List[str]:
        """Get list of used items for activity type."""
        return self._used_items.get(activity_type, [])

    def reset(self, activity_type: str = None):
        """Reset tracking for activity type or all."""
        if activity_type:
            self._used_items[activity_type] = []
        else:
            for key in self._used_items:
                self._used_items[key] = []

    def get_summary(self) -> Dict[str, List[str]]:
        """Get summary of all used items."""
        return {k: v.copy() for k, v in self._used_items.items()}
```

**Usage in claude_processor.py:**
```python
# Old way (scattered across multiple methods):
used = self.used_items.get('coloring', [])
available = [s for s in subjects if s not in used]
if not available:
    self.used_items['coloring'] = []
    available = subjects
selected = random.choice(available)
self.used_items['coloring'].append(selected)

# New way (clean):
selected = self.variety_tracker.select_unused('coloring', subjects)
```

### Success Metrics
- ✅ 50 lines reduced from main file
- ✅ State management centralized
- ✅ Easy to add new tracking strategies
- ✅ Clear API for variety management

### Risk Mitigation
- Test selection logic thoroughly
- Validate reset behavior
- Ensure randomness preserved

### Dependencies
- Phase 2 (works with prompt strategies)

### Output
- Clean state management
- Git commit: `refactor/extract-tracking`

---

## Phase 5: Extract Logging System

### Goal
Create structured logging with better observability.

### What Gets Extracted
- `self.detailed_logs` → `SessionLogger`
- `save_detailed_logs()` → `SessionLogger.save()`
- `_dump_processed_output()` → `OutputDumper.dump()`
- `self.log()` wrapper → `SessionLogger.log()`

### New Structure
```
components/logging/
  __init__.py
  session_logger.py     # SessionLogger class
  output_dumper.py      # OutputDumper class
  formatters.py         # Log formatting utilities
  test_logging.py       # Unit tests
  README.md             # Documentation
```

### Design Pattern: Observer Pattern (simplified)

**Session Logger:**
```python
from datetime import datetime
from typing import List, Dict, Optional
from pathlib import Path

class SessionLogger:
    """Structured session logging for Claude processor."""

    def __init__(self):
        self.session_start = datetime.now()
        self.detailed_logs: List[Dict] = []
        self.messages: List[str] = []

    def log(self, message: str):
        """Log a message."""
        timestamp = datetime.now().isoformat()
        self.messages.append(f"[{timestamp}] {message}")
        print(message)

    def log_api_call(self, page_number: int, prompt: str,
                     response: str, usage: Optional[Dict] = None):
        """Log an API call with details."""
        self.detailed_logs.append({
            'timestamp': datetime.now().isoformat(),
            'page_number': page_number,
            'prompt': prompt,
            'response': response,
            'usage': usage
        })

    def save(self, filename: Optional[str] = None) -> str:
        """Save detailed logs to file."""
        if filename is None:
            timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
            filename = f"claude_logs_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            f.write("="*80 + "\n")
            f.write("CLAUDE ACTIVITY GENERATOR - DETAILED LOG\n")
            f.write("="*80 + "\n")
            f.write(f"Session Start: {self.session_start.isoformat()}\n")
            f.write(f"Total Pages: {len(self.detailed_logs)}\n")
            f.write("="*80 + "\n\n")

            for idx, log in enumerate(self.detailed_logs, 1):
                f.write(f"\n{'#'*80}\n")
                f.write(f"PAGE {log['page_number']} - Entry {idx}\n")
                f.write(f"Timestamp: {log['timestamp']}\n")
                f.write(f"{'#'*80}\n\n")
                f.write("PROMPT:\n")
                f.write("-"*80 + "\n")
                f.write(log['prompt'])
                f.write("\n" + "-"*80 + "\n\n")
                f.write("RESPONSE:\n")
                f.write("-"*80 + "\n")
                f.write(log['response'])
                f.write("\n" + "-"*80 + "\n\n")

        return filename

    def get_summary(self) -> Dict:
        """Get session summary."""
        duration = (datetime.now() - self.session_start).total_seconds()
        return {
            'session_start': self.session_start.isoformat(),
            'duration_seconds': duration,
            'total_api_calls': len(self.detailed_logs),
            'total_messages': len(self.messages)
        }
```

**Output Dumper:**
```python
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

class OutputDumper:
    """Dump processed output to JSON for testing."""

    @staticmethod
    def dump(processed_pages: List[Dict],
             logs: List[Dict],
             output_dir: Path,
             metadata: Optional[Dict] = None) -> Optional[Path]:
        """Dump processed output to JSON file."""
        try:
            output_dir.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"claude_run_{timestamp}.json"

            payload = {
                "meta": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "pages_count": len(processed_pages),
                    **(metadata or {})
                },
                "pages": processed_pages,
                "logs": logs
            }

            file_path = output_dir / filename
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            return file_path

        except Exception as exc:
            print(f"Failed to dump output: {exc}")
            return None
```

**Usage in claude_processor.py:**
```python
# Old way (100+ lines of logging code):
self.detailed_logs.append({...})
# Later...
self.save_detailed_logs()

# New way (clean):
self.logger = SessionLogger()
self.logger.log_api_call(page_number, prompt, response, usage)
# Later...
self.logger.save()
```

### Success Metrics
- ✅ 80 lines reduced from main file
- ✅ Structured logging
- ✅ Easy to add new output formats (JSON, CSV)
- ✅ Better observability

### Risk Mitigation
- Validate log format matches original
- Ensure all details captured
- Test file I/O errors

### Dependencies
- None (can run parallel to other phases)

### Output
- Flexible logging system
- Git commit: `refactor/extract-logging`

---

## Phase 6: Refactor Main Orchestrator

### Goal
Slim down main file to pure orchestration (~200 lines).

### What Remains in claude_processor.py
- Langflow Component integration
- Input/output definitions
- High-level orchestration
- Dependency coordination

### New Structure (Final)
```python
class ClaudeProcessor(Component):
    """Claude Activity Processor - Main Orchestrator."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize subsystems
        self.config = None  # Initialized in process_pages
        self.logger = None
        self.variety_tracker = None
        self.api_client = None

    def process_pages(self) -> List[Data]:
        """Main orchestration method."""
        # 1. Initialize subsystems
        self.logger = SessionLogger()
        self.variety_tracker = VarietyTracker()

        # 2. Parse configuration
        theme_config = ThemeConfig()
        difficulty = DifficultyConfig.normalize(
            getattr(self, "difficulty", "easy")
        )
        limits = PageLimitsConfig(
            max_total=PageLimitsConfig.parse_max_total(
                getattr(self, "max_total_pages", None)
            ),
            per_topic=PageLimitsConfig.parse_pages_per_topic(
                getattr(self, "pages_per_topic", None)
            )
        )

        # 3. Initialize API client
        self.api_client = ClaudeAPIClient(
            self.anthropic_api_key,
            getattr(self, 'model_name', 'claude-3-5-sonnet')
        )
        self.api_client.logger = self.logger.log

        # 4. Process pages
        processed = []
        for page_data_obj in self.pages:
            page = page_data_obj.data

            # Apply limits
            if self._should_skip_page(page, limits, processed):
                continue

            # Build prompt
            builder = PromptBuilderFactory.get_builder(page['type'])
            prompt = builder.build(
                theme_config.sanitize(page['theme']),
                difficulty,
                page['pageNumber'],
                self.variety_tracker.get_used(page['type'])
            )

            # Call API with retry
            response = RetryHandler.call_with_retry(
                lambda: self.api_client.send_message(prompt),
                ResponseParser.extract_json,
                retries=2
            )

            # Process response
            if response[0]:
                parsed = response[0]
                item = builder.extract_used_item(parsed)
                if item:
                    self.variety_tracker.mark_used(page['type'], item)

                processed.append(Data(data={
                    **page,
                    **parsed
                }))

        # 5. Finalize
        self.logger.save()
        return processed

    def _should_skip_page(self, page, limits, processed):
        """Check if page should be skipped based on limits."""
        # Limit checking logic
        pass
```

### Success Metrics
- ✅ Main file ~200 lines (74% reduction)
- ✅ Clear orchestration flow
- ✅ All subsystems integrated
- ✅ Easy to understand and modify

### Risk Mitigation
- Thorough integration testing
- Compare outputs with original
- Performance benchmarking
- User acceptance testing

### Dependencies
- ALL previous phases must be complete

### Output
- Clean, maintainable orchestrator
- Git commit: `refactor/main-orchestrator`
- Merge to main branch

---

## Execution Timeline

### Week 1: Foundation
**Days 1-2: Phase 1 - Configuration**
- Extract config modules
- Write tests
- Integrate and validate

**Days 3-4: Phase 3 - API Client**
- Extract API communication
- Mock tests
- Integrate

**Day 5: Testing & Review**
- Integration testing
- Code review
- Documentation

### Week 2: Core Logic
**Days 1-3: Phase 2 - Prompt Strategies**
- Implement Strategy pattern
- Create all 6 strategies
- Test thoroughly

**Day 4: Testing**
- Validate all prompts
- Regression testing

**Day 5: Phase 6 Part 1 - Start Refactoring**
- Begin orchestrator refactor
- Integrate config and API

### Week 3: Polish & Complete
**Days 1-2: Phase 4 & 5 - Tracking & Logging**
- Extract variety tracker
- Extract logging system
- Test both

**Days 3-4: Phase 6 Part 2 - Complete Orchestrator**
- Finish orchestrator refactor
- Full integration
- Comprehensive testing

**Day 5: Final Review & Merge**
- Performance testing
- Documentation
- Merge to main

---

## Testing Strategy

### Unit Tests
- Each extracted module has doctests
- Mocked dependencies
- Edge cases covered
- 80%+ coverage target

### Integration Tests
- Modules work together
- API contracts honored
- Config flows correctly

### Behavioral Tests
- Output matches original
- No regressions
- Same variety patterns

### End-to-End Tests
- Generate full PDFs
- Compare to baseline
- Performance benchmarks

### Regression Suite
- Run after each phase
- Automated checks
- Visual PDF comparison

---

## Risk Management

### High Risk Areas
1. **Prompt building** (Phase 2)
   - Most complex logic
   - Directly affects output
   - Mitigation: Extensive testing, parallel validation

2. **Main orchestrator** (Phase 6)
   - Integration point
   - Critical path
   - Mitigation: Incremental changes, continuous testing

### Medium Risk Areas
1. **API client** (Phase 3)
   - External dependency
   - Error handling critical
   - Mitigation: Mock testing, retry logic preservation

### Low Risk Areas
1. **Configuration** (Phase 1)
   - Pure data transformation
   - Easy to validate

2. **Tracking** (Phase 4)
   - Simple state management

3. **Logging** (Phase 5)
   - Non-critical path

### Mitigation Strategies
- Git branches for each phase
- Continuous testing
- Rollback procedures
- Feature flags for gradual rollout
- Parallel running (old vs new)

---

## Success Criteria

### Code Quality
- ✅ Main file: 781 → 200 lines (74% reduction)
- ✅ Each module < 150 lines
- ✅ No code duplication
- ✅ Clear naming conventions
- ✅ Comprehensive docstrings

### Architecture
- ✅ Single Responsibility Principle
- ✅ Open/Closed Principle
- ✅ Dependency Inversion
- ✅ Clear module boundaries
- ✅ Low coupling, high cohesion

### Testing
- ✅ 80%+ code coverage
- ✅ All edge cases covered
- ✅ Integration tests pass
- ✅ E2E tests pass
- ✅ Performance benchmarks met

### Functionality
- ✅ Identical output to original
- ✅ No performance regression
- ✅ All features preserved
- ✅ Error handling maintained

### Maintainability
- ✅ Easy to add new activity types
- ✅ Easy to modify prompts
- ✅ Easy to swap API providers
- ✅ Clear documentation
- ✅ New developers onboard quickly

---

## Rollback Procedures

### Per-Phase Rollback
```bash
# If Phase X fails
git checkout main
git branch -D refactor/phase-X
docker compose build
# Verify baseline still works
```

### Partial Rollback
```bash
# Keep some phases, revert others
git revert <commit-hash>  # Revert specific phase
git push origin main
```

### Emergency Rollback
```bash
# If production issues
git revert HEAD~N  # Revert last N commits
git push origin main --force
# Deploy previous version
```

---

## Monitoring & Validation

### During Development
- Run tests after each change
- Check imports continuously
- Monitor console for errors
- Review git diffs

### After Each Phase
- Run full test suite
- Generate sample PDF
- Compare to baseline
- Review code coverage
- Performance benchmark

### After Completion
- User acceptance testing
- Load testing
- Monitor production logs
- Collect feedback

---

## Documentation Updates

### Code Documentation
- Docstrings for all classes/functions
- Type hints throughout
- Clear parameter descriptions
- Usage examples

### Module Documentation
- README.md for each package
- Architecture diagrams
- Integration guides
- API references

### Project Documentation
- Update main README
- Add architecture overview
- Create developer guide
- Document design patterns used

---

## Future Enhancements

After refactoring is complete, these become easier:

### New Features
- Add new activity types (just create new strategy)
- Support multiple AI providers (swap client)
- Advanced tracking strategies (extend tracker)
- Export logs to different formats (extend logger)

### Performance Improvements
- Parallel API calls
- Request batching
- Response caching
- Async processing

### Quality Improvements
- Property-based testing
- Mutation testing
- Performance profiling
- Memory optimization

---

## AI Agent Instructions

### Execution Order
1. Start with Phase 1 (configuration)
2. After Phase 1 succeeds, ask user to proceed to Phase 2 or stop
3. Execute phases sequentially
4. Never skip validation steps
5. Commit after each successful phase

### When to Pause
- ❌ Any test fails
- ❌ Import errors occur
- ❌ Behavioral tests show differences
- ❌ Performance degrades >10%
- ❌ User requests pause

### When to Attempt Fix
- Try once if test fails
- Check imports first
- Verify file paths
- Review error messages
- If fix fails, report to user

### Progress Reporting
- Report start of each phase
- Report completion of major steps
- Report test results
- Report any issues immediately
- Summarize at end

---

## Appendix

### Pattern Reference

**Strategy Pattern** (Phase 2)
- Multiple algorithms (prompt builders)
- Same interface
- Interchangeable at runtime

**Adapter Pattern** (Phase 3)
- Wrap external API
- Provide clean interface
- Hide implementation details

**State Pattern** (Phase 4)
- Manage variety state
- Encapsulate behavior
- Easy to extend

**Observer Pattern** (Phase 5)
- Logging as side effect
- Decouple from main logic
- Multiple output formats

### Anti-Patterns Resolved

**God Object** → Multiple focused classes
**Long Method** → Small, single-purpose methods
**Primitive Obsession** → Value objects and config classes
**Data Clumps** → Configuration objects
**Duplicated Logic** → Strategy pattern
**Feature Envy** → Methods in right classes

---

## Contact & Support

**Questions During Execution:**
- Pause and ask user
- Document decision
- Update plan if needed

**Issues Encountered:**
- Document thoroughly
- Attempt fix once
- Report to user if unresolved

**Success Achieved:**
- Celebrate! 🎉
- Document learnings
- Plan next improvements

---

**Total Estimated Effort:** 15-21 hours (over 2-3 weeks)
**Risk Level:** LOW → MEDIUM → LOW
**Confidence Level:** HIGH (proven patterns, incremental approach)
**Reversibility:** HIGH (git branches, incremental commits)

**Ready to Execute:** Yes ✅
