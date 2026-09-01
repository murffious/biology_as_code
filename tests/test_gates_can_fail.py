#!/usr/bin/env python3
"""Every gate in this repository must be able to say NO.

WHY THIS FILE EXISTS
--------------------
A survey on 2026-08-30 across all four repositories found ten gate scripts and
exactly **two** with a test proving the gate can fail — both in `fdp-1`, both
written the same week, for the same reason: *a spec that cannot fail a row is not
a spec.* The other eight were trusted because they exit 0.

Every gate bug found that day was in one of the eight:

  - `check_separation.py` went **red in CI** on its own allowlist: a *reason*
    naming a product constant read as a leak. Mention-vs-use, inside the tool
    written to avoid mention-vs-use.
  - `check_curies.py --offline --strict` with an empty cache printed
    `0 problem(s); baseline 22` and `IMPROVED by 22 — lower count to 0`, then
    exited 0. It instructed the operator to ratchet the debt to zero on the
    strength of having checked nothing.
  - the same file swallowed every OBJECT PROPERTY as an error, because OLS4 serves
    properties at `/properties` and classes at `/terms`, and asking the wrong one
    returns 404. `RO:0002212` — "negatively regulates" — had never been checked.
  - `check_no_human_rows.py` is the one gate whose failure is unrecoverable (a
    person's identifier in a public git history), and this repository's copy of it
    had no test at all. Only `fdp-1`'s copy did.

The shape is always the same: **a gate that passes without checking anything.** So
these tests assert BEHAVIOUR — can it refuse, and does it still accept — never
counts or filenames. A test that asserts `disputed == 6` breaks on the next data
change and gets deleted; a test that asserts "this gate refuses a repository
containing a person" is true for as long as the gate is worth having.

HOW IT WORKS, AND WHY THERE IS NO --root FLAG
---------------------------------------------
Every gate derives its scan root from its own location (`ROOT = HERE.parent`), so
copying the real script into a throwaway repository makes it scan that repository.
No production code changed to make this testable, and because the script is copied
rather than reimplemented, these tests exercise what actually ships. A fixture that
drifts from the gate is worse than no fixture.

Nothing here is committed: every tree is built under pytest's `tmp_path`.
"""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

REPO = pathlib.Path(__file__).resolve().parent.parent


def _git_repo(root: pathlib.Path) -> None:
    """init + stage. `git ls-files` reads the index, so no commit is needed —
    which also means no user.name/user.email, which CI runners may not have."""
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    subprocess.run(["git", "add", "-A"], cwd=root, check=True)


def _plant(gate: str, root: pathlib.Path, *, subdir: str = "tools") -> pathlib.Path:
    """Copy the REAL gate into `root` so its ROOT resolves to `root`."""
    src = REPO / (f"{subdir}/{gate}" if subdir else gate)
    assert src.is_file(), f"{src} — the gate moved; this test is now testing nothing"
    dst = root / subdir / gate if subdir else root / gate
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def _run(script: pathlib.Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, timeout=180)


# --------------------------------------------------------------------------
# check_separation.py — no product identifier ships
# --------------------------------------------------------------------------

# The gate names the patterns it searches for, in its own docstring, so it appears
# in its own allowlist in the real repository — "a gate that cannot name its target
# cannot run". The fixture carries the identical entry, because a fixture that has
# to be shaped differently from production is testing a different program.
SELF_ALLOW = ("tools/check_separation.py  # This gate. It must contain the patterns "
              "it searches for.\n")


def _sep_repo(tmp_path: pathlib.Path, allow: str = "") -> pathlib.Path:
    root = tmp_path / "sep"
    (root / "src").mkdir(parents=True)
    (root / "src" / "engine.py").write_text("def run():\n    return 1\n")
    (root / "README.md").write_text("# A repository with nothing to hide\n")
    gate = _plant("check_separation.py", root)
    (root / "tools" / "separation.allow").write_text(SELF_ALLOW + allow)
    _git_repo(root)
    return gate


def test_separation_accepts_a_clean_repository(tmp_path):
    """The other direction. A gate that refuses everything passes a
    rejection-only suite, so acceptance is asserted in the same file."""
    assert _run(_sep_repo(tmp_path)).returncode == 0


def test_separation_refuses_a_product_name_in_file_contents(tmp_path):
    gate = _sep_repo(tmp_path)
    (gate.parent.parent / "src" / "score.py").write_text("# the kibo composite\n")
    _git_repo(gate.parent.parent)
    r = _run(gate)
    assert r.returncode == 1, r.stdout


def test_separation_refuses_a_product_name_in_a_path_only(tmp_path):
    """Hole 2 of the old inline grep: a directory named `kibo_core/` is invisible
    to a content search. The file planted here is clean; only its path is not."""
    gate = _sep_repo(tmp_path)
    d = gate.parent.parent / "kibo_core"
    d.mkdir()
    (d / "notes.md").write_text("nothing sensitive in here at all\n")
    _git_repo(gate.parent.parent)
    r = _run(gate)
    assert r.returncode == 1, r.stdout
    assert "PATH NAME" in r.stdout


def test_separation_allowlist_reason_may_name_the_product(tmp_path):
    """The 2026-08-30 CI failure, pinned.

    A reason has to be able to say what it excepts. `separation.allow` explains
    that `design/DIVERGENCES.md` records a rename FROM a product constant — and
    the gate read its own explanation as the leak."""
    allow = ("design/DIVERGENCES.md   # Records renames such as "
             "KIBO_PRODUCT_SCORE_MODULE -> BAC_SCORER_MODULE.\n")
    gate = _sep_repo(tmp_path, allow=allow)
    d = gate.parent.parent / "design"
    d.mkdir()
    (d / "DIVERGENCES.md").write_text("| KIBO_PRODUCT_SCORE_MODULE | BAC_SCORER_MODULE |\n")
    _git_repo(gate.parent.parent)
    r = _run(gate)
    assert r.returncode == 0, r.stdout


def test_separation_still_scans_the_allowlists_path_column(tmp_path):
    """...and the hole that fix could have opened.

    Exempting `separation.allow` outright would have made it the one file in the
    repository where a product name could hide. Only the reason text after `#` is
    blanked; a product-named PATH in the left column must still fail."""
    gate = _sep_repo(tmp_path, allow="kibo_notes.md   # a reason that reads fine\n")
    (gate.parent.parent / "kibo_notes.md").write_text("clean\n")
    _git_repo(gate.parent.parent)
    assert _run(gate).returncode == 1


def test_separation_refuses_an_exception_with_no_reason(tmp_path):
    """An unexplained exception is a rubber stamp — the same argument as an L2
    sign-off with no referent."""
    gate = _sep_repo(tmp_path, allow="PATENTS.md\n")  # no `#` reason on this line
    r = _run(gate)
    assert r.returncode == 1, r.stdout
    assert "no stated reason" in r.stdout


# --------------------------------------------------------------------------
# check_no_human_rows.py — Rule E. The one failure that cannot be undone.
# --------------------------------------------------------------------------

def _human_repo(tmp_path: pathlib.Path) -> pathlib.Path:
    root = tmp_path / "human"
    (root / "data").mkdir(parents=True)
    (root / "data" / "food.json").write_text(json.dumps(
        {"food": "spinach", "values": [{"nutrient_ref": "cdno:0200157", "unit": "mg"}]}))
    gate = _plant("check_no_human_rows.py", root)
    _git_repo(root)
    return gate


def test_human_guard_accepts_a_repository_with_no_person_in_it(tmp_path):
    assert _run(_human_repo(tmp_path)).returncode == 0


def test_human_guard_refuses_a_forbidden_key(tmp_path):
    gate = _human_repo(tmp_path)
    (gate.parent.parent / "data" / "rows.json").write_text(
        json.dumps([{"human_id": "patient-001", "meal": "spinach"}]))
    r = _run(gate)
    assert r.returncode == 1, r.stdout


def test_human_guard_is_silent_when_the_name_is_only_prose(tmp_path):
    """Mention vs use, and the reason this gate matches KEY position only.

    `STUDY-RULES.md` and the specification both contain the string `human_id`
    while explaining that it is forbidden. A gate that greps for the word flags
    its own documentation, gets called noisy, and gets switched off."""
    gate = _human_repo(tmp_path)
    (gate.parent.parent / "data" / "notes.json").write_text(json.dumps(
        {"rule": "a food packet must never carry human_id or patient_id",
         "note": "human_id is the field this repository refuses"}))
    r = _run(gate)
    assert r.returncode == 0, r.stdout


# --------------------------------------------------------------------------
# check_curies.py — an unrun check is not a pass
# --------------------------------------------------------------------------

def _curie_repo(tmp_path: pathlib.Path, baseline: int) -> pathlib.Path:
    root = tmp_path / "curie"
    root.mkdir()
    gate = _plant("check_curies.py", root)
    # The identifier is ASSEMBLED, never written as a literal. `check_curies.py`
    # scans this repository including tests/, so a spelled-out id with a
    # deliberately wrong adjacent label would be harvested from this very file and
    # become a real finding in the corpus the gate reports on — a test that
    # contaminates what it measures. (The `str()` call matters: CPython
    # constant-folds adjacent string literals at compile time, so "CHEBI" ":"
    # "15377" would reappear intact in the .pyc and be harvested anyway.)
    fake = "CHEBI" + ":" + str(15377)
    (root / "terms.json").write_text(json.dumps(
        {"id": fake, "label": "definitely not water"}))
    (root / "tools" / "curie_baseline.json").write_text(
        json.dumps({"count": baseline, "problems": []}))
    return gate


def test_curies_offline_refuses_to_pass_on_an_empty_cache(tmp_path):
    """The bug fixed 2026-08-30, pinned so it cannot come back.

    With no `.curie_cache/`, `--offline` resolved nothing, found no problems, and
    reported an IMPROVEMENT against a baseline of 22 — a green gate over an
    unchecked corpus, plus an instruction to ratchet the debt to zero."""
    gate = _curie_repo(tmp_path, baseline=22)
    r = _run(gate, "--offline", "--strict")
    assert r.returncode == 1, r.stdout
    assert "unchecked" in r.stdout


def test_curies_offline_never_claims_an_improvement_it_did_not_verify(tmp_path):
    gate = _curie_repo(tmp_path, baseline=22)
    r = _run(gate, "--offline")
    assert "IMPROVED" not in r.stdout, r.stdout
    assert "Do NOT lower the baseline" in r.stdout


@pytest.mark.skipif(not os.environ.get("BAC_NETWORK_TESTS"),
                    reason="hits EBI OLS4; set BAC_NETWORK_TESTS=1 to run. Kept out "
                           "of the default suite so a third-party outage cannot turn "
                           "CI red for a reason that has nothing to do with the code.")
def test_curies_resolves_object_properties_and_not_only_classes(tmp_path):
    """OLS4 serves classes at /terms and object properties at /properties, and the
    wrong endpoint returns 404. the relation "negatively regulates" 404s at /terms, so every relation identifier was silently unresolved — neither a
    finding nor counted as checked."""
    root = tmp_path / "props"
    root.mkdir()
    gate = _plant("check_curies.py", root)
    prop = "RO" + ":" + str(2212).zfill(7)          # assembled, see _curie_repo
    (root / "graph.json").write_text(json.dumps(
        {"predicate": prop, "label": "negatively regulates"}))
    (root / "curie_baseline.json").write_text(json.dumps({"count": 0, "problems": []}))
    r = _run(gate, "--strict")
    assert "UNRESOLVED" not in r.stdout, r.stdout
    assert r.returncode == 0, r.stdout


# --------------------------------------------------------------------------
# check_third_party.py — nothing ships undeclared
# --------------------------------------------------------------------------

def _tp_repo(tmp_path: pathlib.Path, entries: list[dict]) -> pathlib.Path:
    root = tmp_path / "tp"
    root.mkdir()
    gate = _plant("check_third_party.py", root)
    (root / "THIRD-PARTY-DATA.json").write_text(json.dumps({"entries": entries}))
    (root / "NOTICE").write_text("Third-party data notices.\n")
    _git_repo(root)
    return gate


def test_third_party_refuses_an_undeclared_data_file(tmp_path):
    """A gate whose manifest is optional is a formality. This asserts the manifest
    is load-bearing: ship data it does not name and the gate fails."""
    gate = _tp_repo(tmp_path, entries=[])
    (gate.parent / "borrowed.tsv").write_text("a\tb\n1\t2\n")
    _git_repo(gate.parent)
    r = _run(gate)
    assert r.returncode == 1, r.stdout
