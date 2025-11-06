"""Reusable primitive shapes for page rendering.

Consolidates duplicate shape drawing code from counting.py and shapes.py.
Provides both small item-sized primitives and full-page shapes.
"""

from __future__ import annotations

import math

from reportlab.pdfgen.canvas import Canvas

from scripts.helpers import constants


class Primitives:
    """
    Reusable primitive shapes with consistent APIs.

    All primitives use (x, y, size, stroke_width) signature for consistency.
    This replaces duplicate implementations across counting.py, matching.py, etc.
    """

    # ==================================================================
    # SMALL ITEM PRIMITIVES (for counting, matching, etc.)
    # ==================================================================

    @staticmethod
    def draw_star(
        c: Canvas,
        x: float,
        y: float,
        outer_radius: float = constants.STAR_OUTER_RADIUS,
        inner_radius: float = constants.STAR_INNER_RADIUS,
    ) -> None:
        """
        Draw a 5-pointed star centered at (x, y).

        Args:
            c: ReportLab canvas
            x: Center X coordinate
            y: Center Y coordinate
            outer_radius: Outer point radius (default: 20)
            inner_radius: Inner point radius (default: 10)
        """
        points = []
        # 10 points total (5 outer, 5 inner)
        for i in range(constants.STAR_POINTS):
            angle = math.radians(i * constants.STAR_ANGLE_DEGREES + constants.STAR_START_ANGLE)
            radius = outer_radius if i % 2 == 0 else inner_radius
            px = x + radius * math.cos(angle)
            py = y + radius * math.sin(angle)
            points.append((px, py))

        path = c.beginPath()
        path.moveTo(points[0][0], points[0][1])
        for px, py in points[1:]:
            path.lineTo(px, py)
        path.close()
        c.drawPath(path, stroke=1, fill=0)

    @staticmethod
    def draw_heart(
        c: Canvas,
        x: float,
        y: float,
        size: float = constants.HEART_SIZE,
    ) -> None:
        """
        Draw a heart centered at (x, y).

        Args:
            c: ReportLab canvas
            x: Center X coordinate
            y: Center Y coordinate
            size: Heart size scale factor (default: 15)
        """
        # Use proportional offsets based on size
        path = c.beginPath()
        path.moveTo(x, y - size)
        path.curveTo(
            x - size * 1.33,  # -20 when size=15
            y + size * 0.67,  # +10 when size=15
            x - size,  # -15 when size=15
            y + size,  # +15 when size=15
            x,
            y + size * 0.33,  # +5 when size=15
        )
        path.curveTo(
            x + size,  # +15 when size=15
            y + size,  # +15 when size=15
            x + size * 1.33,  # +20 when size=15
            y + size * 0.67,  # +10 when size=15
            x,
            y - size,
        )
        c.drawPath(path, stroke=1, fill=0)

    @staticmethod
    def draw_circle(
        c: Canvas,
        x: float,
        y: float,
        radius: float = constants.STAR_OUTER_RADIUS,
    ) -> None:
        """
        Draw a circle centered at (x, y).

        Args:
            c: ReportLab canvas
            x: Center X coordinate
            y: Center Y coordinate
            radius: Circle radius (default: 20)
        """
        c.circle(x, y, radius, stroke=1, fill=0)

    @staticmethod
    def draw_square(
        c: Canvas,
        x: float,
        y: float,
        size: float = 30,
    ) -> None:
        """
        Draw a square centered at (x, y).

        Args:
            c: ReportLab canvas
            x: Center X coordinate
            y: Center Y coordinate
            size: Square side length (default: 30)
        """
        half_size = size / 2
        c.rect(x - half_size, y - half_size, size, size, stroke=1, fill=0)

    # ==================================================================
    # DOT LAYOUTS (for dot-to-dot activities)
    # ==================================================================

    @staticmethod
    def generate_dot_positions_star(
        center_x: float,
        center_y: float,
        num_dots: int,
        outer_radius: float = constants.DOT_SHAPE_STAR_OUTER,
        inner_radius: float = constants.DOT_SHAPE_STAR_INNER,
    ) -> list[tuple[float, float]]:
        """
        Generate dot positions in a star pattern.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            num_dots: Number of dots to generate
            outer_radius: Outer point radius (default: 110)
            inner_radius: Inner point radius (default: 60)

        Returns:
            List of (x, y) dot positions
        """
        dots = []
        for i in range(num_dots):
            angle = (i / num_dots) * 2 * math.pi
            radius = outer_radius if i % 2 == 0 else inner_radius
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            dots.append((x, y))
        return dots

    @staticmethod
    def generate_dot_positions_circle(
        center_x: float,
        center_y: float,
        num_dots: int,
        radius: float = constants.DOT_SHAPE_CIRCLE_RADIUS,
    ) -> list[tuple[float, float]]:
        """
        Generate dot positions in a circle pattern.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            num_dots: Number of dots to generate
            radius: Circle radius (default: 110)

        Returns:
            List of (x, y) dot positions
        """
        dots = []
        for i in range(num_dots):
            angle = (i / num_dots) * 2 * math.pi
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            dots.append((x, y))
        return dots

    @staticmethod
    def generate_dot_positions_heart(
        center_x: float,
        center_y: float,
        num_dots: int,
        scale: float = constants.DOT_SHAPE_HEART_SCALE,
    ) -> list[tuple[float, float]]:
        """
        Generate dot positions in a heart pattern.

        Uses parametric heart equations.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            num_dots: Number of dots to generate
            scale: Heart size scale (default: 60)

        Returns:
            List of (x, y) dot positions
        """
        dots = []
        for i in range(num_dots):
            t = (i / num_dots) * 2 * math.pi
            # Parametric heart equations
            x = center_x + scale * (16 * math.sin(t) ** 3) / 16
            y = center_y + scale * (
                13 * math.cos(t)
                - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t)
                - math.cos(4 * t)
            ) / 13
            dots.append((x, y))
        return dots

    @staticmethod
    def draw_dots(
        c: Canvas,
        positions: list[tuple[float, float]],
        radius: float = constants.DOT_RADIUS,
        numbered: bool = True,
    ) -> None:
        """
        Draw numbered dots at given positions.

        Args:
            c: ReportLab canvas
            positions: List of (x, y) positions
            radius: Dot radius (default: 4)
            numbered: Whether to draw numbers on dots (default: True)
        """
        for idx, (x, y) in enumerate(positions, start=1):
            # Draw the dot
            c.circle(x, y, radius, stroke=1, fill=1)

            # Draw the number if requested
            if numbered:
                c.setFont(constants.FONT_FAMILY_BODY, 10)
                c.drawCentredString(x, y - radius - 8, str(idx))
