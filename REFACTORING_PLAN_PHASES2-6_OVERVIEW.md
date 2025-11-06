# Phases 2-6: Overview with Design Pattern Annotations

**Note:** This document provides architectural overview and design pattern rationale for Phases 2-6. Detailed step-by-step instructions will be created when you're ready to execute each phase.

---

## Phase 2: Extract Prompt Building Strategy (~165 lines saved)

### 🎯 Design Pattern: Strategy Pattern + Factory Pattern

**Problem:**
```python
def get_prompt_for_type(self, page_type, theme, page_num):
    if page_type == "coloring":
        # 20+ lines of coloring-specific logic
    elif page_type == "tracing":
        # 20+ lines of tracing-specific logic
    elif page_type == "counting":
        # 20+ lines of counting-specific logic
    # ... 6 activity types total = 165 lines
```

**Issues:**
- Violates Open/Closed Principle (must modify to add types)
- Long Method anti-pattern (165 lines)
- Code duplication (similar variety selection logic)
- Hard to test individual activity types
- High cyclomatic complexity

**Solution: Strategy Pattern**

Each activity type becomes a separate strategy class:

```python
from abc import ABC, abstractmethod

class PromptStrategy(ABC):
    """Base strategy for prompt generation."""

    @abstractmethod
    def build(self, theme: str, difficulty: str,
              page_number: int, used_items: List[str]) -> str:
        """Generate prompt for this activity type."""
        pass

    @abstractmethod
    def extract_used_item(self, response: dict) -> Optional[str]:
        """Extract item from Claude's response for variety tracking."""
        pass


class ColoringPromptStrategy(PromptStrategy):
    """Strategy for coloring page prompts."""

    def build(self, theme, difficulty, page_number, used_items):
        # Get subjects for theme
        subjects = THEME_SUBJECTS.get(theme, THEME_SUBJECTS['animals'])

        # Select unused subject
        available = [s for s in subjects if s not in used_items]
        if not available:
            available = subjects

        subject = random.choice(available)

        # Build prompt
        return f"""Generate a simple coloring page featuring a {subject}.

        Target age: {TARGET_AGE_MIN}-{TARGET_AGE_MAX} years old
        Style: {STYLE_DESCRIPTION}

        Return JSON:
        {{
            "subject": "{subject}",
            "description": "detailed description..."
        }}"""

    def extract_used_item(self, response):
        return response.get('subject')


class PromptBuilderFactory:
    """Factory for creating strategies."""

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
        strategy_class = cls._strategies.get(page_type)
        if not strategy_class:
            raise ValueError(f"Unknown page type: {page_type}")
        return strategy_class()
```

**Usage in Main Class:**
```python
# Before (165 lines):
prompt = self.get_prompt_for_type(page_type, theme, page_number)

# After (2 lines):
builder = PromptBuilderFactory.get_builder(page_type)
prompt = builder.build(theme, difficulty, page_number, used_items)
```

### Module Structure
```
components/prompts/
  __init__.py           # Exports PromptBuilderFactory, PromptStrategy
  base.py               # PromptStrategy abstract base class
  factory.py            # PromptBuilderFactory
  coloring_strategy.py  # ColoringPromptStrategy (~40 lines)
  tracing_strategy.py   # TracingPromptStrategy (~45 lines)
  counting_strategy.py  # CountingPromptStrategy (~40 lines)
  maze_strategy.py      # MazePromptStrategy (~35 lines)
  matching_strategy.py  # MatchingPromptStrategy (~50 lines)
  dot_to_dot_strategy.py # DotToDotPromptStrategy (~40 lines)
  test_prompts.py       # Unit tests for all strategies
  README.md             # Documentation
```

### SOLID Principles
- ✅ **Single Responsibility**: Each strategy handles ONE activity type
- ✅ **Open/Closed**: Add new activity = create new strategy class (no modification)
- ✅ **Liskov Substitution**: All strategies interchangeable
- ✅ **Interface Segregation**: Minimal interface (2 methods)
- ✅ **Dependency Inversion**: Main class depends on PromptStrategy abstraction

### Benefits
- ✅ Add new activity type: Create 1 new file (~40 lines), register in factory (1 line)
- ✅ Test activity types independently
- ✅ Eliminate code duplication
- ✅ Reduce main file by 165 lines
- ✅ Clear separation of concerns

### Testing Strategy
```python
# Test each strategy in isolation
def test_coloring_strategy():
    strategy = ColoringPromptStrategy()
    prompt = strategy.build("animals", "easy", 1, [])

    # Verify prompt structure
    assert "coloring" in prompt.lower()
    assert "2-3 years" in prompt
    assert "JSON" in prompt

    # Test variety handling
    used_items = ['cat', 'dog', 'rabbit']
    prompt2 = strategy.build("animals", "easy", 2, used_items)

    # Should avoid used items
    # (test extraction and verify not in used list)
```

### Risk: MEDIUM
- Most complex extraction (165 lines)
- Directly affects generated content
- Requires careful testing

**Mitigation:**
- Test each strategy independently
- Compare generated prompts with original (before/after)
- Validate all activity types generate correctly
- Keep old method until new code proven

---

## Phase 3: Extract API Client (~100 lines saved)

### 🎯 Design Pattern: Adapter Pattern + Retry Pattern

**Problem:**
```python
class ClaudeProcessor:
    def call_claude(self, prompt, api_key, page_num):
        # Direct coupling to Anthropic SDK
        client = Anthropic(api_key=api_key)
        message = client.messages.create(...)

        # Retry logic mixed in
        for attempt in range(3):
            # ...

        # Logging mixed in
        self.detailed_logs.append(...)

        # JSON extraction mixed in
        parsed = self._extract_json(response)

        # 80+ lines total
```

**Issues:**
- Tight coupling to Anthropic SDK
- Hard to test (requires real API calls)
- Can't swap API providers
- Mixed concerns (API, retry, logging, parsing)

**Solution: Adapter Pattern**

Create clean interface wrapping external API:

```python
from abc import ABC, abstractmethod

class APIClient(ABC):
    """Abstract interface for AI API clients."""

    @abstractmethod
    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        """Send message and return response."""
        pass


class ClaudeAPIClient(APIClient):
    """Adapter for Anthropic's Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet"):
        self.client = Anthropic(api_key=api_key)
        self.model = model
        self.logger = None

    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        """Send message to Claude."""
        if self.logger:
            self.logger(f"Calling Claude API: {self.model}")

        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        if self.logger and hasattr(message, 'usage'):
            self.logger(f"Token usage: {message.usage}")

        return response_text


class ResponseParser:
    """Parse JSON from Claude responses."""

    @staticmethod
    def extract_json(text: str) -> Optional[dict]:
        """Extract and parse JSON from response."""
        # Strip code fences
        cleaned = re.sub(r"```(?:json)?\s*", "", text)

        # Find JSON object
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            return None

        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            # Try fixing common issues
            return None


class RetryHandler:
    """Handle retries with exponential backoff."""

    @staticmethod
    def call_with_retry(
        func: Callable[[], str],
        parser: Callable[[str], Optional[dict]],
        retries: int = 2
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
                time.sleep(0.4 * (attempt + 1))

        return None, last_raw
```

**Usage:**
```python
# Initialize (once)
self.api_client = ClaudeAPIClient(api_key, model)
self.api_client.logger = self.logger.log

# Use throughout
raw = self.api_client.send_message(prompt)
parsed = ResponseParser.extract_json(raw)

# Or with retry
parsed, raw = RetryHandler.call_with_retry(
    lambda: self.api_client.send_message(prompt),
    ResponseParser.extract_json,
    retries=2
)
```

### Module Structure
```
components/api/
  __init__.py
  base.py               # APIClient abstract interface
  claude_client.py      # ClaudeAPIClient adapter
  response_parser.py    # ResponseParser
  retry_handler.py      # RetryHandler
  exceptions.py         # Custom exceptions
  test_api.py           # Unit tests with mocks
  README.md
```

### Benefits
- ✅ Easy to swap API providers (OpenAI, local models)
- ✅ Testable with mocks (no real API calls)
- ✅ Centralized error handling
- ✅ Can add caching, rate limiting later
- ✅ Reduce main file by ~100 lines

### Testing Strategy
```python
class MockAPIClient(APIClient):
    """Mock for testing."""

    def __init__(self, responses: List[str]):
        self.responses = responses
        self.call_count = 0

    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response


def test_retry_logic():
    """Test retry with mock that fails then succeeds."""
    responses = [
        "invalid response",  # First attempt fails
        '{"valid": "json"}'  # Second attempt succeeds
    ]
    client = MockAPIClient(responses)

    parsed, raw = RetryHandler.call_with_retry(
        client.send_message,
        ResponseParser.extract_json,
        retries=2
    )

    assert parsed == {"valid": "json"}
    assert client.call_count == 2
```

### Risk: LOW
- Well-defined interface
- Easy to test with mocks
- No complex business logic

---

## Phase 4: Extract Variety Tracking (~50 lines saved)

### 🎯 Design Pattern: State Pattern (simplified)

**Problem:**
```python
# State scattered throughout prompt methods
used = self.used_items.get('coloring', [])
available = [s for s in subjects if s not in used]
if not available:
    self.used_items['coloring'] = []
    available = subjects
selected = random.choice(available)
self.used_items['coloring'].append(selected)

# Repeated 6+ times with variations
```

**Issues:**
- State management duplicated across methods
- Hard to change selection strategy
- State transitions not explicit
- Mixed with prompt logic

**Solution: State Pattern**

```python
class VarietyTracker:
    """Manages variety tracking state."""

    def __init__(self):
        self._used_items: Dict[str, List[str]] = defaultdict(list)

    def select_unused(self, activity_type: str,
                      available: List[str]) -> str:
        """Select unused item, auto-reset if exhausted."""
        used = self._used_items[activity_type]
        unused = [item for item in available if item not in used]

        # State transition: reset when exhausted
        if not unused:
            self._used_items[activity_type] = []
            unused = available

        selected = random.choice(unused)

        # State transition: mark used
        self._used_items[activity_type].append(selected)

        return selected

    def mark_used(self, activity_type: str, item: str):
        """Manually mark item as used."""
        self._used_items[activity_type].append(item)

    def get_state(self, activity_type: str) -> List[str]:
        """Get current state."""
        return self._used_items[activity_type].copy()

    def reset(self, activity_type: str = None):
        """Reset state."""
        if activity_type:
            self._used_items[activity_type] = []
        else:
            self._used_items.clear()
```

**Usage:**
```python
# Before (7 lines scattered):
used = self.used_items.get('coloring', [])
available = [s for s in subjects if s not in used]
if not available:
    self.used_items['coloring'] = []
    available = subjects
selected = random.choice(available)
self.used_items['coloring'].append(selected)

# After (1 line):
selected = self.variety_tracker.select_unused('coloring', subjects)
```

### Benefits
- ✅ Centralized state management
- ✅ Easy to change selection strategy
- ✅ Clear state transitions
- ✅ Reduce main file by ~50 lines

### Risk: LOW
- Simple state management
- Easy to test

---

## Phase 5: Extract Logging System (~80 lines saved)

### 🎯 Design Pattern: Observer Pattern (simplified) + Strategy Pattern

**Problem:**
```python
# Logging scattered everywhere
self.detailed_logs.append({...})
print(f"Processing page {page_num}")
# ... later ...
with open('log.txt', 'w') as f:
    for log in self.detailed_logs:
        f.write(str(log))
```

**Issues:**
- Logging mixed with business logic
- Hard to change log format
- Can't easily add new outputs (JSON, DB, etc.)
- File I/O in main class

**Solution: Dedicated Logger**

```python
class SessionLogger:
    """Structured session logging."""

    def __init__(self):
        self.session_start = datetime.now()
        self.detailed_logs: List[Dict] = []
        self.messages: List[str] = []

    def log(self, message: str):
        """Log simple message."""
        timestamp = datetime.now().isoformat()
        self.messages.append(f"[{timestamp}] {message}")
        print(message)

    def log_api_call(self, page_num: int, prompt: str,
                     response: str, usage: Optional[Dict] = None):
        """Log API call with structured data."""
        self.detailed_logs.append({
            'timestamp': datetime.now().isoformat(),
            'page_number': page_num,
            'prompt': prompt,
            'response': response,
            'usage': usage
        })

    def save(self, filename: Optional[str] = None) -> str:
        """Persist logs to file."""
        if not filename:
            timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
            filename = f"claude_logs_{timestamp}.txt"

        with open(filename, 'w', encoding='utf-8') as f:
            # Write formatted logs
            ...

        return filename


class OutputDumper:
    """Strategy for JSON output."""

    @staticmethod
    def dump(processed_pages, logs, output_dir) -> Optional[Path]:
        """Dump to JSON format."""
        # Create structured JSON output
        ...
```

**Usage:**
```python
# Initialize
self.logger = SessionLogger()

# Use throughout
self.logger.log(f"Processing page {page_num}")
self.logger.log_api_call(page_num, prompt, response, usage)

# Finalize
self.logger.save()
OutputDumper.dump(processed_pages, self.logger.detailed_logs, output_dir)
```

### Benefits
- ✅ Clean separation of concerns
- ✅ Easy to add new output formats
- ✅ Better observability
- ✅ Testable without file I/O
- ✅ Reduce main file by ~80 lines

### Risk: LOW
- Non-critical path
- Easy to validate

---

## Phase 6: Refactor Main Orchestrator (Final Integration)

### 🎯 Design Pattern: Facade Pattern + Dependency Injection

**Problem:**
Current monolith doing everything in `process_pages()`:
- Configuration parsing
- Prompt building
- API calls
- State management
- Logging
- Error handling
- File I/O

All mixed together in 600+ lines.

**Solution: Slim Orchestrator**

```python
class ClaudeProcessor(Component):
    """Facade that orchestrates focused subsystems."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Dependency injection points
        self.logger: Optional[SessionLogger] = None
        self.variety_tracker: Optional[VarietyTracker] = None
        self.api_client: Optional[APIClient] = None

    def process_pages(self) -> List[Data]:
        """High-level orchestration (~100 lines)."""

        # 1. Initialize subsystems
        self._initialize_subsystems()

        # 2. Parse configuration
        config = self._parse_configuration()

        # 3. Process pages
        processed = self._process_all_pages(config)

        # 4. Finalize
        self._finalize()

        return processed

    def _initialize_subsystems(self):
        """Initialize all subsystems."""
        self.logger = SessionLogger()
        self.variety_tracker = VarietyTracker()
        self.api_client = ClaudeAPIClient(
            self.anthropic_api_key,
            self.model_name
        )
        self.api_client.logger = self.logger.log

    def _parse_configuration(self) -> ProcessorConfig:
        """Parse all configuration."""
        return ProcessorConfig(
            theme=ThemeConfig.sanitize(self.theme),
            difficulty=DifficultyConfig.normalize(self.difficulty),
            limits=PageLimitsConfig(
                max_total=PageLimitsConfig.parse_max_total(self.max_total_pages),
                per_topic=PageLimitsConfig.parse_pages_per_topic(self.pages_per_topic)
            )
        )

    def _process_all_pages(self, config: ProcessorConfig) -> List[Data]:
        """Process all pages."""
        processed = []

        for page_data in self.pages:
            page = page_data.data

            # Check limits
            if self._should_skip(page, config.limits, processed):
                continue

            # Process page (delegates to subsystems)
            result = self._process_single_page(page, config)
            if result:
                processed.append(result)

        return processed

    def _process_single_page(self, page: Dict, config: ProcessorConfig) -> Optional[Data]:
        """Process single page (delegates to subsystems)."""

        # Build prompt (Strategy Pattern)
        builder = PromptBuilderFactory.get_builder(page['type'])
        prompt = builder.build(
            config.theme,
            config.difficulty,
            page['pageNumber'],
            self.variety_tracker.get_state(page['type'])
        )

        # Call API (Adapter Pattern)
        response = self.api_client.send_message(prompt)
        parsed = ResponseParser.extract_json(response)

        if not parsed:
            self.logger.log(f"Failed to parse response for page {page['pageNumber']}")
            return None

        # Track variety (State Pattern)
        item = builder.extract_used_item(parsed)
        if item:
            self.variety_tracker.mark_used(page['type'], item)

        return Data(data={**page, **parsed})

    def _finalize(self):
        """Finalize processing."""
        self.logger.save()

    def _should_skip(self, page, limits, processed):
        """Check if page should be skipped."""
        # Simple limit checking logic
        pass
```

### Key Characteristics
- **~200 lines total** (vs 781)
- **Reads like a story** (initialize → configure → process → finalize)
- **Delegates everything** to subsystems
- **No complex logic** in orchestrator
- **Easy to test** with mocked dependencies

### Final Structure
```
components/
├── claude_processor.py (~200 lines) - Orchestrator
├── config/                           - Phase 1
│   ├── theme_config.py
│   ├── difficulty_config.py
│   └── ...
├── prompts/                          - Phase 2
│   ├── base.py
│   ├── factory.py
│   ├── coloring_strategy.py
│   └── ...
├── api/                              - Phase 3
│   ├── claude_client.py
│   ├── response_parser.py
│   └── ...
├── tracking/                         - Phase 4
│   └── variety_tracker.py
└── logging/                          - Phase 5
    ├── session_logger.py
    └── output_dumper.py
```

### Benefits
- ✅ Main file 781 → 200 lines (74% reduction)
- ✅ Clear orchestration flow
- ✅ All subsystems independently testable
- ✅ Easy to understand and modify
- ✅ Flexible composition

### Testing Strategy
```python
def test_orchestrator_integration():
    """Test with all mocks."""
    processor = ClaudeProcessor()

    # Inject mocks
    processor.api_client = MockAPIClient(['{"subject": "cat"}'])
    processor.logger = SessionLogger()
    processor.variety_tracker = VarietyTracker()

    # Test orchestration
    result = processor.process_pages()

    # Verify subsystems coordinated correctly
    assert len(result) > 0
    assert processor.api_client.call_count > 0
```

### Risk: MEDIUM
- Integration point for all phases
- Critical path
- Must maintain backward compatibility

**Mitigation:**
- Incremental refactoring
- Continuous testing after each change
- Compare outputs with original
- Performance benchmarking

---

## Execution Order

1. ✅ **Phase 1: Config** (READY - See REFACTORING_PLAN_PHASE1_ENHANCED.md)
2. **Phase 2: Prompts** (Execute after Phase 1 succeeds)
3. **Phase 3: API** (Can run parallel with Phase 2)
4. **Phase 4: Tracking** (Execute after Phase 2)
5. **Phase 5: Logging** (Can run parallel with Phase 2-4)
6. **Phase 6: Orchestrator** (Execute after all others complete)

---

## Timeline

- **Week 1**: Phases 1, 3 (Foundation)
- **Week 2**: Phase 2 (Core logic)
- **Week 3**: Phases 4, 5, 6 (Complete & Polish)

**Total**: 15-21 hours over 2-3 weeks

---

## Success Metrics

### Code Quality
- Main file: 781 → ~200 lines (74% reduction)
- Each module < 150 lines
- Clear module boundaries
- No code duplication

### Testing
- 80%+ code coverage
- All edge cases covered
- Integration tests pass
- E2E tests pass

### Functionality
- Identical output to original
- No performance regression
- All features preserved

### Maintainability
- Easy to add new activity types
- Easy to modify prompts
- Easy to swap API providers
- Clear documentation

---

## When You're Ready

Let me know when Phase 1 is complete and you want to proceed with Phase 2. I'll create detailed step-by-step instructions similar to Phase 1, including:

- Exact line numbers to modify
- Complete code snippets
- Validation commands
- Design pattern annotations
- Testing strategy

**Current Status: Ready to execute Phase 1** ✅

---

## References

- **ARCHITECTURE_OVERVIEW.md** - Design patterns explained in detail
- **REFACTORING_PLAN_PHASE1_ENHANCED.md** - Detailed Phase 1 steps
- **REFACTORING_PLAN_COMPLETE.md** - Original comprehensive plan

**All plans now enhanced with design pattern annotations!** 🎯
