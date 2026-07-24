"""
version_manifest.py — load package VERSION_MANIFEST.json (SSOT for product version).

Usage:
    from biology_as_code.data.version_manifest import package_version, load_manifest, component_version
    print(package_version())  # "0.1.0"
"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_MANIFEST_PATH = Path(__file__).resolve().parent / "VERSION_MANIFEST.json"


@lru_cache(maxsize=1)
def load_manifest() -> dict[str, Any]:
    if not _MANIFEST_PATH.is_file():
        return {
            "package_version": "0.0.0-unknown",
            "components": {},
            "data_artifacts": {},
        }
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def package_version() -> str:
    return str(load_manifest().get("package_version", "0.0.0-unknown"))


def component_version(component_id: str) -> str | None:
    comps = load_manifest().get("components") or {}
    # match by key or nested id
    if component_id in comps:
        return comps[component_id].get("version")
    for meta in comps.values():
        if isinstance(meta, dict) and meta.get("id") == component_id:
            return meta.get("version")
    return None


def data_artifact(name: str) -> dict[str, Any] | None:
    arts = load_manifest().get("data_artifacts") or {}
    return arts.get(name)


def report_version_block() -> dict[str, Any]:
    """Small dict for engine meal reports."""
    m = load_manifest()
    return {
        "package_version": m.get("package_version"),
        "released": m.get("released"),
        "engine_component": (m.get("components") or {}).get("engine", {}).get("version"),
        "kibo_core_component": (m.get("components") or {}).get("kibo_core", {}).get("version"),
        "colon_fermentation_unit": (m.get("data_artifacts") or {})
        .get("base_unit_colon_fermentation", {})
        .get("version"),
        "manifest_schema": m.get("schema"),
    }


def clear_cache() -> None:
    load_manifest.cache_clear()


if __name__ == "__main__":
    print(json.dumps(report_version_block(), indent=2))
    print("package", package_version())
