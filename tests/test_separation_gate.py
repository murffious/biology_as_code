"""
The separation gate, as a test — by RUNNING the gate, not by re-deriving it.

This repository is the open commons: the Biology as Code specification and its
reference implementation. It carries no product. ``tools/check_separation.py`` is
the definition of that rule and CI runs it; this file makes it fail at ``pytest``
time too, so a reintroduced product identifier is caught before push.

WHY THIS FILE SHRANK ON 2026-08-30
----------------------------------
It used to re-implement the scan: its own pattern, its own file walk, its own skip
list. That copy was written against the ORIGINAL inline grep, and when the grep was
replaced it silently kept all four of the holes the replacement exists to close —

  1. it scanned an explicit directory list, ``("src", "tests")``, which is exactly
     how ``ontology-sdk/`` accumulated ten references while CI stayed green;
  2. it matched file CONTENTS only, so a directory named for the product was
     invisible to it;
  3. it treated the author's name as a product identifier, which is what forced
     the documents that RESERVE the claims to be excluded wholesale;
  4. it carried its own ``.egg-info`` skip rule, the exclusion that hid a stale
     ``PKG-INFO``.

So the repository held two definitions of one rule, and the older, weaker one was
the one running under ``pytest``. That is the same mistake as re-writing a
validator that already exists: the duplicate does not disagree loudly, it disagrees
quietly and in the permissive direction.

What is left here are the two assertions that are NOT about the scan and therefore
are not duplicates: there is no in-package slot for private code, and the IP
documents survive. Mutation coverage for the gate itself — can it refuse a product
name in a path, in contents, in its own allowlist — lives in
``tests/test_gates_can_fail.py``, which runs the real script against throwaway
fixture repositories.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
GATE = REPO_ROOT / "tools" / "check_separation.py"


def test_the_separation_gate_passes_on_this_repository():
    """One definition of the rule, invoked. If this fails, read the gate's output:
    it names the file, the line, and whether the hit was a path or contents."""
    r = subprocess.run([sys.executable, str(GATE)], cwd=REPO_ROOT,
                       capture_output=True, text=True, timeout=300)
    assert r.returncode == 0, r.stdout + r.stderr


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
