# activity_renderer.py
# Procedural SVG renderers for preschool coloring pages.
# Big white space, thick strokes, no fill, friendly silhouettes.

from typing import Optional
from components.geometry import render_svg

# ---------- Subject renderers ----------

def draw_circle(width=800, height=1000):
    return render_svg("circle", width, height)

def draw_rounded_square(width=800, height=1000):
    return render_svg("rounded square", width, height)

def draw_triangle(width=800, height=1000):
    return render_svg("triangle", width, height)

def draw_star(width=800, height=1000, points=5):
    # Note: points parameter is not used in current implementation
    # as star_geometry uses fixed 5 points
    return render_svg("star", width, height)

def draw_heart(width=800, height=1000):
    return render_svg("heart", width, height)

def draw_cloud(width=800, height=1000):
    return render_svg("cloud", width, height)

def draw_leaf(width=800, height=1000):
    return render_svg("leaf", width, height)

def draw_acorn(width=800, height=1000):
    return render_svg("acorn", width, height)

def draw_mushroom(width=800, height=1000):
    return render_svg("mushroom", width, height)

def draw_pine_tree(width=800, height=1000):
    return render_svg("pine tree", width, height)

def draw_sun(width=800, height=1000):
    return render_svg("sun", width, height)

def draw_raindrop(width=800, height=1000):
    return render_svg("raindrop", width, height)

# ---------- Dispatcher ----------

_CANON = {
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

_SYNONYMS = {
    "wobbly circle": "circle",
    "rounded square": "rounded square",
    "smiling star": "star",   # still simple outline
    "spiky sun": "sun",
    "striped mushroom": "mushroom",
    "dotted leaf": "leaf",
}

def render_subject_svg(subject: str, width: int = 800, height: int = 1000) -> str:
    name = (subject or "").strip().lower()
    name = _SYNONYMS.get(name, name)
    func = _CANON.get(name)
    if not func:
        # gentle fallback: big circle
        return draw_circle(width, height)
    return func(width, height)
