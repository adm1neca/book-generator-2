"""Tracing page renderer."""

from __future__ import annotations

import logging
import math
from typing import Any, Dict

from reportlab.pdfgen.canvas import Canvas

from scripts.drawing.shapes import get_renderer, RENDERERS


logger = logging.getLogger(__name__)


def _is_shape(content: str) -> bool:
    """Check if content is a known shape name."""
    normalized = content.lower().strip()
    return normalized in RENDERERS or get_renderer(content) is not None


def _draw_traceable_shape(c: Canvas, x: float, y: float, shape_name: str, size: float = 100) -> None:
    """Draw a shape with dotted outline for tracing."""
    renderer = get_renderer(shape_name)
    if renderer:
        logger.debug(f"Drawing traceable shape '{shape_name}' at ({x}, {y}), size={size}")
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
    else:
        logger.warning(f"No renderer found for shape '{shape_name}'")


def _draw_traceable_text(c: Canvas, x: float, y: float, text: str, font_size: int = 96) -> None:
    """Draw text with dotted outline (stroke-only) for tracing."""
    logger.debug(f"Drawing traceable text '{text}' at ({x}, {y}), font_size={font_size}")
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
    title = page_spec.get("title", "Tracing")
    content = page_spec.get("content", "A")
    repetitions = page_spec.get("repetitions", 12)

    logger.info(f"Rendering tracing page: {title}")
    logger.info(f"Content: '{content}', repetitions: {repetitions}")

    helpers["draw_border"]()
    helpers["draw_title"](title)
    helpers["draw_instruction"]("Trace over the dotted lines")

    # Check if content is a shape or text
    is_shape = _is_shape(str(content))
    logger.info(f"Content type: {'shape' if is_shape else 'text'}")

    cols = 3
    rows = math.ceil(repetitions / cols)
    start_y = helpers["height"] - 160
    spacing_x = (helpers["width"] - 2 * helpers["margin"]) / cols
    spacing_y = (helpers["height"] - 250) / rows

    logger.debug(f"Layout: {cols} cols x {rows} rows, spacing_x={spacing_x:.1f}, spacing_y={spacing_y:.1f}")

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

    logger.info("Tracing page rendering complete")
