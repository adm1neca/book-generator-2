#!/usr/bin/env python3
"""Command-line interface for generating activity booklets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.generator import generate_booklet, sample_pages


PageSpec = Dict[str, Any]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a children's activity booklet PDF."
    )
    parser.add_argument(
        "input_json", nargs="?", help="Path to input JSON (list of page specs)."
    )
    parser.add_argument("output_pdf", nargs="?", help="Path to output PDF.")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Generate a 6-page test booklet without an input JSON.",
    )
    parser.add_argument(
        "--output",
        help="Output PDF path for --test mode (default: test.pdf).",
    )
    return parser.parse_args()


def load_pages(path: str) -> List[PageSpec]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    args = parse_args()

    if args.test:
        output = args.output or "test.pdf"
        pages = sample_pages()
        generate_booklet(pages, output)
        sys.exit(0)

    if not args.input_json or not args.output_pdf:
        print("Usage:")
        print("  python3 activity_generator.py <input_json> <output_pdf>")
        print("  python3 activity_generator.py --test [--output test.pdf]")
        sys.exit(1)

    pages_data = load_pages(args.input_json)
    generate_booklet(pages_data, args.output_pdf)


if __name__ == "__main__":
    main()
