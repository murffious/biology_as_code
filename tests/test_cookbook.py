"""
Executes every ``python`` block in the cookbook.

Documentation that is not run is documentation that is wrong. Each cookbook page
is executed as a single script — blocks share a namespace, matching how a reader
works through the page top to bottom — so a rename in the public API turns this
red instead of leaving a broken lab on the site.

Also asserts the generated notebooks are in sync with their markdown source.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
COOKBOOK = REPO_ROOT / "docs" / "cookbook"

_FENCE = re.compile(r"^```(\w*)\n(.*?)^```\s*$", re.MULTILINE | re.DOTALL)


def python_blocks(markdown: str) -> list[str]:
    return [body for language, body in _FENCE.findall(markdown) if language == "python"]


def cookbook_pages() -> list[Path]:
    pages = sorted(p for p in COOKBOOK.glob("*.md") if p.stem != "index")
    assert pages, "no cookbook pages found"
    return pages


@pytest.mark.parametrize("page", cookbook_pages(), ids=lambda p: p.stem)
def test_every_python_block_runs(page: Path):
    blocks = python_blocks(page.read_text(encoding="utf-8"))
    assert blocks, f"{page.name} has no runnable python blocks"

    # One shared namespace per page: later blocks may rely on earlier imports.
    namespace: dict = {"__name__": "__cookbook__"}
    for index, block in enumerate(blocks, start=1):
        try:
            exec(compile(block, f"{page.name}#block{index}", "exec"), namespace)
        except Exception as exc:  # noqa: BLE001 - surface which block broke
            pytest.fail(f"{page.name} block {index} raised {type(exc).__name__}: {exc}")


def test_index_links_every_lab():
    index = (COOKBOOK / "index.md").read_text(encoding="utf-8")
    for page in cookbook_pages():
        assert page.name in index, f"cookbook index does not link {page.name}"


def test_notebooks_are_in_sync():
    """The notebooks are generated; a stale one means the source moved without them."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "build_notebooks.py"), "--check"],
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_expected_output_blocks_are_marked_text_not_python():
    """Expected-output samples must not be tagged python, or the runner would exec them."""
    for page in cookbook_pages():
        for block in python_blocks(page.read_text(encoding="utf-8")):
            first = block.strip().splitlines()[0] if block.strip() else ""
            assert not first.startswith("ex."), (
                f"{page.name}: output sample tagged as python:\n{first}"
            )
