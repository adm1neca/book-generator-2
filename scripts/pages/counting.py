"""Counting page renderer."""

from __future__ import annotations

from typing import Any, Dict

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from scripts.helpers import GridConfig, LayoutHelpers, Primitives, RenderContext, constants


def render(c: Canvas, page_spec: Dict[str, Any], ctx: RenderContext) -> None:
    """
    Render a counting activity page.

    Refactored to use typed RenderContext, reusable Primitives,
    LayoutHelpers, and constants instead of magic numbers.
    """
    # Draw page frame
    ctx.draw_border()
    ctx.draw_title(page_spec.get("title", "Count"), constants.OFFSET_TITLE)
    ctx.draw_instruction("Count and write the number", constants.OFFSET_INSTRUCTION)

    # Get page configuration
    try:
        count = int(page_spec.get("count", 5))
    except (TypeError, ValueError):
        count = 0
    count = max(count, 0)
    item = page_spec.get("item", "circle")

    # Set stroke width using kid-friendly width
    c.setLineWidth(max(2, ctx.kid_stroke_width - 2))
    c.setStrokeColor(colors.black)

    # Calculate grid positions using LayoutHelpers
    grid_config = GridConfig(
        item_count=count,
        spacing=constants.GRID_SPACING_SMALL,
        max_cols=constants.MAX_GRID_COLS,
        start_y_offset=constants.OFFSET_CONTENT_START_COUNTING,
    )
    positions = LayoutHelpers.calculate_grid_positions(ctx.width, ctx.height, grid_config)

    # Draw items at calculated positions using Primitives
    lower_item = str(item).lower()
    if positions:
        for pos in positions:
            if "circle" in lower_item:
                Primitives.draw_circle(c, pos.x, pos.y, constants.STAR_OUTER_RADIUS)
            elif "star" in lower_item:
                Primitives.draw_star(c, pos.x, pos.y)
            elif "heart" in lower_item:
                Primitives.draw_heart(c, pos.x, pos.y)
            else:
                Primitives.draw_square(c, pos.x, pos.y, 30)

    # Draw answer box
    c.setFont(constants.FONT_FAMILY_BODY, constants.FONT_SIZE_NUMBER)
    c.setFillColor(colors.black)
    c.drawCentredString(ctx.center_x, 150, "How many? Write your answer:")
    c.setStrokeColor(colors.black)
    c.setLineWidth(2)
    c.rect(ctx.center_x - 40, 100, 80, 60, stroke=1, fill=0)
