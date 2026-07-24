"""
Load the open declarative digestion machines (packaged JSON).

Machines are versioned, inspectable state graphs — one GI stage per file. The
registry is the single index; code reads machines through it (never hard-coded).
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_DATA = Path(__file__).resolve().parent / "data"
_REGISTRY = _DATA / "registry.json"


@lru_cache(maxsize=1)
def load_registry() -> dict[str, Any]:
    """The machine index: {generated, machines: [{id, kind, path, version, revision, status, hash}]}."""
    return json.loads(_REGISTRY.read_text(encoding="utf-8"))


def list_machines(kind: str | None = None) -> list[str]:
    """All machine ids, optionally filtered by kind ('stage' | 'lens' | 'process')."""
    rows = load_registry().get("machines", [])
    return [m["id"] for m in rows if kind is None or m.get("kind") == kind]


def machine_path(machine_id: str) -> Path | None:
    """Absolute path to a machine's JSON file, or None if unknown."""
    for m in load_registry().get("machines", []):
        if m.get("id") == machine_id:
            return _DATA / m["path"]
    return None


# Cache the raw text (I/O), but parse per call so every caller gets a fresh,
# independently-mutable dict — no shared-state footgun across callers.
@lru_cache(maxsize=None)
def _machine_text(machine_id: str) -> str | None:
    p = machine_path(machine_id)
    if p is None or not p.is_file():
        return None
    return p.read_text(encoding="utf-8")


def get_machine(machine_id: str) -> dict[str, Any] | None:
    """Return one machine graph as a dict (fresh copy each call), or None if not found."""
    if not machine_id:
        return None
    txt = _machine_text(machine_id)
    return json.loads(txt) if txt is not None else None
