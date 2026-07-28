"""
Golden digests for the exported pathway packs.

`test_pathway_packs.py::test_packs_not_stale` checks that the packs on disk match
what the generator produces right now. That passes even if a pathway module and
its pack both change together — which is exactly what happens during the
per-module migration in docs/python/PATHWAY_TYPES_REFACTOR.md Phase 3.

This test pins the bytes. Migrating a module must produce *identical* packs; if a
digest moves, that is either a real regression or a deliberate improvement, and
either way it should be looked at rather than absorbed silently.

To accept an intended change:

    ./.venv/bin/python tests/test_pathway_packs_golden.py --update
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKS = ROOT / "src" / "biology_as_code" / "pathways" / "packs"
GOLDEN = Path(__file__).parent / "data" / "pathway_packs.sha256.json"


def _digests() -> dict[str, str]:
    out = {}
    for path in sorted(PACKS.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(PACKS).as_posix()
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest()
    return out


def test_packs_match_golden_digests():
    assert GOLDEN.exists(), f"golden file missing — regenerate with: {__file__} --update"
    expected = json.loads(GOLDEN.read_text())
    actual = _digests()

    added = sorted(set(actual) - set(expected))
    removed = sorted(set(expected) - set(actual))
    changed = sorted(k for k in set(actual) & set(expected) if actual[k] != expected[k])

    assert not (added or removed or changed), (
        f"pathway packs drifted from golden.\n"
        f"  changed: {changed}\n  added: {added}\n  removed: {removed}\n"
        f"If intended, re-run: python tests/test_pathway_packs_golden.py --update"
    )


if __name__ == "__main__":
    if "--update" in sys.argv:
        GOLDEN.parent.mkdir(parents=True, exist_ok=True)
        GOLDEN.write_text(json.dumps(_digests(), indent=2, sort_keys=True) + "\n")
        print(f"wrote {GOLDEN.relative_to(ROOT)} ({len(_digests())} files)")
    else:
        print("pass --update to rewrite the golden digests")
