"""
Output Dumper Module

Provides functionality for dumping processed output to JSON files
for testing, debugging, and downstream processing.

Design Pattern: Single Responsibility
Handles only the concern of writing output to files.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


class OutputDumper:
    """Dump processed output to JSON for testing and debugging.

    Provides static methods for dumping structured data to JSON files
    with metadata and logging information.

    Examples:
        >>> import tempfile
        >>> dumper = OutputDumper()
        >>> pages = [{'pageNumber': 1, 'type': 'coloring'}]
        >>> logs = [{'timestamp': '2024-01-01', 'page': 1}]
        >>> with tempfile.TemporaryDirectory() as tmpdir:
        ...     path = Path(tmpdir)
        ...     result = dumper.dump(pages, logs, path)
        ...     result is not None
        True
    """

    @staticmethod
    def dump(
        processed_pages: List[Dict[str, Any]],
        logs: List[Dict[str, Any]],
        output_dir: Path,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """Dump processed output to JSON file.

        Args:
            processed_pages: List of processed page dictionaries
            logs: List of log dictionaries
            output_dir: Directory to write output file
            metadata: Optional metadata to include in output

        Returns:
            Path to created file, or None if dump failed

        Examples:
            >>> import tempfile
            >>> pages = [{'page': 1, 'content': 'test'}]
            >>> logs = [{'time': 'now'}]
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     out_dir = Path(tmpdir)
            ...     result = OutputDumper.dump(pages, logs, out_dir)
            ...     result.exists()
            True

            >>> # Test with metadata
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     out_dir = Path(tmpdir)
            ...     meta = {'model': 'claude-3', 'difficulty': 'easy'}
            ...     result = OutputDumper.dump(pages, logs, out_dir, metadata=meta)
            ...     result is not None
            True
        """
        try:
            # Ensure output directory exists
            output_dir.mkdir(parents=True, exist_ok=True)

            # Generate filename with timestamp
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"claude_run_{timestamp}.json"

            # Build payload
            payload = {
                "meta": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "pages_count": len(processed_pages),
                    **(metadata or {})
                },
                "pages": processed_pages,
                "claude_logs": logs
            }

            # Write to file
            file_path = output_dir / filename
            with file_path.open("w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)

            return file_path

        except Exception as exc:
            print(f"Failed to dump output: {exc}")
            return None

    @staticmethod
    def dump_simple(
        data: Dict[str, Any],
        output_path: Path
    ) -> bool:
        """Dump simple dictionary to JSON file.

        Args:
            data: Dictionary to dump
            output_path: Full path including filename

        Returns:
            True if successful, False otherwise

        Examples:
            >>> import tempfile
            >>> import os
            >>> data = {'key': 'value', 'number': 42}
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     path = Path(tmpdir) / "test.json"
            ...     success = OutputDumper.dump_simple(data, path)
            ...     success
            True
        """
        try:
            # Ensure parent directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True

        except Exception as exc:
            print(f"Failed to dump to {output_path}: {exc}")
            return False

    @staticmethod
    def read_dump(file_path: Path) -> Optional[Dict[str, Any]]:
        """Read a dumped JSON file.

        Args:
            file_path: Path to JSON file

        Returns:
            Parsed JSON dictionary, or None if read failed

        Examples:
            >>> import tempfile
            >>> data = {'test': 'data'}
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     path = Path(tmpdir) / "test.json"
            ...     _ = OutputDumper.dump_simple(data, path)
            ...     loaded = OutputDumper.read_dump(path)
            ...     loaded['test']
            'data'
        """
        try:
            with file_path.open("r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            print(f"Failed to read {file_path}: {exc}")
            return None

    @staticmethod
    def get_latest_dump(output_dir: Path, pattern: str = "claude_run_*.json") -> Optional[Path]:
        """Get the most recently created dump file.

        Args:
            output_dir: Directory to search
            pattern: Glob pattern for dump files

        Returns:
            Path to latest dump file, or None if none found

        Examples:
            >>> import tempfile
            >>> import time
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     out_dir = Path(tmpdir)
            ...     _ = OutputDumper.dump([], [], out_dir)
            ...     time.sleep(0.1)
            ...     _ = OutputDumper.dump([], [], out_dir)
            ...     latest = OutputDumper.get_latest_dump(out_dir)
            ...     latest is not None
            True
        """
        try:
            dumps = list(output_dir.glob(pattern))
            if not dumps:
                return None

            # Sort by modification time, newest first
            return max(dumps, key=lambda p: p.stat().st_mtime)

        except Exception as exc:
            print(f"Failed to find latest dump: {exc}")
            return None


if __name__ == "__main__":
    import doctest
    print("Running doctests for OutputDumper...")
    results = doctest.testmod(verbose=False)
    if results.failed == 0:
        print(f"✅ All {results.attempted} doctests passed!")
    else:
        print(f"❌ {results.failed}/{results.attempted} doctests failed")
