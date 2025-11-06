"""Coloring page renderer."""

from __future__ import annotations

from typing import Any, Dict

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from scripts.drawing.shapes import get_renderer


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Coloring Page"))
    helpers["draw_instruction"](
        page_spec.get("instruction", "Use your favorite crayons!")
    )

    subject = (
        page_spec.get("subject")
        or page_spec.get("subjectHint")
        or "circle"
    )
    renderer = get_renderer(subject)

    helpers["prep_kid_lines"]()
    c.setFillColor(colors.white)

    renderer(c, helpers["width"], helpers["height"])
