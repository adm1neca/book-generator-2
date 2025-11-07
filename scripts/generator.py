"""Core activity booklet generator."""

from __future__ import annotations
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from scripts.assets import load_assets, normalize_slug
from scripts.helpers import Primitives, RenderContext
from scripts.pages import coloring, counting, dot_to_dot, matching, maze, tracing

PageSpec = Dict[str, Any]
# Updated signature to use RenderContext instead of Dict
PageRenderer = Callable[[canvas.Canvas, PageSpec, RenderContext], None]


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
        self.asset_map = load_assets()
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
    def _page_helpers(self) -> RenderContext:
        """
        Create typed RenderContext for page rendering.

        Replaces the old untyped dict-based helpers.
        """
        return RenderContext(
            canvas=self.c,
            width=self.width,
            height=self.height,
            margin=self.margin,
            draw_border=self.draw_border,
            draw_title=self.draw_title,
            draw_instruction=self.draw_instruction,
            prep_kid_lines=self.prep_kid_lines,
            kid_stroke_width=self.kid_stroke(),
            generate_dot_positions=self.generate_dot_positions,
            asset_lookup=self.lookup_asset,
        )

    def lookup_asset(self, name: str | None) -> Path | None:
        if not name:
            return None
        slug = normalize_slug(str(name))
        return self.asset_map.get(slug)

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
        shape_key = str(shape or "circle").lower().strip()

        generators: Dict[str, Callable[[float, float, int], List[Tuple[float, float]]]] = {
            "star": Primitives.generate_dot_positions_star,
            "circle": Primitives.generate_dot_positions_circle,
            "heart": Primitives.generate_dot_positions_heart,
            "square": Primitives.generate_dot_positions_square,
            "triangle": Primitives.generate_dot_positions_triangle,
            "diamond": Primitives.generate_dot_positions_diamond,
            "house": Primitives.generate_dot_positions_house,
            "tree": Primitives.generate_dot_positions_tree,
            "flower": Primitives.generate_dot_positions_flower,
            "butterfly": Primitives.generate_dot_positions_butterfly,
            "fish": Primitives.generate_dot_positions_fish,
            "apple": Primitives.generate_dot_positions_apple,
        }

        generator = generators.get(shape_key, Primitives.generate_dot_positions_circle)
        return generator(center_x, center_y, num_dots)

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
