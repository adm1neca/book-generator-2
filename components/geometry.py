"""
Shared geometry module for activity shapes.
Canonical shape specifications that can render to both SVG and PDF (ReportLab).
"""

from __future__ import annotations
import math
from dataclasses import dataclass
from typing import List, Union


# ============================================================================
# Common layout utilities
# ============================================================================

def kid_margin(width: float, height: float) -> float:
    """Return a playful margin proportionate to canvas size (~7% of short side)."""
    return float(min(width, height) * 0.07)


def center_box(width: float, height: float) -> tuple[float, float, float, float]:
    """Return (x, y, w, h) for the centered drawing area after margins."""
    margin = kid_margin(width, height)
    return margin, margin, width - 2 * margin, height - 2 * margin


def stroke_width_for_page(width: float, height: float) -> int:
    """Calculate stroke width (~1.2% of short side, clamped 8-16px)."""
    sw = int(min(width, height) * 0.012)
    return max(8, min(sw, 16))


# ============================================================================
# Geometric primitive classes
# ============================================================================

@dataclass
class Circle:
    """A circle primitive."""
    cx: float
    cy: float
    r: float


@dataclass
class Line:
    """A line segment."""
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass
class RoundedRect:
    """A rounded rectangle."""
    x: float
    y: float
    w: float
    h: float
    radius: float


@dataclass
class Path:
    """A path with bezier curves and lines."""
    commands: List[Union['MoveTo', 'LineTo', 'CurveTo', 'QuadTo', 'ArcTo', 'Close']]


@dataclass
class MoveTo:
    """Move to a point without drawing."""
    x: float
    y: float


@dataclass
class LineTo:
    """Draw a line to a point."""
    x: float
    y: float


@dataclass
class CurveTo:
    """Cubic Bezier curve (2 control points)."""
    x1: float
    y1: float
    x2: float
    y2: float
    x: float
    y: float


@dataclass
class QuadTo:
    """Quadratic Bezier curve (1 control point)."""
    x1: float
    y1: float
    x: float
    y: float


@dataclass
class ArcTo:
    """Elliptical arc."""
    rx: float
    ry: float
    rotation: float
    large_arc: int
    sweep: int
    x: float
    y: float


@dataclass
class Close:
    """Close the path."""
    pass


# Type alias for any geometric primitive
Primitive = Union[Circle, Line, RoundedRect, Path]


# ============================================================================
# Shape geometry specifications
# ============================================================================

def circle_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a circle."""
    _, _, w, h = center_box(width, height)
    r = min(w, h) * 0.35
    cx, cy = width / 2, height / 2
    return [Circle(cx, cy, r)]


def rounded_square_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a rounded square."""
    _, _, w, h = center_box(width, height)
    size = min(w, h) * 0.65
    radius = size * 0.18
    x0 = (width - size) / 2
    y0 = (height - size) / 2
    return [RoundedRect(x0, y0, size, size, radius)]


def triangle_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a triangle."""
    _, _, w, h = center_box(width, height)
    size = min(w, h) * 0.75
    cx, cy = width / 2, height / 2 + size * 0.05
    return [Path([
        MoveTo(cx, cy - 0.50 * size),
        LineTo(cx - 0.50 * size, cy + 0.35 * size),
        LineTo(cx + 0.50 * size, cy + 0.35 * size),
        Close()
    ])]


def star_geometry(width: float, height: float, points: int = 5) -> List[Primitive]:
    """Generate geometry for a star."""
    _, _, w, h = center_box(width, height)
    outer_radius = min(w, h) * 0.36
    inner_radius = outer_radius * 0.45
    cx, cy = width / 2, height / 2

    points_xy = []
    for i in range(points * 2):
        angle = math.pi / 2 + i * math.pi / points
        radius = outer_radius if i % 2 == 0 else inner_radius
        points_xy.append((cx + radius * math.cos(angle), cy - radius * math.sin(angle)))

    commands = [MoveTo(points_xy[0][0], points_xy[0][1])]
    for px, py in points_xy[1:]:
        commands.append(LineTo(px, py))
    commands.append(Close())

    return [Path(commands)]


def heart_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a heart."""
    _, _, w, h = center_box(width, height)
    size = min(w, h) * 0.55
    cx, cy = width / 2, height / 2 + size * 0.05

    return [Path([
        MoveTo(cx, cy + 0.28 * size),
        CurveTo(
            cx - 0.60 * size, cy - 0.20 * size,
            cx - 0.18 * size, cy - 0.65 * size,
            cx, cy - 0.30 * size
        ),
        CurveTo(
            cx + 0.18 * size, cy - 0.65 * size,
            cx + 0.60 * size, cy - 0.20 * size,
            cx, cy + 0.28 * size
        ),
        Close()
    ])]


def cloud_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a cloud."""
    _, _, w, h = center_box(width, height)
    cx, cy = width / 2, height / 2
    radius = min(w, h) * 0.20

    return [
        Circle(cx - 1.1 * radius, cy + 0.2 * radius, 0.9 * radius),
        Circle(cx - 0.3 * radius, cy - 0.2 * radius, 1.05 * radius),
        Circle(cx + 0.7 * radius, cy + 0.1 * radius, 0.85 * radius),
        Line(cx - 1.5 * radius, cy + 0.8 * radius, cx + 1.5 * radius, cy + 0.8 * radius)
    ]


def leaf_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a leaf."""
    cx, cy = width / 2, height * 0.52
    size = min(width, height) * 0.48

    outline = Path([
        MoveTo(cx, cy - 0.60 * size),
        CurveTo(
            cx + 0.55 * size, cy - 0.55 * size,
            cx + 0.65 * size, cy + 0.10 * size,
            cx, cy + 0.65 * size
        ),
        CurveTo(
            cx - 0.65 * size, cy + 0.10 * size,
            cx - 0.55 * size, cy - 0.55 * size,
            cx, cy - 0.60 * size
        ),
        Close()
    ])

    midrib = Line(cx, cy - 0.55 * size, cx, cy + 0.72 * size)

    right_vein = Path([
        MoveTo(cx, cy + 0.10 * size),
        CurveTo(
            cx + 0.25 * size, cy,
            cx + 0.30 * size, cy - 0.15 * size,
            cx + 0.35 * size, cy - 0.25 * size
        )
    ])

    left_vein = Path([
        MoveTo(cx, cy),
        CurveTo(
            cx - 0.22 * size, cy - 0.10 * size,
            cx - 0.30 * size, cy - 0.22 * size,
            cx - 0.38 * size, cy - 0.30 * size
        )
    ])

    return [outline, midrib, right_vein, left_vein]


def acorn_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for an acorn."""
    cx, cy = width / 2, height / 2
    size = min(width, height) * 0.50

    body = Path([
        MoveTo(cx, cy - 0.10 * size),
        CurveTo(
            cx + 0.48 * size, cy - 0.05 * size,
            cx + 0.48 * size, cy + 0.55 * size,
            cx, cy + 0.60 * size
        ),
        CurveTo(
            cx - 0.48 * size, cy + 0.55 * size,
            cx - 0.48 * size, cy - 0.05 * size,
            cx, cy - 0.10 * size
        ),
        Close()
    ])

    cap_top = Path([
        MoveTo(cx - 0.55 * size, cy - 0.02 * size),
        CurveTo(
            cx - 0.15 * size, cy - 0.35 * size,
            cx + 0.15 * size, cy - 0.35 * size,
            cx + 0.55 * size, cy - 0.02 * size
        )
    ])

    cap_curve = Path([
        MoveTo(cx - 0.55 * size, cy - 0.02 * size),
        CurveTo(
            cx - 0.40 * size, cy + 0.10 * size,
            cx - 0.20 * size, cy + 0.10 * size,
            cx - 0.05 * size, cy - 0.02 * size
        ),
        CurveTo(
            cx + 0.10 * size, cy + 0.10 * size,
            cx + 0.30 * size, cy + 0.10 * size,
            cx + 0.45 * size, cy - 0.02 * size
        )
    ])

    stem = Path([
        MoveTo(cx + 0.10 * size, cy - 0.30 * size),
        CurveTo(
            cx + 0.20 * size, cy - 0.45 * size,
            cx + 0.05 * size, cy - 0.55 * size,
            cx - 0.05 * size, cy - 0.48 * size
        )
    ])

    return [body, cap_top, cap_curve, stem]


def mushroom_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a mushroom."""
    _, _, w, h = center_box(width, height)
    size = min(w, h) * 0.65
    cx, cy = width / 2, height / 2

    cap = Path([
        MoveTo(cx - 0.55 * size, cy),
        CurveTo(
            cx - 0.20 * size, cy - 0.60 * size,
            cx + 0.20 * size, cy - 0.60 * size,
            cx + 0.55 * size, cy
        )
    ])

    brim = Path([
        MoveTo(cx - 0.55 * size, cy),
        QuadTo(cx, cy + 0.15 * size, cx + 0.55 * size, cy)
    ])

    stem = RoundedRect(
        cx - 0.12 * size, cy,
        0.24 * size, 0.55 * size,
        0.10 * size
    )

    # Mushroom spots
    dots = [
        Circle(cx - 0.25 * size, cy - 0.18 * size, 0.06 * size),
        Circle(cx + 0.15 * size, cy - 0.22 * size, 0.07 * size),
        Circle(cx, cy - 0.05 * size, 0.05 * size)
    ]

    return [cap, brim, stem] + dots


def pine_tree_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a pine tree."""
    _, _, w, h = center_box(width, height)
    size = min(w, h) * 0.75
    cx, cy = width / 2, height / 2 + size * 0.05

    def triangle(top_y: float, base_width: float, base_y: float) -> Path:
        return Path([
            MoveTo(cx, top_y),
            LineTo(cx - base_width / 2, base_y),
            LineTo(cx + base_width / 2, base_y),
            Close()
        ])

    t1 = triangle(cy - 0.55 * size, 0.55 * size, cy - 0.25 * size)
    t2 = triangle(cy - 0.35 * size, 0.70 * size, cy - 0.05 * size)
    t3 = triangle(cy - 0.15 * size, 0.85 * size, cy + 0.15 * size)

    trunk = RoundedRect(
        cx - 0.07 * size, cy + 0.15 * size,
        0.14 * size, 0.30 * size,
        0.04 * size
    )

    return [t1, t2, t3, trunk]


def sun_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a sun."""
    _, _, w, h = center_box(width, height)
    cx, cy = width / 2, height / 2
    radius = min(w, h) * 0.28

    primitives = [Circle(cx, cy, radius)]

    # Sun rays
    for i in range(12):
        angle = i * math.tau / 12
        inner_radius = radius * 1.25
        outer_radius = radius * 1.55
        x1 = cx + inner_radius * math.cos(angle)
        y1 = cy - inner_radius * math.sin(angle)
        x2 = cx + outer_radius * math.cos(angle)
        y2 = cy - outer_radius * math.sin(angle)
        primitives.append(Line(x1, y1, x2, y2))

    return primitives


def raindrop_geometry(width: float, height: float) -> List[Primitive]:
    """Generate geometry for a raindrop."""
    _, _, w, h = center_box(width, height)
    size = min(w, h) * 0.60
    cx, cy = width / 2, height / 2

    return [Path([
        MoveTo(cx, cy - 0.45 * size),
        CurveTo(
            cx + 0.26 * size, cy - 0.10 * size,
            cx + 0.26 * size, cy + 0.35 * size,
            cx, cy + 0.42 * size
        ),
        CurveTo(
            cx - 0.26 * size, cy + 0.35 * size,
            cx - 0.26 * size, cy - 0.10 * size,
            cx, cy - 0.45 * size
        ),
        Close()
    ])]


# ============================================================================
# Shape registry
# ============================================================================

SHAPE_REGISTRY = {
    "circle": circle_geometry,
    "rounded square": rounded_square_geometry,
    "square": rounded_square_geometry,
    "triangle": triangle_geometry,
    "star": star_geometry,
    "heart": heart_geometry,
    "cloud": cloud_geometry,
    "leaf": leaf_geometry,
    "acorn": acorn_geometry,
    "mushroom": mushroom_geometry,
    "pine tree": pine_tree_geometry,
    "tree": pine_tree_geometry,
    "sun": sun_geometry,
    "raindrop": raindrop_geometry,
    "drop": raindrop_geometry,
}


def get_shape_geometry(shape_name: str, width: float, height: float) -> List[Primitive]:
    """Get geometry primitives for a shape by name."""
    shape_func = SHAPE_REGISTRY.get(shape_name.lower().strip())
    if shape_func is None:
        # Default to circle
        shape_func = circle_geometry
    return shape_func(width, height)


# ============================================================================
# SVG Renderer
# ============================================================================

def _rounded_rect_to_svg_path(x: float, y: float, w: float, h: float, r: float) -> str:
    """Convert a rounded rectangle to SVG path."""
    r = min(r, w / 2, h / 2)
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


def _path_commands_to_svg(commands: List) -> str:
    """Convert path commands to SVG path data."""
    parts = []
    for cmd in commands:
        if isinstance(cmd, MoveTo):
            parts.append(f"M {cmd.x} {cmd.y}")
        elif isinstance(cmd, LineTo):
            parts.append(f"L {cmd.x} {cmd.y}")
        elif isinstance(cmd, CurveTo):
            parts.append(f"C {cmd.x1} {cmd.y1}, {cmd.x2} {cmd.y2}, {cmd.x} {cmd.y}")
        elif isinstance(cmd, QuadTo):
            parts.append(f"Q {cmd.x1} {cmd.y1} {cmd.x} {cmd.y}")
        elif isinstance(cmd, ArcTo):
            parts.append(f"A {cmd.rx} {cmd.ry} {cmd.rotation} {cmd.large_arc} {cmd.sweep} {cmd.x} {cmd.y}")
        elif isinstance(cmd, Close):
            parts.append("Z")
    return " ".join(parts)


def primitive_to_svg(primitive: Primitive) -> str:
    """Convert a geometric primitive to SVG element string."""
    if isinstance(primitive, Circle):
        return f'<circle cx="{primitive.cx}" cy="{primitive.cy}" r="{primitive.r}"/>'
    elif isinstance(primitive, Line):
        return f'<line x1="{primitive.x1}" y1="{primitive.y1}" x2="{primitive.x2}" y2="{primitive.y2}"/>'
    elif isinstance(primitive, RoundedRect):
        path_data = _rounded_rect_to_svg_path(
            primitive.x, primitive.y, primitive.w, primitive.h, primitive.radius
        )
        return f'<path d="{path_data}"/>'
    elif isinstance(primitive, Path):
        path_data = _path_commands_to_svg(primitive.commands)
        return f'<path d="{path_data}"/>'
    else:
        return ""


def render_svg(shape_name: str, width: int = 800, height: int = 1000) -> str:
    """Render a shape as complete SVG."""
    stroke_width = stroke_width_for_page(width, height)
    primitives = get_shape_geometry(shape_name, width, height)

    svg_elements = [primitive_to_svg(p) for p in primitives]
    inner_svg = "\n        ".join(svg_elements)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}"
        viewBox="0 0 {width} {height}">
      <rect x="0" y="0" width="{width}" height="{height}" fill="white"/>
      <g fill="none" stroke="black" stroke-width="{stroke_width}" stroke-linecap="round" stroke-linejoin="round">
        {inner_svg}
      </g>
    </svg>'''


# ============================================================================
# ReportLab Renderer
# ============================================================================

def _render_path_to_canvas(canvas, commands: List) -> None:
    """Render path commands to ReportLab canvas path."""
    path = canvas.beginPath()
    current_x, current_y = 0.0, 0.0  # Track current position manually

    for cmd in commands:
        if isinstance(cmd, MoveTo):
            path.moveTo(cmd.x, cmd.y)
            current_x, current_y = cmd.x, cmd.y
        elif isinstance(cmd, LineTo):
            path.lineTo(cmd.x, cmd.y)
            current_x, current_y = cmd.x, cmd.y
        elif isinstance(cmd, CurveTo):
            path.curveTo(cmd.x1, cmd.y1, cmd.x2, cmd.y2, cmd.x, cmd.y)
            current_x, current_y = cmd.x, cmd.y
        elif isinstance(cmd, QuadTo):
            # ReportLab doesn't have quadratic curves, convert to cubic
            # Quadratic to cubic Bezier conversion formula:
            # CP1 = P0 + 2/3 * (P1 - P0)
            # CP2 = P2 + 2/3 * (P1 - P2)
            cx1 = current_x + 2/3 * (cmd.x1 - current_x)
            cy1 = current_y + 2/3 * (cmd.y1 - current_y)
            cx2 = cmd.x + 2/3 * (cmd.x1 - cmd.x)
            cy2 = cmd.y + 2/3 * (cmd.y1 - cmd.y)
            path.curveTo(cx1, cy1, cx2, cy2, cmd.x, cmd.y)
            current_x, current_y = cmd.x, cmd.y
        elif isinstance(cmd, Close):
            path.close()
    canvas.drawPath(path, stroke=1, fill=0)


def primitive_to_canvas(canvas, primitive: Primitive) -> None:
    """Render a geometric primitive to ReportLab canvas."""
    if isinstance(primitive, Circle):
        canvas.circle(primitive.cx, primitive.cy, primitive.r, stroke=1, fill=0)
    elif isinstance(primitive, Line):
        canvas.line(primitive.x1, primitive.y1, primitive.x2, primitive.y2)
    elif isinstance(primitive, RoundedRect):
        canvas.roundRect(
            primitive.x, primitive.y,
            primitive.w, primitive.h,
            primitive.radius,
            stroke=1, fill=0
        )
    elif isinstance(primitive, Path):
        _render_path_to_canvas(canvas, primitive.commands)


def render_to_canvas(canvas, shape_name: str, width: float, height: float) -> None:
    """Render a shape to a ReportLab canvas."""
    primitives = get_shape_geometry(shape_name, width, height)
    for primitive in primitives:
        primitive_to_canvas(canvas, primitive)
