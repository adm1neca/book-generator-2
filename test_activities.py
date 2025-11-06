#!/usr/bin/env python3
"""Test script for individual activity page renderers.

This script allows you to test each activity type independently
and generate sample PDFs for verification.

Usage:
    python test_activities.py --all                    # Test all activities
    python test_activities.py --activity matching      # Test specific activity
    python test_activities.py --activity maze --debug  # Test with debug logging
"""

import argparse
import logging
import sys
from pathlib import Path

from reportlab.pdfgen.canvas import Canvas
from reportlab.lib.pagesizes import letter

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from scripts.pages import matching, maze, dot_to_dot, tracing


# Configure logging
def setup_logging(debug: bool = False):
    """Setup logging configuration."""
    level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )


# Helper functions that mimic the actual generator helpers
def create_helpers(width: float, height: float, margin: float = 50):
    """Create helper functions for renderers."""

    def draw_border():
        """Draw page border."""
        c = helpers["canvas"]
        c.rect(margin, margin, width - 2 * margin, height - 2 * margin)

    def draw_title(title: str):
        """Draw page title."""
        c = helpers["canvas"]
        c.setFont("Helvetica-Bold", 24)
        c.drawCentredString(width / 2, height - 70, title)

    def draw_instruction(instruction: str):
        """Draw instruction text."""
        c = helpers["canvas"]
        c.setFont("Helvetica", 14)
        c.drawCentredString(width / 2, height - 100, instruction)

    def kid_stroke():
        """Return kid-friendly stroke width."""
        return 4

    def generate_dot_positions(shape: str, num_dots: int):
        """Generate dot positions for dot-to-dot activity."""
        import math
        center_x, center_y = width / 2, height / 2
        positions = []

        if shape == "star":
            outer_radius = 110
            inner_radius = 60
            for i in range(num_dots):
                angle = math.pi / 2 + i * 2 * math.pi / num_dots
                radius = outer_radius if i % 2 == 0 else inner_radius
                x = center_x + radius * math.cos(angle)
                y = center_y - radius * math.sin(angle)
                positions.append((x, y))
        elif shape == "circle":
            radius = 110
            for i in range(num_dots):
                angle = i * 2 * math.pi / num_dots
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                positions.append((x, y))
        elif shape == "heart":
            for i in range(num_dots):
                t = i * 2 * math.pi / num_dots
                x = center_x + 16 * math.pow(math.sin(t), 3) * 5
                y = center_y + (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) * 5
                positions.append((x, y))
        else:
            # Default to circle
            radius = 110
            for i in range(num_dots):
                angle = i * 2 * math.pi / num_dots
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                positions.append((x, y))

        return positions

    helpers = {
        "width": width,
        "height": height,
        "margin": margin,
        "canvas": None,  # Will be set later
        "draw_border": draw_border,
        "draw_title": draw_title,
        "draw_instruction": draw_instruction,
        "kid_stroke": kid_stroke,
        "generate_dot_positions": generate_dot_positions,
    }

    return helpers


# Sample page specifications for testing
SAMPLE_PAGES = {
    "matching": {
        "title": "Test Match the Pairs",
        "type": "matching",
        "pairs": [
            [{"type": "shape", "shape": "star"}, {"type": "shape", "shape": "star"}],
            [{"type": "shape", "shape": "heart"}, {"type": "shape", "shape": "heart"}],
            [{"type": "shape", "shape": "circle"}, {"type": "shape", "shape": "circle"}],
            ["apple", "apple"],
        ]
    },
    "maze": {
        "title": "Test Maze Easy",
        "type": "maze",
        "difficulty": "easy"
    },
    "maze_medium": {
        "title": "Test Maze Medium",
        "type": "maze",
        "difficulty": "medium"
    },
    "maze_hard": {
        "title": "Test Maze Hard",
        "type": "maze",
        "difficulty": "hard"
    },
    "dot_to_dot": {
        "title": "Test Connect the Dots",
        "type": "dot-to-dot",
        "shape": "star",
        "dots": 12
    },
    "dot_to_dot_heart": {
        "title": "Test Connect the Dots (Heart)",
        "type": "dot-to-dot",
        "shape": "heart",
        "dots": 15
    },
    "tracing": {
        "title": "Test Tracing Letter A",
        "type": "tracing",
        "content": "A",
        "repetitions": 9
    },
    "tracing_number": {
        "title": "Test Tracing Number 5",
        "type": "tracing",
        "content": "5",
        "repetitions": 9
    },
    "tracing_shape": {
        "title": "Test Tracing Circle",
        "type": "tracing",
        "content": "circle",
        "repetitions": 6
    }
}


def render_activity_page(activity_type: str, page_spec: dict, output_path: Path):
    """Render a single activity page to PDF."""
    logger = logging.getLogger(__name__)
    logger.info(f"Rendering {activity_type} activity to {output_path}")

    # Create PDF canvas
    width, height = letter
    c = Canvas(str(output_path), pagesize=letter)

    # Create helpers
    helpers = create_helpers(width, height)
    helpers["canvas"] = c

    # Render based on activity type
    try:
        if activity_type == "matching":
            matching.render(c, page_spec, helpers)
        elif activity_type == "maze":
            maze.render(c, page_spec, helpers)
        elif activity_type == "dot-to-dot":
            dot_to_dot.render(c, page_spec, helpers)
        elif activity_type == "tracing":
            tracing.render(c, page_spec, helpers)
        else:
            logger.error(f"Unknown activity type: {activity_type}")
            return False

        # Save PDF
        c.showPage()
        c.save()
        logger.info(f"✓ Successfully created: {output_path}")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to render {activity_type}: {e}", exc_info=True)
        return False


def test_activity(activity_name: str, debug: bool = False):
    """Test a specific activity."""
    setup_logging(debug)
    logger = logging.getLogger(__name__)

    if activity_name not in SAMPLE_PAGES:
        logger.error(f"Unknown activity: {activity_name}")
        logger.info(f"Available activities: {', '.join(SAMPLE_PAGES.keys())}")
        return False

    page_spec = SAMPLE_PAGES[activity_name]
    activity_type = page_spec["type"]

    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    output_path = output_dir / f"test_{activity_name}.pdf"

    logger.info(f"Testing {activity_name} ({activity_type})")
    success = render_activity_page(activity_type, page_spec, output_path)

    if success:
        logger.info(f"\n✓ Test passed! PDF created at: {output_path}")
    else:
        logger.error(f"\n✗ Test failed for {activity_name}")

    return success


def test_all_activities(debug: bool = False):
    """Test all activities."""
    setup_logging(debug)
    logger = logging.getLogger(__name__)

    logger.info("Testing all activities...")
    logger.info("=" * 60)

    results = {}
    for activity_name in SAMPLE_PAGES.keys():
        logger.info(f"\nTesting: {activity_name}")
        logger.info("-" * 60)
        results[activity_name] = test_activity(activity_name, debug=False)

    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("TEST SUMMARY")
    logger.info("=" * 60)

    passed = sum(1 for v in results.values() if v)
    failed = len(results) - passed

    for activity_name, success in results.items():
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{status}: {activity_name}")

    logger.info(f"\nTotal: {len(results)} tests, {passed} passed, {failed} failed")

    return failed == 0


def main():
    parser = argparse.ArgumentParser(description="Test activity page renderers")
    parser.add_argument("--all", action="store_true", help="Test all activities")
    parser.add_argument("--activity", type=str, help="Test specific activity")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    parser.add_argument("--list", action="store_true", help="List available activities")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable activities:")
        for name, spec in SAMPLE_PAGES.items():
            print(f"  - {name:20} ({spec['type']}): {spec['title']}")
        return 0

    if args.all:
        success = test_all_activities(args.debug)
        return 0 if success else 1

    if args.activity:
        success = test_activity(args.activity, args.debug)
        return 0 if success else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
