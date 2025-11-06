"""Counting page renderer."""

from __future__ import annotations

import math
from typing import Any, Dict

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


def _draw_star(c: Canvas, x: float, y: float) -> None:
    points = []
    for i in range(10):
        angle = math.radians(i * 36 - 90)
        radius = 20 if i % 2 == 0 else 10
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        points.append((px, py))
    path = c.beginPath()
    path.moveTo(points[0][0], points[0][1])
    for px, py in points[1:]:
        path.lineTo(px, py)
    path.close()
    c.drawPath(path, stroke=1, fill=0)


def _draw_heart(c: Canvas, x: float, y: float) -> None:
    path = c.beginPath()
    path.moveTo(x, y - 15)
    path.curveTo(x - 20, y + 10, x - 15, y + 15, x, y + 5)
    path.curveTo(x + 15, y + 15, x + 20, y + 10, x, y - 15)
    c.drawPath(path, stroke=1, fill=0)


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Count"))
    helpers["draw_instruction"]("Count and write the number")

    count = page_spec.get("count", 5)
    item = page_spec.get("item", "circle")

    c.setLineWidth(max(2, helpers["kid_stroke"]() - 2))
    c.setStrokeColor(colors.black)

    cols = min(5, count)
    rows = math.ceil(count / cols)
    start_x = helpers["width"] / 2 - (cols * 60) / 2
    start_y = helpers["height"] - 220

    for i in range(count):
        row = i // cols
        col = i % cols
        x = start_x + col * 60
        y = start_y - row * 60

        lower_item = str(item).lower()
        if "circle" in lower_item:
            c.circle(x, y, 20, stroke=1, fill=0)
        elif "star" in lower_item:
            _draw_star(c, x, y)
        elif "heart" in lower_item:
            _draw_heart(c, x, y)
        else:
            c.rect(x - 15, y - 15, 30, 30, stroke=1, fill=0)

    c.setFont("Helvetica", 18)
    c.setFillColor(colors.black)
    c.drawCentredString(helpers["width"] / 2, 150, "How many? Write your answer:")
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(helpers["width"] / 2 - 40, 100, 80, 60, stroke=1, fill=0)
