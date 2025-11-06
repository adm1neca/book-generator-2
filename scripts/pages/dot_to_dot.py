"""Dot-to-dot page renderer."""

from __future__ import annotations

import math
from typing import Any, Dict, Iterable, Tuple

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


Dot = Tuple[float, float]


def _draw_shape_outline_dashed(c: Canvas, shape: str, dots: Iterable[Dot]) -> None:
    """Draw a dashed outline connecting the dot positions as a guide."""
    dot_list = list(dots)
    if len(dot_list) < 3:
        return

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
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Connect the Dots"))

    dots_count = page_spec.get("dots", 12)
    helpers["draw_instruction"](f"Connect 1 to {dots_count}")

    if "dot_positions" not in page_spec:
        page_spec["dot_positions"] = helpers["generate_dot_positions"](
            page_spec.get("shape", "star"), dots_count
        )

    dots: Iterable[Dot] = page_spec["dot_positions"]
    dot_list = list(dots)

    # Draw dashed outline guide
    _draw_shape_outline_dashed(c, page_spec.get("shape", "star"), dot_list)

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)

    for i, (x, y) in enumerate(dot_list[:dots_count], start=1):
        c.circle(x, y, 4, stroke=1, fill=1)
        c.drawCentredString(x, y + 10, str(i))
