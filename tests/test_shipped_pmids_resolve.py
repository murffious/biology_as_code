"""Every PMID we emit as provenance must name the paper we cited.

This is `tools/check_pmids.py` run inside the normal suite, offline against the
committed cache. It is a test and not only a CI step because the ids it guards
are emitted in `to_dict()` provenance: a consumer reads them as the warrant for a
HOLDS, so a wrong one is a wrong claim, not a typo in a bibliography.

The gate exists because a resolve-and-diff pass on 2026-09-07 found 12 of 17
shipped PMIDs naming a different paper -- including two ids that were themselves
"corrections" of an earlier wrong id, reasoned about rather than resolved.
"""

from __future__ import annotations

import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_every_shipped_pmid_resolves_to_its_citation():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_pmids.py"), "--offline", "--strict"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr
