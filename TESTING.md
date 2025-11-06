# Testing the Refactored Claude Processor

## Quick Start - Run All Tests

```bash
# In your Docker container:
cd /home/user/book-generator-2
python3 test_refactored.py
```

This comprehensive test suite validates all 5 refactored subsystems:
1. ✅ Configuration Management
2. ✅ Prompt Strategies
3. ✅ Variety Tracking
4. ✅ Logging System
5. ✅ Integration Testing

---

## Individual Module Tests

### Test 1: Configuration Module Doctests

```bash
python3 components/config/test_config.py
```

**Expected:** 25+ doctests pass

### Test 2: Variety Tracker Doctests

```bash
python3 components/tracking/variety_tracker.py
```

**Expected:** 44 doctests pass

### Test 3: Session Logger Doctests

```bash
python3 components/logging/session_logger.py
```

**Expected:** 36 doctests pass

### Test 4: Output Dumper Doctests

```bash
python3 components/logging/output_dumper.py
```

**Expected:** 20 doctests pass

### Test 5: Response Parser Doctests

```bash
cd components/api
python3 response_parser.py
```

**Expected:** 10 doctests pass

### Test 6: Retry Handler Doctests

```bash
cd components/api
python3 retry_handler.py
```

**Expected:** 13 doctests pass

---

## Test Individual Subsystems

### Configuration System

```python
from components.config import ThemeConfig, DifficultyConfig, PageLimitsConfig

# Test theme sanitization
theme = ThemeConfig.sanitize("ANIMALS")
print(f"Theme: {theme}")  # Output: animals

# Test difficulty
diff = DifficultyConfig.normalize("hard")
print(f"Difficulty: {diff}")  # Output: hard

# Test limits
limits = PageLimitsConfig.parse_pages_per_topic("coloring=5,tracing=3")
print(f"Limits: {limits}")  # Output: {'coloring': 5, 'tracing': 3}
```

### Prompt Strategies

```python
from components.prompts import PromptBuilderFactory

# Get available types
types = PromptBuilderFactory.get_available_types()
print(f"Available: {types}")

# Test a strategy
strategy = PromptBuilderFactory.get_builder('coloring')
prompt, selected = strategy.build(
    theme='animals',
    difficulty='easy',
    page_number=1,
    used_items=[],
    style_guard='STYLE REQUIREMENTS HERE'
)
print(f"Selected: {selected}")
print(f"Prompt length: {len(prompt)}")
```

### Variety Tracking

```python
from components.tracking import VarietyTracker

tracker = VarietyTracker()

# Select items with automatic variety
options = ['cat', 'dog', 'bird', 'fish']
for i in range(6):
    item = tracker.select_unused('coloring', options)
    print(f"Page {i+1}: {item}")

# Check what's been used
used = tracker.get_used('coloring')
print(f"Used: {used}")

# Get summary
summary = tracker.get_summary()
print(f"Summary: {summary}")
```

### Logging System

```python
from components.logging import SessionLogger, OutputDumper
from pathlib import Path

# Session logging
logger = SessionLogger()
logger.log("Starting process")
logger.log_api_call(1, "prompt", "response", model="claude-3")

# Get summary
summary = logger.get_summary()
print(f"Duration: {summary['duration_seconds']:.2f}s")

# Save logs
log_file = logger.save()
print(f"Saved to: {log_file}")

# Dump output
pages = [{'pageNumber': 1, 'type': 'coloring'}]
logs = logger.get_detailed_logs()
output_file = OutputDumper.dump(pages, logs, Path("/tmp"))
print(f"Output: {output_file}")
```

---

## Test With Langflow

If you're using Langflow, the refactored component should work exactly as before:

1. **Start Langflow** (if not already running)
2. **Import your flow** with the Claude Processor component
3. **Configure inputs:**
   - Pages: Connect from your page generator
   - API Key: Your Anthropic API key
   - Model: `claude-haiku-4-5-20251001` (or your preferred model)
4. **Run the flow**

The refactored code maintains 100% backward compatibility.

---

## Test Original Variety Logic

Run the existing test file:

```bash
python3 test_simple.py
```

This tests the variety tracking logic (now in VarietyTracker class).

---

## Verify Syntax

Check all files compile without errors:

```bash
python3 -m py_compile components/claude_processor.py
python3 -m py_compile components/config/*.py
python3 -m py_compile components/prompts/*.py
python3 -m py_compile components/api/*.py
python3 -m py_compile components/tracking/*.py
python3 -m py_compile components/logging/*.py
```

---

## Expected Test Results

When you run `python3 test_refactored.py`, you should see:

```
TEST 1: Module Imports          ✅ PASS
TEST 2: Configuration Module    ✅ PASS
TEST 3: Prompt Strategies       ✅ PASS
TEST 4: Variety Tracking        ✅ PASS
TEST 5: Logging System          ✅ PASS
TEST 6: Running Doctests        ✅ PASS (118 tests)
TEST 7: Integration Test        ✅ PASS

🎉 ALL TESTS PASSED! 🎉
```

---

## Troubleshooting

### Import Error: No module named 'anthropic'

This is **expected** and **OK**. The ClaudeAPIClient requires the `anthropic` package, but:
- It's only loaded when actually making API calls
- All other modules work independently
- The test suite skips API import tests
- When Langflow runs, it provides the anthropic package

### Import Error: No module named 'langflow'

This is also **expected** and **OK**. The main `claude_processor.py` imports Langflow components, but:
- Langflow provides these when running in Langflow
- Tests import specific modules, not the main processor
- Structure validation doesn't require Langflow

### Test Failures

If any tests fail:
1. Check the error message carefully
2. Run individual module tests to isolate the issue
3. Verify file permissions: `ls -la components/*/`
4. Check Python version: `python3 --version` (should be 3.8+)

---

## What Gets Tested

✅ **Module Structure** - All 26 modules import correctly
✅ **Configuration** - Theme/difficulty/limits parsing
✅ **Strategies** - All 6 activity types generate prompts
✅ **Variety** - Selection, tracking, auto-reset
✅ **Logging** - Session logs, API call tracking, file output
✅ **Doctests** - 118+ inline examples
✅ **Integration** - End-to-end flow without API

---

## Performance Note

The refactored code is actually **more efficient** because:
- Strategy objects are lightweight
- Variety tracking uses efficient set operations
- Logging is buffered and written once
- No duplicate logic execution

---

## Need Help?

- Check `ARCHITECTURE_OVERVIEW.md` for system architecture
- Check `DESIGN_PATTERNS_REFERENCE.md` for pattern explanations
- Each module has comprehensive docstrings
- All modules have 118+ doctests as usage examples
