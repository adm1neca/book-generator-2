"""Dot-to-dot page renderer."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Tuple

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


logger = logging.getLogger(__name__)


Dot = Tuple[float, float]


def _draw_shape_outline_dashed(c: Canvas, shape: str, dots: Iterable[Dot]) -> None:
    """Draw a dashed outline connecting the dot positions as a guide."""
    dot_list = list(dots)
    if len(dot_list) < 3:
        logger.warning(f"Not enough dots to draw outline: {len(dot_list)} < 3")
        return

    logger.debug(f"Drawing dashed outline for shape '{shape}' with {len(dot_list)} dots")

    # Save current state
    c.saveState()

    # Set dashed line style - lighter and more visible
    c.setDash(8, 8)  # 8px dash, 8px gap
    c.setStrokeGray(0.5)  # Medium gray
    c.setLineWidth(1.5)

    # Draw path connecting all dots
    path = c.beginPath()
    path.moveTo(dot_list[0][0], dot_list[0][1])
    for x, y in dot_list[1:]:
        path.lineTo(x, y)
    path.close()

    c.drawPath(path, stroke=1, fill=0)

    # Restore state
    c.restoreState()


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    title = page_spec.get("title", "Connect the Dots")
    shape = page_spec.get("shape", "star")
    logger.info(f"Rendering dot-to-dot page: {title}, shape: {shape}")

    helpers["draw_border"]()
    helpers["draw_title"](title)

    dots_count = page_spec.get("dots", 12)
    helpers["draw_instruction"](f"Connect 1 to {dots_count}")

    if "dot_positions" not in page_spec:
        logger.debug(f"Generating dot positions for shape '{shape}' with {dots_count} dots")
        page_spec["dot_positions"] = helpers["generate_dot_positions"](shape, dots_count)

    dots: Iterable[Dot] = page_spec["dot_positions"]
    dot_list = list(dots)
    logger.info(f"Drawing {len(dot_list)} dots")

    # Draw dashed outline guide first
    _draw_shape_outline_dashed(c, shape, dot_list)

    # Reset to solid line and black for dots
    c.setDash()  # Remove dash pattern
    c.setStrokeColor(colors.black)
    c.setFillColor(colors.black)
    c.setLineWidth(1)
    c.setFont("Helvetica-Bold", 12)

    # Draw numbered dots
    for i, (x, y) in enumerate(dot_list[:dots_count], start=1):
        # Draw filled circle for dot
        c.circle(x, y, 4, stroke=1, fill=1)
        # Draw number above dot
        c.drawCentredString(x, y + 10, str(i))

    logger.info("Dot-to-dot page rendering complete")
