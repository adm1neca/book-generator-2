"""
Variety Tracker Module

Manages variety tracking state for activity pages to ensure diverse content.
Tracks which items have been used for each activity type and provides
intelligent selection that avoids repetition.

Design Pattern: State Pattern
Encapsulates the state of variety tracking and provides clean methods for
state transitions (selecting items, marking as used, resetting).
"""

from typing import Dict, List, Optional
import random


class VarietyTracker:
    """Track and manage variety across activity pages.

    Maintains state of which items have been used for each activity type
    and provides methods for selecting unused items with automatic reset
    when all options have been exhausted.

    Examples:
        >>> tracker = VarietyTracker()
        >>> selected = tracker.select_unused('coloring', ['cat', 'dog', 'bird'])
        >>> selected in ['cat', 'dog', 'bird']
        True
        >>> len(tracker.get_used('coloring'))
        1
    """

    def __init__(self, activity_types: Optional[List[str]] = None):
        """Initialize variety tracker.

        Args:
            activity_types: List of activity types to track. If None, uses defaults.
        """
        if activity_types is None:
            activity_types = ['coloring', 'tracing', 'counting', 'dot-to-dot',
                            'maze', 'matching']

        self._used_items: Dict[str, List[str]] = {
            activity_type: [] for activity_type in activity_types
        }

    def select_unused(
        self,
        activity_type: str,
        available: List[str]
    ) -> str:
        """Select an unused item from available options.

        Automatically resets tracking if all items have been used.

        Args:
            activity_type: Type of activity (e.g., 'coloring', 'tracing')
            available: List of available items to choose from

        Returns:
            Selected item (randomly chosen from unused items)

        Raises:
            ValueError: If available list is empty

        Examples:
            >>> tracker = VarietyTracker()
            >>> options = ['A', 'B', 'C']
            >>> first = tracker.select_unused('tracing', options)
            >>> first in options
            True
            >>> used = tracker.get_used('tracing')
            >>> first in used
            True

            >>> # Test reset when all used
            >>> tracker2 = VarietyTracker()
            >>> options2 = ['X', 'Y']
            >>> _ = tracker2.select_unused('test', options2)
            >>> _ = tracker2.select_unused('test', options2)
            >>> third = tracker2.select_unused('test', options2)
            >>> third in options2  # Should work, tracker auto-reset
            True
        """
        if not available:
            raise ValueError(f"Available list is empty for {activity_type}")

        # Ensure activity type is tracked
        if activity_type not in self._used_items:
            self._used_items[activity_type] = []

        used = self._used_items[activity_type]
        unused = [item for item in available if item not in used]

        # Reset if all items have been used
        if not unused:
            self._used_items[activity_type] = []
            unused = available

        # Select random item
        selected = random.choice(unused)

        # Mark as used
        self._used_items[activity_type].append(selected)

        return selected

    def mark_used(self, activity_type: str, item: str):
        """Mark an item as used for an activity type.

        Args:
            activity_type: Type of activity
            item: Item to mark as used

        Examples:
            >>> tracker = VarietyTracker()
            >>> tracker.mark_used('coloring', 'cat')
            >>> 'cat' in tracker.get_used('coloring')
            True
        """
        if activity_type not in self._used_items:
            self._used_items[activity_type] = []

        if item not in self._used_items[activity_type]:
            self._used_items[activity_type].append(item)

    def get_used(self, activity_type: str) -> List[str]:
        """Get list of used items for activity type.

        Args:
            activity_type: Type of activity

        Returns:
            Copy of list of used items (modifications won't affect tracker)

        Examples:
            >>> tracker = VarietyTracker()
            >>> tracker.mark_used('counting', '5-apple')
            >>> tracker.get_used('counting')
            ['5-apple']
        """
        return self._used_items.get(activity_type, []).copy()

    def reset(self, activity_type: Optional[str] = None):
        """Reset tracking for activity type or all types.

        Args:
            activity_type: Specific activity type to reset, or None for all

        Examples:
            >>> tracker = VarietyTracker()
            >>> tracker.mark_used('coloring', 'cat')
            >>> tracker.mark_used('tracing', 'A')
            >>> tracker.reset('coloring')
            >>> tracker.get_used('coloring')
            []
            >>> tracker.get_used('tracing')
            ['A']

            >>> tracker.reset()
            >>> tracker.get_used('tracing')
            []
        """
        if activity_type:
            if activity_type in self._used_items:
                self._used_items[activity_type] = []
        else:
            # Reset all
            for key in self._used_items:
                self._used_items[key] = []

    def get_summary(self) -> Dict[str, List[str]]:
        """Get summary of all used items across all activity types.

        Returns:
            Dictionary mapping activity types to lists of used items (copies)

        Examples:
            >>> tracker = VarietyTracker()
            >>> tracker.mark_used('coloring', 'cat')
            >>> tracker.mark_used('coloring', 'dog')
            >>> summary = tracker.get_summary()
            >>> summary['coloring']
            ['cat', 'dog']
        """
        return {k: v.copy() for k, v in self._used_items.items()}

    def has_available(self, activity_type: str, available: List[str]) -> bool:
        """Check if there are unused items available.

        Args:
            activity_type: Type of activity
            available: List of available items

        Returns:
            True if there are unused items, False if all have been used

        Examples:
            >>> tracker = VarietyTracker()
            >>> tracker.has_available('coloring', ['cat', 'dog'])
            True
            >>> tracker.mark_used('coloring', 'cat')
            >>> tracker.mark_used('coloring', 'dog')
            >>> tracker.has_available('coloring', ['cat', 'dog'])
            False
        """
        used = self._used_items.get(activity_type, [])
        return any(item not in used for item in available)

    def get_count(self, activity_type: str) -> int:
        """Get count of used items for activity type.

        Args:
            activity_type: Type of activity

        Returns:
            Number of items marked as used

        Examples:
            >>> tracker = VarietyTracker()
            >>> tracker.get_count('coloring')
            0
            >>> tracker.mark_used('coloring', 'cat')
            >>> tracker.get_count('coloring')
            1
        """
        return len(self._used_items.get(activity_type, []))


if __name__ == "__main__":
    import doctest
    print("Running doctests for VarietyTracker...")
    results = doctest.testmod(verbose=False)
    if results.failed == 0:
        print(f"✅ All {results.attempted} doctests passed!")
    else:
        print(f"❌ {results.failed}/{results.attempted} doctests failed")
