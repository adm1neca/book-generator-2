"""Constants for page rendering - centralizes magic numbers."""

from __future__ import annotations

# ===================================================================
# COLORS
# ===================================================================
COLOR_BORDER = "#FF69B4"  # Pink border
COLOR_TITLE = "#4A90E2"  # Blue title text
COLOR_TEXT = "#000000"  # Black body text
COLOR_INSTRUCTION = "#000000"  # Black instruction text
COLOR_KID_STROKE = "#000000"  # Black kid-friendly stroke

# ===================================================================
# TYPOGRAPHY
# ===================================================================
FONT_SIZE_TITLE = 24
FONT_SIZE_INSTRUCTION = 14
FONT_SIZE_TRACING_LARGE = 96
FONT_SIZE_TRACING_MEDIUM = 48
FONT_SIZE_TRACING_SMALL = 36
FONT_SIZE_NUMBER = 18

FONT_FAMILY_TITLE = "Helvetica-Bold"
FONT_FAMILY_BODY = "Helvetica"

# ===================================================================
# LAYOUT OFFSETS (from top of page)
# ===================================================================
OFFSET_TITLE = 50  # Y offset for title from top
OFFSET_INSTRUCTION = 80  # Y offset for instruction from top
OFFSET_CONTENT_START_COUNTING = 220  # Where counting items start
OFFSET_CONTENT_START_MATCHING = 150  # Where matching items start
OFFSET_CONTENT_START_TRACING = 160  # Where tracing items start
OFFSET_CONTENT_START_DEFAULT = 150  # Default content start

# ===================================================================
# GRID SPACING
# ===================================================================
GRID_SPACING_SMALL = 60  # Small item spacing (counting)
GRID_SPACING_MEDIUM = 80  # Medium item spacing
GRID_SPACING_LARGE = 110  # Large item spacing (matching pairs)

# ===================================================================
# ITEM SIZES
# ===================================================================
ITEM_SIZE_SMALL = 50  # Small items/shapes
ITEM_SIZE_MEDIUM = 70  # Medium items (matching)
ITEM_SIZE_LARGE = 100  # Large items (tracing)

# Default sizes for primitives
STAR_OUTER_RADIUS = 20
STAR_INNER_RADIUS = 10
HEART_SIZE = 15  # Base size for heart shape

# ===================================================================
# DOT-TO-DOT SHAPE SIZES
# ===================================================================
DOT_SHAPE_STAR_OUTER = 110
DOT_SHAPE_STAR_INNER = 60
DOT_SHAPE_CIRCLE_RADIUS = 110
DOT_SHAPE_HEART_SCALE = 60

# ===================================================================
# STROKE WIDTHS
# ===================================================================
BORDER_WIDTH = 3  # Border stroke width
DOT_RADIUS = 4  # Radius for dots in dot-to-dot

# Stroke width calculation bounds
STROKE_WIDTH_MIN = 4
STROKE_WIDTH_MAX = 12
STROKE_WIDTH_FACTOR = 0.012  # Percentage of min(width, height)

# ===================================================================
# MARGINS
# ===================================================================
MARGIN_FACTOR = 0.07  # Percentage of min(width, height)
MIN_MARGIN_INCHES = 0.75  # Minimum margin in inches

# ===================================================================
# GRID DEFAULTS
# ===================================================================
MAX_GRID_COLS = 5  # Maximum columns for counting grid
DEFAULT_TRACING_COLS = 3  # Default columns for tracing
DEFAULT_TRACING_REPETITIONS = 6  # How many times to repeat tracing

# ===================================================================
# STAR SHAPE
# ===================================================================
STAR_POINTS = 10  # Number of points in a star (5 outer + 5 inner)
STAR_ANGLE_DEGREES = 36  # 360 / 10
STAR_START_ANGLE = -90  # Start at top

# ===================================================================
# SHAPE SIZE SCALES (for full-page shapes)
# ===================================================================
SHAPE_SCALE_STAR_OUTER = 0.36  # Outer radius as % of canvas size
SHAPE_SCALE_STAR_INNER = 0.45  # Inner radius relative to outer
SHAPE_SCALE_HEART = 0.55  # Heart size as % of canvas size
