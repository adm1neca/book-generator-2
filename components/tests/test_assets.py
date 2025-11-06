"""Smoke tests for the asset discovery helpers."""

from __future__ import annotations

from pathlib import Path

from scripts.assets import load_assets, normalize_slug


def test_normalize_slug_handles_non_alnum_sequences() -> None:
    assert normalize_slug(" Sleepy Bear!!! ") == "sleepy-bear"
    assert normalize_slug("--Rocket__Ship--") == "rocket-ship"


def test_load_assets_filters_suffixes_and_normalizes(tmp_path) -> None:
    base = tmp_path / "assets"
    base.mkdir()
    (base / "Rainbow Party!!.JPG").touch()

    animals = base / "Animals"
    animals.mkdir()
    (animals / "Penguin.SVG").touch()
    (base / "notes.txt").write_text("skip me")

    assets = load_assets(base)

    assert "rainbow-party" in assets
    assert assets["rainbow-party"].suffix.lower() == ".jpg"

    assert "penguin" in assets
    assert assets["penguin"].name == "Penguin.SVG"

    assert "notes" not in assets