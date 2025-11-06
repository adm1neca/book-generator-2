"""Matching page renderer."""

from __future__ import annotations

import random
from typing import Any, Dict, Sequence

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


def _draw_shape(c: Canvas, x: float, y: float, shape: str) -> None:
    if shape == "circle":
        c.circle(x, y, 25, stroke=1, fill=0)
    elif shape == "square":
        c.rect(x - 25, y - 25, 50, 50, stroke=1, fill=0)
    elif shape == "triangle":
        path = c.beginPath()
        path.moveTo(x, y + 25)
        path.lineTo(x - 25, y - 25)
        path.lineTo(x + 25, y - 25)
        path.close()
        c.drawPath(path, stroke=1, fill=0)


def _draw_matching_item(c: Canvas, x: float, y: float, item: Any) -> None:
    if isinstance(item, dict):
        item_type = item.get("type", "shape")
        if item_type == "shape":
            _draw_shape(c, x, y, item.get("shape", "circle"))
        elif item_type == "number":
            c.setFont("Helvetica-Bold", 36)
            c.drawCentredString(x, y - 12, str(item.get("value", "1")))
        elif item_type == "color":
            try:
                c.setFillColor(colors.HexColor(item.get("color", "#000000")))
                c.circle(x, y, 25, stroke=1, fill=1)
            except Exception:
                c.circle(x, y, 25, stroke=1, fill=0)
            finally:
                c.setFillColor(colors.black)
    else:
        c.setFont("Helvetica-Bold", 36)
        c.drawCentredString(x, y - 12, str(item))


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Match the Pairs"))
    helpers["draw_instruction"]("Draw lines to match the pairs!")

    pairs: Sequence[Any] = page_spec.get("pairs", [])
    left_x = helpers["width"] * 0.25
    right_x = helpers["width"] * 0.75
    start_y = helpers["height"] - 150
    spacing = 100

    c.setLineWidth(max(2, helpers["kid_stroke"]() - 2))
    c.setStrokeColor(colors.black)

    paired_types = (list, tuple)
    right_items = [pair[1] if isinstance(pair, paired_types) else pair for pair in pairs]
    random.shuffle(right_items)

    for i, pair in enumerate(pairs):
        if i >= 4:
            break
        y = start_y - i * spacing
        left_item = pair[0] if isinstance(pair, paired_types) else pair
        _draw_matching_item(c, left_x, y, left_item)
        if i < len(right_items):
            _draw_matching_item(c, right_x, y, right_items[i])
        c.circle(left_x + 40, y, 5, stroke=1, fill=0)
        c.circle(right_x - 40, y, 5, stroke=1, fill=0)
