"""Typed render context to replace untyped helpers dict."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from reportlab.pdfgen import canvas


@dataclass
class RenderContext:
    """
    Typed context for page rendering, replacing the untyped helpers dict.

    Provides access to canvas, dimensions, drawing utilities, and styling helpers.
    This gives IDEs autocomplete support and catches errors at development time.
    """

    # Canvas and dimensions
    canvas: canvas.Canvas
    width: float
    height: float
    margin: float

    # Drawing utilities
    draw_border: Callable[[], None]
    draw_title: Callable[[str, int], None]
    draw_instruction: Callable[[str, int], None]

    # Stroke and line preparation
    prep_kid_lines: Callable[[], None]
    kid_stroke_width: int  # Replaces kid_stroke() callable

    # Dot position generation
    generate_dot_positions: Callable[[str, int], List[Tuple[float, float]]]

    # Asset lookup
    asset_lookup: Callable[[Optional[str]], Optional[Path]]

    @property
    def center_x(self) -> float:
        """Center X coordinate of canvas."""
        return self.width / 2

    @property
    def center_y(self) -> float:
        """Center Y coordinate of canvas."""
        return self.height / 2

    @property
    def content_width(self) -> float:
        """Available width inside margins."""
        return self.width - (2 * self.margin)

    @property
    def content_height(self) -> float:
        """Available height inside margins."""
        return self.height - (2 * self.margin)
