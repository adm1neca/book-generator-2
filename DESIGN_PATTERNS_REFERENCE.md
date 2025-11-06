# Design Patterns Reference Guide

Quick reference for design patterns used in the Claude Processor refactoring.

---

## Table of Contents

1. [Value Object Pattern](#value-object-pattern) - Phase 1
2. [Strategy Pattern](#strategy-pattern) - Phase 2
3. [Factory Pattern](#factory-pattern) - Phase 2
4. [Adapter Pattern](#adapter-pattern) - Phase 3
5. [State Pattern](#state-pattern) - Phase 4
6. [Observer Pattern](#observer-pattern) - Phase 5
7. [Facade Pattern](#facade-pattern) - Phase 6
8. [Dependency Injection](#dependency-injection) - Phase 6

---

## Value Object Pattern

**Category:** Creational / Domain Pattern

**When to Use:**
- Encapsulating configuration or domain data
- Ensuring validation rules are centralized
- Replacing primitive obsession (raw strings, ints)
- Making invalid states unrepresentable

**Structure:**
```python
class ValueObject:
    """Encapsulates data with validation rules."""

    @staticmethod
    def create(raw_value) -> ValidType:
        """
        Always returns valid value.
        Invalid inputs converted to defaults.
        Makes invalid states impossible.
        """
        # Validation logic
        # Return guaranteed-valid value
```

**Example from Project:**
```python
class ThemeConfig:
    """Value Object for theme configuration."""

    @staticmethod
    def sanitize(theme: Optional[str]) -> str:
        """Always returns valid theme."""
        t = (theme or "").strip().lower()

        # Apply mappings
        for key, value in THEME_FALLBACKS.items():
            if key in t:
                return value

        # Block invalid themes
        if any(blocked in t for blocked in BLOCKED_THEMES):
            return DEFAULT_THEME

        return t or DEFAULT_THEME
```

**Benefits:**
- ✅ Validation in ONE place
- ✅ No invalid states possible
- ✅ Easy to test (pure function)
- ✅ Reusable across application

**Anti-Pattern Avoided:**
Primitive Obsession - passing raw strings/ints that may be invalid

**Testing:**
```python
def test_value_object():
    # Test valid input
    assert ThemeConfig.sanitize("Forest") == "forest-friends"

    # Test invalid input → default
    assert ThemeConfig.sanitize("invalid") == "animals"

    # Test None → default
    assert ThemeConfig.sanitize(None) == "animals"
```

**SOLID Principles:**
- ✅ Single Responsibility: Only handles validation
- ✅ Open/Closed: Can extend validation rules

---

## Strategy Pattern

**Category:** Behavioral Pattern

**When to Use:**
- Multiple algorithms/behaviors that do similar things differently
- Large if/elif chains selecting behavior
- Need to add new algorithms without modifying existing code
- Each algorithm should be independently testable

**Structure:**
```python
from abc import ABC, abstractmethod

class Strategy(ABC):
    """Abstract base class defining interface."""

    @abstractmethod
    def execute(self, data) -> Result:
        """Algorithm to be implemented by concrete strategies."""
        pass


class ConcreteStrategyA(Strategy):
    """One implementation."""

    def execute(self, data) -> Result:
        # Implementation A
        pass


class ConcreteStrategyB(Strategy):
    """Another implementation."""

    def execute(self, data) -> Result:
        # Implementation B
        pass


# Usage
strategy = get_strategy()  # Returns A or B
result = strategy.execute(data)  # Polymorphism
```

**Example from Project:**
```python
class PromptStrategy(ABC):
    """Strategy interface for prompt generation."""

    @abstractmethod
    def build(self, theme, difficulty, page_num, used_items) -> str:
        """Generate prompt for this activity type."""
        pass


class ColoringPromptStrategy(PromptStrategy):
    """Concrete strategy for coloring pages."""

    def build(self, theme, difficulty, page_num, used_items) -> str:
        subjects = THEME_SUBJECTS.get(theme)
        subject = select_unused(subjects, used_items)
        return f"Generate coloring page with {subject}..."


class TracingPromptStrategy(PromptStrategy):
    """Concrete strategy for tracing pages."""

    def build(self, theme, difficulty, page_num, used_items) -> str:
        words = get_tracing_words(difficulty)
        word = select_unused(words, used_items)
        return f"Generate tracing page for '{word}'..."


# Usage (polymorphism - all strategies work the same way)
strategy = PromptBuilderFactory.get_builder(page_type)
prompt = strategy.build(theme, difficulty, page_num, used_items)
```

**Benefits:**
- ✅ Open/Closed Principle: Add new strategies without modifying existing
- ✅ Single Responsibility: Each strategy does ONE thing
- ✅ Testability: Test strategies independently
- ✅ Eliminates large if/elif chains

**Anti-Pattern Avoided:**
Long Method with conditional logic

**Before (Anti-Pattern):**
```python
def get_prompt_for_type(self, page_type, theme, page_num):
    if page_type == "coloring":
        # 20 lines
    elif page_type == "tracing":
        # 20 lines
    elif page_type == "counting":
        # 20 lines
    # 165 lines total, must modify to add new type
```

**After (Strategy Pattern):**
```python
# Main class:
builder = PromptBuilderFactory.get_builder(page_type)
prompt = builder.build(theme, difficulty, page_num, used_items)

# To add new type: Create new file, no modifications needed
class PuzzlePromptStrategy(PromptStrategy):
    def build(self, ...):
        # New logic
```

**Testing:**
```python
def test_coloring_strategy():
    """Test strategy in isolation."""
    strategy = ColoringPromptStrategy()
    prompt = strategy.build("animals", "easy", 1, [])

    assert "coloring" in prompt
    assert "JSON" in prompt
```

**SOLID Principles:**
- ✅ Single Responsibility: Each strategy = one algorithm
- ✅ Open/Closed: Extend by adding, not modifying
- ✅ Liskov Substitution: All strategies interchangeable
- ✅ Interface Segregation: Minimal interface

---

## Factory Pattern

**Category:** Creational Pattern

**When to Use:**
- Need to create objects but don't want to specify exact class
- Creation logic is complex or varies based on input
- Want to centralize object creation
- Often paired with Strategy Pattern

**Structure:**
```python
class Factory:
    """Centralized object creation."""

    _registry = {
        'type_a': ClassA,
        'type_b': ClassB,
    }

    @classmethod
    def create(cls, object_type: str):
        """Create appropriate object."""
        klass = cls._registry.get(object_type)
        if not klass:
            raise ValueError(f"Unknown type: {object_type}")
        return klass()
```

**Example from Project:**
```python
class PromptBuilderFactory:
    """Factory for creating prompt strategies."""

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
        """Get appropriate strategy for page type."""
        strategy_class = cls._strategies.get(page_type)
        if not strategy_class:
            raise ValueError(f"Unknown page type: {page_type}")
        return strategy_class()
```

**Benefits:**
- ✅ Centralized creation logic
- ✅ Easy to register new types
- ✅ Decouples client from concrete classes

**Usage:**
```python
# Client doesn't need to know about concrete classes
builder = PromptBuilderFactory.get_builder("coloring")
# Returns ColoringPromptStrategy instance

# To add new type:
PromptBuilderFactory._strategies['puzzle'] = PuzzlePromptStrategy
```

**SOLID Principles:**
- ✅ Open/Closed: Add types by registration, not modification
- ✅ Dependency Inversion: Client depends on factory, not concrete types

---

## Adapter Pattern

**Category:** Structural Pattern

**When to Use:**
- Need to use third-party library but don't want tight coupling
- Want to provide consistent interface to varying implementations
- Testing requires mocking external dependencies
- May need to swap implementations later

**Structure:**
```python
from abc import ABC, abstractmethod

class TargetInterface(ABC):
    """Interface we want to use."""

    @abstractmethod
    def request(self) -> Result:
        pass


class Adapter(TargetInterface):
    """Adapts external library to our interface."""

    def __init__(self):
        self.adaptee = ExternalLibrary()

    def request(self) -> Result:
        """Translate our interface to external library's interface."""
        # Convert input format
        external_input = self._convert_input()

        # Call external library
        external_result = self.adaptee.external_method(external_input)

        # Convert output format
        return self._convert_output(external_result)
```

**Example from Project:**
```python
class APIClient(ABC):
    """Our interface for AI APIs."""

    @abstractmethod
    def send_message(self, prompt: str) -> str:
        """Send message and get response."""
        pass


class ClaudeAPIClient(APIClient):
    """Adapter for Anthropic's Claude SDK."""

    def __init__(self, api_key: str, model: str):
        # Wrapped external dependency
        self.client = Anthropic(api_key=api_key)
        self.model = model

    def send_message(self, prompt: str) -> str:
        """Adapt our interface to Anthropic's SDK."""

        # Translate to Anthropic's format
        message = self.client.messages.create(
            model=self.model,
            max_tokens=768,
            messages=[{"role": "user", "content": prompt}]
        )

        # Extract and return response
        return message.content[0].text


class OpenAIAdapter(APIClient):
    """Alternative adapter for OpenAI."""

    def __init__(self, api_key: str, model: str):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def send_message(self, prompt: str) -> str:
        """Adapt our interface to OpenAI's SDK."""

        # Translate to OpenAI's format
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content


# Usage - same interface, different implementations
client = ClaudeAPIClient(api_key, "claude-3-5-sonnet")
# OR
client = OpenAIAdapter(api_key, "gpt-4")

# Both work the same way
response = client.send_message("Hello")
```

**Benefits:**
- ✅ Decouples from external dependencies
- ✅ Easy to swap implementations
- ✅ Testable with mocks
- ✅ Consistent interface across different providers

**Testing:**
```python
class MockAPIClient(APIClient):
    """Mock adapter for testing."""

    def __init__(self, canned_responses):
        self.responses = canned_responses
        self.call_count = 0

    def send_message(self, prompt: str) -> str:
        response = self.responses[self.call_count]
        self.call_count += 1
        return response


def test_with_mock():
    client = MockAPIClient(["response 1", "response 2"])
    assert client.send_message("test") == "response 1"
    assert client.call_count == 1
```

**SOLID Principles:**
- ✅ Dependency Inversion: Depend on interface, not concrete SDK
- ✅ Open/Closed: Add new providers without modifying existing
- ✅ Liskov Substitution: All adapters interchangeable

---

## State Pattern

**Category:** Behavioral Pattern

**When to Use:**
- Object behavior changes based on internal state
- State transitions need to be explicit and controlled
- State management logic scattered across codebase
- Multiple objects need to share state

**Structure:**
```python
class StateManager:
    """Manages state and state transitions."""

    def __init__(self):
        self._state = {}

    def transition_a(self):
        """Explicit state transition."""
        # Update state
        self._state['key'] = new_value

    def transition_b(self):
        """Another state transition."""
        # Update state differently
        pass

    def get_state(self):
        """Query current state."""
        return self._state.copy()
```

**Example from Project:**
```python
class VarietyTracker:
    """Manages variety tracking state."""

    def __init__(self):
        self._used_items: Dict[str, List[str]] = defaultdict(list)

    def select_unused(self, activity_type: str,
                      available: List[str]) -> str:
        """State transition: select item, auto-reset if needed."""

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

    def mark_used(self, activity_type: str, item: str):
        """Explicit state transition."""
        self._used_items[activity_type].append(item)

    def get_state(self, activity_type: str) -> List[str]:
        """Query state."""
        return self._used_items[activity_type].copy()

    def reset(self, activity_type: str = None):
        """Explicit reset transition."""
        if activity_type:
            self._used_items[activity_type] = []
        else:
            self._used_items.clear()
```

**Benefits:**
- ✅ Centralized state management
- ✅ Explicit state transitions
- ✅ Easy to reason about state changes
- ✅ Testable in isolation

**Before (Scattered State):**
```python
# State management mixed with business logic
used = self.used_items.get('coloring', [])
available = [s for s in subjects if s not in used]
if not available:
    self.used_items['coloring'] = []  # Manual reset
    available = subjects
selected = random.choice(available)
self.used_items['coloring'].append(selected)  # Manual tracking
```

**After (State Pattern):**
```python
# Clean, centralized state management
selected = self.variety_tracker.select_unused('coloring', subjects)
# All state transitions handled internally
```

**Testing:**
```python
def test_state_transitions():
    tracker = VarietyTracker()
    items = ['a', 'b', 'c']

    # Select all items
    selected = [tracker.select_unused('test', items) for _ in range(3)]
    assert set(selected) == {'a', 'b', 'c'}

    # Should reset and allow reuse
    next_item = tracker.select_unused('test', items)
    assert next_item in items
```

**SOLID Principles:**
- ✅ Single Responsibility: Only manages state
- ✅ Open/Closed: Can extend with new selection strategies

---

## Observer Pattern

**Category:** Behavioral Pattern

**When to Use:**
- Need to notify multiple objects of state changes
- Logging/monitoring without cluttering business logic
- Multiple outputs for same event (file, console, database)
- Decoupling event producers from consumers

**Structure:**
```python
class Subject:
    """Object being observed."""

    def __init__(self):
        self._observers = []

    def attach(self, observer):
        self._observers.append(observer)

    def notify(self, event):
        for observer in self._observers:
            observer.update(event)


class Observer:
    """Observes subject."""

    def update(self, event):
        # React to event
        pass
```

**Example from Project (Simplified):**
```python
class SessionLogger:
    """Logs session activity (simplified observer)."""

    def __init__(self):
        self.detailed_logs: List[Dict] = []
        self.messages: List[str] = []

    def log(self, message: str):
        """Observe: message event."""
        self.messages.append(f"[{datetime.now()}] {message}")
        print(message)

    def log_api_call(self, page_num: int, prompt: str,
                     response: str, usage: Dict):
        """Observe: API call event."""
        self.detailed_logs.append({
            'timestamp': datetime.now().isoformat(),
            'page_number': page_num,
            'prompt': prompt,
            'response': response,
            'usage': usage
        })


# Usage in main class
class ClaudeProcessor:
    def process_pages(self):
        # Attach logger
        self.logger = SessionLogger()
        self.api_client.logger = self.logger.log  # Observer attached

        # Business logic - just does its thing
        for page in pages:
            self.logger.log(f"Processing {page}")  # Event notification
            response = self.api_client.send_message(prompt)
            self.logger.log_api_call(...)  # Event notification
```

**Benefits:**
- ✅ Decouples logging from business logic
- ✅ Can add multiple observers (file, console, database)
- ✅ Easy to enable/disable logging

**SOLID Principles:**
- ✅ Single Responsibility: Logger only logs
- ✅ Open/Closed: Add new observers without modifying subject

---

## Facade Pattern

**Category:** Structural Pattern

**When to Use:**
- Complex subsystem needs simple interface
- Want to hide implementation details
- Providing unified interface to set of interfaces
- Orchestrating multiple subsystems

**Structure:**
```python
class Facade:
    """Simple interface to complex subsystem."""

    def __init__(self):
        # Initialize subsystems
        self.subsystem_a = SubsystemA()
        self.subsystem_b = SubsystemB()
        self.subsystem_c = SubsystemC()

    def simple_operation(self):
        """Coordinate subsystems behind simple interface."""
        # Step 1: Use subsystem A
        self.subsystem_a.operation_1()

        # Step 2: Use subsystem B
        result = self.subsystem_b.operation_2()

        # Step 3: Use subsystem C
        self.subsystem_c.operation_3(result)

        return final_result
```

**Example from Project:**
```python
class ClaudeProcessor(Component):
    """Facade for activity generation system."""

    def __init__(self):
        # Subsystems
        self.logger = None
        self.variety_tracker = None
        self.api_client = None

    def process_pages(self) -> List[Data]:
        """Simple interface hiding complex orchestration."""

        # Initialize subsystems
        self._initialize_subsystems()

        # Parse configuration (delegates to config subsystem)
        config = self._parse_configuration()

        # Process pages (coordinates multiple subsystems)
        processed = []
        for page in self.pages:
            # Uses: limits (config), prompts (strategy),
            #       API (adapter), tracking (state), logging (observer)
            result = self._process_single_page(page, config)
            processed.append(result)

        # Finalize (delegates to logging subsystem)
        self._finalize()

        return processed

    def _process_single_page(self, page, config):
        """Coordinates all subsystems for one page."""

        # Prompt subsystem (Strategy)
        builder = PromptBuilderFactory.get_builder(page['type'])
        prompt = builder.build(config.theme, config.difficulty, ...)

        # API subsystem (Adapter)
        response = self.api_client.send_message(prompt)

        # Tracking subsystem (State)
        item = builder.extract_used_item(response)
        self.variety_tracker.mark_used(page['type'], item)

        return Data(data={**page, **response})
```

**Benefits:**
- ✅ Hides complexity
- ✅ Provides simple interface
- ✅ Coordinates subsystems
- ✅ Easy to use

**Before (No Facade):**
```python
# Client must know about all subsystems
theme = ThemeConfig.sanitize(raw_theme)
difficulty = DifficultyConfig.normalize(raw_diff)
builder = PromptBuilderFactory.get_builder(type)
prompt = builder.build(theme, difficulty, ...)
client = ClaudeAPIClient(api_key)
response = client.send_message(prompt)
# ... many more steps
```

**After (Facade):**
```python
# Simple interface
processor = ClaudeProcessor()
results = processor.process_pages()
# All complexity hidden
```

**SOLID Principles:**
- ✅ Single Responsibility: Orchestrates, doesn't implement
- ✅ Dependency Inversion: Depends on subsystem interfaces

---

## Dependency Injection

**Category:** Design Principle / Pattern

**When to Use:**
- Need to swap implementations (testing, different providers)
- Want loose coupling between classes
- Testing requires mocking dependencies
- Following Dependency Inversion Principle

**Structure:**
```python
class Service:
    """Class that depends on other classes."""

    def __init__(self, dependency: DependencyInterface):
        """Inject dependency via constructor."""
        self.dependency = dependency

    # OR property injection:
    def set_dependency(self, dependency: DependencyInterface):
        """Inject dependency via setter."""
        self.dependency = dependency

    def do_work(self):
        """Use injected dependency."""
        result = self.dependency.operation()
        return result
```

**Example from Project:**
```python
class ClaudeProcessor:
    """Uses dependency injection for flexibility."""

    def __init__(self):
        # Dependencies injected later (property injection)
        self.api_client: Optional[APIClient] = None
        self.logger: Optional[SessionLogger] = None
        self.variety_tracker: Optional[VarietyTracker] = None

    def process_pages(self):
        """Initialize dependencies."""

        # Production dependencies
        self.api_client = ClaudeAPIClient(api_key, model)
        self.logger = SessionLogger()
        self.variety_tracker = VarietyTracker()

        # Use dependencies
        response = self.api_client.send_message(prompt)
        self.logger.log("Processing...")

# Testing with injected mocks
def test_processor():
    processor = ClaudeProcessor()

    # Inject mocks
    processor.api_client = MockAPIClient(["test response"])
    processor.logger = MockLogger()
    processor.variety_tracker = MockTracker()

    # Test with mocked dependencies
    result = processor.process_pages()
```

**Benefits:**
- ✅ Loose coupling
- ✅ Easy to test with mocks
- ✅ Easy to swap implementations
- ✅ Follows Dependency Inversion Principle

**Before (Tight Coupling):**
```python
class ClaudeProcessor:
    def process_pages(self):
        # Hard-coded dependency (tight coupling)
        client = Anthropic(api_key=self.api_key)

        # Can't swap implementations
        # Hard to test (requires real API)
```

**After (Dependency Injection):**
```python
class ClaudeProcessor:
    def __init__(self):
        self.api_client = None  # Injection point

    def process_pages(self):
        # Production
        self.api_client = ClaudeAPIClient(...)

        # OR Testing
        self.api_client = MockAPIClient(...)

        # Same interface, different implementations
        response = self.api_client.send_message(prompt)
```

**SOLID Principles:**
- ✅ Dependency Inversion: Depend on abstractions, not concretions
- ✅ Open/Closed: Swap implementations without modifying class

---

## Pattern Combinations in This Project

Our refactoring uses multiple patterns working together:

```
┌─────────────────────────────────────────────┐
│   ClaudeProcessor (Facade + DI)            │
│   - Orchestrates subsystems                 │
│   - Dependencies injected                   │
└────────────┬────────────────────────────────┘
             │
     ┌───────┼───────┬────────┬────────┬─────────┐
     ▼       ▼       ▼        ▼        ▼         ▼
┌────────┐ ┌────┐ ┌─────┐ ┌─────┐ ┌────────┐ ┌─────┐
│Config  │ │API │ │Prompt│ │Track│ │Logging │ │...  │
│(Value  │ │(Ada│ │(Stra │ │(Sta │ │(Obser  │ │     │
│Object) │ │pter│ │tegy+│ │te)  │ │ver)    │ │     │
│        │ │)   │ │Factor│ │     │ │        │ │     │
└────────┘ └────┘ └─────┘ └─────┘ └────────┘ └─────┘
```

**Pattern Synergy:**
- **Facade** (ClaudeProcessor) coordinates all subsystems
- **Dependency Injection** allows swapping subsystems
- **Value Objects** (Config) ensure valid input
- **Strategy** (Prompts) handles different activity types
- **Adapter** (API) decouples from external SDK
- **State** (Tracking) manages variety
- **Observer** (Logging) monitors without coupling

**Result:** Clean, maintainable, testable, extensible architecture

---

## Quick Pattern Selection Guide

| Problem | Pattern | Phase |
|---------|---------|-------|
| Validation scattered | Value Object | 1 |
| Large if/elif for behavior | Strategy | 2 |
| Need to create many related objects | Factory | 2 |
| Tight coupling to external library | Adapter | 3 |
| State management scattered | State | 4 |
| Logging clutters business logic | Observer | 5 |
| Complex subsystem needs simple interface | Facade | 6 |
| Need to swap implementations | Dependency Injection | 6 |

---

## Further Reading

**Books:**
- "Design Patterns" - Gang of Four (1994)
- "Head First Design Patterns" - Freeman & Freeman (2004)
- "Clean Code" - Robert C. Martin (2008)
- "Refactoring" - Martin Fowler (2018)

**Online:**
- https://refactoring.guru/design-patterns
- https://sourcemaking.com/design_patterns

---

**Use this guide alongside the detailed phase plans for implementation guidance!** 🎯
