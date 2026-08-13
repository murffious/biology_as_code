"""Package paths — all data lives under engine/data/."""

from __future__ import annotations

from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent
DATA = PACKAGE_ROOT / "data"


def data_file(*parts: str) -> Path:
    return DATA.joinpath(*parts)
