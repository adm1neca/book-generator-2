"""Layout and grid positioning utilities.

Centralizes grid calculation logic that was scattered across page modules.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from scripts.helpers import constants


@dataclass
class GridConfig:
    """Configuration for grid-based layouts."""

    item_count: int
    spacing: float = constants.GRID_SPACING_SMALL
    max_cols: int = constants.MAX_GRID_COLS
    start_y_offset: float = constants.OFFSET_CONTENT_START_DEFAULT


@dataclass
class GridPosition:
    """A single position in a grid."""

    x: float
    y: float
    row: int
    col: int


class LayoutHelpers:
    """
    Grid and positioning utilities.

    Replaces manual grid calculations scattered across counting.py, matching.py, etc.
    """

    @staticmethod
    def calculate_grid_positions(
        canvas_width: float,
        canvas_height: float,
        config: GridConfig,
    ) -> list[GridPosition]:
        """
        Calculate grid positions for items.

        Args:
            canvas_width: Canvas width
            canvas_height: Canvas height
            config: Grid configuration

        Returns:
            List of GridPosition objects with x, y, row, col for each item
        """
        # Calculate grid dimensions
        cols = min(config.max_cols, config.item_count)
        rows = math.ceil(config.item_count / cols)

        # Calculate starting position (centered)
        grid_width = cols * config.spacing
        start_x = canvas_width / 2 - grid_width / 2

        # Start Y position from top
        start_y = canvas_height - config.start_y_offset

        # Generate positions
        positions = []
        for i in range(config.item_count):
            row = i // cols
            col = i % cols
            x = start_x + col * config.spacing
            y = start_y - row * config.spacing
            positions.append(GridPosition(x=x, y=y, row=row, col=col))

        return positions

    @staticmethod
    def calculate_centered_grid(
        canvas_width: float,
        item_count: int,
        spacing: float,
        max_cols: int = constants.MAX_GRID_COLS,
    ) -> tuple[int, int, float]:
        """
        Calculate grid dimensions and starting X position.

        Args:
            canvas_width: Canvas width
            item_count: Number of items to lay out
            spacing: Spacing between items
            max_cols: Maximum columns (default: 5)

        Returns:
            Tuple of (cols, rows, start_x)
        """
        cols = min(max_cols, item_count)
        rows = math.ceil(item_count / cols)
        grid_width = cols * spacing
        start_x = canvas_width / 2 - grid_width / 2
        return cols, rows, start_x

    @staticmethod
    def calculate_two_column_layout(
        canvas_width: float,
        canvas_height: float,
        item_count: int,
        spacing: float = constants.GRID_SPACING_LARGE,
        start_y_offset: float = constants.OFFSET_CONTENT_START_MATCHING,
    ) -> tuple[list[tuple[float, float]], list[tuple[float, float]]]:
        """
        Calculate positions for two-column matching layout.

        Args:
            canvas_width: Canvas width
            canvas_height: Canvas height
            item_count: Number of items per column
            spacing: Vertical spacing between items (default: 110)
            start_y_offset: Y offset from top (default: 150)

        Returns:
            Tuple of (left_positions, right_positions)
        """
        left_x = canvas_width * 0.25
        right_x = canvas_width * 0.75
        start_y = canvas_height - start_y_offset

        left_positions = []
        right_positions = []

        for i in range(item_count):
            y = start_y - i * spacing
            left_positions.append((left_x, y))
            right_positions.append((right_x, y))

        return left_positions, right_positions

    @staticmethod
    def center_x(canvas_width: float, item_width: float) -> float:
        """
        Calculate X position to center an item.

        Args:
            canvas_width: Canvas width
            item_width: Item width

        Returns:
            X position for centering
        """
        return (canvas_width - item_width) / 2

    @staticmethod
    def center_y(canvas_height: float, item_height: float) -> float:
        """
        Calculate Y position to center an item.

        Args:
            canvas_height: Canvas height
            item_height: Item height

        Returns:
            Y position for centering
        """
        return (canvas_height - item_height) / 2

    @staticmethod
    def distribute_horizontal(
        canvas_width: float,
        margin: float,
        item_count: int,
    ) -> list[float]:
        """
        Distribute items evenly across horizontal space.

        Args:
            canvas_width: Canvas width
            margin: Left/right margin
            item_count: Number of items

        Returns:
            List of X positions
        """
        available_width = canvas_width - 2 * margin
        spacing = available_width / (item_count + 1)
        return [margin + spacing * (i + 1) for i in range(item_count)]

    @staticmethod
    def distribute_vertical(
        canvas_height: float,
        top_offset: float,
        bottom_offset: float,
        item_count: int,
    ) -> list[float]:
        """
        Distribute items evenly across vertical space.

        Args:
            canvas_height: Canvas height
            top_offset: Offset from top
            bottom_offset: Offset from bottom
            item_count: Number of items

        Returns:
            List of Y positions
        """
        available_height = canvas_height - top_offset - bottom_offset
        spacing = available_height / (item_count + 1)
        return [canvas_height - top_offset - spacing * (i + 1) for i in range(item_count)]
