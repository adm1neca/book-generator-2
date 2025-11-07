"""Shape drawing helpers for activity pages."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from reportlab.pdfgen.canvas import Canvas

from components.geometry import render_to_canvas


CanvasRenderer = Callable[[Canvas, float, float], None]


def draw_circle(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "circle", width, height)


def draw_rounded_square(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "rounded square", width, height)


def draw_triangle(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "triangle", width, height)


def draw_star(c: Canvas, width: float, height: float, points: int = 5) -> None:
    # Note: points parameter is not used in current implementation
    # as star_geometry uses fixed 5 points
    render_to_canvas(c, "star", width, height)


def draw_heart(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "heart", width, height)


def draw_cloud(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "cloud", width, height)


def draw_leaf(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "leaf", width, height)


def draw_acorn(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "acorn", width, height)


def draw_mushroom(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "mushroom", width, height)


def draw_pine_tree(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "pine tree", width, height)


def draw_sun(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "sun", width, height)


def draw_raindrop(c: Canvas, width: float, height: float) -> None:
    render_to_canvas(c, "raindrop", width, height)


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
