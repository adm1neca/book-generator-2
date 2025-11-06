"""Utilities for loading external art assets."""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict


logger = logging.getLogger(__name__)


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"

_SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".svg"}

_NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_slug(value: str) -> str:
    """Normalize a filename stem into a lookup slug."""

    slug = value.strip().lower()
    slug = _NON_ALNUM_RE.sub("-", slug)
    slug = slug.strip("-")
    return slug


def load_assets(directory: Path | None = None) -> Dict[str, Path]:
    """Scan the assets directory and build a slug-to-path map."""

    base = directory or ASSETS_DIR
    if not base.exists():
        logger.warning("Asset directory %s is missing", base)
        return {}

    assets: Dict[str, Path] = {}
    for path in base.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in _SUPPORTED_EXTENSIONS:
            continue
        slug = normalize_slug(path.stem)
        if not slug:
            continue
        assets[slug] = path
    return assets

