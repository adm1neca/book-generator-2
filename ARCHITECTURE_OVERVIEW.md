# Architecture Overview: Claude Processor Refactoring

## Executive Summary

This document provides the architectural rationale and design pattern explanations for the Claude Processor refactoring. Use this alongside the detailed phase plans to understand **WHY** we make each architectural decision.

## Current Architecture Anti-Patterns

### The God Object Problem

**What it is:**
```
ClaudeProcessor (781 lines)
├── Configuration Management (14 responsibilities)
├── Prompt Generation (6 activity types × 2 methods each)
├── API Communication (retry, error handling, logging)
├── State Management (variety tracking)
├── Logging (detailed logs, file I/O)
├── Validation (theme, difficulty, limits)
└── Orchestration (page processing loop)
```

**Why it's problematic:**
- **Low Cohesion**: Unrelated concerns bundled together
- **High Coupling**: Changes ripple across entire class
- **Hard to Test**: Can't test components in isolation
- **Hard to Extend**: Adding new activity types requires modifying monolith
- **Code Duplication**: Similar logic repeated across methods
- **Violates Single Responsibility Principle (SRP)**

### The Long Method Problem

**Current `get_prompt_for_type()` method:**
- 165 lines
- 6 different code paths (one per activity type)
- Duplicated variety selection logic
- Mixed concerns: prompt building + state management

**Why it's problematic:**
- Hard to understand flow
- Difficult to unit test specific activity types
- Changes to one activity type risk breaking others
- **Violates Open/Closed Principle** - must modify existing code to add features

---

## Target Architecture: SOLID Principles

### Single Responsibility Principle (SRP)

**Each class should have ONE reason to change.**

| Class | Single Responsibility |
|-------|----------------------|
| `ThemeConfig` | Theme validation and normalization |
| `DifficultyConfig` | Difficulty level management |
| `PageLimitsConfig` | Page limit parsing and validation |
| `ColoringPromptStrategy` | Generate coloring page prompts |
| `ClaudeAPIClient` | Communicate with Claude API |
| `VarietyTracker` | Track item usage for variety |
| `SessionLogger` | Log session activity |
| `ClaudeProcessor` | Orchestrate subsystems |

### Open/Closed Principle (OCP)

**Open for extension, closed for modification.**

**Before (violates OCP):**
```python
def get_prompt_for_type(self, page_type, theme, page_num):
    if page_type == "coloring":
        # 20 lines of coloring logic
    elif page_type == "tracing":
        # 20 lines of tracing logic
    elif page_type == "matching":
        # 20 lines of matching logic
    # ... adding new type = MODIFY this method
```

**After (follows OCP):**
```python
# Adding new activity type:
# 1. Create new strategy class (NEW file, NO modification of existing)
class PuzzlePromptStrategy(PromptStrategy):
    def build(self, theme, difficulty, page_num, used_items):
        # New logic here
        pass

# 2. Register in factory (ONE line change)
PromptBuilderFactory._strategies['puzzle'] = PuzzlePromptStrategy
```

### Liskov Substitution Principle (LSP)

**Derived classes must be substitutable for their base classes.**

All `PromptStrategy` implementations can be used interchangeably:
```python
# ANY strategy works the same way
strategy = PromptBuilderFactory.get_builder(page_type)
prompt = strategy.build(theme, difficulty, page_num, used_items)
item = strategy.extract_used_item(response)
```

### Interface Segregation Principle (ISP)

**Clients shouldn't depend on interfaces they don't use.**

**Before (fat interface):**
```python
class ClaudeProcessor:
    # 20+ methods, some only used by specific page types
    def _sanitize_theme(...)
    def _get_coloring_subject(...)
    def _get_tracing_word(...)
    def _get_counting_item(...)
    # Clients must inherit ALL methods even if they only need one
```

**After (focused interfaces):**
```python
class PromptStrategy(ABC):
    # Only 2 methods - minimal interface
    @abstractmethod
    def build(...): pass

    @abstractmethod
    def extract_used_item(...): pass
```

### Dependency Inversion Principle (DIP)

**Depend on abstractions, not concretions.**

**Before:**
```python
class ClaudeProcessor:
    def process_pages(self):
        # DIRECTLY creates Anthropic client (tight coupling)
        client = Anthropic(api_key=self.key)
        message = client.messages.create(...)
        # Hard to test, hard to swap providers
```

**After:**
```python
class ClaudeProcessor:
    def __init__(self):
        # Depends on abstraction (interface)
        self.api_client: APIClient = None

    def process_pages(self):
        # Use interface, not concrete implementation
        response = self.api_client.send_message(prompt)
        # Easy to swap: ClaudeAPIClient, OpenAIClient, MockClient, etc.
```

---

## Design Patterns Applied

### Phase 1: Configuration Management

**Pattern: Value Object Pattern**

**Problem:** Configuration data scattered as primitive types (strings, ints) throughout code.

**Solution:** Encapsulate related data and validation into dedicated classes.

**Benefits:**
- ✅ Validation in ONE place
- ✅ Immutable, predictable behavior
- ✅ Easy to test
- ✅ Type safety

**Implementation:**
```python
# Value Objects
class ThemeConfig:
    @staticmethod
    def sanitize(theme: str) -> str:
        """Always returns valid theme"""
        pass

class DifficultyConfig:
    @staticmethod
    def normalize(difficulty: str) -> str:
        """Always returns 'easy', 'medium', or 'hard'"""
        pass

# Usage: Guaranteed valid values
theme = ThemeConfig.sanitize(user_input)  # Never returns invalid theme
difficulty = DifficultyConfig.normalize(user_input)  # Never returns invalid difficulty
```

**SOLID Principles Addressed:**
- ✅ SRP: Each config class has one responsibility
- ✅ OCP: Can add new themes without modifying validation logic
- ✅ DIP: Main class depends on config abstraction, not raw strings

---

### Phase 2: Prompt Building Strategy

**Pattern: Strategy Pattern**

**Problem:** Large conditional logic to select prompt generation behavior.

**Solution:** Encapsulate each algorithm (prompt generation) in separate class with common interface.

**Benefits:**
- ✅ Add new activity types without modifying existing code (OCP)
- ✅ Each strategy independently testable (SRP)
- ✅ Strategies interchangeable (LSP)
- ✅ Eliminates code duplication

**Implementation:**

**Base Strategy (Interface):**
```python
from abc import ABC, abstractmethod

class PromptStrategy(ABC):
    """Abstract base class for prompt generation strategies."""

    @abstractmethod
    def build(self, theme: str, difficulty: str,
              page_number: int, used_items: List[str]) -> str:
        """Generate prompt for this activity type."""
        pass

    @abstractmethod
    def extract_used_item(self, response: dict) -> Optional[str]:
        """Extract the item used from Claude's response."""
        pass
```

**Concrete Strategy Example:**
```python
class ColoringPromptStrategy(PromptStrategy):
    """Strategy for generating coloring page prompts."""

    def build(self, theme, difficulty, page_number, used_items):
        # Specific to coloring pages
        subjects = THEME_SUBJECTS.get(theme, THEME_SUBJECTS['animals'])
        available = [s for s in subjects if s not in used_items]

        if not available:
            available = subjects

        subject = random.choice(available)

        return f"""Generate a coloring page with a {subject}...
        {TARGET_AGE_MIN}-{TARGET_AGE_MAX} years old...
        Style: {STYLE_DESCRIPTION}"""

    def extract_used_item(self, response):
        return response.get('subject')
```

**Factory for Creation:**
```python
class PromptBuilderFactory:
    """Factory for creating prompt strategies by type."""

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

**Usage (Polymorphism):**
```python
# Old way: 165 lines of if/elif
prompt = self.get_prompt_for_type(page_type, theme, page_num)

# New way: 2 lines (same code works for ANY activity type)
builder = PromptBuilderFactory.get_builder(page_type)
prompt = builder.build(theme, difficulty, page_num, used_items)
```

**SOLID Principles Addressed:**
- ✅ SRP: Each strategy only handles ONE activity type
- ✅ OCP: Add new activity types by creating new strategy class (no modification)
- ✅ LSP: All strategies can be used interchangeably
- ✅ ISP: Minimal interface (only 2 methods)
- ✅ DIP: Main class depends on PromptStrategy abstraction

**Testing Benefits:**
```python
# Before: Must test entire 781-line class to test coloring prompts
def test_coloring_prompt():
    processor = ClaudeProcessor()  # Heavy initialization
    processor.anthropic_api_key = "test"
    # ... lots of setup ...
    prompt = processor.get_prompt_for_type("coloring", "animals", 1)
    assert "coloring" in prompt

# After: Test strategy in isolation
def test_coloring_prompt():
    strategy = ColoringPromptStrategy()  # Lightweight
    prompt = strategy.build("animals", "easy", 1, [])
    assert "coloring" in prompt
```

---

### Phase 3: API Client

**Pattern: Adapter Pattern**

**Problem:** Direct dependency on third-party Anthropic SDK creates tight coupling.

**Solution:** Create adapter that wraps external API behind our own interface.

**Benefits:**
- ✅ Easy to swap API providers (OpenAI, local models, etc.)
- ✅ Testable with mocks (no real API calls in tests)
- ✅ Centralized error handling and retry logic
- ✅ Can add caching, rate limiting, etc. in ONE place

**Implementation:**

**Our Interface:**
```python
class APIClient(ABC):
    """Abstract interface for AI API clients."""

    @abstractmethod
    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        """Send message and return response text."""
        pass
```

**Concrete Adapter:**
```python
class ClaudeAPIClient(APIClient):
    """Adapter for Anthropic's Claude API."""

    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet"):
        self.client = Anthropic(api_key=api_key)  # Wrapped dependency
        self.model = model
        self.logger = None

    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        """Adapt our interface to Anthropic's SDK."""
        if self.logger:
            self.logger(f"Calling Claude API (model: {self.model})")

        # Translate our call to Anthropic's format
        message = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            messages=[{"role": "user", "content": prompt}]
        )

        response_text = message.content[0].text

        if self.logger and hasattr(message, 'usage'):
            self.logger(f"Token usage: {message.usage}")

        return response_text
```

**Alternative Adapters (easy to add):**
```python
class OpenAIAdapter(APIClient):
    """Adapter for OpenAI's API."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        # Translate to OpenAI's format
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens
        )
        return response.choices[0].message.content


class MockAPIClient(APIClient):
    """Mock adapter for testing."""

    def __init__(self, canned_responses: List[str]):
        self.responses = canned_responses
        self.call_count = 0

    def send_message(self, prompt: str, max_tokens: int = 768) -> str:
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return response
```

**Usage:**
```python
# Production
client = ClaudeAPIClient(api_key="sk-...", model="claude-3-5-sonnet")

# Testing
client = MockAPIClient(canned_responses=["Mock response"])

# Easy to swap
client = OpenAIAdapter(api_key="sk-...", model="gpt-4")

# All use same interface
response = client.send_message("Hello")
```

**SOLID Principles Addressed:**
- ✅ SRP: Client only handles API communication
- ✅ OCP: Add new providers without modifying existing code
- ✅ LSP: All adapters interchangeable
- ✅ DIP: Main class depends on APIClient interface, not concrete Anthropic SDK

---

### Phase 4: Variety Tracking

**Pattern: State Pattern (simplified)**

**Problem:** State management (used items) scattered throughout prompt methods.

**Solution:** Encapsulate state and state transitions in dedicated class.

**Benefits:**
- ✅ Centralized state management
- ✅ Easy to change tracking strategy
- ✅ Testable in isolation
- ✅ Clear API for state operations

**Implementation:**
```python
class VarietyTracker:
    """Manages variety tracking state for activity pages."""

    def __init__(self):
        self._used_items: Dict[str, List[str]] = defaultdict(list)

    def select_unused(self, activity_type: str,
                      available: List[str]) -> str:
        """State transition: select unused item, auto-reset if needed."""
        used = self._used_items[activity_type]
        unused = [item for item in available if item not in used]

        # State transition: reset when exhausted
        if not unused:
            self._used_items[activity_type] = []
            unused = available

        selected = random.choice(unused)

        # State transition: mark as used
        self._used_items[activity_type].append(selected)

        return selected

    def get_state(self, activity_type: str) -> List[str]:
        """Query current state."""
        return self._used_items[activity_type].copy()

    def reset_state(self, activity_type: str = None):
        """Explicit state transition."""
        if activity_type:
            self._used_items[activity_type] = []
        else:
            self._used_items.clear()
```

**Usage:**
```python
# Before: State management mixed with prompt logic
used = self.used_items.get('coloring', [])
available = [s for s in subjects if s not in used]
if not available:
    self.used_items['coloring'] = []  # Reset logic here
    available = subjects
selected = random.choice(available)
self.used_items['coloring'].append(selected)  # Mutation here

# After: Clean state management
selected = self.variety_tracker.select_unused('coloring', subjects)
# All state transitions handled internally
```

**SOLID Principles Addressed:**
- ✅ SRP: Only manages variety state
- ✅ OCP: Can extend with different selection strategies
- ✅ DIP: Main class depends on tracker interface

---

### Phase 5: Logging System

**Pattern: Observer Pattern (simplified) + Strategy Pattern**

**Problem:** Logging logic intertwined with business logic.

**Solution:** Separate logging concerns with dedicated logger class.

**Benefits:**
- ✅ Logging doesn't clutter business logic
- ✅ Easy to change log format/destination
- ✅ Can add multiple log outputs (file, database, monitoring)
- ✅ Testable without file I/O

**Implementation:**

**Session Logger:**
```python
class SessionLogger:
    """Centralized session logging."""

    def __init__(self):
        self.session_start = datetime.now()
        self.detailed_logs: List[Dict] = []
        self.messages: List[str] = []

    def log(self, message: str):
        """Log a simple message."""
        timestamp = datetime.now().isoformat()
        self.messages.append(f"[{timestamp}] {message}")
        print(message)

    def log_api_call(self, page_num: int, prompt: str,
                     response: str, usage: Optional[Dict] = None):
        """Log structured API call data."""
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
```

**Output Dumper (Strategy for JSON output):**
```python
class OutputDumper:
    """Strategy for dumping output to JSON."""

    @staticmethod
    def dump(processed_pages: List[Dict],
             logs: List[Dict],
             output_dir: Path) -> Optional[Path]:
        """Dump to JSON format."""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"claude_run_{timestamp}.json"

        payload = {
            "meta": {
                "generated_at": datetime.utcnow().isoformat(),
                "pages_count": len(processed_pages)
            },
            "pages": processed_pages,
            "logs": logs
        }

        file_path = output_dir / filename
        with file_path.open("w") as f:
            json.dump(payload, f, indent=2)

        return file_path
```

**Usage:**
```python
# Before: Logging mixed everywhere
self.detailed_logs.append({'page': 1, 'prompt': '...'})
print(f"Processing page {page_num}")
# ... business logic ...
with open('log.txt', 'w') as f:
    f.write(str(self.detailed_logs))

# After: Clean separation
self.logger.log(f"Processing page {page_num}")
# ... business logic ...
self.logger.log_api_call(page_num, prompt, response, usage)
# At end
self.logger.save()
```

**SOLID Principles Addressed:**
- ✅ SRP: Logger only handles logging
- ✅ OCP: Can add new output formats (JSON, CSV, DB) without modifying logger
- ✅ ISP: Simple interface, not bloated

---

### Phase 6: Main Orchestrator

**Pattern: Facade Pattern + Dependency Injection**

**Problem:** Monolithic class doing everything.

**Solution:** Slim orchestrator that coordinates focused subsystems.

**Benefits:**
- ✅ Clear separation of concerns
- ✅ Easy to understand flow
- ✅ Each subsystem independently testable
- ✅ Flexible composition

**Implementation:**

**Before (Monolithic):**
```python
class ClaudeProcessor(Component):
    def process_pages(self):
        # 600+ lines mixing:
        # - Configuration parsing
        # - Prompt building
        # - API calls
        # - State management
        # - Logging
        # - Error handling
        # All intertwined
```

**After (Orchestrator):**
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
        """High-level orchestration only (~100 lines)."""

        # 1. Initialize subsystems (Dependency Injection)
        self.logger = SessionLogger()
        self.variety_tracker = VarietyTracker()
        self.api_client = ClaudeAPIClient(
            self.anthropic_api_key,
            self.model_name
        )
        self.api_client.logger = self.logger.log

        # 2. Parse configuration (delegation)
        theme = ThemeConfig.sanitize(self.theme)
        difficulty = DifficultyConfig.normalize(self.difficulty)
        limits = PageLimitsConfig(
            max_total=PageLimitsConfig.parse_max_total(self.max_total_pages),
            per_topic=PageLimitsConfig.parse_pages_per_topic(self.pages_per_topic)
        )

        # 3. Process pages (orchestration)
        processed = []
        for page_data in self.pages:
            page = page_data.data

            # 3a. Check limits (delegation)
            if self._should_skip(page, limits, processed):
                continue

            # 3b. Build prompt (delegation via Strategy)
            builder = PromptBuilderFactory.get_builder(page['type'])
            prompt = builder.build(
                theme,
                difficulty,
                page['pageNumber'],
                self.variety_tracker.get_state(page['type'])
            )

            # 3c. Call API (delegation via Adapter)
            response = self.api_client.send_message(prompt)
            parsed = ResponseParser.extract_json(response)

            # 3d. Track variety (delegation)
            if parsed:
                item = builder.extract_used_item(parsed)
                if item:
                    self.variety_tracker.mark_used(page['type'], item)

                processed.append(Data(data={**page, **parsed}))

        # 4. Finalize (delegation)
        self.logger.save()
        return processed

    def _should_skip(self, page, limits, processed):
        """Simple helper method."""
        # Limit checking logic
        pass
```

**Key Characteristics:**
- **~200 lines total** (vs 781)
- **Reads like a story** (initialize → configure → process → finalize)
- **Each step delegates** to focused subsystems
- **No complex logic** in orchestrator itself
- **Easy to test** with mocked dependencies

**SOLID Principles Addressed:**
- ✅ SRP: Orchestrator only coordinates, doesn't implement
- ✅ OCP: Add new features by extending subsystems
- ✅ LSP: All subsystems swappable via interfaces
- ✅ ISP: Uses minimal interfaces from each subsystem
- ✅ DIP: Depends on abstractions (APIClient, PromptStrategy, etc.)

---

## Architecture Diagram

### Before (Monolithic)
```
┌────────────────────────────────────────┐
│                                        │
│         ClaudeProcessor                │
│              (781 lines)               │
│                                        │
│  ┌──────────────────────────────────┐ │
│  │ Config, Prompts, API, State,     │ │
│  │ Logging, Validation, Orchestration│ │
│  │      ALL MIXED TOGETHER           │ │
│  └──────────────────────────────────┘ │
│                                        │
└────────────────────────────────────────┘
         │
         ▼
    Anthropic SDK (tight coupling)
```

### After (Modular)
```
┌─────────────────────────────────────────────────────────────┐
│              ClaudeProcessor (Orchestrator)                 │
│                      (~200 lines)                           │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │      Coordinates subsystems, no complex logic        │  │
│  └─────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │
         ├──────────┬──────────┬────────────┬───────────┬─────────
         ▼          ▼          ▼            ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌──────────┐ ┌──────┐ ┌─────────┐
    │ Config  │ │ Prompt  │ │   API    │ │Variety│ │ Logger  │
    │Subsystem│ │Strategy │ │ Adapter  │ │Tracker│ │         │
    └─────────┘ └─────────┘ └──────────┘ └──────┘ └─────────┘
                                 │
                                 ▼
                          Anthropic SDK
                        (loose coupling)
```

---

## Benefits Summary

### Code Metrics
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Main file lines | 781 | ~200 | 74% reduction |
| Cyclomatic complexity | High (nested ifs) | Low (delegation) | ✅ |
| Test coverage | ~0% | Target 80%+ | ✅ |
| Number of responsibilities | 14 | 1 (orchestration) | ✅ |
| Longest method | 202 lines | ~30 lines | 85% reduction |

### Development Velocity
| Task | Before | After | Improvement |
|------|--------|-------|-------------|
| Add new activity type | Modify 781-line file | Add 1 new file (~50 lines) | 10x faster |
| Test specific feature | Test entire monolith | Test isolated module | Instant |
| Debug issue | Search 781 lines | Go to specific module | 5x faster |
| Swap API provider | Rewrite API calls | Add new adapter | 20x faster |

### Quality Improvements
- ✅ **Testability**: Each module independently testable
- ✅ **Maintainability**: Clear module boundaries
- ✅ **Extensibility**: Add features without modifying existing code
- ✅ **Readability**: Each module <150 lines
- ✅ **Reliability**: Isolated changes reduce regression risk

---

## Anti-Patterns Eliminated

### 1. God Object → Focused Classes
**Before:** One class with 14 responsibilities
**After:** 10+ focused classes, each with ONE responsibility

### 2. Long Method → Small Methods
**Before:** 202-line method with nested logic
**After:** Methods ~10-30 lines, single purpose

### 3. Primitive Obsession → Value Objects
**Before:** Raw strings/ints everywhere
**After:** ThemeConfig, DifficultyConfig with validation

### 4. Data Clumps → Configuration Objects
**Before:** Individual parameters passed everywhere
**After:** PageLimitsConfig object encapsulates related data

### 5. Duplicated Code → Strategy Pattern
**Before:** Similar prompt logic repeated 6 times
**After:** Shared base class, unique logic in concrete strategies

### 6. Feature Envy → Proper Encapsulation
**Before:** Main class accessing internal state of many concerns
**After:** Each class manages its own state

---

## Testing Strategy by Pattern

### Value Objects (Config)
```python
# Test validation rules
def test_theme_config():
    assert ThemeConfig.sanitize("peppa") == "animals"  # Blocked
    assert ThemeConfig.sanitize("Forest") == "forest-friends"  # Normalized
```

### Strategy Pattern (Prompts)
```python
# Test each strategy in isolation
def test_coloring_strategy():
    strategy = ColoringPromptStrategy()
    prompt = strategy.build("animals", "easy", 1, [])
    assert "coloring" in prompt.lower()
    assert "2-3 years" in prompt
```

### Adapter Pattern (API)
```python
# Test with mock, no real API calls
def test_api_client():
    mock_client = MockAPIClient(["test response"])
    response = mock_client.send_message("test prompt")
    assert response == "test response"
    assert mock_client.call_count == 1
```

### State Pattern (Variety)
```python
# Test state transitions
def test_variety_tracker():
    tracker = VarietyTracker()
    items = ['a', 'b', 'c']

    # Select all items
    selected = [tracker.select_unused('test', items) for _ in range(3)]
    assert set(selected) == {'a', 'b', 'c'}

    # Should reset and allow reuse
    next_item = tracker.select_unused('test', items)
    assert next_item in items
```

### Orchestrator (Integration)
```python
# Test with all mocks
def test_orchestrator():
    processor = ClaudeProcessor()
    processor.api_client = MockAPIClient(["mock response"])
    processor.logger = SessionLogger()
    processor.variety_tracker = VarietyTracker()

    result = processor.process_pages()
    # Verify orchestration logic
```

---

## References

### Design Patterns
- **Strategy Pattern**: Gang of Four, "Design Patterns" (1994)
- **Adapter Pattern**: Gang of Four, "Design Patterns" (1994)
- **State Pattern**: Gang of Four, "Design Patterns" (1994)
- **Facade Pattern**: Gang of Four, "Design Patterns" (1994)
- **Value Object Pattern**: Eric Evans, "Domain-Driven Design" (2003)

### SOLID Principles
- Robert C. Martin, "Agile Software Development: Principles, Patterns, and Practices" (2002)
- Robert C. Martin, "Clean Code" (2008)

### Refactoring
- Martin Fowler, "Refactoring: Improving the Design of Existing Code" (2018)

---

## Next Steps

1. Read this document to understand architectural rationale
2. Follow detailed phase plans (REFACTORING_PLAN_PHASE1.md, etc.)
3. Reference design patterns here when implementing
4. Use this document to explain changes to team members

**Remember:** Good architecture is not about clever patterns—it's about code that's easy to understand, test, and modify.
