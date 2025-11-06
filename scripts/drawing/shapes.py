"""Shape drawing helpers for activity pages."""

from __future__ import annotations

import math
from typing import Callable, Dict, Optional

from reportlab.pdfgen.canvas import Canvas


CanvasRenderer = Callable[[Canvas, float, float], None]


def _kid_margin(width: float, height: float) -> float:
    """Return a playful margin proportionate to the canvas size."""

    return float(min(width, height) * 0.07)


def _center_box(width: float, height: float) -> tuple[float, float, float, float]:
    margin = _kid_margin(width, height)
    return margin, margin, width - 2 * margin, height - 2 * margin


def draw_circle(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    radius = min(w, h) * 0.35
    cx, cy = width / 2, height / 2
    c.circle(cx, cy, radius, stroke=1, fill=0)


def draw_rounded_square(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    size = min(w, h) * 0.65
    radius = size * 0.18
    x0 = (width - size) / 2
    y0 = (height - size) / 2
    c.roundRect(x0, y0, size, size, radius, stroke=1, fill=0)


def draw_triangle(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    size = min(w, h) * 0.75
    cx, cy = width / 2, height / 2 + size * 0.05
    path = c.beginPath()
    path.moveTo(cx, cy - 0.50 * size)
    path.lineTo(cx - 0.50 * size, cy + 0.35 * size)
    path.lineTo(cx + 0.50 * size, cy + 0.35 * size)
    path.close()
    c.drawPath(path, stroke=1, fill=0)


def draw_star(c: Canvas, width: float, height: float, points: int = 5) -> None:
    _, _, w, h = _center_box(width, height)
    outer_radius = min(w, h) * 0.36
    inner_radius = outer_radius * 0.45
    cx, cy = width / 2, height / 2
    points_xy = []
    for i in range(points * 2):
        angle = math.pi / 2 + i * math.pi / points
        radius = outer_radius if i % 2 == 0 else inner_radius
        points_xy.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))
    path = c.beginPath()
    path.moveTo(points_xy[0][0], points_xy[0][1])
    for px, py in points_xy[1:]:
        path.lineTo(px, py)
    path.close()
    c.drawPath(path, stroke=1, fill=0)


def draw_heart(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    size = min(w, h) * 0.55
    cx, cy = width / 2, height / 2 + size * 0.05
    path = c.beginPath()
    path.moveTo(cx, cy + 0.28 * size)
    path.curveTo(
        cx - 0.60 * size,
        cy - 0.20 * size,
        cx - 0.18 * size,
        cy - 0.65 * size,
        cx,
        cy - 0.30 * size,
    )
    path.curveTo(
        cx + 0.18 * size,
        cy - 0.65 * size,
        cx + 0.60 * size,
        cy - 0.20 * size,
        cx,
        cy + 0.28 * size,
    )
    path.close()
    c.drawPath(path, stroke=1, fill=0)


def draw_cloud(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    cx, cy = width / 2, height / 2
    radius = min(w, h) * 0.20
    c.circle(cx - 1.1 * radius, cy + 0.2 * radius, 0.9 * radius, stroke=1, fill=0)
    c.circle(cx - 0.3 * radius, cy - 0.2 * radius, 1.05 * radius, stroke=1, fill=0)
    c.circle(cx + 0.7 * radius, cy + 0.1 * radius, 0.85 * radius, stroke=1, fill=0)
    c.line(cx - 1.5 * radius, cy + 0.8 * radius, cx + 1.5 * radius, cy + 0.8 * radius)


def draw_leaf(c: Canvas, width: float, height: float) -> None:
    cx, cy = width / 2, int(height * 0.52)
    size = min(width, height) * 0.48
    outline = c.beginPath()
    outline.moveTo(cx, cy - 0.60 * size)
    outline.curveTo(
        cx + 0.55 * size,
        cy - 0.55 * size,
        cx + 0.65 * size,
        cy + 0.10 * size,
        cx,
        cy + 0.65 * size,
    )
    outline.curveTo(
        cx - 0.65 * size,
        cy + 0.10 * size,
        cx - 0.55 * size,
        cy - 0.55 * size,
        cx,
        cy - 0.60 * size,
    )
    outline.close()
    c.drawPath(outline, stroke=1, fill=0)
    c.line(cx, cy - 0.55 * size, cx, cy + 0.72 * size)

    right_vein = c.beginPath()
    right_vein.moveTo(cx, cy + 0.10 * size)
    right_vein.curveTo(
        cx + 0.25 * size,
        cy,
        cx + 0.30 * size,
        cy - 0.15 * size,
        cx + 0.35 * size,
        cy - 0.25 * size,
    )
    c.drawPath(right_vein, stroke=1, fill=0)

    left_vein = c.beginPath()
    left_vein.moveTo(cx, cy)
    left_vein.curveTo(
        cx - 0.22 * size,
        cy - 0.10 * size,
        cx - 0.30 * size,
        cy - 0.22 * size,
        cx - 0.38 * size,
        cy - 0.30 * size,
    )
    c.drawPath(left_vein, stroke=1, fill=0)


def draw_acorn(c: Canvas, width: float, height: float) -> None:
    cx, cy = width / 2, height / 2
    size = min(width, height) * 0.50
    body = c.beginPath()
    body.moveTo(cx, cy - 0.10 * size)
    body.curveTo(
        cx + 0.48 * size,
        cy - 0.05 * size,
        cx + 0.48 * size,
        cy + 0.55 * size,
        cx,
        cy + 0.60 * size,
    )
    body.curveTo(
        cx - 0.48 * size,
        cy + 0.55 * size,
        cx - 0.48 * size,
        cy - 0.05 * size,
        cx,
        cy - 0.10 * size,
    )
    body.close()
    c.drawPath(body, stroke=1, fill=0)

    cap_top = c.beginPath()
    cap_top.moveTo(cx - 0.55 * size, cy - 0.02 * size)
    cap_top.curveTo(
        cx - 0.15 * size,
        cy - 0.35 * size,
        cx + 0.15 * size,
        cy - 0.35 * size,
        cx + 0.55 * size,
        cy - 0.02 * size,
    )
    c.drawPath(cap_top, stroke=1, fill=0)

    cap_curve = c.beginPath()
    cap_curve.moveTo(cx - 0.55 * size, cy - 0.02 * size)
    cap_curve.curveTo(
        cx - 0.40 * size,
        cy + 0.10 * size,
        cx - 0.20 * size,
        cy + 0.10 * size,
        cx - 0.05 * size,
        cy - 0.02 * size,
    )
    cap_curve.curveTo(
        cx + 0.10 * size,
        cy + 0.10 * size,
        cx + 0.30 * size,
        cy + 0.10 * size,
        cx + 0.45 * size,
        cy - 0.02 * size,
    )
    c.drawPath(cap_curve, stroke=1, fill=0)

    stem = c.beginPath()
    stem.moveTo(cx + 0.10 * size, cy - 0.30 * size)
    stem.curveTo(
        cx + 0.20 * size,
        cy - 0.45 * size,
        cx + 0.05 * size,
        cy - 0.55 * size,
        cx - 0.05 * size,
        cy - 0.48 * size,
    )
    c.drawPath(stem, stroke=1, fill=0)


def draw_mushroom(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    size = min(w, h) * 0.65
    cx, cy = width / 2, height / 2

    cap = c.beginPath()
    cap.moveTo(cx - 0.55 * size, cy)
    cap.curveTo(cx - 0.20 * size, cy - 0.60 * size, cx + 0.20 * size, cy - 0.60 * size, cx + 0.55 * size, cy)
    c.drawPath(cap, stroke=1, fill=0)

    brim = c.beginPath()
    brim.moveTo(cx - 0.55 * size, cy)
    brim.curveTo(cx - 0.20 * size, cy + 0.25 * size, cx + 0.20 * size, cy + 0.25 * size, cx + 0.55 * size, cy)
    c.drawPath(brim, stroke=1, fill=0)

    stem_width = 0.24 * size
    stem_height = 0.55 * size
    stem_radius = 0.10 * size
    x0, y0 = cx - stem_width / 2, cy
    c.roundRect(x0, y0, stem_width, stem_height, stem_radius, stroke=1, fill=0)

    c.circle(cx - 0.25 * size, cy - 0.18 * size, 0.06 * size, stroke=1, fill=0)
    c.circle(cx + 0.15 * size, cy - 0.22 * size, 0.07 * size, stroke=1, fill=0)
    c.circle(cx, cy - 0.05 * size, 0.05 * size, stroke=1, fill=0)


def draw_pine_tree(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    size = min(w, h) * 0.75
    cx, cy = width / 2, height / 2 + size * 0.05

    def triangle(top_y: float, base_width: float, base_y: float) -> None:
        path = c.beginPath()
        path.moveTo(cx, top_y)
        path.lineTo(cx - base_width / 2, base_y)
        path.lineTo(cx + base_width / 2, base_y)
        path.close()
        c.drawPath(path, stroke=1, fill=0)

    triangle(cy - 0.55 * size, 0.55 * size, cy - 0.25 * size)
    triangle(cy - 0.35 * size, 0.70 * size, cy - 0.05 * size)
    triangle(cy - 0.15 * size, 0.85 * size, cy + 0.15 * size)

    trunk_width = 0.14 * size
    trunk_height = 0.30 * size
    trunk_radius = 0.04 * size
    x0, y0 = cx - trunk_width / 2, cy + 0.15 * size
    c.roundRect(x0, y0, trunk_width, trunk_height, trunk_radius, stroke=1, fill=0)


def draw_sun(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    cx, cy = width / 2, height / 2
    radius = min(w, h) * 0.28
    c.circle(cx, cy, radius, stroke=1, fill=0)
    for i in range(12):
        angle = i * (2 * math.pi / 12.0)
        inner_radius = radius * 1.25
        outer_radius = radius * 1.55
        x1, y1 = cx + inner_radius * math.cos(angle), cy + inner_radius * math.sin(angle)
        x2, y2 = cx + outer_radius * math.cos(angle), cy + outer_radius * math.sin(angle)
        c.line(x1, y1, x2, y2)


def draw_raindrop(c: Canvas, width: float, height: float) -> None:
    _, _, w, h = _center_box(width, height)
    size = min(w, h) * 0.60
    cx, cy = width / 2, height / 2
    path = c.beginPath()
    path.moveTo(cx, cy - 0.45 * size)
    path.curveTo(
        cx + 0.26 * size,
        cy - 0.10 * size,
        cx + 0.26 * size,
        cy + 0.35 * size,
        cx,
        cy + 0.42 * size,
    )
    path.curveTo(
        cx - 0.26 * size,
        cy + 0.35 * size,
        cx - 0.26 * size,
        cy - 0.10 * size,
        cx,
        cy - 0.45 * size,
    )
    path.close()
    c.drawPath(path, stroke=1, fill=0)


RENDERERS: Dict[str, CanvasRenderer] = {
    "circle": draw_circle,
    "rounded square": draw_rounded_square,
    "square": draw_rounded_square,
    "triangle": draw_triangle,
    "star": draw_star,
    "heart": draw_heart,
    "cloud": draw_cloud,
    "leaf": draw_leaf,
    "acorn": draw_acorn,
    "mushroom": draw_mushroom,
    "pine tree": draw_pine_tree,
    "tree": draw_pine_tree,
    "sun": draw_sun,
    "raindrop": draw_raindrop,
    "drop": draw_raindrop,
}

SYNONYMS: Dict[str, str] = {
    "wobbly circle": "circle",
    "rounded-square": "rounded square",
    "smiling star": "star",
    "spiky sun": "sun",
    "striped mushroom": "mushroom",
    "dotted leaf": "leaf",
}


def get_renderer(subject: Optional[str]) -> Optional[CanvasRenderer]:
    if not subject:
        return RENDERERS.get("circle")

    normalized = subject.lower().strip()
    normalized = SYNONYMS.get(normalized, normalized)
    return RENDERERS.get(normalized, RENDERERS.get("circle"))


__all__ = [
    "get_renderer",
    "RENDERERS",
    "SYNONYMS",
    "draw_circle",
    "draw_rounded_square",
    "draw_triangle",
    "draw_star",
    "draw_heart",
    "draw_cloud",
    "draw_leaf",
    "draw_acorn",
    "draw_mushroom",
    "draw_pine_tree",
    "draw_sun",
    "draw_raindrop",
]
