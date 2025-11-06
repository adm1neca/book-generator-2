"""Tracing page renderer."""

from __future__ import annotations

import math
from typing import Any, Dict

from reportlab.pdfgen.canvas import Canvas


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Tracing"))
    helpers["draw_instruction"]("Trace over the dotted lines")

    content = page_spec.get("content", "A")
    repetitions = page_spec.get("repetitions", 12)

    cols = 3
    rows = math.ceil(repetitions / cols)
    start_y = helpers["height"] - 150
    spacing_x = (helpers["width"] - 2 * helpers["margin"]) / cols
    spacing_y = (helpers["height"] - 250) / rows

    c.setFont("Helvetica-Bold", 72)
    c.setDash(6, 6)
    c.setStrokeGray(0.5)
    c.setFillGray(0.0)

    for row in range(rows):
        for col in range(cols):
            if row * cols + col >= repetitions:
                break
            x = helpers["margin"] + col * spacing_x + spacing_x / 2 - 30
            y = start_y - row * spacing_y
            c.drawString(x, y, str(content))
    c.setDash()
