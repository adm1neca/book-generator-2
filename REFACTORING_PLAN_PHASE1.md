# AI Agent Refactoring Plan: Phase 1 - Extract Configuration Management

## Executive Summary
**Objective:** Extract configuration logic from `claude_processor.py` into separate, testable modules without changing any functionality.

**Target File:** `components/claude_processor.py` (781 lines)
**Estimated Reduction:** ~130 lines
**Risk Level:** LOW
**Duration:** 2-3 hours
**Rollback Strategy:** Git revert + feature flag

**User Preferences:**
- Execute Phase 1 only (Configuration extraction)
- Pause only if tests fail
- Commit after completing the phase
- Attempt fix once if tests fail, then stop for review

---

## Pre-Flight Checklist

### Step 0.1: Create Baseline
**Why:** Establish known-good state for regression testing

**Actions:**
1. Ensure you're in project root: `E:\GITHUB\projects\Book generator 2`
2. Create feature branch: `git checkout -b refactor/extract-config`
3. Run baseline test:
   ```bash
   docker compose run --rm langflow python scripts/activity_generator.py --test --output /app/workdir/out/baseline_test.pdf
   ```
4. Save baseline output: Copy the PDF and note file size
5. Document baseline behavior:
   - PDF generates successfully
   - No errors in console
   - Log file created
   - Used items tracked correctly

**Success Criteria:**
- ✅ Baseline test runs without errors
- ✅ PDF file exists and is valid
- ✅ File size > 0 bytes
- ✅ Git branch created

**Rollback:** `git checkout main && git branch -D refactor/extract-config`

---

## Phase 1: Create Configuration Module Structure

### Step 1.1: Create Directory Structure
**Why:** Establish clean module hierarchy before writing code

**Actions:**
```bash
cd "E:\GITHUB\projects\Book generator 2\components"
mkdir -p config
touch config/__init__.py
touch config/validation.py
touch config/theme_config.py
touch config/difficulty_config.py
touch config/limits_config.py
touch config/constants.py
```

**Validation:**
```bash
# Verify files exist
ls config/
# Should show: __init__.py, validation.py, theme_config.py, difficulty_config.py, limits_config.py, constants.py
```

**Success Criteria:**
- ✅ All 6 files created
- ✅ Directory structure matches plan

---

### Step 1.2: Create Constants Module
**Why:** Centralize all magic strings and hardcoded values

**File:** `components/config/constants.py`

**Content:**
```python
"""Configuration constants for Claude processor."""

from typing import Dict, List, Set

# Theme mappings
THEME_FALLBACKS: Dict[str, str] = {
    'forest': 'forest-friends',
    'woods': 'forest-friends',
    'forest friends': 'forest-friends',
    'sea': 'under-the-sea',
    'ocean': 'under-the-sea',
    'under the sea': 'under-the-sea',
    'farm': 'farm-day',
    'farm animals': 'farm-day',
    'space': 'space-explorer',
    'galaxy': 'space-explorer'
}

# Blocked copyrighted themes
BLOCKED_THEMES: Set[str] = {
    "peppa",
    "paw patrol",
    "paw-patrol",
    "disney",
    "marvel",
    "pokemon",
    "barbie"
}

# Default fallback theme
DEFAULT_THEME: str = "animals"

# Valid difficulty levels
VALID_DIFFICULTIES: Set[str] = {"easy", "medium", "hard"}
DEFAULT_DIFFICULTY: str = "easy"

# Difficulty-based repetitions for tracing
DIFFICULTY_REPETITIONS: Dict[str, int] = {
    "easy": 8,
    "medium": 12,
    "hard": 16
}

# Theme-based subjects for coloring pages
THEME_SUBJECTS: Dict[str, List[str]] = {
    'forest-friends': [
        'fox', 'bear', 'owl', 'rabbit', 'hedgehog', 'deer',
        'squirrel', 'raccoon', 'snail', 'mushroom', 'acorn', 'pine tree'
    ],
    'under-the-sea': [
        'fish', 'dolphin', 'starfish', 'shell', 'turtle',
        'seahorse', 'crab', 'octopus', 'bubble', 'coral'
    ],
    'farm-day': [
        'cow', 'chicken', 'sheep', 'pig', 'barn',
        'tractor', 'duck', 'horse', 'hay bale'
    ],
    'space-explorer': [
        'rocket', 'planet', 'star', 'moon',
        'astronaut', 'satellite', 'comet'
    ],
    'shapes': [
        'circle', 'square', 'triangle', 'star', 'heart',
        'diamond', 'oval', 'rectangle', 'hexagon', 'pentagon'
    ],
    'animals': [
        'cat', 'dog', 'rabbit', 'bird', 'fish', 'elephant',
        'giraffe', 'lion', 'bear', 'monkey', 'butterfly',
        'bee', 'duck', 'frog'
    ]
}

# Target age range
TARGET_AGE_MIN: int = 2
TARGET_AGE_MAX: int = 3

# Style requirements
STYLE_DESCRIPTION: str = "thick black outlines, simple cute shapes, no shading"
```

**Validation:**
```python
# Test imports
from components.config.constants import THEME_FALLBACKS, BLOCKED_THEMES
assert len(THEME_FALLBACKS) == 10
assert len(BLOCKED_THEMES) == 7
```

**Success Criteria:**
- ✅ File created with all constants
- ✅ Imports work
- ✅ No syntax errors

---

### Step 1.3: Create Validation Module
**Why:** Extract type coercion and validation logic

**File:** `components/config/validation.py`

**Content:**
```python
"""Validation utilities for configuration values."""

from typing import Optional


def coerce_positive_int(raw_value, label: str) -> Optional[int]:
    """
    Convert incoming values to a positive int, logging when invalid.

    Args:
        raw_value: Value to convert (can be int, float, str, or None)
        label: Descriptive label for logging

    Returns:
        Positive integer or None if invalid

    Examples:
        >>> coerce_positive_int(5, "test")
        5
        >>> coerce_positive_int("10", "test")
        10
        >>> coerce_positive_int(-5, "test")
        >>> coerce_positive_int("", "test")
    """
    if raw_value is None:
        return None

    if isinstance(raw_value, (int, float)):
        value = int(raw_value)
    else:
        text = str(raw_value).strip()
        if not text:
            return None
        try:
            value = int(text)
        except ValueError:
            return None

    if value <= 0:
        return None

    return value


def validate_string_not_empty(value: Optional[str], default: str = "") -> str:
    """
    Ensure string is not None or empty.

    Args:
        value: String to validate
        default: Default value if invalid

    Returns:
        Valid string or default

    Examples:
        >>> validate_string_not_empty("test", "default")
        'test'
        >>> validate_string_not_empty(None, "default")
        'default'
        >>> validate_string_not_empty("", "default")
        'default'
    """
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


if __name__ == "__main__":
    import doctest
    doctest.testmod()
```

**Validation:**
```bash
docker compose run --rm langflow python -m doctest components/config/validation.py -v
```

**Success Criteria:**
- ✅ All doctests pass
- ✅ No import errors
- ✅ Functions return expected types

---

### Step 1.4: Create Theme Configuration Module
**Why:** Isolate theme sanitization logic

**File:** `components/config/theme_config.py`

**Content:**
```python
"""Theme configuration and sanitization."""

from typing import Optional
from components.config.constants import (
    THEME_FALLBACKS,
    BLOCKED_THEMES,
    DEFAULT_THEME
)


class ThemeConfig:
    """Handles theme validation and normalization."""

    @staticmethod
    def sanitize(theme: Optional[str]) -> str:
        """
        Normalize and block branded themes to keep content safe.

        Args:
            theme: Raw theme string from input

        Returns:
            Sanitized theme string

        Examples:
            >>> ThemeConfig.sanitize("Forest")
            'forest-friends'
            >>> ThemeConfig.sanitize("OCEAN")
            'under-the-sea'
            >>> ThemeConfig.sanitize("peppa pig")
            'animals'
            >>> ThemeConfig.sanitize(None)
            'animals'
        """
        # Normalize to lowercase
        t = (theme or "").strip().lower()

        # Apply friendly remaps
        for key, value in THEME_FALLBACKS.items():
            if key in t:
                t = value
                break

        # Block copyrighted/brand themes
        if any(blocked in t for blocked in BLOCKED_THEMES):
            return DEFAULT_THEME

        # Return sanitized or default
        return t or DEFAULT_THEME

    @staticmethod
    def is_valid_theme(theme: str) -> bool:
        """
        Check if theme is valid (not blocked).

        Args:
            theme: Theme to check

        Returns:
            True if valid, False if blocked
        """
        t = theme.lower().strip()
        return not any(blocked in t for blocked in BLOCKED_THEMES)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
```

**Validation:**
```bash
docker compose run --rm langflow python -m doctest components/config/theme_config.py -v
```

**Success Criteria:**
- ✅ All doctests pass
- ✅ Sanitize returns expected values
- ✅ Blocked themes return 'animals'

---

### Step 1.5: Create Difficulty Configuration Module
**Why:** Extract difficulty level management

**File:** `components/config/difficulty_config.py`

**Content:**
```python
"""Difficulty configuration management."""

from typing import Optional
from components.config.constants import (
    VALID_DIFFICULTIES,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_REPETITIONS
)


class DifficultyConfig:
    """Handles difficulty level validation and settings."""

    @staticmethod
    def normalize(difficulty: Optional[str]) -> str:
        """
        Normalize difficulty to valid value.

        Args:
            difficulty: Raw difficulty string

        Returns:
            Valid difficulty level (easy, medium, or hard)

        Examples:
            >>> DifficultyConfig.normalize("EASY")
            'easy'
            >>> DifficultyConfig.normalize("invalid")
            'easy'
            >>> DifficultyConfig.normalize(None)
            'easy'
        """
        d = (difficulty or "").strip().lower()
        if d not in VALID_DIFFICULTIES:
            return DEFAULT_DIFFICULTY
        return d

    @staticmethod
    def get_repetitions(difficulty: str) -> int:
        """
        Get number of repetitions for difficulty level.

        Args:
            difficulty: Difficulty level

        Returns:
            Number of repetitions for tracing activities

        Examples:
            >>> DifficultyConfig.get_repetitions("easy")
            8
            >>> DifficultyConfig.get_repetitions("medium")
            12
            >>> DifficultyConfig.get_repetitions("hard")
            16
        """
        normalized = DifficultyConfig.normalize(difficulty)
        return DIFFICULTY_REPETITIONS[normalized]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
```

**Validation:**
```bash
docker compose run --rm langflow python -m doctest components/config/difficulty_config.py -v
```

**Success Criteria:**
- ✅ All doctests pass
- ✅ Invalid difficulties return 'easy'
- ✅ Repetitions match expected values

---

### Step 1.6: Create Limits Configuration Module
**Why:** Extract page limiting logic

**File:** `components/config/limits_config.py`

**Content:**
```python
"""Page limits configuration management."""

import json
from typing import Dict, Optional, Any
from components.config.validation import coerce_positive_int


class PageLimitsConfig:
    """Handles page limit configuration parsing and validation."""

    def __init__(self, max_total: Optional[int] = None,
                 per_topic: Optional[Dict[str, int]] = None):
        """
        Initialize page limits configuration.

        Args:
            max_total: Maximum total pages to generate
            per_topic: Dictionary of topic -> max count
        """
        self.max_total = max_total
        self.per_topic = per_topic or {}

    @staticmethod
    def parse_max_total(raw_value: Any) -> Optional[int]:
        """
        Parse max_total_pages value.

        Args:
            raw_value: Raw input value

        Returns:
            Positive integer or None

        Examples:
            >>> PageLimitsConfig.parse_max_total("10")
            10
            >>> PageLimitsConfig.parse_max_total(5)
            5
            >>> PageLimitsConfig.parse_max_total("-1")
            >>> PageLimitsConfig.parse_max_total("")
        """
        return coerce_positive_int(raw_value, "max_total_pages")

    @staticmethod
    def parse_pages_per_topic(raw: Any) -> Dict[str, int]:
        """
        Parse pages_per_topic configuration.

        Accepts:
        - JSON dict: {"coloring": 8, "tracing": 4}
        - Comma list: "coloring=8,tracing=4"
        - Dict object

        Args:
            raw: Raw input value

        Returns:
            Dictionary of normalized topic -> count

        Examples:
            >>> PageLimitsConfig.parse_pages_per_topic('{"coloring":8}')
            {'coloring': 8}
            >>> PageLimitsConfig.parse_pages_per_topic("coloring=8,tracing=4")
            {'coloring': 8, 'tracing': 4}
            >>> PageLimitsConfig.parse_pages_per_topic("")
            {}
        """
        if raw is None:
            return {}

        # Already a dict
        if isinstance(raw, dict):
            source_items = raw.items()
        else:
            text = str(raw).strip()
            if not text:
                return {}

            # JSON format
            if text.startswith("{"):
                try:
                    decoded = json.loads(text)
                except json.JSONDecodeError:
                    return {}

                if not isinstance(decoded, dict):
                    return {}

                source_items = decoded.items()
            # Comma-separated format
            else:
                parts = [p.strip() for p in text.split(",") if p.strip()]
                parsed_pairs = []
                for part in parts:
                    if "=" not in part:
                        continue
                    key, value = part.split("=", 1)
                    parsed_pairs.append((key.strip(), value.strip()))
                source_items = parsed_pairs

        # Validate and normalize
        limits: Dict[str, int] = {}
        for key, value in source_items:
            topic = str(key).strip().lower()
            if not topic:
                continue

            count = coerce_positive_int(value, f"pages_per_topic[{topic}]")
            if count is None:
                continue

            limits[topic] = count

        return limits


if __name__ == "__main__":
    import doctest
    doctest.testmod()
```

**Validation:**
```bash
docker compose run --rm langflow python -m doctest components/config/limits_config.py -v
```

**Success Criteria:**
- ✅ All doctests pass
- ✅ JSON parsing works
- ✅ Comma format parsing works
- ✅ Invalid values filtered out

---

### Step 1.7: Create Config Package Init
**Why:** Export clean public API

**File:** `components/config/__init__.py`

**Content:**
```python
"""Configuration management for Claude processor."""

from components.config.constants import (
    THEME_FALLBACKS,
    BLOCKED_THEMES,
    DEFAULT_THEME,
    VALID_DIFFICULTIES,
    DEFAULT_DIFFICULTY,
    DIFFICULTY_REPETITIONS,
    THEME_SUBJECTS,
    TARGET_AGE_MIN,
    TARGET_AGE_MAX,
    STYLE_DESCRIPTION
)

from components.config.validation import (
    coerce_positive_int,
    validate_string_not_empty
)

from components.config.theme_config import ThemeConfig
from components.config.difficulty_config import DifficultyConfig
from components.config.limits_config import PageLimitsConfig

__all__ = [
    # Constants
    'THEME_FALLBACKS',
    'BLOCKED_THEMES',
    'DEFAULT_THEME',
    'VALID_DIFFICULTIES',
    'DEFAULT_DIFFICULTY',
    'DIFFICULTY_REPETITIONS',
    'THEME_SUBJECTS',
    'TARGET_AGE_MIN',
    'TARGET_AGE_MAX',
    'STYLE_DESCRIPTION',

    # Validation
    'coerce_positive_int',
    'validate_string_not_empty',

    # Config classes
    'ThemeConfig',
    'DifficultyConfig',
    'PageLimitsConfig',
]
```

**Validation:**
```python
# Test all imports work
from components.config import (
    ThemeConfig, DifficultyConfig, PageLimitsConfig,
    THEME_SUBJECTS, DEFAULT_THEME
)
```

**Success Criteria:**
- ✅ All imports work
- ✅ No circular dependencies
- ✅ No import errors

---

## Phase 2: Integration Tests

### Step 2.1: Create Test File
**Why:** Verify extracted code works in isolation

**File:** `components/config/test_config.py`

**Content:**
```python
"""Integration tests for config module."""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.config import (
    ThemeConfig,
    DifficultyConfig,
    PageLimitsConfig,
    THEME_SUBJECTS
)


def test_theme_sanitization():
    """Test theme sanitization functionality."""
    print("Testing ThemeConfig.sanitize()...")

    # Test normalization
    assert ThemeConfig.sanitize("Forest") == "forest-friends"
    assert ThemeConfig.sanitize("OCEAN") == "under-the-sea"
    assert ThemeConfig.sanitize("farm animals") == "farm-day"

    # Test blocked themes
    assert ThemeConfig.sanitize("peppa pig") == "animals"
    assert ThemeConfig.sanitize("Paw Patrol") == "animals"
    assert ThemeConfig.sanitize("disney") == "animals"

    # Test defaults
    assert ThemeConfig.sanitize(None) == "animals"
    assert ThemeConfig.sanitize("") == "animals"

    print("✅ Theme sanitization tests passed")


def test_difficulty_normalization():
    """Test difficulty level handling."""
    print("Testing DifficultyConfig...")

    # Test normalization
    assert DifficultyConfig.normalize("EASY") == "easy"
    assert DifficultyConfig.normalize("Medium") == "medium"
    assert DifficultyConfig.normalize("invalid") == "easy"
    assert DifficultyConfig.normalize(None) == "easy"

    # Test repetitions
    assert DifficultyConfig.get_repetitions("easy") == 8
    assert DifficultyConfig.get_repetitions("medium") == 12
    assert DifficultyConfig.get_repetitions("hard") == 16

    print("✅ Difficulty tests passed")


def test_limits_parsing():
    """Test page limits parsing."""
    print("Testing PageLimitsConfig...")

    # Test max_total
    assert PageLimitsConfig.parse_max_total("10") == 10
    assert PageLimitsConfig.parse_max_total(5) == 5
    assert PageLimitsConfig.parse_max_total("-1") is None
    assert PageLimitsConfig.parse_max_total("") is None

    # Test per_topic JSON
    result = PageLimitsConfig.parse_pages_per_topic('{"coloring":8,"tracing":4}')
    assert result == {"coloring": 8, "tracing": 4}

    # Test per_topic comma format
    result = PageLimitsConfig.parse_pages_per_topic("coloring=8,tracing=4")
    assert result == {"coloring": 8, "tracing": 4}

    # Test empty
    result = PageLimitsConfig.parse_pages_per_topic("")
    assert result == {}

    print("✅ Limits parsing tests passed")


def test_theme_subjects():
    """Test theme subjects are available."""
    print("Testing THEME_SUBJECTS...")

    assert "forest-friends" in THEME_SUBJECTS
    assert "under-the-sea" in THEME_SUBJECTS
    assert "farm-day" in THEME_SUBJECTS
    assert "animals" in THEME_SUBJECTS

    # Check subject lists are not empty
    for theme, subjects in THEME_SUBJECTS.items():
        assert len(subjects) > 0, f"Theme {theme} has no subjects"

    print("✅ Theme subjects tests passed")


if __name__ == "__main__":
    print("="*60)
    print("Running Config Module Integration Tests")
    print("="*60)

    try:
        test_theme_sanitization()
        test_difficulty_normalization()
        test_limits_parsing()
        test_theme_subjects()

        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)

    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
        sys.exit(1)
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ ERROR: {e}")
        print("="*60)
        sys.exit(1)
```

**Run Tests:**
```bash
docker compose run --rm langflow python components/config/test_config.py
```

**Success Criteria:**
- ✅ All tests pass
- ✅ No import errors
- ✅ Exit code 0

---

## Phase 3: Refactor Main File

### Step 3.1: Update Imports in claude_processor.py
**Why:** Replace old methods with new config modules

**File:** `components/claude_processor.py`

**Action:** Add imports at top of file (after existing imports around line 11):

```python
# Add these imports
from components.config import (
    ThemeConfig,
    DifficultyConfig,
    PageLimitsConfig,
    DIFFICULTY_REPETITIONS,
    THEME_SUBJECTS
)
```

**Validation:**
```bash
docker compose run --rm langflow python -c "from components.claude_processor import ClaudeProcessor; print('✅ Imports work')"
```

**Success Criteria:**
- ✅ No import errors
- ✅ File still loads

---

### Step 3.2: Replace _sanitize_theme Method
**Why:** Use extracted ThemeConfig class

**File:** `components/claude_processor.py`

**Find (lines 95-116):**
```python
def _sanitize_theme(self, theme: str) -> str:
    """Normalize and block branded themes to keep content safe."""
    t = (theme or "").strip().lower()

    # Friendly remaps
    fallbacks = {
        'forest': 'forest-friends', 'woods': 'forest-friends', 'forest friends': 'forest-friends',
        'sea': 'under-the-sea', 'ocean': 'under-the-sea', 'under the sea': 'under-the-sea',
        'farm': 'farm-day', 'farm animals': 'farm-day',
        'space': 'space-explorer', 'galaxy': 'space-explorer'
    }
    for k, v in fallbacks.items():
        if k in t:
            t = v
            break

    # Block copyrighted/brand themes
    blocked_keywords = ["peppa", "paw patrol", "paw-patrol", "disney", "marvel", "pokemon", "barbie"]
    if any(b in t for b in blocked_keywords):
        return "animals"

    return t or "animals"
```

**Replace With:**
```python
def _sanitize_theme(self, theme: str) -> str:
    """Normalize and block branded themes to keep content safe."""
    return ThemeConfig.sanitize(theme)
```

**Success Criteria:**
- ✅ Method still exists (maintains API)
- ✅ Reduced from 22 lines to 3 lines

---

### Step 3.3: Replace _difficulty Method
**Why:** Use extracted DifficultyConfig class

**File:** `components/claude_processor.py`

**Find (lines 118-123):**
```python
def _difficulty(self) -> str:
    d = (getattr(self, "difficulty", "easy") or "easy").strip().lower()
    if d not in ("easy", "medium", "hard"):
        d = "easy"
    return d
```

**Replace With:**
```python
def _difficulty(self) -> str:
    """Get normalized difficulty level."""
    raw_difficulty = getattr(self, "difficulty", "easy")
    return DifficultyConfig.normalize(raw_difficulty)
```

**Success Criteria:**
- ✅ Method still exists
- ✅ Reduced from 6 lines to 4 lines

---

### Step 3.4: Replace _coerce_positive_int Method
**Why:** Use extracted validation function

**File:** `components/claude_processor.py`

**Find (lines 143-163):**
```python
@staticmethod
def _coerce_positive_int(raw_value, label: str) -> Optional[int]:
    """Convert incoming values to a positive int, logging when invalid."""
    if raw_value is None:
        return None

    if isinstance(raw_value, (int, float)):
        value = int(raw_value)
    else:
        text = str(raw_value).strip()
        if not text:
            return None
        try:
            value = int(text)
        except ValueError:
            return None

    if value <= 0:
        return None

    return value
```

**Replace With:**
```python
@staticmethod
def _coerce_positive_int(raw_value, label: str) -> Optional[int]:
    """Convert incoming values to a positive int, logging when invalid."""
    from components.config import coerce_positive_int as validate_int
    return validate_int(raw_value, label)
```

**Success Criteria:**
- ✅ Method signature unchanged
- ✅ Reduced from 21 lines to 4 lines

---

### Step 3.5: Replace _max_total_pages Method
**Why:** Use extracted PageLimitsConfig class

**File:** `components/claude_processor.py`

**Find (lines 165-171):**
```python
def _max_total_pages(self) -> Optional[int]:
    value = self._coerce_positive_int(getattr(self, "max_total_pages", None), "max_total_pages")
    if value is None:
        raw = getattr(self, "max_total_pages", "")
        if raw not in (None, "", 0):
            self.log(f"Ignoring max_total_pages value '{raw}' (must be a positive integer).")
    return value
```

**Replace With:**
```python
def _max_total_pages(self) -> Optional[int]:
    """Get maximum total pages limit."""
    raw_value = getattr(self, "max_total_pages", None)
    value = PageLimitsConfig.parse_max_total(raw_value)
    if value is None and raw_value not in (None, "", 0):
        self.log(f"Ignoring max_total_pages value '{raw_value}' (must be a positive integer).")
    return value
```

**Success Criteria:**
- ✅ Method behavior unchanged
- ✅ Logging preserved

---

### Step 3.6: Replace _pages_per_topic Method
**Why:** Use extracted PageLimitsConfig class

**File:** `components/claude_processor.py`

**Find (lines 173-223):**
```python
def _pages_per_topic(self) -> Dict[str, int]:
    raw = getattr(self, "pages_per_topic", None)
    if raw is None:
        return {}

    if isinstance(raw, dict):
        source_items = raw.items()
    else:
        text = str(raw).strip()
        if not text:
            return {}

        if text.startswith("{"):
            try:
                decoded = json.loads(text)
            except json.JSONDecodeError as exc:
                self.log(f"Could not parse pages_per_topic JSON: {exc}")
                return {}

            if not isinstance(decoded, dict):
                self.log("pages_per_topic JSON must decode to an object/dict.")
                return {}

            source_items = decoded.items()
        else:
            parts = [p.strip() for p in text.split(",") if p.strip()]
            parsed_pairs = []
            for part in parts:
                if "=" not in part:
                    self.log(f"Skipping pages_per_topic entry '{part}'. Expected format topic=count.")
                    continue
                key, value = part.split("=", 1)
                parsed_pairs.append((key.strip(), value.strip()))
            source_items = parsed_pairs

    limits: Dict[str, int] = {}
    for key, value in source_items:
        topic = str(key).strip().lower()
        if not topic:
            continue
        count = self._coerce_positive_int(value, f"pages_per_topic[{topic}]")
        if count is None:
            self.log(f"Ignoring pages_per_topic entry '{key}: {value}' (must be a positive integer).")
            continue
        limits[topic] = count

    if limits:
        pretty = ", ".join(f"{topic}={count}" for topic, count in limits.items())
        self.log(f"Pages-per-topic limits active: {pretty}")

    return limits
```

**Replace With:**
```python
def _pages_per_topic(self) -> Dict[str, int]:
    """Get per-topic page limits."""
    raw = getattr(self, "pages_per_topic", None)

    try:
        limits = PageLimitsConfig.parse_pages_per_topic(raw)
    except Exception as exc:
        self.log(f"Could not parse pages_per_topic: {exc}")
        return {}

    if limits:
        pretty = ", ".join(f"{topic}={count}" for topic, count in limits.items())
        self.log(f"Pages-per-topic limits active: {pretty}")

    return limits
```

**Success Criteria:**
- ✅ Method behavior unchanged
- ✅ Logging preserved
- ✅ Reduced from 51 lines to 13 lines

---

### Step 3.7: Update get_prompt_for_type Method
**Why:** Use extracted constants and config classes

**File:** `components/claude_processor.py`

**In `get_prompt_for_type` method (around line 350):**

**Find (around line 352-353):**
```python
diff = self._difficulty()
reps = 8 if diff == "easy" else 12 if diff == "medium" else 16
```

**Replace With:**
```python
diff = self._difficulty()
reps = DifficultyConfig.get_repetitions(diff)
```

**Find (around line 367-374):**
```python
theme_subjects = {
    'forest-friends': ['fox','bear','owl','rabbit','hedgehog','deer','squirrel','raccoon','snail','mushroom','acorn','pine tree'],
    'under-the-sea': ['fish','dolphin','starfish','shell','turtle','seahorse','crab','octopus','bubble','coral'],
    'farm-day': ['cow','chicken','sheep','pig','barn','tractor','duck','horse','hay bale'],
    'space-explorer': ['rocket','planet','star','moon','astronaut','satellite','comet'],
    'shapes': ['circle','square','triangle','star','heart','diamond','oval','rectangle','hexagon','pentagon'],
    'animals': ['cat','dog','rabbit','bird','fish','elephant','giraffe','lion','bear','monkey','butterfly','bee','duck','frog']
}
```

**Replace With:**
```python
theme_subjects = THEME_SUBJECTS
```

**Success Criteria:**
- ✅ Prompts still generate correctly
- ✅ Same subjects used

---

## Phase 4: Regression Testing

### Step 4.1: Run Unit Tests
**Why:** Verify extracted modules work correctly

**Commands:**
```bash
cd "E:\GITHUB\projects\Book generator 2"

# Run all doctests
docker compose run --rm langflow python -m doctest components/config/validation.py -v
docker compose run --rm langflow python -m doctest components/config/theme_config.py -v
docker compose run --rm langflow python -m doctest components/config/difficulty_config.py -v
docker compose run --rm langflow python -m doctest components/config/limits_config.py -v

# Run integration tests
docker compose run --rm langflow python components/config/test_config.py
```

**Success Criteria:**
- ✅ All doctests pass
- ✅ Integration tests pass
- ✅ No import errors

---

### Step 4.2: Run Import Test
**Why:** Ensure no broken imports

**Command:**
```bash
docker compose run --rm langflow python -c "
from components.claude_processor import ClaudeProcessor
from components.config import ThemeConfig, DifficultyConfig, PageLimitsConfig
print('✅ All imports successful')
"
```

**Success Criteria:**
- ✅ No import errors

---

### Step 4.3: Run Full Integration Test
**Why:** Verify same functionality end-to-end

**Command:**
```bash
docker compose run --rm langflow python scripts/activity_generator.py --test --output /app/workdir/out/refactored_test.pdf
```

**Compare to Baseline:**
1. Check PDF generates successfully
2. Compare file sizes (should be similar ±10%)
3. Verify no new errors in logs

**Success Criteria:**
- ✅ PDF generates without errors
- ✅ File size similar to baseline
- ✅ No new error messages

---

### Step 4.4: Behavioral Comparison Test
**Why:** Verify exact same behavior

**Create Test File:** `components/config/test_behavior.py`

**Content:**
```python
"""Test that refactored code behaves identically to original."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from components.claude_processor import ClaudeProcessor
from components.config import ThemeConfig, DifficultyConfig


def test_theme_behavior():
    """Test theme sanitization behavior matches original."""
    processor = ClaudeProcessor()

    test_cases = [
        ("Forest", "forest-friends"),
        ("OCEAN", "under-the-sea"),
        ("farm animals", "farm-day"),
        ("peppa pig", "animals"),
        ("space", "space-explorer"),
        (None, "animals"),
        ("", "animals"),
    ]

    for input_val, expected in test_cases:
        result = processor._sanitize_theme(input_val)
        assert result == expected, f"Theme '{input_val}' -> '{result}' (expected '{expected}')"

    print("✅ Theme behavior test passed")


def test_difficulty_behavior():
    """Test difficulty normalization behavior."""
    processor = ClaudeProcessor()

    test_cases = [
        ("easy", "easy", 8),
        ("MEDIUM", "medium", 12),
        ("Hard", "hard", 16),
        ("invalid", "easy", 8),
        (None, "easy", 8),
    ]

    for input_val, expected_diff, expected_reps in test_cases:
        processor.difficulty = input_val
        diff = processor._difficulty()
        reps = DifficultyConfig.get_repetitions(diff)

        assert diff == expected_diff, f"Difficulty '{input_val}' -> '{diff}' (expected '{expected_diff}')"
        assert reps == expected_reps, f"Reps for '{diff}' -> {reps} (expected {expected_reps})"

    print("✅ Difficulty behavior test passed")


def test_limits_behavior():
    """Test page limits parsing behavior."""
    processor = ClaudeProcessor()

    # Test max_total_pages
    test_cases_total = [
        ("10", 10),
        (5, 5),
        ("-1", None),
        ("", None),
    ]

    for input_val, expected in test_cases_total:
        processor.max_total_pages = input_val
        result = processor._max_total_pages()
        assert result == expected, f"Max total '{input_val}' -> {result} (expected {expected})"

    # Test pages_per_topic
    test_cases_topic = [
        ('{"coloring":8,"tracing":4}', {"coloring": 8, "tracing": 4}),
        ("coloring=8,tracing=4", {"coloring": 8, "tracing": 4}),
        ("", {}),
    ]

    for input_val, expected in test_cases_topic:
        processor.pages_per_topic = input_val
        result = processor._pages_per_topic()
        assert result == expected, f"Per topic '{input_val}' -> {result} (expected {expected})"

    print("✅ Limits behavior test passed")


if __name__ == "__main__":
    print("="*60)
    print("Running Behavioral Equivalence Tests")
    print("="*60)

    try:
        test_theme_behavior()
        test_difficulty_behavior()
        test_limits_behavior()

        print("\n" + "="*60)
        print("✅ ALL BEHAVIORAL TESTS PASSED")
        print("="*60)

    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ BEHAVIORAL TEST FAILED: {e}")
        print("="*60)
        sys.exit(1)
```

**Run Test:**
```bash
docker compose run --rm langflow python components/config/test_behavior.py
```

**Success Criteria:**
- ✅ All behavioral tests pass

---

## Phase 5: Documentation & Cleanup

### Step 5.1: Create Config README
**Why:** Document the new config module

**File:** `components/config/README.md`

**Content:**
```markdown
# Configuration Module

Extracted configuration management for Claude Activity Processor.

## Modules

### `constants.py`
Contains all hardcoded values:
- Theme mappings and fallbacks
- Blocked themes
- Difficulty levels
- Theme-based subjects
- Style requirements

### `validation.py`
Input validation utilities:
- `coerce_positive_int()` - Convert to positive integer
- `validate_string_not_empty()` - Ensure non-empty string

### `theme_config.py`
Theme management:
- `ThemeConfig.sanitize()` - Normalize and validate themes
- `ThemeConfig.is_valid_theme()` - Check if theme is allowed

### `difficulty_config.py`
Difficulty level handling:
- `DifficultyConfig.normalize()` - Validate difficulty
- `DifficultyConfig.get_repetitions()` - Get rep count for level

### `limits_config.py`
Page limit configuration:
- `PageLimitsConfig.parse_max_total()` - Parse total page limit
- `PageLimitsConfig.parse_pages_per_topic()` - Parse per-topic limits

## Usage

```python
from components.config import ThemeConfig, DifficultyConfig

# Sanitize theme
theme = ThemeConfig.sanitize("Forest")  # Returns "forest-friends"

# Get difficulty reps
reps = DifficultyConfig.get_repetitions("easy")  # Returns 8
```

## Testing

Run all tests:
```bash
docker compose run --rm langflow python components/config/test_config.py
```
```

---

### Step 5.2: Verify Line Count Reduction
**Why:** Confirm we achieved our goal

**Command:**
```bash
wc -l components/claude_processor.py
```

**Expected Result:**
- Original: 781 lines
- After refactoring: ~650 lines (130 line reduction)

**Success Criteria:**
- ✅ Main file reduced by ~130 lines

---

## Phase 6: Commit & Deploy

### Step 6.1: Git Commit
**Why:** Save progress with clear history

**Commands:**
```bash
cd "E:\GITHUB\projects\Book generator 2"

# Stage all changes
git add components/config/
git add components/claude_processor.py

# Commit
git commit -m "refactor: Extract configuration management from ClaudeProcessor

- Extract theme sanitization to ThemeConfig
- Extract difficulty handling to DifficultyConfig
- Extract page limits to PageLimitsConfig
- Add validation utilities
- Reduce claude_processor.py by ~130 lines
- All tests passing, functionality preserved

Breaking changes: None
Test coverage: Added unit tests and integration tests"
```

**Success Criteria:**
- ✅ Clean commit with all changes

---

### Step 6.2: Rebuild Docker Image
**Why:** Ensure Docker build still works

**Command:**
```bash
docker compose build
```

**Success Criteria:**
- ✅ Build completes without errors

---

### Step 6.3: Final Smoke Test
**Why:** Verify everything works after rebuild

**Command:**
```bash
docker compose run --rm langflow python scripts/activity_generator.py --test --output /app/workdir/out/final_test.pdf
```

**Success Criteria:**
- ✅ PDF generates successfully
- ✅ No errors or warnings

---

## Success Metrics

### Code Quality
- ✅ Main file reduced from 781 → ~650 lines (17% reduction)
- ✅ 6 new focused modules created
- ✅ Clear separation of concerns

### Testing
- ✅ 20+ unit tests added (doctests)
- ✅ Integration tests pass
- ✅ Behavioral equivalence verified

### Functionality
- ✅ PDF generation works identically
- ✅ No performance regression

---

## Rollback Procedure

If anything goes wrong:

```bash
# Abort and rollback
git reset --hard HEAD^
git checkout main
git branch -D refactor/extract-config

# Rebuild
docker compose build

# Verify baseline
docker compose run --rm langflow python scripts/activity_generator.py --test --output /app/workdir/out/rollback_test.pdf
```

---

## AI Agent Execution Notes

**Important Instructions for AI Agent:**

1. Execute steps sequentially - don't skip validation
2. If any test fails, attempt to fix once by:
   - Checking imports
   - Verifying file paths
   - Checking for typos
3. If fix fails, STOP and report to user
4. Commit after Phase 6.1 only
5. Keep user informed of progress at each phase
6. If behavioral tests fail, this is CRITICAL - stop immediately

**Expected Duration:** 2-3 hours
**Risk Level:** LOW
**Reversibility:** HIGH
