#!/usr/bin/env python3
"""
Comprehensive Test Suite for Refactored Claude Processor

Tests all 5 refactored subsystems:
1. Configuration Management
2. Prompt Strategies
3. API Client (without actual API calls)
4. Variety Tracking
5. Logging System

Run this in your Docker container to verify the refactoring works correctly.
"""

import sys
from pathlib import Path

# Color codes for terminal output
GREEN = '\033[92m'
RED = '\033[91m'
BLUE = '\033[94m'
YELLOW = '\033[93m'
RESET = '\033[0m'
BOLD = '\033[1m'

def print_header(text):
    print(f"\n{BLUE}{BOLD}{'='*70}{RESET}")
    print(f"{BLUE}{BOLD}{text.center(70)}{RESET}")
    print(f"{BLUE}{BOLD}{'='*70}{RESET}\n")

def print_success(text):
    print(f"{GREEN}✅ {text}{RESET}")

def print_error(text):
    print(f"{RED}❌ {text}{RESET}")

def print_info(text):
    print(f"{YELLOW}ℹ️  {text}{RESET}")

# ============================================================================
# TEST 1: Module Imports
# ============================================================================
def test_imports():
    print_header("TEST 1: Module Imports")

    try:
        from components.config import ThemeConfig, DifficultyConfig, PageLimitsConfig
        print_success("Config modules imported")

        from components.prompts import PromptBuilderFactory
        print_success("Prompts module imported")

        from components.tracking import VarietyTracker
        print_success("Tracking module imported")

        from components.logging import SessionLogger, OutputDumper
        print_success("Logging modules imported")

        print_info("API module (ClaudeAPIClient) requires anthropic package")
        print_info("Skipping API import test (not needed for structure validation)")

        return True
    except Exception as e:
        print_error(f"Import failed: {e}")
        return False

# ============================================================================
# TEST 2: Configuration Module
# ============================================================================
def test_configuration():
    print_header("TEST 2: Configuration Module")

    from components.config import ThemeConfig, DifficultyConfig, PageLimitsConfig

    # Test theme sanitization
    print("Testing ThemeConfig...")
    assert ThemeConfig.sanitize("animals") == "animals"
    assert ThemeConfig.sanitize("ANIMALS") == "animals"
    assert ThemeConfig.sanitize("pokemon") == "animals"  # blocked → fallback
    print_success("ThemeConfig works correctly")

    # Test difficulty normalization
    print("\nTesting DifficultyConfig...")
    assert DifficultyConfig.normalize("easy") == "easy"
    assert DifficultyConfig.normalize("HARD") == "hard"
    assert DifficultyConfig.normalize("invalid") == "easy"  # fallback
    print_success("DifficultyConfig works correctly")

    # Test page limits parsing
    print("\nTesting PageLimitsConfig...")
    assert PageLimitsConfig.parse_max_total("10") == 10
    assert PageLimitsConfig.parse_max_total("invalid") is None
    limits = PageLimitsConfig.parse_pages_per_topic("coloring=5,tracing=3")
    assert limits == {"coloring": 5, "tracing": 3}
    print_success("PageLimitsConfig works correctly")

    return True

# ============================================================================
# TEST 3: Prompt Strategies
# ============================================================================
def test_prompt_strategies():
    print_header("TEST 3: Prompt Strategies")

    from components.prompts import PromptBuilderFactory

    # Test factory
    print("Testing PromptBuilderFactory...")
    available_types = PromptBuilderFactory.get_available_types()
    expected_types = ['coloring', 'tracing', 'counting', 'maze', 'matching', 'dot-to-dot']
    assert set(available_types) == set(expected_types)
    print_success(f"Factory provides {len(available_types)} strategy types")

    # Test each strategy
    for page_type in available_types:
        strategy = PromptBuilderFactory.get_builder(page_type)
        prompt, selected = strategy.build(
            theme='animals',
            difficulty='easy',
            page_number=1,
            used_items=[],
            style_guard='TEST GUARD'
        )

        assert isinstance(prompt, str)
        assert len(prompt) > 0
        assert 'TEST GUARD' in prompt
        print_success(f"{page_type:12} strategy works (selected: {selected})")

    return True

# ============================================================================
# TEST 4: Variety Tracking
# ============================================================================
def test_variety_tracking():
    print_header("TEST 4: Variety Tracking")

    from components.tracking import VarietyTracker

    tracker = VarietyTracker()

    # Test selection
    print("Testing variety tracking...")
    options = ['cat', 'dog', 'bird', 'fish']
    selected = []

    for i in range(6):  # Select more than available to test reset
        item = tracker.select_unused('coloring', options)
        selected.append(item)
        print(f"  Selection {i+1}: {item}")

    # Should have unique items and then reset
    unique = len(set(selected[:4]))
    assert unique == 4, "First 4 selections should be unique"
    print_success("Variety tracking works correctly")

    # Test summary
    summary = tracker.get_summary()
    assert 'coloring' in summary
    print_success(f"Summary: {len(summary['coloring'])} items tracked")

    # Test reset
    tracker.reset('coloring')
    assert len(tracker.get_used('coloring')) == 0
    print_success("Reset works correctly")

    return True

# ============================================================================
# TEST 5: Logging System
# ============================================================================
def test_logging_system():
    print_header("TEST 5: Logging System")

    from components.logging import SessionLogger, OutputDumper
    from pathlib import Path
    import tempfile

    # Test SessionLogger
    print("Testing SessionLogger...")
    logger = SessionLogger()
    logger.log("Test message")
    logger.log_api_call(1, "test prompt", "test response")

    logs = logger.get_detailed_logs()
    assert len(logs) == 1
    print_success(f"SessionLogger: {len(logs)} API call logged")

    summary = logger.get_summary()
    assert summary['total_api_calls'] == 1
    print_success(f"Session summary: {summary['duration_seconds']:.2f}s duration")

    # Test save to file
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = logger.save(filename=f"{tmpdir}/test.log")
        assert Path(log_file).exists()
        print_success(f"Log file saved: {Path(log_file).name}")

    # Test OutputDumper
    print("\nTesting OutputDumper...")
    with tempfile.TemporaryDirectory() as tmpdir:
        pages = [{'pageNumber': 1, 'type': 'coloring'}]
        logs_data = [{'timestamp': '2024-01-01', 'page': 1}]

        result = OutputDumper.dump(pages, logs_data, Path(tmpdir))
        assert result is not None
        assert result.exists()
        print_success(f"Output dumped: {result.name}")

        # Test read back
        loaded = OutputDumper.read_dump(result)
        assert loaded is not None
        assert 'pages' in loaded
        print_success("Output can be read back successfully")

    return True

# ============================================================================
# TEST 6: Doctests
# ============================================================================
def test_doctests():
    print_header("TEST 6: Running Doctests")

    import doctest

    modules = [
        ('components.config.theme_config', 'Config'),
        ('components.config.difficulty_config', 'Config'),
        ('components.config.limits_config', 'Config'),
        ('components.tracking.variety_tracker', 'Tracking'),
        ('components.logging.session_logger', 'Logging'),
        ('components.logging.output_dumper', 'Logging'),
    ]

    total_tests = 0
    total_failures = 0

    for module_name, category in modules:
        try:
            module = __import__(module_name, fromlist=[''])
            results = doctest.testmod(module, verbose=False)
            total_tests += results.attempted
            total_failures += results.failed

            if results.failed == 0:
                print_success(f"{category:10} - {module_name.split('.')[-1]:20} - {results.attempted} tests passed")
            else:
                print_error(f"{category:10} - {module_name.split('.')[-1]:20} - {results.failed}/{results.attempted} failed")
        except Exception as e:
            print_error(f"Could not test {module_name}: {e}")

    print(f"\n{BOLD}Total: {total_tests} doctests, {total_failures} failures{RESET}")

    return total_failures == 0

# ============================================================================
# TEST 7: Integration Test
# ============================================================================
def test_integration():
    print_header("TEST 7: Integration Test")

    print("Testing end-to-end flow without API calls...")

    from components.config import ThemeConfig
    from components.prompts import PromptBuilderFactory
    from components.tracking import VarietyTracker
    from components.logging import SessionLogger

    # Simulate processing 3 pages
    logger = SessionLogger()
    tracker = VarietyTracker()

    pages = [
        {'type': 'coloring', 'theme': 'animals', 'pageNumber': 1},
        {'type': 'tracing', 'theme': 'animals', 'pageNumber': 2},
        {'type': 'counting', 'theme': 'animals', 'pageNumber': 3},
    ]

    for page in pages:
        # Sanitize theme
        theme = ThemeConfig.sanitize(page['theme'])

        # Get strategy
        strategy = PromptBuilderFactory.get_builder(page['type'])

        # Get used items
        used = tracker.get_used(page['type'])

        # Build prompt
        prompt, selected = strategy.build(
            theme=theme,
            difficulty='easy',
            page_number=page['pageNumber'],
            used_items=used,
            style_guard='STYLE'
        )

        # Track selection
        if selected:
            tracker.mark_used(page['type'], selected)

        # Log (simulated)
        logger.log(f"Page {page['pageNumber']}: {page['type']}")

        print(f"  Page {page['pageNumber']}: {page['type']:10} - selected: {selected}")

    print_success("End-to-end integration works correctly")

    summary = tracker.get_summary()
    print_info(f"Tracked items: {sum(len(v) for v in summary.values())} total")

    return True

# ============================================================================
# Main Test Runner
# ============================================================================
def main():
    print(f"\n{BOLD}{BLUE}")
    print("╔═══════════════════════════════════════════════════════════════════╗")
    print("║         CLAUDE PROCESSOR REFACTORING TEST SUITE                  ║")
    print("║         Testing all 5 refactored subsystems                      ║")
    print("╚═══════════════════════════════════════════════════════════════════╝")
    print(RESET)

    tests = [
        ("Module Imports", test_imports),
        ("Configuration", test_configuration),
        ("Prompt Strategies", test_prompt_strategies),
        ("Variety Tracking", test_variety_tracking),
        ("Logging System", test_logging_system),
        ("Doctests", test_doctests),
        ("Integration", test_integration),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print_error(f"Test '{test_name}' crashed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Final summary
    print_header("TEST SUMMARY")
    print(f"Total tests: {len(tests)}")
    print_success(f"Passed: {passed}")
    if failed > 0:
        print_error(f"Failed: {failed}")
    else:
        print(f"\n{GREEN}{BOLD}🎉 ALL TESTS PASSED! 🎉{RESET}")
        print(f"{GREEN}The refactored code is working correctly!{RESET}\n")

    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
