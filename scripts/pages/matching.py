"""Matching page renderer."""

from __future__ import annotations

import logging
import random
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas
from reportlab.graphics import renderPDF
from svglib.svglib import svg2rlg

from scripts.drawing.shapes import get_renderer
from scripts.assets import load_assets


logger = logging.getLogger(__name__)


# Lazy load assets
_ASSETS = None


def _get_assets():
    """Lazy load assets on first use."""
    global _ASSETS
    if _ASSETS is None:
        logger.info("Loading assets from assets directory...")
        _ASSETS = load_assets()
        logger.info(f"Loaded {len(_ASSETS)} assets: {list(_ASSETS.keys())}")
    return _ASSETS


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


def _draw_svg_asset(c: Canvas, x: float, y: float, asset_name: str, size: float = 50) -> None:
    """Draw an SVG asset from the assets directory, scaled to size."""
    assets = _get_assets()

    # Normalize asset name to slug
    slug = asset_name.lower().strip().replace(' ', '-')

    if slug in assets:
        asset_path = assets[slug]
        logger.debug(f"Found asset '{slug}' at path: {asset_path}")
        if asset_path.suffix.lower() == '.svg':
            try:
                # Load and render SVG
                drawing = svg2rlg(str(asset_path))
                if drawing:
                    # Calculate scale to fit in size box
                    scale = min(size / drawing.width, size / drawing.height)
                    logger.debug(f"Rendering SVG '{slug}' at ({x}, {y}), scale={scale:.2f}")

                    # Save state, translate and scale
                    c.saveState()
                    c.translate(x - (drawing.width * scale) / 2, y - (drawing.height * scale) / 2)
                    c.scale(scale, scale)

                    # Render the SVG
                    renderPDF.draw(drawing, c, 0, 0)
                    c.restoreState()
                    return
            except Exception as e:
                logger.error(f"Failed to render SVG '{slug}': {e}")
    else:
        logger.debug(f"Asset '{slug}' not found in assets, trying shape library")

    # Fallback: try to draw from shape library
    _draw_shape_from_library(c, x, y, asset_name, size)


def _draw_shape(c: Canvas, x: float, y: float, shape: str, size: float = 50) -> None:
    """Draw a shape - checks assets first, then shape library."""
    # First try to load from assets
    _draw_svg_asset(c, x, y, shape, size)


def _draw_matching_item(c: Canvas, x: float, y: float, item: Any, size: float = 60) -> None:
    """Draw a matching item - supports shapes, SVG assets, numbers, colors, and animals."""
    if isinstance(item, dict):
        item_type = item.get("type", "shape")
        logger.debug(f"Drawing matching item type '{item_type}': {item}")

        if item_type == "shape":
            _draw_shape(c, x, y, item.get("shape", "circle"), size)
        elif item_type == "animal":
            # Handle animal type - Claude uses either "name" or "animal" as key
            animal_name = item.get("name") or item.get("animal", "circle")
            logger.debug(f"Drawing animal '{animal_name}'")
            _draw_shape(c, x, y, animal_name, size)
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
            _draw_svg_asset(c, x, y, item.get("name", "circle"), size)
        else:
            # Unknown type - log warning and try to render as text
            logger.warning(f"Unknown item type '{item_type}', treating as text")
            c.setFont("Helvetica-Bold", 24)
            c.drawCentredString(x, y - 8, str(item_type))
    else:
        # Plain string - try to interpret as shape/asset name first
        item_str = str(item)
        assets = _get_assets()
        # Check if it's a known shape or asset
        if item_str.lower() in assets or get_renderer(item_str):
            logger.debug(f"Rendering plain string '{item_str}' as shape/asset")
            _draw_shape(c, x, y, item_str, size)
        else:
            # Otherwise render as text
            logger.debug(f"Rendering plain string '{item_str}' as text")
            c.setFont("Helvetica-Bold", 36)
            c.drawCentredString(x, y - 12, item_str)


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    logger.info(f"Rendering matching page: {page_spec.get('title', 'Match the Pairs')}")

    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Match the Pairs"))
    helpers["draw_instruction"]("Draw lines to match the pairs!")

    pairs: Sequence[Any] = page_spec.get("pairs", [])
    logger.info(f"Rendering {len(pairs)} pairs")

    left_x = helpers["width"] * 0.25
    right_x = helpers["width"] * 0.75
    start_y = helpers["height"] - 150
    spacing = 110  # Increased spacing for larger shapes
    item_size = 70  # Size for shape/asset rendering

    c.setLineWidth(max(2, helpers["kid_stroke"]() - 2))
    c.setStrokeColor(colors.black)

    paired_types = (list, tuple)
    right_items = [pair[1] if isinstance(pair, paired_types) else pair for pair in pairs]
    random.shuffle(right_items)

    for i, pair in enumerate(pairs):
        if i >= 4:
            logger.debug(f"Limiting to 4 pairs (skipping remaining {len(pairs) - 4})")
            break
        y = start_y - i * spacing
        left_item = pair[0] if isinstance(pair, paired_types) else pair
        logger.debug(f"Pair {i+1}: left={left_item}, right={right_items[i] if i < len(right_items) else 'none'}")

        _draw_matching_item(c, left_x, y, left_item, item_size)
        if i < len(right_items):
            _draw_matching_item(c, right_x, y, right_items[i], item_size)
        c.circle(left_x + 45, y, 5, stroke=1, fill=0)
        c.circle(right_x - 45, y, 5, stroke=1, fill=0)

    logger.info("Matching page rendering complete")
