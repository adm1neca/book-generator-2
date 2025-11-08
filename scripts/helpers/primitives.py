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
    def _sample_closed_path(
        points: list[tuple[float, float]],
        num_samples: int,
    ) -> list[tuple[float, float]]:
        """Sample evenly spaced points along a closed polyline path."""

        if num_samples <= 0:
            return []

        if not points:
            return []

        # Ensure we have at least two points to form segments
        if len(points) == 1:
            return [points[0]] * num_samples

        # Pre-compute cumulative segment lengths for proportional sampling
        segment_lengths: list[float] = []
        total_length = 0.0
        for index, start in enumerate(points):
            end = points[(index + 1) % len(points)]
            length = math.hypot(end[0] - start[0], end[1] - start[1])
            segment_lengths.append(length)
            total_length += length

        if total_length == 0:
            return [points[0]] * num_samples

        cumulative: list[float] = [0.0]
        running_total = 0.0
        for length in segment_lengths:
            running_total += length
            cumulative.append(running_total)

        sampled: list[tuple[float, float]] = []
        targets = [
            (total_length * i) / num_samples for i in range(num_samples)
        ]

        segment_index = 0
        for target in targets:
            # Advance to the segment that contains the current target distance
            while (
                segment_index < len(segment_lengths) - 1
                and target >= cumulative[segment_index + 1]
            ):
                segment_index += 1

            segment_length = segment_lengths[segment_index]
            if segment_length == 0:
                sampled.append(points[segment_index])
                continue

            start = points[segment_index]
            end = points[(segment_index + 1) % len(points)]
            segment_start_distance = cumulative[segment_index]
            position_ratio = (target - segment_start_distance) / segment_length

            x = start[0] + (end[0] - start[0]) * position_ratio
            y = start[1] + (end[1] - start[1]) * position_ratio
            sampled.append((x, y))

        return sampled

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
    def generate_dot_positions_square(
        center_x: float,
        center_y: float,
        num_dots: int,
        side_length: float = 200,
    ) -> list[tuple[float, float]]:
        """
        Generate dot positions in a square pattern.

        Distributes dots evenly around the perimeter of a square.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            num_dots: Number of dots to generate
            side_length: Square side length (default: 200)

        Returns:
            List of (x, y) dot positions
        """
        dots = []
        perimeter = 4 * side_length

        for i in range(num_dots):
            # Calculate position along perimeter (0 to perimeter)
            pos = (i / num_dots) * perimeter

            if pos < side_length:  # Top side
                x = center_x - side_length / 2 + pos
                y = center_y + side_length / 2
            elif pos < 2 * side_length:  # Right side
                x = center_x + side_length / 2
                y = center_y + side_length / 2 - (pos - side_length)
            elif pos < 3 * side_length:  # Bottom side
                x = center_x + side_length / 2 - (pos - 2 * side_length)
                y = center_y - side_length / 2
            else:  # Left side
                x = center_x - side_length / 2
                y = center_y - side_length / 2 + (pos - 3 * side_length)

            dots.append((x, y))
        return dots

    @staticmethod
    def generate_dot_positions_triangle(
        center_x: float,
        center_y: float,
        num_dots: int,
        height: float = 190,
    ) -> list[tuple[float, float]]:
        """
        Generate dot positions in a triangle pattern.

        Distributes dots evenly around the perimeter of an equilateral triangle.

        Args:
            center_x: Center X coordinate
            center_y: Center Y coordinate
            num_dots: Number of dots to generate
            height: Triangle height (default: 190)

        Returns:
            List of (x, y) dot positions
        """
        dots = []
        base = height * 2 / math.sqrt(3)  # Equilateral triangle ratio

        # Define the three vertices (top, bottom-right, bottom-left)
        vertices = [
            (center_x, center_y + height / 2),  # Top
            (center_x + base / 2, center_y - height / 2),  # Bottom-right
            (center_x - base / 2, center_y - height / 2),  # Bottom-left
        ]

        # Calculate perimeter
        side_length = base
        perimeter = 3 * side_length

        for i in range(num_dots):
            # Calculate position along perimeter
            pos = (i / num_dots) * perimeter

            if pos < side_length:  # Side 1: top to bottom-right
                t = pos / side_length
                x = vertices[0][0] + t * (vertices[1][0] - vertices[0][0])
                y = vertices[0][1] + t * (vertices[1][1] - vertices[0][1])
            elif pos < 2 * side_length:  # Side 2: bottom-right to bottom-left
                t = (pos - side_length) / side_length
                x = vertices[1][0] + t * (vertices[2][0] - vertices[1][0])
                y = vertices[1][1] + t * (vertices[2][1] - vertices[1][1])
            else:  # Side 3: bottom-left to top
                t = (pos - 2 * side_length) / side_length
                x = vertices[2][0] + t * (vertices[0][0] - vertices[2][0])
                y = vertices[2][1] + t * (vertices[0][1] - vertices[2][1])

            dots.append((x, y))
        return dots

    @staticmethod
    def generate_dot_positions_diamond(
        center_x: float,
        center_y: float,
        num_dots: int,
        width: float = 200,
        height: float = 220,
    ) -> list[tuple[float, float]]:
        """Generate dot positions outlining a diamond shape."""

        points = [
            (center_x, center_y + height / 2),
            (center_x + width / 2, center_y),
            (center_x, center_y - height / 2),
            (center_x - width / 2, center_y),
        ]
        return Primitives._sample_closed_path(points, max(num_dots, 4))

    @staticmethod
    def generate_dot_positions_house(
        center_x: float,
        center_y: float,
        num_dots: int,
        body_width: float = 220,
        body_height: float = 140,
        roof_height: float = 110,
    ) -> list[tuple[float, float]]:
        """Generate dot positions outlining a classic house silhouette."""

        base_y = center_y - body_height / 2
        top_y = base_y + body_height

        points = [
            (center_x - body_width / 2, base_y),
            (center_x + body_width / 2, base_y),
            (center_x + body_width / 2, top_y),
            (center_x, top_y + roof_height),
            (center_x - body_width / 2, top_y),
        ]

        return Primitives._sample_closed_path(points, max(num_dots, 8))

    @staticmethod
    def generate_dot_positions_tree(
        center_x: float,
        center_y: float,
        num_dots: int,
        canopy_radius: float = 120,
        trunk_width: float = 60,
        trunk_height: float = 120,
    ) -> list[tuple[float, float]]:
        """Generate dot positions outlining a stylized tree."""

        target = max(num_dots, 12)

        canopy_center_y = center_y + trunk_height * 0.25
        canopy_points: list[tuple[float, float]] = []
        lobes = 6
        for i in range(lobes * 2):
            angle = (i / (lobes * 2)) * 2 * math.pi
            radius = canopy_radius * (0.8 + 0.2 * math.sin(lobes * angle))
            x = center_x + radius * math.cos(angle)
            y = canopy_center_y + radius * 0.8 * math.sin(angle)
            canopy_points.append((x, y))

        trunk_top_y = center_y - trunk_height / 2
        trunk_bottom_y = trunk_top_y - trunk_height
        trunk_points = [
            (center_x - trunk_width / 2, trunk_bottom_y),
            (center_x + trunk_width / 2, trunk_bottom_y),
            (center_x + trunk_width / 2, trunk_top_y),
            (center_x - trunk_width / 2, trunk_top_y),
        ]

        path = canopy_points + trunk_points
        return Primitives._sample_closed_path(path, target)

    @staticmethod
    def generate_dot_positions_flower(
        center_x: float,
        center_y: float,
        num_dots: int,
        base_radius: float = 80,
        petal_amplitude: float = 40,
        petals: int = 6,
    ) -> list[tuple[float, float]]:
        """Generate dot positions approximating a multi-petal flower."""

        target = max(num_dots, petals * 2)
        dots = []
        for i in range(target):
            angle = (i / target) * 2 * math.pi
            radius = base_radius + petal_amplitude * math.sin(petals * angle)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            dots.append((x, y))
        return dots

    @staticmethod
    def generate_dot_positions_butterfly(
        center_x: float,
        center_y: float,
        num_dots: int,
        wing_span: float = 200,
        wing_height: float = 140,
    ) -> list[tuple[float, float]]:
        """Generate dot positions for a stylized butterfly silhouette."""

        target = max(num_dots, 16)
        dots = []
        for i in range(target):
            angle = (i / target) * 2 * math.pi
            # Create mirrored lobes for left/right wings using cosine weighting
            horizontal = math.cos(angle)
            vertical = math.sin(angle)
            lobe_factor = 0.6 + 0.4 * abs(vertical)
            wing_x = wing_span * 0.5 * horizontal * lobe_factor
            wing_y = wing_height * 0.5 * vertical * (0.7 + 0.3 * abs(horizontal))

            # Pinch shape toward the body at the center
            body_pull = 40 * math.cos(2 * angle)
            x = center_x + wing_x + body_pull
            y = center_y + wing_y
            dots.append((x, y))
        return dots

    @staticmethod
    def generate_dot_positions_fish(
        center_x: float,
        center_y: float,
        num_dots: int,
        body_length: float = 220,
        body_height: float = 110,
        tail_length: float = 90,
    ) -> list[tuple[float, float]]:
        """Generate dot positions outlining a fish with a triangular tail."""

        points = [
            (center_x + body_length / 2, center_y),  # nose
            (center_x + body_length / 2 - 30, center_y + body_height / 2),
            (center_x, center_y + body_height * 0.7),
            (center_x - body_length / 2 + 20, center_y + body_height / 2),
            (center_x - body_length / 2, center_y + tail_length / 2),
            (center_x - body_length / 2 - tail_length, center_y),
            (center_x - body_length / 2, center_y - tail_length / 2),
            (center_x - body_length / 2 + 20, center_y - body_height / 2),
            (center_x, center_y - body_height * 0.7),
            (center_x + body_length / 2 - 30, center_y - body_height / 2),
        ]

        return Primitives._sample_closed_path(points, max(num_dots, 10))

    @staticmethod
    def generate_dot_positions_apple(
        center_x: float,
        center_y: float,
        num_dots: int,
        width: float = 170,
        height: float = 190,
    ) -> list[tuple[float, float]]:
        """Generate dot positions outlining a plump apple."""

        top_y = center_y + height / 2
        bottom_y = center_y - height / 2

        points = [
            (center_x, top_y),
            (center_x + width * 0.25, top_y * 0.98 + bottom_y * 0.02),
            (center_x + width * 0.45, center_y + height * 0.35),
            (center_x + width * 0.5, center_y),
            (center_x + width * 0.35, center_y - height * 0.35),
            (center_x, bottom_y),
            (center_x - width * 0.35, center_y - height * 0.35),
            (center_x - width * 0.5, center_y),
            (center_x - width * 0.45, center_y + height * 0.35),
            (center_x - width * 0.25, top_y * 0.98 + bottom_y * 0.02),
        ]

        # Create a gentle indentation at the top by nudging the first and last points inward
        indentation = width * 0.15
        points[0] = (center_x, top_y)
        points[1] = (center_x + width * 0.2, top_y - indentation)
        points[-1] = (center_x - width * 0.2, top_y - indentation)

        return Primitives._sample_closed_path(points, max(num_dots, 12))

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
