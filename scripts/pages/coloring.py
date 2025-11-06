"""Coloring page renderer."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, Tuple

from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from scripts.drawing.shapes import get_renderer


logger = logging.getLogger(__name__)

_RASTER_EXTENSIONS = {".png", ".jpg", ".jpeg"}


def _coloring_box(helpers: Dict[str, Any]) -> Tuple[float, float, float, float]:
    width = float(helpers["width"])
    height = float(helpers["height"])
    margin = float(helpers.get("margin", min(width, height) * 0.07))
    return margin, margin, width - 2 * margin, height - 2 * margin


def _draw_asset(c: Canvas, path: Path, box: Tuple[float, float, float, float]) -> bool:
    x, y, box_width, box_height = box
    suffix = path.suffix.lower()
    try:
        if suffix == ".svg":
            drawing = svg2rlg(str(path))
            if drawing is None or drawing.width == 0 or drawing.height == 0:
                return False
            scale = min(box_width / drawing.width, box_height / drawing.height)
            min_x = getattr(drawing, "minX", 0.0)
            min_y = getattr(drawing, "minY", 0.0)
            translate_x = x + (box_width - drawing.width * scale) / 2
            translate_y = y + (box_height - drawing.height * scale) / 2
            drawing.scale(scale, scale)
            renderPDF.draw(
                drawing,
                c,
                translate_x - min_x * scale,
                translate_y - min_y * scale,
            )
        elif suffix in _RASTER_EXTENSIONS:
            image = ImageReader(str(path))
            img_width, img_height = image.getSize()
            if img_width == 0 or img_height == 0:
                return False
            scale = min(box_width / img_width, box_height / img_height)
            draw_width = img_width * scale
            draw_height = img_height * scale
            draw_x = x + (box_width - draw_width) / 2
            draw_y = y + (box_height - draw_height) / 2
            c.drawImage(
                image,
                draw_x,
                draw_y,
                width=draw_width,
                height=draw_height,
                preserveAspectRatio=True,
                mask="auto",
            )
        else:
            return False
    except Exception as exc:  # pragma: no cover - rendering errors are non-critical
        logger.warning("Failed to draw asset %s: %s", path, exc)
        return False
    return True


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Coloring Page"))
    helpers["draw_instruction"](
        page_spec.get("instruction", "Use your favorite crayons!")
    )

    helpers["prep_kid_lines"]()
    c.setFillColor(colors.white)
    asset_lookup = helpers.get("asset_lookup")
    subject = (
        page_spec.get("subject")
        or page_spec.get("subjectHint")
        or "circle"
    )

    asset_path = None
    if callable(asset_lookup):
        if page_spec.get("asset"):
            asset_path = asset_lookup(page_spec["asset"])
        if asset_path is None and subject:
            asset_path = asset_lookup(subject)

    if isinstance(asset_path, Path) and asset_path.exists():
        if _draw_asset(c, asset_path, _coloring_box(helpers)):
            return

    renderer = get_renderer(subject)
    renderer(c, helpers["width"], helpers["height"])
