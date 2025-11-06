"""Tracing page renderer."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict

from reportlab.pdfgen.canvas import Canvas

# Import shape renderers
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from drawing.shapes import get_renderer, RENDERERS


def _is_shape(content: str) -> bool:
    """Check if content is a known shape name."""
    normalized = content.lower().strip()
    return normalized in RENDERERS or get_renderer(content) is not None


def _draw_traceable_shape(c: Canvas, x: float, y: float, shape_name: str, size: float = 100) -> None:
    """Draw a shape with dotted outline for tracing."""
    renderer = get_renderer(shape_name)
    if renderer:
        c.saveState()
        # Set dotted line style
        c.setDash(6, 6)
        c.setStrokeGray(0.5)
        c.setLineWidth(2)
        # Translate to position
        c.translate(x, y)
        # Render the shape
        renderer(c, size, size)
        c.restoreState()


def _draw_traceable_text(c: Canvas, x: float, y: float, text: str, font_size: int = 96) -> None:
    """Draw text with dotted outline (stroke-only) for tracing."""
    c.saveState()

    # Set font
    c.setFont("Helvetica-Bold", font_size)

    # Use text render mode 1 = stroke only (no fill)
    c.setTextRenderMode(1)

    # Set dotted line style
    c.setDash(6, 6)
    c.setStrokeGray(0.5)
    c.setLineWidth(2.5)  # Thinner stroke for tracing

    # Draw the text
    c.drawString(x, y, text)

    c.restoreState()


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Tracing"))
    helpers["draw_instruction"]("Trace over the dotted lines")

    content = page_spec.get("content", "A")
    repetitions = page_spec.get("repetitions", 12)

    # Check if content is a shape or text
    is_shape = _is_shape(str(content))

    cols = 3
    rows = math.ceil(repetitions / cols)
    start_y = helpers["height"] - 160
    spacing_x = (helpers["width"] - 2 * helpers["margin"]) / cols
    spacing_y = (helpers["height"] - 250) / rows

    for row in range(rows):
        for col in range(cols):
            if row * cols + col >= repetitions:
                break

            if is_shape:
                # Draw shape with dotted outline
                x = helpers["margin"] + col * spacing_x + spacing_x / 2
                y = start_y - row * spacing_y - 50
                _draw_traceable_shape(c, x, y, str(content), size=80)
            else:
                # Draw text with dotted outline (stroke-only)
                x = helpers["margin"] + col * spacing_x + spacing_x / 2 - 35
                y = start_y - row * spacing_y
                _draw_traceable_text(c, x, y, str(content), font_size=96)
