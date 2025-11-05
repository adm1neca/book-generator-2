# activity_renderer.py
# Procedural SVG renderers for preschool coloring pages.
# Big white space, thick strokes, no fill, friendly silhouettes.

from typing import Optional
import math

# ---------- Page + stroke helpers ----------

def _stroke_for_page(width: int, height: int) -> int:
    # ~1.2% of short side, clamped for A4/Letter-like pages
    sw = int(min(width, height) * 0.012)
    return max(8, min(sw, 16))

def _margins_for_page(width: int, height: int) -> int:
    # generous white margins: ~7% of short side
    return int(min(width, height) * 0.07)

def svg_wrap(width: int, height: int, inner_svg: str, stroke_width: Optional[int] = None) -> str:
    stroke_width = stroke_width or _stroke_for_page(width, height)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
        viewBox="0 0 {width} {height}">
      <rect x="0" y="0" width="{width}" height="{height}" fill="white"/>
      <g fill="none" stroke="black" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
        {inner_svg}
      </g>
    </svg>'''

def _center_box(width: int, height: int):
    m = _margins_for_page(width, height)
    return m, m, width - 2*m, height - 2*m

# ---------- Primitive helpers ----------

def _rounded_rect_path(x, y, w, h, r):
    r = min(r, w/2, h/2)
    return (
        f"M {x+r} {y} "
        f"H {x+w-r} "
        f"A {r} {r} 0 0 1 {x+w} {y+r} "
        f"V {y+h-r} "
        f"A {r} {r} 0 0 1 {x+w-r} {y+h} "
        f"H {x+r} "
        f"A {r} {r} 0 0 1 {x} {y+h-r} "
        f"V {y+r} "
        f"A {r} {r} 0 0 1 {x+r} {y} Z"
    )

# ---------- Subject renderers ----------

def draw_circle(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    r = min(w, h) * 0.35
    cx, cy = width//2, height//2
    return svg_wrap(width, height, f'<circle cx="{cx}" cy="{cy}" r="{r}"/>')

def draw_rounded_square(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    size = min(w, h) * 0.65
    r = size * 0.18
    x0 = (width - size) / 2
    y0 = (height - size) / 2
    return svg_wrap(width, height, f'<path d="{_rounded_rect_path(x0, y0, size, size, r)}"/>')

def draw_triangle(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    s = min(w, h) * 0.75
    cx, cy = width/2, height/2 + s*0.05
    p1 = (cx, cy - s*0.50)
    p2 = (cx - s*0.50, cy + s*0.35)
    p3 = (cx + s*0.50, cy + s*0.35)
    d = f"M {p1[0]} {p1[1]} L {p2[0]} {p2[1]} L {p3[0]} {p3[1]} Z"
    return svg_wrap(width, height, f'<path d="{d}"/>')

def draw_star(width=800, height=1000, points=5):
    x, y, w, h = _center_box(width, height)
    R = min(w, h) * 0.36
    r = R * 0.45
    cx, cy = width/2, height/2
    pts = []
    for i in range(points*2):
        ang = math.pi/2 + i * math.pi/points
        rad = R if i % 2 == 0 else r
        pts.append((cx + rad*math.cos(ang), cy - rad*math.sin(ang)))
    d = "M " + " L ".join(f"{px} {py}" for px, py in pts) + " Z"
    return svg_wrap(width, height, f'<path d="{d}"/>')

def draw_heart(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    s = min(w, h) * 0.55
    cx, cy = width/2, height/2 + s*0.05
    path = [
        f"M {cx} {cy + 0.28*s}",
        f"C {cx - 0.60*s} {cy - 0.20*s}, {cx - 0.18*s} {cy - 0.65*s}, {cx} {cy - 0.30*s}",
        f"C {cx + 0.18*s} {cy - 0.65*s}, {cx + 0.60*s} {cy - 0.20*s}, {cx} {cy + 0.28*s}",
        "Z"
    ]
    return svg_wrap(width, height, f'<path d="{" ".join(path)}"/>')

def draw_cloud(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    cx, cy = width/2, height/2
    R = min(w, h)*0.20
    bumps = [
        (cx - 1.1*R, cy + 0.2*R, 0.9*R),
        (cx - 0.3*R, cy - 0.2*R, 1.05*R),
        (cx + 0.7*R, cy + 0.1*R, 0.85*R),
    ]
    circles = ''.join([f'<circle cx="{bx}" cy="{by}" r="{br}"/>' for bx,by,br in bumps])
    base_w = R*3.0
    base = f'<path d="M {cx - base_w/2} {cy + 0.8*R} H {cx + base_w/2}"/>'
    return svg_wrap(width, height, circles + base)

def draw_leaf(width=800, height=1000):
    cx, cy = width//2, int(height*0.52)
    s = min(width, height) * 0.48
    outline = (
        f"M {cx} {cy - 0.60*s} "
        f"C {cx + 0.55*s} {cy - 0.55*s}, {cx + 0.65*s} {cy + 0.10*s}, {cx} {cy + 0.65*s} "
        f"C {cx - 0.65*s} {cy + 0.10*s}, {cx - 0.55*s} {cy - 0.55*s}, {cx} {cy - 0.60*s} Z"
    )
    midrib = f"M {cx} {cy - 0.55*s} L {cx} {cy + 0.72*s}"
    vein_r = f"M {cx} {cy + 0.10*s} C {cx + 0.25*s} {cy} {cx + 0.30*s} {cy - 0.15*s} {cx + 0.35*s} {cy - 0.25*s}"
    vein_l = f"M {cx} {cy} C {cx - 0.22*s} {cy - 0.10*s} {cx - 0.30*s} {cy - 0.22*s} {cx - 0.38*s} {cy - 0.30*s}"
    return svg_wrap(width, height, f'<path d="{outline}"/><path d="{midrib}"/><path d="{vein_r}"/><path d="{vein_l}"/>')

def draw_acorn(width=800, height=1000):
    cx, cy = width//2, height//2
    s = min(width, height) * 0.50
    body = (
        f"M {cx} {cy - 0.10*s} "
        f"C {cx + 0.48*s} {cy - 0.05*s}, {cx + 0.48*s} {cy + 0.55*s}, {cx} {cy + 0.60*s} "
        f"C {cx - 0.48*s} {cy + 0.55*s}, {cx - 0.48*s} {cy - 0.05*s}, {cx} {cy - 0.10*s} Z"
    )
    cap_top = f"M {cx - 0.55*s} {cy - 0.02*s} C {cx - 0.15*s} {cy - 0.35*s}, {cx + 0.15*s} {cy - 0.35*s}, {cx + 0.55*s} {cy - 0.02*s}"
    scallop = (
        f"M {cx - 0.55*s} {cy - 0.02*s} "
        f"C {cx - 0.40*s} {cy + 0.10*s}, {cx - 0.20*s} {cy + 0.10*s}, {cx - 0.05*s} {cy - 0.02*s} "
        f"C {cx + 0.10*s} {cy + 0.10*s}, {cx + 0.30*s} {cy + 0.10*s}, {cx + 0.45*s} {cy - 0.02*s}"
    )
    stem = f"M {cx + 0.10*s} {cy - 0.30*s} C {cx + 0.20*s} {cy - 0.45*s}, {cx + 0.05*s} {cy - 0.55*s}, {cx - 0.05*s} {cy - 0.48*s}"
    group = f'<path d="{body}"/><path d="{cap_top}"/><path d="{scallop}"/><path d="{stem}"/>'
    return svg_wrap(width, height, group)

def draw_mushroom(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    s = min(w, h) * 0.65
    cx, cy = width/2, height/2
    cap = f"M {cx - 0.55*s} {cy} C {cx - 0.20*s} {cy - 0.60*s}, {cx + 0.20*s} {cy - 0.60*s}, {cx + 0.55*s} {cy}"
    brim = f"M {cx - 0.55*s} {cy} Q {cx} {cy + 0.15*s} {cx + 0.55*s} {cy}"
    stem = _rounded_rect_path(cx - 0.12*s, cy, 0.24*s, 0.55*s, 0.10*s)
    dots = ''.join([
        f'<circle cx="{cx - 0.25*s}" cy="{cy - 0.18*s}" r="{0.06*s}"/>',
        f'<circle cx="{cx + 0.15*s}" cy="{cy - 0.22*s}" r="{0.07*s}"/>',
        f'<circle cx="{cx}" cy="{cy - 0.05*s}" r="{0.05*s}"/>',
    ])
    group = f'<path d="{cap}"/><path d="{brim}"/><path d="{stem}"/>{dots}'
    return svg_wrap(width, height, group)

def draw_pine_tree(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    s = min(w, h) * 0.75
    cx, cy = width/2, height/2 + s*0.05
    def tri(top_y, base_w, base_y):
        return f"M {cx} {top_y} L {cx - base_w/2} {base_y} L {cx + base_w/2} {base_y} Z"
    t1 = tri(cy - 0.55*s, 0.55*s, cy - 0.25*s)
    t2 = tri(cy - 0.35*s, 0.70*s, cy - 0.05*s)
    t3 = tri(cy - 0.15*s, 0.85*s, cy + 0.15*s)
    trunk = _rounded_rect_path(cx - 0.07*s, cy + 0.15*s, 0.14*s, 0.30*s, 0.04*s)
    return svg_wrap(width, height, f'<path d="{t1}"/><path d="{t2}"/><path d="{t3}"/><path d="{trunk}"/>')

def draw_sun(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    cx, cy = width/2, height/2
    r = min(w, h)*0.28
    core = f'<circle cx="{cx}" cy="{cy}" r="{r}"/>'
    rays = []
    for i in range(12):
        ang = i * math.tau/12
        r1 = r*1.25
        r2 = r*1.55
        x1, y1 = cx + r1*math.cos(ang), cy - r1*math.sin(ang)
        x2, y2 = cx + r2*math.cos(ang), cy - r2*math.sin(ang)
        rays.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>')
    return svg_wrap(width, height, core + "".join(rays))

def draw_raindrop(width=800, height=1000):
    x, y, w, h = _center_box(width, height)
    s = min(w, h)*0.60
    cx, cy = width/2, height/2
    path = (
        f"M {cx} {cy - 0.45*s} "
        f"C {cx + 0.26*s} {cy - 0.10*s}, {cx + 0.26*s} {cy + 0.35*s}, {cx} {cy + 0.42*s} "
        f"C {cx - 0.26*s} {cy + 0.35*s}, {cx - 0.26*s} {cy - 0.10*s}, {cx} {cy - 0.45*s} Z"
    )
    return svg_wrap(width, height, f'<path d="{path}"/>')

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
