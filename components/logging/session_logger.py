"""
Session Logger Module

Provides structured session logging for Claude processor with:
- Message logging with timestamps
- API call tracking with detailed information
- Session summary and statistics
- File output with formatted logs

Design Pattern: Observer Pattern (simplified)
Collects and aggregates log events for later output.
"""

from datetime import datetime
from typing import List, Dict, Optional, Callable, Any
from pathlib import Path


class SessionLogger:
    """Structured session logging for Claude API processor.

    Tracks session events, API calls, and provides formatted output
    for debugging and monitoring purposes.

    Examples:
        >>> logger = SessionLogger()
        >>> logger.log("Starting process")
        Starting process
        >>> logger.log_api_call(1, "Hello", "Hi there")
        >>> len(logger.get_detailed_logs())
        1
        >>> summary = logger.get_summary()
        >>> summary['total_api_calls']
        1
    """

    def __init__(self):
        """Initialize session logger."""
        self.session_start = datetime.now()
        self.detailed_logs: List[Dict[str, Any]] = []
        self.messages: List[str] = []

    def log(self, message: str):
        """Log a message with timestamp.

        Args:
            message: Message to log

        Side Effects:
            - Prints message to console
            - Stores message with timestamp internally

        Examples:
            >>> logger = SessionLogger()
            >>> logger.log("Test message")
            Test message
            >>> len(logger.messages)
            1
        """
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        self.messages.append(log_entry)
        print(message)

    def log_api_call(
        self,
        page_number: int,
        prompt: str,
        response: str,
        model: Optional[str] = None,
        usage: Optional[Dict[str, int]] = None
    ):
        """Log an API call with full details.

        Args:
            page_number: Page number being processed
            prompt: Prompt sent to API
            response: Response received from API
            model: Model name used (optional)
            usage: Token usage dictionary (optional)

        Examples:
            >>> logger = SessionLogger()
            >>> logger.log_api_call(1, "prompt text", "response text")
            >>> logs = logger.get_detailed_logs()
            >>> logs[0]['page_number']
            1
            >>> logs[0]['prompt']
            'prompt text'
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'page_number': page_number,
            'prompt': prompt,
            'response': response
        }

        if model:
            log_entry['model'] = model

        if usage:
            log_entry['usage'] = usage

        self.detailed_logs.append(log_entry)

    def get_detailed_logs(self) -> List[Dict[str, Any]]:
        """Get all detailed API call logs.

        Returns:
            List of log dictionaries with API call details

        Examples:
            >>> logger = SessionLogger()
            >>> logger.log_api_call(1, "test", "response")
            >>> logs = logger.get_detailed_logs()
            >>> len(logs)
            1
        """
        return self.detailed_logs.copy()

    def get_summary(self) -> Dict[str, Any]:
        """Get session summary with statistics.

        Returns:
            Dictionary with session statistics

        Examples:
            >>> logger = SessionLogger()
            >>> logger.log("message")
            message
            >>> logger.log_api_call(1, "test", "response")
            >>> summary = logger.get_summary()
            >>> summary['total_api_calls']
            1
            >>> summary['total_messages']
            1
            >>> 'duration_seconds' in summary
            True
        """
        duration = (datetime.now() - self.session_start).total_seconds()
        return {
            'session_start': self.session_start.isoformat(),
            'duration_seconds': duration,
            'total_api_calls': len(self.detailed_logs),
            'total_messages': len(self.messages)
        }

    def save(
        self,
        filename: Optional[str] = None,
        variety_summary: Optional[Dict[str, List[str]]] = None
    ) -> Optional[str]:
        """Save detailed logs to file.

        Args:
            filename: Output filename (auto-generated if None)
            variety_summary: Optional variety tracking summary to include

        Returns:
            Filename where logs were saved, or None if save failed

        Examples:
            >>> import tempfile
            >>> import os
            >>> logger = SessionLogger()
            >>> logger.log_api_call(1, "Hello", "Hi")
            >>> with tempfile.TemporaryDirectory() as tmpdir:
            ...     path = os.path.join(tmpdir, "test.txt")
            ...     result = logger.save(filename=path)
            ...     result == path
            True
        """
        try:
            if filename is None:
                timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
                filename = f"claude_logs_{timestamp}.txt"

            with open(filename, 'w', encoding='utf-8') as f:
                # Header
                f.write("=" * 80 + "\n")
                f.write("CLAUDE ACTIVITY GENERATOR - DETAILED LOG\n")
                f.write("=" * 80 + "\n")
                f.write(f"Session Start: {self.session_start.isoformat()}\n")
                f.write(f"Total Pages Processed: {len(self.detailed_logs)}\n")
                f.write("=" * 80 + "\n\n")

                # Detailed logs for each page
                for idx, log_entry in enumerate(self.detailed_logs, 1):
                    f.write(f"\n{'#' * 80}\n")
                    f.write(f"PAGE {log_entry['page_number']} - Entry {idx}/{len(self.detailed_logs)}\n")
                    f.write(f"Timestamp: {log_entry['timestamp']}\n")
                    f.write(f"{'#' * 80}\n\n")

                    f.write("PROMPT SENT TO CLAUDE:\n")
                    f.write("-" * 80 + "\n")
                    f.write(log_entry['prompt'])
                    f.write("\n" + "-" * 80 + "\n\n")

                    f.write("CLAUDE RESPONSE:\n")
                    f.write("-" * 80 + "\n")
                    f.write(log_entry['response'])
                    f.write("\n" + "-" * 80 + "\n\n")

                # Summary section
                f.write("\n" + "=" * 80 + "\n")
                f.write("SUMMARY\n")
                f.write("=" * 80 + "\n")
                f.write(f"Total API calls: {len(self.detailed_logs)}\n")
                duration = (datetime.now() - self.session_start).total_seconds()
                f.write(f"Session duration: {duration:.2f} seconds\n")

                # Variety summary if provided
                if variety_summary:
                    f.write("\nItems used per activity type:\n")
                    for activity_type, items in variety_summary.items():
                        items_str = ', '.join(items) if items else 'none'
                        f.write(f"  {activity_type}: {items_str}\n")

                f.write("=" * 80 + "\n")

            return filename

        except Exception as e:
            print(f"⚠️ Failed to save detailed logs: {str(e)}")
            return None

    def clear(self):
        """Clear all logs and reset session start time.

        Examples:
            >>> logger = SessionLogger()
            >>> logger.log("test")
            test
            >>> logger.log_api_call(1, "prompt", "response")
            >>> logger.clear()
            >>> len(logger.get_detailed_logs())
            0
            >>> len(logger.messages)
            0
        """
        self.session_start = datetime.now()
        self.detailed_logs.clear()
        self.messages.clear()


if __name__ == "__main__":
    import doctest
    print("Running doctests for SessionLogger...")
    results = doctest.testmod(verbose=False)
    if results.failed == 0:
        print(f"✅ All {results.attempted} doctests passed!")
    else:
        print(f"❌ {results.failed}/{results.attempted} doctests failed")
