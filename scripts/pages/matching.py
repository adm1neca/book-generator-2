"""Matching page renderer."""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, Sequence

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics import renderPDF
from reportlab.lib.utils import ImageReader
from svglib.svglib import svg2rlg

from scripts.assets import normalize_slug
from scripts.drawing.shapes import get_renderer
from scripts.helpers import RenderContext, constants


logger = logging.getLogger(__name__)


def _draw_shape_from_library(c: Canvas, x: float, y: float, shape_name: str, size: float = 50) -> None:
    """Draw a shape from the shape library, centered at (x, y)."""
    renderer = get_renderer(shape_name)
    if renderer:
        logger.debug(f"Drawing shape from library: {shape_name} at ({x}, {y}), size={size}")
        # Save state and translate to create centered box
        c.saveState()
        c.translate(x - size / 2, y - size / 2)
        renderer(c, size, size)
        c.restoreState()
    else:
        logger.warning(f"Shape renderer not found for '{shape_name}', using fallback circle")
        # Fallback to circle
        c.circle(x, y, size / 2, stroke=1, fill=0)


def _draw_initial_placeholder(c: Canvas, x: float, y: float, name: str, size: float) -> None:
    """Draw a large initial as a kid-friendly fallback."""

    letter = (name or "?").strip()[:1].upper() or "?"
    font_size = max(28, size * 0.75)
    c.saveState()
    c.setFillColor(colors.HexColor("#FF69B4"))
    c.setFont("Helvetica-Bold", font_size)
    c.drawCentredString(x, y - font_size / 3, letter)
    c.restoreState()


def _draw_svg_asset(
    c: Canvas,
    ctx: RenderContext,
    x: float,
    y: float,
    asset_name: str,
    size: float = 50,
) -> None:
    """Draw an external asset via the shared context lookup."""

    if not asset_name:
        logger.debug("No asset name provided; falling back to shape library")
        _draw_shape_from_library(c, x, y, "circle", size)
        return

    slug = normalize_slug(asset_name)
    asset_path = ctx.asset_lookup(slug) or ctx.asset_lookup(asset_name)

    if not asset_path:
        logger.debug(f"Asset '{asset_name}' not found via context lookup; trying shape library")
        _draw_shape_from_library(c, x, y, asset_name, size)
        return

    try:
        suffix = asset_path.suffix.lower()
        if suffix == ".svg":
            drawing = svg2rlg(str(asset_path))
            if drawing:
                scale = min(size / drawing.width, size / drawing.height)
                logger.debug(
                    f"Rendering SVG '{asset_name}' from {asset_path} at ({x}, {y}), scale={scale:.2f}"
                )
                c.saveState()
                c.translate(x - (drawing.width * scale) / 2, y - (drawing.height * scale) / 2)
                c.scale(scale, scale)
                renderPDF.draw(drawing, c, 0, 0)
                c.restoreState()
                return
        elif suffix in {".png", ".jpg", ".jpeg"}:
            image = ImageReader(str(asset_path))
            width, height = image.getSize()
            scale = min(size / width, size / height)
            render_width = width * scale
            render_height = height * scale
            logger.debug(
                f"Rendering raster '{asset_name}' from {asset_path} at ({x}, {y}) sized {render_width:.1f}x{render_height:.1f}"
            )
            c.drawImage(
                image,
                x - render_width / 2,
                y - render_height / 2,
                width=render_width,
                height=render_height,
                mask="auto",
                preserveAspectRatio=True,
                anchor="c",
            )
            return
        else:
            logger.warning(f"Unsupported asset type '{asset_path.suffix}' for '{asset_name}'")
    except Exception as exc:
        logger.error(f"Failed to render asset '{asset_name}' from {asset_path}: {exc}")
        _draw_initial_placeholder(c, x, y, asset_name, size)
        return

    # If the asset couldn't be rendered (e.g., empty SVG), fall back to initial placeholder
    logger.warning(f"Asset '{asset_name}' from {asset_path} could not be rendered; drawing initial instead")
    _draw_initial_placeholder(c, x, y, asset_name, size)


def _draw_shape(c: Canvas, ctx: RenderContext, x: float, y: float, shape: str, size: float = 50) -> None:
    """Draw a shape - checks assets first, then shape library."""
    # First try to load from assets
    _draw_svg_asset(c, ctx, x, y, shape, size)


def _draw_matching_item(
    c: Canvas,
    ctx: RenderContext,
    x: float,
    y: float,
    item: Any,
    size: float = 60,
) -> None:
    """Draw a matching item - supports shapes, SVG assets, numbers, colors, and animals."""
    if isinstance(item, dict):
        item_type = item.get("type", "shape")
        logger.debug(f"Drawing matching item type '{item_type}': {item}")

        if item_type == "shape":
            _draw_shape(c, ctx, x, y, item.get("shape", "circle"), size)
        elif item_type == "animal":
            # Handle animal type - Claude uses either "name" or "animal" as key
            animal_name = item.get("name") or item.get("animal", "circle")
            logger.debug(f"Drawing animal '{animal_name}'")
            _draw_shape(c, ctx, x, y, animal_name, size)
        elif item_type == "number":
            c.setFont("Helvetica-Bold", 36)
            c.drawCentredString(x, y - 12, str(item.get("value", "1")))
        elif item_type == "color":
            try:
                c.setFillColor(colors.HexColor(item.get("color", "#000000")))
                c.circle(x, y, size / 2, stroke=1, fill=1)
            except Exception as e:
                logger.error(f"Failed to render color {item.get('color')}: {e}")
                c.circle(x, y, size / 2, stroke=1, fill=0)
            finally:
                c.setFillColor(colors.black)
        elif item_type == "asset":
            # Direct asset reference
            _draw_svg_asset(c, ctx, x, y, item.get("name", "circle"), size)
        else:
            # Unknown type - log warning and try to render as text
            logger.warning(f"Unknown item type '{item_type}', treating as text")
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(x, y - 8, str(item_type))
    else:
        # Plain string - try to interpret as shape/asset name first
        item_str = str(item)
        # Check if it's a known shape or asset
        slug = normalize_slug(item_str)
        asset_path = ctx.asset_lookup(slug) or ctx.asset_lookup(item_str)
        if asset_path or get_renderer(item_str):
            logger.debug(f"Rendering plain string '{item_str}' as shape/asset")
            _draw_shape(c, ctx, x, y, item_str, size)
        else:
            # Otherwise render as text
            logger.debug(f"Rendering plain string '{item_str}' as text")
            c.setFont("Helvetica-Bold", 36)
            c.drawCentredString(x, y - 12, item_str)


def render(c: Canvas, page_spec: Dict[str, Any], ctx: RenderContext) -> None:
    """
    Render a matching activity page.

    Refactored to use typed RenderContext and constants.
    """
    logger.info(f"Rendering matching page: {page_spec.get('title', 'Match the Pairs')}")

    # Draw page frame
    ctx.draw_border()
    ctx.draw_title(page_spec.get("title", "Match the Pairs"), constants.OFFSET_TITLE)
    ctx.draw_instruction("Draw lines to match the pairs!", constants.OFFSET_INSTRUCTION)

    # Get pairs configuration
    pairs: Sequence[Any] = page_spec.get("pairs", [])
    logger.info(f"Rendering {len(pairs)} pairs")

    # Use constants for layout
    left_x = ctx.width * 0.25
    right_x = ctx.width * 0.75
    start_y = ctx.height - constants.OFFSET_CONTENT_START_MATCHING
    spacing = constants.GRID_SPACING_LARGE
    item_size = constants.ITEM_SIZE_MEDIUM

    # Set stroke width
    c.setLineWidth(max(2, ctx.kid_stroke_width - 2))
    c.setStrokeColor(colors.black)

    # Shuffle right items for matching activity
    paired_types = (list, tuple)
    right_items = [pair[1] if isinstance(pair, paired_types) else pair for pair in pairs]
    random.shuffle(right_items)

    # Draw matching pairs (limit to 4 to fit on page)
    for i, pair in enumerate(pairs):
        if i >= 4:
            logger.debug(f"Limiting to 4 pairs (skipping remaining {len(pairs) - 4})")
            break

        y = start_y - i * spacing
        left_item = pair[0] if isinstance(pair, paired_types) else pair
        logger.debug(f"Pair {i+1}: left={left_item}, right={right_items[i] if i < len(right_items) else 'none'}")

        # Draw items
        _draw_matching_item(c, ctx, left_x, y, left_item, item_size)
        if i < len(right_items):
            _draw_matching_item(c, ctx, right_x, y, right_items[i], item_size)

        # Draw connection dots
        c.circle(left_x + 45, y, 5, stroke=1, fill=0)
        c.circle(right_x - 45, y, 5, stroke=1, fill=0)

    logger.info("Matching page rendering complete")
