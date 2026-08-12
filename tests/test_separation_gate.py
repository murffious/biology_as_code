"""
The separation gate, as a test.

This repository is the open commons: the Biology as Code specification and its
reference implementation. It carries no product. CI enforces that with a grep
job (``.github/workflows/ci.yml``, job ``separation``); this test runs the same
check locally so a reintroduced product identifier fails at ``pytest`` time
rather than at push time.

Root-level IP documents (``PATENTS.md``, ``PROPRIETARY_IP.md``,
``LICENSE-SAMPLES.md``) are deliberately **out of scope**. Their patent
disposition is a pending legal decision; they are annotated as under review, not
rewritten.

Note the terms are assembled from fragments rather than written out. A test that
spelled them would be found by its own search.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNED = ("src", "tests")

# Assembled so this file does not match itself.
FORBIDDEN = (
    "ki" + "bo",
    "meal" + "coach",
    "mo" + "rf",
)
_PATTERN = re.compile("|".join(FORBIDDEN), re.IGNORECASE)

_SKIP_DIRS = {"__pycache__", ".pytest_cache", ".git", ".ruff_cache"}
_SKIP_SUFFIXES = {".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".JPG"}


def _is_build_artifact(path: Path) -> bool:
    """
    Generated metadata is not source.

    ``src/*.egg-info/PKG-INFO`` restates the author's email from
    ``pyproject.toml``, which is authorship, not a product identifier — but the
    gate is a blunt substring search and cannot tell the difference. CI checks
    out clean so it never sees this directory; a developer who has run a build
    would otherwise get a spurious failure.
    """
    return any(part.endswith(".egg-info") for part in path.parts)


def _scanned_files() -> list[Path]:
    out: list[Path] = []
    for root in SCANNED:
        for path in sorted((REPO_ROOT / root).rglob("*")):
            if not path.is_file():
                continue
            if _SKIP_DIRS & set(path.parts):
                continue
            if path.suffix in _SKIP_SUFFIXES:
                continue
            if _is_build_artifact(path):
                continue
            if path.resolve() == Path(__file__).resolve():
                continue
            out.append(path)
    return out


def test_the_gate_can_actually_find_something():
    """A gate that cannot fail is not a gate."""
    assert _PATTERN.search("a " + FORBIDDEN[0] + " reference")
    assert _PATTERN.search("A " + FORBIDDEN[1].upper() + " reference")
    assert not _PATTERN.search("morphology and biology of the gut")


def test_no_product_identifiers_in_shipped_code():
    offenders: list[str] = []
    for path in _scanned_files():
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for lineno, line in enumerate(text.splitlines(), start=1):
            if _PATTERN.search(line):
                rel = path.relative_to(REPO_ROOT)
                offenders.append(f"{rel}:{lineno}: {line.strip()[:120]}")

    assert not offenders, (
        "product identifiers found in shipped code — this repository is the open "
        "commons and carries no product (see PROPRIETARY_IP.md):\n  "
        + "\n  ".join(offenders[:40])
    )


def test_no_in_package_proprietary_slot():
    """There is no directory inside the package for private code to land in."""
    pkg = REPO_ROOT / "src" / "biology_as_code"
    slots = [p for p in pkg.rglob("proprietary") if p.is_dir()]
    assert not slots, f"in-package proprietary slot(s) present: {slots}"


@pytest.mark.parametrize("doc", ["PATENTS.md", "PROPRIETARY_IP.md", "LICENSE-SAMPLES.md"])
def test_ip_documents_are_retained_and_annotated(doc: str):
    """
    Patent disposition is a pending legal decision, so these documents must
    survive the separation work — annotated, never deleted.
    """
    path = REPO_ROOT / doc
    assert path.is_file(), f"{doc} must not be deleted while patent disposition is pending"
    text = path.read_text(encoding="utf-8")
    assert "pending legal decision" in text, f"{doc} is missing its under-review annotation"
