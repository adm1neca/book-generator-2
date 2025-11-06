"""Core activity booklet generator."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from scripts.pages import coloring, counting, dot_to_dot, matching, maze, tracing

PageSpec = Dict[str, Any]
PageRenderer = Callable[[canvas.Canvas, PageSpec, Dict[str, Any]], None]


def kid_stroke(width: float, height: float) -> int:
    stroke = int(min(width, height) * 0.012)
    return max(4, min(stroke, 12))


def kid_margin(width: float, height: float) -> int:
    return int(min(width, height) * 0.07)


class ActivityBookletGenerator:
    """Render activity pages onto a PDF canvas."""

    def __init__(self, output_file: str):
        output_path = Path(output_file)
        parent = output_path.parent
        if parent and str(parent) not in {"", "."}:
            parent.mkdir(parents=True, exist_ok=True)
        self.c = canvas.Canvas(str(output_path), pagesize=A4)
        self.width, self.height = A4
        self.margin = max(0.75 * inch, kid_margin(self.width, self.height))
        self._renderers: Dict[str, PageRenderer] = {
            "coloring": coloring.render,
            "tracing": tracing.render,
            "counting": counting.render,
            "maze": maze.render,
            "matching": matching.render,
            "dot-to-dot": dot_to_dot.render,
        }

    # ------------------------------------------------------------------
    # Shared helpers exposed to page modules
    # ------------------------------------------------------------------
    def draw_border(self) -> None:
        self.c.setStrokeColor(colors.HexColor("#FF69B4"))
        self.c.setLineWidth(3)
        self.c.rect(
            self.margin / 2,
            self.margin / 2,
            self.width - self.margin,
            self.height - self.margin,
        )

    def draw_title(self, title: str, y_offset: int = 50) -> None:
        self.c.setFont("Helvetica-Bold", 24)
        self.c.setFillColor(colors.HexColor("#4A90E2"))
        self.c.drawCentredString(self.width / 2, self.height - y_offset, title)

    def draw_instruction(self, instruction: str, y_offset: int = 80) -> None:
        self.c.setFont("Helvetica", 14)
        self.c.setFillColor(colors.black)
        self.c.drawCentredString(self.width / 2, self.height - y_offset, instruction)

    def prep_kid_lines(self) -> None:
        self.c.setLineWidth(kid_stroke(self.width, self.height))
        self.c.setStrokeColor(colors.black)
        self.c.setFillColor(colors.white)

    def kid_stroke(self) -> int:
        return kid_stroke(self.width, self.height)

    # ------------------------------------------------------------------
    # Page rendering orchestration
    # ------------------------------------------------------------------
    def _page_helpers(self) -> Dict[str, Any]:
        return {
            "draw_border": self.draw_border,
            "draw_title": self.draw_title,
            "draw_instruction": self.draw_instruction,
            "prep_kid_lines": self.prep_kid_lines,
            "kid_stroke": self.kid_stroke,
            "generate_dot_positions": self.generate_dot_positions,
            "width": self.width,
            "height": self.height,
            "margin": self.margin,
        }

    def _resolve_renderer(self, page_type: Any) -> PageRenderer:
        normalized = str(page_type or "coloring").lower().strip()
        normalized = normalized.replace("_", "-")
        normalized = normalized.replace(" ", "-")
        renderer = self._renderers.get(normalized)
        if renderer is None and normalized != "coloring":
            renderer = self._renderers.get("coloring")
        return renderer or self._renderers["coloring"]

    def render_page(self, page_spec: PageSpec) -> None:
        renderer = self._resolve_renderer(page_spec.get("type"))
        renderer(self.c, page_spec, self._page_helpers())
        self.c.showPage()

    # ------------------------------------------------------------------
    # Specialized helpers
    # ------------------------------------------------------------------
    def generate_dot_positions(
        self, shape: str = "star", num_dots: int = 15
    ) -> List[Tuple[float, float]]:
        center_x = self.width / 2
        center_y = self.height / 2
        dots: List[Tuple[float, float]] = []

        if shape == "star":
            for i in range(num_dots):
                angle = (i / num_dots) * 2 * math.pi
                radius = 110 if i % 2 == 0 else 60
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                dots.append((x, y))
        elif shape == "circle":
            for i in range(num_dots):
                angle = (i / num_dots) * 2 * math.pi
                radius = 110
                x = center_x + radius * math.cos(angle)
                y = center_y + radius * math.sin(angle)
                dots.append((x, y))
        elif shape == "heart":
            for i in range(num_dots):
                t = (i / num_dots) * 2 * math.pi
                x = center_x + 60 * (16 * math.sin(t) ** 3) / 16
                y = center_y + 60 * (
                    13 * math.cos(t)
                    - 5 * math.cos(2 * t)
                    - 2 * math.cos(3 * t)
                    - math.cos(4 * t)
                ) / 13
                dots.append((x, y))
        return dots

    def save(self) -> None:
        self.c.save()


def generate_booklet(pages_data: List[PageSpec], output_file: str) -> None:
    generator = ActivityBookletGenerator(output_file)
    for page in pages_data:
        generator.render_page(page)
    generator.save()
    print(f"Booklet generated: {output_file}")


def sample_pages() -> List[PageSpec]:
    return [
        {
            "type": "coloring",
            "title": "Color the Leaf",
            "instruction": "Use your favorite crayons!",
            "subject": "leaf",
        },
        {
            "type": "coloring",
            "title": "Color the Acorn",
            "instruction": "Big bold lines!",
            "subject": "acorn",
        },
        {
            "type": "coloring",
            "title": "Color the Mushroom",
            "instruction": "Keep inside the lines!",
            "subject": "mushroom",
        },
        {
            "type": "coloring",
            "title": "Color the Pine Tree",
            "instruction": "One big outline!",
            "subject": "pine tree",
        },
        {
            "type": "coloring",
            "title": "Color the Cloud",
            "instruction": "Add a sky if you like!",
            "subject": "cloud",
        },
        {
            "type": "coloring",
            "title": "Color the Square",
            "instruction": "Go wild with colors!",
            "subject": "rounded square",
        },
    ]
