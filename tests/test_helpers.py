#!/usr/bin/env python3
"""Unit tests for refactored helper classes.

Tests the new typed helper system:
- RenderContext
- Primitives
- LayoutHelpers
- constants module
"""

import math
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from scripts.helpers import RenderContext, Primitives, LayoutHelpers, GridConfig, constants


# ===================================================================
# TESTS FOR constants MODULE
# ===================================================================
def test_constants_defined():
    """Test that all expected constants are defined."""
    # Colors
    assert hasattr(constants, 'COLOR_BORDER')
    assert hasattr(constants, 'COLOR_TITLE')
    assert constants.COLOR_BORDER == "#FF69B4"
    assert constants.COLOR_TITLE == "#4A90E2"

    # Spacing
    assert hasattr(constants, 'GRID_SPACING_SMALL')
    assert hasattr(constants, 'GRID_SPACING_LARGE')
    assert constants.GRID_SPACING_SMALL == 60
    assert constants.GRID_SPACING_LARGE == 110

    # Offsets
    assert hasattr(constants, 'OFFSET_TITLE')
    assert hasattr(constants, 'OFFSET_INSTRUCTION')
    assert constants.OFFSET_TITLE == 50
    assert constants.OFFSET_INSTRUCTION == 80

    # Typography
    assert hasattr(constants, 'FONT_SIZE_TITLE')
    assert hasattr(constants, 'FONT_FAMILY_TITLE')
    assert constants.FONT_SIZE_TITLE == 24

    print("✓ All constants are defined correctly")
    return True


# ===================================================================
# TESTS FOR RenderContext
# ===================================================================
def test_render_context_properties():
    """Test RenderContext properties."""

    # Mock functions
    def mock_draw_border(): pass
    def mock_draw_title(t, o): pass
    def mock_draw_instruction(i, o): pass
    def mock_prep_kid_lines(): pass
    def mock_generate_dots(s, n): return []
    def mock_asset_lookup(n): return None

    class MockCanvas:
        pass

    ctx = RenderContext(
        canvas=MockCanvas(),
        width=595.0,
        height=842.0,
        margin=50.0,
        draw_border=mock_draw_border,
        draw_title=mock_draw_title,
        draw_instruction=mock_draw_instruction,
        prep_kid_lines=mock_prep_kid_lines,
        kid_stroke_width=4,
        generate_dot_positions=mock_generate_dots,
        asset_lookup=mock_asset_lookup,
    )

    # Test basic properties
    assert ctx.width == 595.0
    assert ctx.height == 842.0
    assert ctx.margin == 50.0
    assert ctx.kid_stroke_width == 4

    # Test computed properties
    assert ctx.center_x == 595.0 / 2
    assert ctx.center_y == 842.0 / 2
    assert ctx.content_width == 595.0 - (2 * 50.0)
    assert ctx.content_height == 842.0 - (2 * 50.0)

    print("✓ RenderContext properties work correctly")
    return True


# ===================================================================
# TESTS FOR LayoutHelpers
# ===================================================================
def test_layout_grid_positions():
    """Test LayoutHelpers.calculate_grid_positions."""
    config = GridConfig(
        item_count=6,
        spacing=60,
        max_cols=3,
        start_y_offset=150,
    )

    positions = LayoutHelpers.calculate_grid_positions(
        canvas_width=595,
        canvas_height=842,
        config=config,
    )

    # Should have 6 positions
    assert len(positions) == 6

    # Check first position
    assert positions[0].row == 0
    assert positions[0].col == 0

    # Check that positions are spread in grid
    # 6 items with max 3 cols = 2 rows
    rows = {p.row for p in positions}
    cols = {p.col for p in positions}
    assert len(rows) == 2  # 2 rows
    assert len(cols) == 3  # 3 columns

    print("✓ LayoutHelpers.calculate_grid_positions works correctly")
    return True


def test_layout_two_column():
    """Test LayoutHelpers.calculate_two_column_layout."""
    left_pos, right_pos = LayoutHelpers.calculate_two_column_layout(
        canvas_width=595,
        canvas_height=842,
        item_count=4,
        spacing=110,
        start_y_offset=150,
    )

    # Should have 4 positions each
    assert len(left_pos) == 4
    assert len(right_pos) == 4

    # Left and right should be at different x positions
    assert left_pos[0][0] != right_pos[0][0]

    # Y positions should match
    assert left_pos[0][1] == right_pos[0][1]

    print("✓ LayoutHelpers.calculate_two_column_layout works correctly")
    return True


def test_layout_centering():
    """Test LayoutHelpers centering functions."""
    # Test center_x
    x = LayoutHelpers.center_x(canvas_width=600, item_width=100)
    assert x == 250  # (600 - 100) / 2

    # Test center_y
    y = LayoutHelpers.center_y(canvas_height=800, item_height=200)
    assert y == 300  # (800 - 200) / 2

    print("✓ LayoutHelpers centering functions work correctly")
    return True


def test_layout_distribution():
    """Test LayoutHelpers distribution functions."""
    # Test horizontal distribution
    x_positions = LayoutHelpers.distribute_horizontal(
        canvas_width=600,
        margin=50,
        item_count=3,
    )

    assert len(x_positions) == 3
    # All positions should be within margins
    assert all(50 <= x <= 550 for x in x_positions)

    # Test vertical distribution
    y_positions = LayoutHelpers.distribute_vertical(
        canvas_height=800,
        top_offset=100,
        bottom_offset=100,
        item_count=3,
    )

    assert len(y_positions) == 3
    # All positions should be within offsets
    assert all(100 <= y <= 700 for y in y_positions)

    print("✓ LayoutHelpers distribution functions work correctly")
    return True


# ===================================================================
# TESTS FOR Primitives
# ===================================================================
def test_primitives_dot_positions():
    """Test Primitives dot position generators."""

    # Test star dots
    star_dots = Primitives.generate_dot_positions_star(
        center_x=300,
        center_y=400,
        num_dots=10,
    )
    assert len(star_dots) == 10

    # Test circle dots
    circle_dots = Primitives.generate_dot_positions_circle(
        center_x=300,
        center_y=400,
        num_dots=12,
    )
    assert len(circle_dots) == 12

    # Test heart dots
    heart_dots = Primitives.generate_dot_positions_heart(
        center_x=300,
        center_y=400,
        num_dots=15,
    )
    assert len(heart_dots) == 15

    print("✓ Primitives dot position generators work correctly")
    return True


def test_primitives_shape_consistency():
    """Test that primitives use consistent APIs."""
    # All shape drawing functions should exist
    assert hasattr(Primitives, 'draw_star')
    assert hasattr(Primitives, 'draw_heart')
    assert hasattr(Primitives, 'draw_circle')
    assert hasattr(Primitives, 'draw_square')

    # All should be static methods
    assert callable(Primitives.draw_star)
    assert callable(Primitives.draw_heart)
    assert callable(Primitives.draw_circle)
    assert callable(Primitives.draw_square)

    print("✓ Primitives have consistent API")
    return True


# ===================================================================
# INTEGRATION TESTS
# ===================================================================
def test_integration_grid_with_constants():
    """Test using LayoutHelpers with constants."""
    config = GridConfig(
        item_count=5,
        spacing=constants.GRID_SPACING_SMALL,
        max_cols=constants.MAX_GRID_COLS,
        start_y_offset=constants.OFFSET_CONTENT_START_COUNTING,
    )

    positions = LayoutHelpers.calculate_grid_positions(
        canvas_width=595,
        canvas_height=842,
        config=config,
    )

    assert len(positions) == 5

    print("✓ Integration of LayoutHelpers with constants works")
    return True


# ===================================================================
# MAIN TEST RUNNER
# ===================================================================
def main():
    print("\n" + "="*70)
    print("HELPER CLASSES UNIT TESTS")
    print("="*70 + "\n")

    tests = [
        ("constants module", test_constants_defined),
        ("RenderContext properties", test_render_context_properties),
        ("LayoutHelpers grid positions", test_layout_grid_positions),
        ("LayoutHelpers two-column", test_layout_two_column),
        ("LayoutHelpers centering", test_layout_centering),
        ("LayoutHelpers distribution", test_layout_distribution),
        ("Primitives dot positions", test_primitives_dot_positions),
        ("Primitives shape consistency", test_primitives_shape_consistency),
        ("Integration test", test_integration_grid_with_constants),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            print(f"\nTesting: {test_name}")
            if test_func():
                passed += 1
            else:
                print(f"✗ FAILED: {test_name}")
                failed += 1
        except Exception as e:
            print(f"✗ CRASHED: {test_name}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if failed == 0:
        print("\n🎉 ALL UNIT TESTS PASSED! 🎉\n")
        return 0
    else:
        print(f"\n❌ {failed} test(s) failed\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
