"""Maze page renderer."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Tuple

from reportlab.lib import colors
from reportlab.pdfgen.canvas import Canvas


MazeWall = Tuple[int, int, int]


def _draw_walls(c: Canvas, walls: Iterable[MazeWall], start_x: float, start_y: float, cell_size: float) -> None:
    for x, y, length in walls:
        wall_x = start_x + x * cell_size
        wall_y = start_y - (y + 1) * cell_size
        c.line(wall_x, wall_y, wall_x + length * cell_size, wall_y)


def render(c: Canvas, page_spec: Dict[str, Any], helpers: Dict[str, Any]) -> None:
    helpers["draw_border"]()
    helpers["draw_title"](page_spec.get("title", "Maze"))
    helpers["draw_instruction"]("Help find the way through the maze!")

    maze_size = page_spec.get("maze_size", 7)
    cell_size = page_spec.get("cell_size", 50)
    start_x = helpers["width"] / 2 - (maze_size * cell_size) / 2
    start_y = helpers["height"] / 2 + (maze_size * cell_size) / 2

    c.setLineWidth(max(3, helpers["kid_stroke"]() - 1))
    c.setStrokeColor(colors.black)

    default_walls: Iterable[MazeWall] = (
        (0, 0, 3), (4, 0, 3), (1, 1, 2), (5, 1, 2),
        (0, 2, 2), (3, 2, 2), (6, 2, 1), (1, 3, 1),
        (3, 3, 3), (0, 4, 2), (4, 4, 3), (2, 5, 2),
        (5, 5, 2), (0, 6, 2), (3, 6, 4),
    )
    walls = page_spec.get("walls", default_walls)

    c.rect(
        start_x,
        start_y - maze_size * cell_size,
        maze_size * cell_size,
        maze_size * cell_size,
        stroke=1,
        fill=0,
    )

    _draw_walls(c, walls, start_x, start_y, cell_size)

    c.setFillColor(colors.green)
    c.circle(start_x + cell_size / 2, start_y - cell_size / 2, 8, stroke=0, fill=1)
    c.setFillColor(colors.red)
    c.circle(
        start_x + (maze_size - 0.5) * cell_size,
        start_y - (maze_size - 0.5) * cell_size,
        8,
        stroke=0,
        fill=1,
    )

    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(start_x - 40, start_y - cell_size / 2, "START")
    c.drawString(
        start_x + maze_size * cell_size + 10,
        start_y - (maze_size - 0.5) * cell_size,
        "END",
    )
