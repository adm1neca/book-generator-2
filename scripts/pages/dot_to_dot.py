"""Dot-to-dot page renderer."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


Dot = Tuple[float, float]


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

    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(colors.black)

    for i, (x, y) in enumerate(dot_list[:dots_count], start=1):
        c.circle(x, y, 4, stroke=1, fill=1)
        c.drawCentredString(x, y + 10, str(i))
