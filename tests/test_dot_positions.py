"""Tests for dot-to-dot coordinate generators."""

from __future__ import annotations

import math
from pathlib import Path

import pytest

pytest.importorskip("reportlab")

from components.prompts.dot_to_dot_strategy import DotToDotPromptStrategy
from scripts.generator import ActivityBookletGenerator
from scripts.helpers import Primitives


@pytest.fixture()
def generator(tmp_path: Path) -> ActivityBookletGenerator:
    """Provide a generator writing to a temporary PDF file."""

    output_path = tmp_path / "test.pdf"
    gen = ActivityBookletGenerator(str(output_path))
    setattr(gen, "_test_output_path", output_path)
    return gen


def test_generate_dot_positions_for_supported_shapes(generator: ActivityBookletGenerator):
    """Ensure every supported shape yields a non-empty coordinate list."""

    for shape in DotToDotPromptStrategy.SHAPE_OPTIONS:
        dots = generator.generate_dot_positions(shape, 12)
        assert len(dots) >= 12, f"Expected at least 12 dots for shape {shape}"
        # Coordinates should span a meaningful area on the page
        xs = [x for x, _ in dots]
        ys = [y for _, y in dots]
        assert max(xs) - min(xs) > 40, f"Shape {shape} collapsed horizontally"
        assert max(ys) - min(ys) > 40, f"Shape {shape} collapsed vertically"


@pytest.mark.parametrize(
    "shape, generator_fn",
    [
        ("diamond", Primitives.generate_dot_positions_diamond),
        ("house", Primitives.generate_dot_positions_house),
        ("tree", Primitives.generate_dot_positions_tree),
        ("flower", Primitives.generate_dot_positions_flower),
        ("butterfly", Primitives.generate_dot_positions_butterfly),
        ("fish", Primitives.generate_dot_positions_fish),
        ("apple", Primitives.generate_dot_positions_apple),
    ],
)
def test_custom_shape_generators_have_expected_lobes(
    generator: ActivityBookletGenerator,
    shape: str,
    generator_fn,
) -> None:
    """Composite shapes should produce at least a dozen well-distributed dots."""

    dots = generator_fn(generator.width / 2, generator.height / 2, 8)
    assert len(dots) >= 12
    # Ensure the points trace some curvature by checking angle variance
    center_x, center_y = generator.width / 2, generator.height / 2
    angles = [math.atan2(y - center_y, x - center_x) for x, y in dots]
    assert len({round(a, 1) for a in angles}) >= 6


def test_render_sample_pdf_contains_outline(generator: ActivityBookletGenerator):
    """Render a sample dot-to-dot page and ensure the PDF has drawn content."""

    page_spec = {
        "title": "Butterfly Surprise",
        "type": "dot-to-dot",
        "shape": "butterfly",
        "dots": 14,
    }

    generator.render_page(page_spec)
    generator.c.save()

    pdf_path = Path(getattr(generator, "_test_output_path"))
    assert pdf_path.exists()
    size = pdf_path.stat().st_size
    # ReportLab writes ~1.5KB for empty pages; ensure we exceed that significantly
    assert size > 1800, f"Unexpectedly small PDF ({size} bytes)"

    dots = page_spec.get("dot_positions")
    assert dots and len(dots) >= 14
    xs = [x for x, _ in dots]
    ys = [y for _, y in dots]
    assert max(xs) - min(xs) > 40
    assert max(ys) - min(ys) > 40
