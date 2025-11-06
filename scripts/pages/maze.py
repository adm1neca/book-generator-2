"""Maze page renderer with proper maze generation."""

from __future__ import annotations

import logging
import random
from typing import Any, Dict, Set, Tuple

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas

from scripts.helpers import RenderContext, constants


logger = logging.getLogger(__name__)


def _generate_simple_maze(grid_size: int, seed: int = None) -> Set[Tuple[int, int, str]]:
    """Generate a simple maze for toddlers using DFS.

    Args:
        grid_size: Size of the maze grid (NxN)
        seed: Random seed for reproducibility

    Returns:
        Set of (x, y, direction) tuples representing walls to REMOVE
        where direction is 'right' (remove wall to the right of cell)
        or 'down' (remove wall below cell)
    """
    if seed is not None:
        random.seed(seed)
        logger.debug(f"Generating maze with seed={seed}, grid_size={grid_size}")

    # Track visited cells
    visited: Set[Tuple[int, int]] = set()
    walls_to_remove: Set[Tuple[int, int, str]] = set()

    def get_unvisited_neighbors(x: int, y: int) -> list[Tuple[int, int, str]]:
        """Get unvisited neighbors of cell (x, y)."""
        neighbors = []
        # Right
        if x < grid_size - 1 and (x + 1, y) not in visited:
            neighbors.append((x + 1, y, 'right'))
        # Down
        if y < grid_size - 1 and (x, y + 1) not in visited:
            neighbors.append((x, y + 1, 'down'))
        # Left
        if x > 0 and (x - 1, y) not in visited:
            neighbors.append((x - 1, y, 'left'))
        # Up
        if y > 0 and (x, y - 1) not in visited:
            neighbors.append((x, y - 1, 'up'))
        return neighbors

    def carve_path(x: int, y: int) -> None:
        """Recursively carve paths through the maze using DFS."""
        visited.add((x, y))

        # Get neighbors in random order
        neighbors = get_unvisited_neighbors(x, y)
        random.shuffle(neighbors)

        for nx, ny, direction in neighbors:
            if (nx, ny) not in visited:
                # Remove wall between current cell and neighbor
                if direction == 'right':
                    walls_to_remove.add((x, y, 'right'))
                elif direction == 'down':
                    walls_to_remove.add((x, y, 'down'))
                elif direction == 'left':
                    walls_to_remove.add((nx, ny, 'right'))
                elif direction == 'up':
                    walls_to_remove.add((nx, ny, 'down'))

                # Recursively carve from neighbor
                carve_path(nx, ny)

    # Start from top-left (0, 0)
    carve_path(0, 0)

    logger.info(f"Generated maze: {len(visited)} cells visited, {len(walls_to_remove)} walls removed")
    logger.debug(f"Walls removed: {walls_to_remove}")

    return walls_to_remove


def _draw_maze_grid(c: Canvas, grid_size: int, start_x: float, start_y: float,
                    cell_size: float, walls_to_remove: Set[Tuple[int, int, str]]) -> None:
    """Draw a maze grid with walls."""
    logger.debug(f"Drawing maze grid: grid_size={grid_size}, cell_size={cell_size}")

    horizontal_walls = 0
    vertical_walls = 0

    # Draw all horizontal lines (except where walls are removed)
    for y in range(grid_size + 1):
        for x in range(grid_size):
            # Check if this horizontal wall should be drawn
            # Horizontal walls are below cells, so check if (x, y-1, 'down') is in walls_to_remove
            should_draw = True
            if y > 0 and y < grid_size and (x, y - 1, 'down') in walls_to_remove:
                should_draw = False

            if should_draw:
                x1 = start_x + x * cell_size
                x2 = start_x + (x + 1) * cell_size
                y_pos = start_y - y * cell_size
                c.line(x1, y_pos, x2, y_pos)
                horizontal_walls += 1

    # Draw all vertical lines (except where walls are removed)
    for x in range(grid_size + 1):
        for y in range(grid_size):
            # Check if this vertical wall should be drawn
            # Vertical walls are to the right of cells, so check if (x-1, y, 'right') is in walls_to_remove
            should_draw = True
            if x > 0 and x < grid_size and (x - 1, y, 'right') in walls_to_remove:
                should_draw = False

            if should_draw:
                y1 = start_y - y * cell_size
                y2 = start_y - (y + 1) * cell_size
                x_pos = start_x + x * cell_size
                c.line(x_pos, y1, x_pos, y2)
                vertical_walls += 1

    logger.debug(f"Drew {horizontal_walls} horizontal walls and {vertical_walls} vertical walls")


def render(c: Canvas, page_spec: Dict[str, Any], ctx: RenderContext) -> None:
    """
    Render a maze activity page.

    Refactored to use typed RenderContext and constants.
    """
    title = page_spec.get("title", "Maze")
    logger.info(f"Rendering maze page: {title}")

    # Draw page frame
    ctx.draw_border()
    ctx.draw_title(title, constants.OFFSET_TITLE)
    ctx.draw_instruction("Help find the way through the maze!", constants.OFFSET_INSTRUCTION)

    # Determine maze size based on difficulty
    difficulty = page_spec.get("difficulty", "easy")
    if difficulty == "easy":
        maze_size = 5
        cell_size = constants.GRID_SPACING_SMALL
    elif difficulty == "medium":
        maze_size = 6
        cell_size = 52
    elif difficulty == "hard":
        maze_size = 7
        cell_size = 46
    else:
        # Fallback to custom size if provided
        maze_size = page_spec.get("maze_size", 5)
        cell_size = page_spec.get("cell_size", constants.GRID_SPACING_SMALL)

    logger.info(f"Maze difficulty: {difficulty}, size: {maze_size}x{maze_size}, cell_size: {cell_size}px")

    # Generate unique maze using page title hash as seed
    seed = abs(hash(title)) % 10000
    logger.debug(f"Using seed {seed} (from hash of '{title}')")

    # Generate maze
    walls_to_remove = _generate_simple_maze(maze_size, seed)

    # Center the maze on the canvas
    start_x = ctx.center_x - (maze_size * cell_size) / 2
    start_y = ctx.center_y + (maze_size * cell_size) / 2 - 20

    # Set line width using kid-friendly stroke
    c.setLineWidth(max(3, ctx.kid_stroke_width - 1))
    c.setStrokeColor(colors.black)

    # Draw maze grid
    _draw_maze_grid(c, maze_size, start_x, start_y, cell_size, walls_to_remove)

    # Draw START marker (green circle)
    c.setFillColor(colors.green)
    c.circle(start_x + cell_size / 2, start_y - cell_size / 2, 8, stroke=0, fill=1)

    # Draw END marker (red circle)
    c.setFillColor(colors.red)
    c.circle(
        start_x + (maze_size - 0.5) * cell_size,
        start_y - (maze_size - 0.5) * cell_size,
        8,
        stroke=0,
        fill=1,
    )

    # Draw labels
    c.setFillColor(colors.black)
    c.setFont(constants.FONT_FAMILY_TITLE, 12)
    c.drawString(start_x - 40, start_y - cell_size / 2 - 4, "START")
    c.drawString(
        start_x + maze_size * cell_size + 10,
        start_y - (maze_size - 0.5) * cell_size - 4,
        "END",
    )

    logger.info("Maze page rendering complete")
