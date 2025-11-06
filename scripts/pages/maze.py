"""Maze page renderer."""

from __future__ import annotations

import random
from typing import Any, Dict, List, Set, Tuple

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


MazeWall = Tuple[int, int, int]


def _generate_maze(grid_size: int, seed: int = None) -> List[MazeWall]:
    """Generate a unique maze using recursive backtracking algorithm.

    Args:
        grid_size: Size of the maze grid (NxN)
        seed: Random seed for reproducibility

    Returns:
        List of horizontal wall segments as (x, y, length) tuples
    """
    if seed is not None:
        random.seed(seed)

    # Track visited cells
    visited: Set[Tuple[int, int]] = set()

    # Track removed walls (horizontal walls between cells)
    # We store walls as (x, y) where the wall is below cell (x, y)
    removed_horizontal: Set[Tuple[int, int]] = set()
    removed_vertical: Set[Tuple[int, int]] = set()

    def get_neighbors(x: int, y: int) -> List[Tuple[int, int, str]]:
        """Get unvisited neighbors of cell (x, y)."""
        neighbors = []
        # Check all four directions: up, down, left, right
        if y > 0 and (x, y - 1) not in visited:
            neighbors.append((x, y - 1, 'up'))
        if y < grid_size - 1 and (x, y + 1) not in visited:
            neighbors.append((x, y + 1, 'down'))
        if x > 0 and (x - 1, y) not in visited:
            neighbors.append((x - 1, y, 'left'))
        if x < grid_size - 1 and (x + 1, y) not in visited:
            neighbors.append((x + 1, y, 'right'))
        return neighbors

    def carve_path(x: int, y: int) -> None:
        """Recursively carve paths through the maze."""
        visited.add((x, y))

        # Get neighbors in random order
        neighbors = get_neighbors(x, y)
        random.shuffle(neighbors)

        for nx, ny, direction in neighbors:
            if (nx, ny) not in visited:
                # Remove wall between current cell and neighbor
                if direction == 'up':
                    removed_horizontal.add((x, y))
                elif direction == 'down':
                    removed_horizontal.add((x, y + 1))
                elif direction == 'left':
                    removed_vertical.add((x, y))
                elif direction == 'right':
                    removed_vertical.add((x + 1, y))

                # Recursively carve from neighbor
                carve_path(nx, ny)

    # Start carving from top-left (0, 0)
    carve_path(0, 0)

    # Build wall list - only include walls that weren't removed
    walls: List[MazeWall] = []

    # Add horizontal walls (walls below each cell)
    for y in range(grid_size + 1):
        current_wall_start = None
        current_wall_length = 0

        for x in range(grid_size):
            # Check if wall below this cell should exist
            should_have_wall = (x, y) not in removed_horizontal

            if should_have_wall:
                if current_wall_start is None:
                    current_wall_start = x
                    current_wall_length = 1
                else:
                    current_wall_length += 1
            else:
                if current_wall_start is not None:
                    walls.append((current_wall_start, y, current_wall_length))
                    current_wall_start = None
                    current_wall_length = 0

        # Add remaining wall segment if any
        if current_wall_start is not None:
            walls.append((current_wall_start, y, current_wall_length))

    return walls


def _draw_walls(c: Canvas, walls: Iterable[MazeWall], start_x: float, start_y: float, cell_size: float) -> None:
    for x, y, length in walls:
        wall_x = start_x + x * cell_size
        wall_y = start_y - (y + 1) * cell_size
        c.line(wall_x, wall_y, wall_x + length * cell_size, wall_y)


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Maze"))
    helpers["draw_instruction"]("Help find the way through the maze!")

    # Determine maze size based on difficulty
    difficulty = page_spec.get("difficulty", "easy")
    if difficulty == "easy":
        maze_size = 5
        cell_size = 60
    elif difficulty == "medium":
        maze_size = 6
        cell_size = 52
    elif difficulty == "hard":
        maze_size = 7
        cell_size = 46
    else:
        # Fallback to custom size if provided
        maze_size = page_spec.get("maze_size", 5)
        cell_size = page_spec.get("cell_size", 60)

    # Generate unique maze using page title or a hash as seed
    seed = hash(page_spec.get("title", "Maze")) % 10000

    # Generate or use provided walls
    if "walls" not in page_spec:
        walls = _generate_maze(maze_size, seed)
    else:
        walls = page_spec["walls"]

    start_x = helpers["width"] / 2 - (maze_size * cell_size) / 2
    start_y = helpers["height"] / 2 + (maze_size * cell_size) / 2

    c.setLineWidth(max(3, helpers["kid_stroke"]() - 1))
    c.setStrokeColor(colors.black)

    # Draw outer border
    c.rect(
        start_x,
        start_y - maze_size * cell_size,
        maze_size * cell_size,
        maze_size * cell_size,
        stroke=1,
        fill=0,
    )

    # Draw internal walls
    _draw_walls(c, walls, start_x, start_y, cell_size)

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
    c.setFont("Helvetica-Bold", 12)
    c.drawString(start_x - 40, start_y - cell_size / 2 - 4, "START")
    c.drawString(
        start_x + maze_size * cell_size + 10,
        start_y - (maze_size - 0.5) * cell_size - 4,
        "END",
    )
