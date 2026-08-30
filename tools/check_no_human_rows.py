#!/usr/bin/env python3
# SYNCED COPY — canonical source is murffious/fdp-1 tools/check_no_human_rows.py
# Edit it there, then copy here. `check_todo.py` in nutri-collective compares the two
# and reports drift, because two copies of a guard that disagree is worse than one.
"""Refuse any data file in this repository that carries a person.

THIS IS A STUDY RULE, NOT FDP-1 CONFORMANCE
-------------------------------------------
FDP-1 §6 asks *is this value properly provenanced*. This asks *does this repository
contain a human being*. Different questions, and this one deliberately lives outside
the specification: adding a policy rule to §6 would change conformance for every third
party implementing FDP-1, which is not ours to do.

WHY IT EXISTS
-------------
Tested 2026-08-29: a food declaration carrying `"human_id": "patient-001"` was handed
to validate_fdp.py and came back **CONFORMS, exit 0**. It sails straight through as an
ignored extra key. Every other failure in this project is recoverable — a wrong id gets
corrected, a bad licence gets renegotiated, a stale score gets re-run. A person's
identifier in a public git history is not. It survives deletion, it survives force-push,
it is in every clone and every fork and the GitHub API.

So this is the one gate that runs before the others.

MENTION vs USE — THE REASON THIS IS NOT A GREP
----------------------------------------------
`STUDY-RULES.md` contains the sentence "no human_id in the food repo". So does this
file, several times. A naive grep flags both and the guard gets switched off inside a
week — the same 27%-false-positive death that nearly killed check_curies.py.

The rule that makes it usable: **a violation is a forbidden name in KEY position in a
structured data file.** Prose that talks about human_id is a mention. A JSON object
with `"human_id":` as a key is a use. Markdown and source code are deliberately out of
scope and that is a design decision, not an oversight — code that *builds* a record is
caught when the record is written, which is the moment that matters.

    python3 tools/check_no_human_rows.py            # scan the working tree
    python3 tools/check_no_human_rows.py --staged   # scan what is about to be committed
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent

# Field names that identify or describe a person. Kept deliberately tight: every
# entry must be a name that has NO legitimate meaning in a food or provenance record.
# `name`, `id`, `subject` and `sample` are absent on purpose — they are ambiguous, and
# an ambiguous rule produces noise, and noise gets the gate disabled.
FORBIDDEN = {
    "human_id", "humanid", "patient_id", "patientid", "participant_id", "subject_id",
    "person_id", "mrn", "medical_record_number", "ssn", "nhs_number", "insurance_id",
    "date_of_birth", "dateofbirth", "dob", "birth_date", "birthdate",
    "genetic_profile", "geneticprofile", "genotype", "rsid", "snp_call",
    "email", "email_address", "phone", "phone_number", "home_address", "street_address",
    "meal_log", "meallog", "lab_result", "labresult", "nutrient_gap_for_human",
}
DATA_SUFFIX = {".json", ".jsonl", ".csv", ".tsv", ".yaml", ".yml"}
SKIP_DIRS = {".git", ".venv", "node_modules", "__pycache__", "cache", "out",
             "cache_citations", "cache_qu", "cache_instrument_selected"}
# An explicit, reviewed exception list. Empty, and it should stay that way.
ALLOW = ROOT / "tools" / "human-rows.allow"


def norm(k: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(k).lower())


def json_keys(node, trail=""):
    """Every key, with its path — key position only, never values."""
    if isinstance(node, dict):
        for k, v in node.items():
            yield str(k), f"{trail}.{k}"
            yield from json_keys(v, f"{trail}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from json_keys(v, f"{trail}[{i}]")


def scan_text(path: pathlib.Path, text: str) -> list[str]:
    hits: list[str] = []
    suf = path.suffix.lower()
    if suf in {".json", ".jsonl"}:
        docs = []
        if suf == ".jsonl":
            for line in text.splitlines():
                if line.strip():
                    try:
                        docs.append(json.loads(line))
                    except Exception:                            # noqa: BLE001
                        pass
        else:
            try:
                docs.append(json.loads(text))
            except Exception:                                    # noqa: BLE001
                return []          # unparseable JSON is a different problem
        for d in docs:
            for k, where in json_keys(d):
                if norm(k) in FORBIDDEN:
                    hits.append(f"key '{k}' at {where or '<root>'}")
    elif suf in {".csv", ".tsv"}:
        delim = "\t" if suf == ".tsv" else ","
        try:
            header = next(csv.reader(io.StringIO(text), delimiter=delim))
        except Exception:                                        # noqa: BLE001
            return []
        for col in header:
            if norm(col) in FORBIDDEN:
                hits.append(f"column '{col.strip()}'")
    else:                                       # yaml — key position, no parser needed
        for m in re.finditer(r"(?m)^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*:", text):
            if norm(m.group(1)) in FORBIDDEN:
                hits.append(f"key '{m.group(1)}' line {text[:m.start()].count(chr(10))+1}")
    return hits


def staged_files() -> list[pathlib.Path]:
    out = subprocess.run(["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
                         cwd=ROOT, capture_output=True, text=True).stdout.split()
    return [ROOT / f for f in out]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--staged", action="store_true",
                    help="scan only what is about to be committed")
    a = ap.parse_args()

    # An entry is `path  # reason`. The reason is MANDATORY: an exception with no
    # stated justification is a rubber stamp, and this is the one gate whose failure
    # cannot be undone. Same rule as a referent on an L2 sign-off.
    allowed, bad_allow = {}, []
    if ALLOW.exists():
        for raw in ALLOW.read_text().splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            path, _, reason = line.partition("#")
            if not reason.strip():
                bad_allow.append(path.strip())
            else:
                allowed[path.strip()] = reason.strip()

    files = (staged_files() if a.staged else
             [p for p in ROOT.rglob("*") if not SKIP_DIRS & set(p.parts)])
    files = [p for p in files if p.is_file() and p.suffix.lower() in DATA_SUFFIX]

    violations, scanned = [], 0
    for p in files:
        rel = p.relative_to(ROOT).as_posix()
        if rel in allowed:
            continue
        try:
            text = p.read_text(errors="replace")
        except Exception:                                        # noqa: BLE001
            continue
        scanned += 1
        for h in scan_text(p, text):
            violations.append((rel, h))

    if bad_allow:
        print(f"FAIL — {len(bad_allow)} allowlist entr(ies) with no stated reason:")
        for x in bad_allow:
            print(f"  {x}")
        print("Every exception must say why. An unexplained one is a rubber stamp.")
        return 1

    print(f"no-human-rows: scanned {scanned} data file(s)"
          f"{' (staged only)' if a.staged else ''}"
          + (f", {len(allowed)} allowlisted" if allowed else ""))
    for rel, why in sorted(allowed.items()):
        print(f"  allowed  {rel}\n      {why}")
    if violations:
        print(f"\nFAIL — {len(violations)} human-row field(s) in a public repository:\n")
        for rel, h in violations:
            print(f"  {rel}\n      {h}")
        print("\nThis is the one failure that cannot be undone by a later commit.")
        print("Remove it from the file AND from git history before pushing.")
        return 1
    print("OK — no human-row fields in key position.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
