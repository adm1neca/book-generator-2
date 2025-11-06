"""
Response Parser Module

Provides utilities for parsing JSON from Claude API responses.
Handles common formatting issues like code fences and trailing commas.
"""

import re
import json
from typing import Optional


class ResponseParser:
    """Parse and extract JSON from Claude API responses.

    This class handles common response formatting issues:
    - Markdown code fences (```json...```)
    - Trailing commas before } or ]
    - Embedded JSON within text

    Examples:
        >>> parser = ResponseParser()
        >>> parser.extract_json('{"key": "value"}')
        {'key': 'value'}

        >>> parser.extract_json('```json\\n{"key": "value"}\\n```')
        {'key': 'value'}

        >>> parser.extract_json('{"key": "value",}')
        {'key': 'value'}

        >>> parser.extract_json('Some text')

        >>> parser.extract_json('Here is data: {"key": "value"} and more text')
        {'key': 'value'}
    """

    @staticmethod
    def extract_json(text: str) -> Optional[dict]:
        """Extract and parse JSON from response text.

        Args:
            text: Raw response text that may contain JSON

        Returns:
            Parsed JSON as dict, or None if no valid JSON found

        Extraction strategy:
            1. Strip markdown code fences
            2. Find JSON object using regex
            3. Attempt parse with json.loads()
            4. If fails, try fixing trailing commas
            5. Return None if all attempts fail
        """
        if not text:
            return None

        # Strip code fences (```json ... ``` or ``` ... ```)
        cleaned = re.sub(r"```(?:json)?\s*", "", text)
        cleaned = cleaned.replace("```", "")

        # Find JSON object (anything between { and })
        match = re.search(r"\{[\s\S]*\}", cleaned)
        if not match:
            return None

        blob = match.group(0)

        # Attempt 1: Parse as-is
        try:
            return json.loads(blob)
        except json.JSONDecodeError:
            pass

        # Attempt 2: Fix trailing commas and try again
        # Replaces patterns like ",}" or ",]" with "}" or "]"
        blob_fixed = re.sub(r",\s*([}\]])", r"\1", blob)
        try:
            return json.loads(blob_fixed)
        except Exception:
            return None

    @staticmethod
    def validate_json_structure(data: dict, required_keys: list) -> bool:
        """Validate that parsed JSON contains required keys.

        Args:
            data: Parsed JSON dictionary
            required_keys: List of required key names

        Returns:
            True if all required keys present, False otherwise

        Example:
            >>> parser = ResponseParser()
            >>> data = {"title": "Test", "content": "Data"}
            >>> parser.validate_json_structure(data, ["title", "content"])
            True
            >>> parser.validate_json_structure(data, ["title", "missing"])
            False
        """
        if not data:
            return False
        return all(key in data for key in required_keys)


if __name__ == "__main__":
    import doctest
    print("Running doctests for ResponseParser...")
    results = doctest.testmod(verbose=False)
    if results.failed == 0:
        print(f"✅ All {results.attempted} doctests passed!")
    else:
        print(f"❌ {results.failed}/{results.attempted} doctests failed")
