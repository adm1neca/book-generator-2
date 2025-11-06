"""Integration tests for config module.

Testing Strategy:
- Black box testing (test public API only)
- Test expected behavior, not implementation
- Validate edge cases
- Ensure backward compatibility
"""

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
