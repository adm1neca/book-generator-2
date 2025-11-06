"""
Tracking Module

Provides variety tracking capabilities for activity generation.
Manages state to ensure diverse content across pages.

Design Pattern: State Pattern
Encapsulates tracking state and provides clean state management interface.

Example Usage:
    from components.tracking import VarietyTracker

    # Initialize tracker
    tracker = VarietyTracker()

    # Select unused items
    subject = tracker.select_unused('coloring', ['cat', 'dog', 'bird'])

    # Check what's been used
    used_items = tracker.get_used('coloring')

    # Reset when needed
    tracker.reset('coloring')

    # Get summary of all tracking
    summary = tracker.get_summary()
"""

from .variety_tracker import VarietyTracker

__all__ = ['VarietyTracker']

# Version info
__version__ = '1.0.0'
__author__ = 'Book Generator Team'
__description__ = 'Variety tracking for diverse content generation'
