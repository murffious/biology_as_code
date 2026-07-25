#!/usr/bin/env python3
"""
Generate Colab-ready notebooks from the cookbook markdown.

The markdown pages in ``docs/cookbook/`` are the single source of truth. This
script derives ``notebooks/*.ipynb`` from them so a lab cannot say one thing on
the site and another in the classroom.

    python scripts/build_notebooks.py            # write notebooks
    python scripts/build_notebooks.py --check    # fail if out of sync (CI)

Only ``python`` fenced blocks become code cells. ``text`` and ``bash`` blocks stay
in the surrounding markdown as expected output or setup notes, because executing
them would either fail or reinstall the environment.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
COOKBOOK = REPO_ROOT / "docs" / "cookbook"
NOTEBOOKS = REPO_ROOT / "notebooks"

# Matches a fenced block and captures its language and body.
_FENCE = re.compile(r"^```(\w*)\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)

_COLAB_PREAMBLE = (
    "# Colab / fresh-environment setup.\n"
    "# Food packets live in the repository, not the wheel, so clone rather than pip install.\n"
    "#\n"
    "#   !git clone https://github.com/murffious/biology_as_code\n"
    "#   %cd biology_as_code\n"
    "#   !pip install -e .\n"
)


def _cell(kind: str, source: str) -> dict:
    lines = source.rstrip("\n").split("\n")
    payload = [line + "\n" for line in lines[:-1]] + [lines[-1]] if lines else []
    cell = {"cell_type": kind, "metadata": {}, "source": payload}
    if kind == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def build_cells(markdown: str) -> list[dict]:
    """Split markdown into alternating markdown/code cells."""
    cells: list[dict] = [_cell("code", _COLAB_PREAMBLE)]
    cursor = 0
    for match in _FENCE.finditer(markdown):
        prose = markdown[cursor : match.start()].strip()
        if prose:
            cells.append(_cell("markdown", prose))
        language, body = match.group(1), match.group(2)
        if language == "python":
            cells.append(_cell("code", body))
        else:
            fence = f"```{language}\n{body}```"
            cells.append(_cell("markdown", fence))
        cursor = match.end()
    tail = markdown[cursor:].strip()
    if tail:
        cells.append(_cell("markdown", tail))
    return cells


def build_notebook(markdown: str) -> dict:
    return {
        "cells": build_cells(markdown),
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def sources() -> list[Path]:
    return sorted(p for p in COOKBOOK.glob("*.md") if p.stem != "index")


def target_for(source: Path) -> Path:
    return NOTEBOOKS / f"{source.stem}.ipynb"


def render(source: Path) -> str:
    notebook = build_notebook(source.read_text(encoding="utf-8"))
    return json.dumps(notebook, indent=1, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="exit non-zero if any notebook is stale instead of writing",
    )
    args = parser.parse_args()

    NOTEBOOKS.mkdir(exist_ok=True)
    stale: list[str] = []

    for source in sources():
        target = target_for(source)
        rendered = render(source)
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if current != rendered:
                stale.append(target.relative_to(REPO_ROOT).as_posix())
        else:
            target.write_text(rendered, encoding="utf-8")
            print(f"wrote {target.relative_to(REPO_ROOT)}")

    if stale:
        print("stale notebooks (run scripts/build_notebooks.py):", file=sys.stderr)
        for name in stale:
            print(f"  {name}", file=sys.stderr)
        return 1

    if args.check:
        print(f"{len(sources())} notebooks in sync")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
