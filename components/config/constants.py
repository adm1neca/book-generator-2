"""Configuration constants for Claude processor.

Design Pattern: Configuration Constants Pattern
- Single source of truth for all configuration data
- Easy to modify without code changes
- Can be externalized to config files later
"""

from typing import Dict, List, Set

# Theme mappings
THEME_FALLBACKS: Dict[str, str] = {
    'forest': 'forest-friends',
    'woods': 'forest-friends',
    'forest friends': 'forest-friends',
    'sea': 'under-the-sea',
    'ocean': 'under-the-sea',
    'under the sea': 'under-the-sea',
    'farm': 'farm-day',
    'farm animals': 'farm-day',
    'space': 'space-explorer',
    'galaxy': 'space-explorer'
}

# Blocked copyrighted themes
BLOCKED_THEMES: Set[str] = {
    "peppa",
    "paw patrol",
    "paw-patrol",
    "disney",
    "marvel",
    "pokemon",
    "barbie"
}

# Default fallback theme
DEFAULT_THEME: str = "animals"

# Valid difficulty levels
VALID_DIFFICULTIES: Set[str] = {"easy", "medium", "hard"}
DEFAULT_DIFFICULTY: str = "easy"

# Difficulty-based repetitions for tracing
DIFFICULTY_REPETITIONS: Dict[str, int] = {
    "easy": 8,
    "medium": 12,
    "hard": 16
}

# Theme-based subjects for coloring pages
THEME_SUBJECTS: Dict[str, List[str]] = {
    'forest-friends': [
        'fox', 'bear', 'owl', 'rabbit', 'hedgehog', 'deer',
        'squirrel', 'raccoon', 'snail', 'mushroom', 'acorn', 'pine tree'
    ],
    'under-the-sea': [
        'fish', 'dolphin', 'starfish', 'shell', 'turtle',
        'seahorse', 'crab', 'octopus', 'bubble', 'coral'
    ],
    'farm-day': [
        'cow', 'chicken', 'sheep', 'pig', 'barn',
        'tractor', 'duck', 'horse', 'hay bale'
    ],
    'space-explorer': [
        'rocket', 'planet', 'star', 'moon',
        'astronaut', 'satellite', 'comet'
    ],
    'shapes': [
        'circle', 'square', 'triangle', 'star', 'heart',
        'diamond', 'oval', 'rectangle', 'hexagon', 'pentagon'
    ],
    'animals': [
        'cat', 'dog', 'rabbit', 'bird', 'fish', 'elephant',
        'giraffe', 'lion', 'bear', 'monkey', 'butterfly',
        'bee', 'duck', 'frog'
    ]
}

# Target age range
TARGET_AGE_MIN: int = 2
TARGET_AGE_MAX: int = 3

# Style requirements
STYLE_DESCRIPTION: str = "thick black outlines, simple cute shapes, no shading"
