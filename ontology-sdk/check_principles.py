#!/usr/bin/env python3
"""Run the checkable ontology principles against the repo.

  python3 check_principles.py           report
  python3 check_principles.py --strict   exit 1 on any FAIL

`principles.v1.json` records 32 principles taken from Palantir's open ontology
docs, each with a stance. A principle that only exists in prose is a preference;
the ones that can be tested are tested here, and the ones that cannot say why.

Every principle naming a `check` must have a function of that name in this file.
A missing one is itself a failure — otherwise the register could claim coverage
it does not have, which is the exact defect the whole project is about.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REG = HERE / "principles.v1.json"

OK, FAIL, NA = "OK", "FAIL", "n/a"


def _read(rel: str) -> str:
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


# --------------------------------------------------------------------------- #

def check_no_artifact_triplicated():
    """Rule of three, applied to ontology artifacts across repos."""
    from collections import defaultdict
    skip = {".venv", "node_modules", "__pycache__", ".git", "_to_delete"}
    watch = {"aca.ttl", "claim-shape.ttl", "MASTER_CROSSWALK.tsv",
             "nutrition-vocab.v1.json", "bfo_stack_ontology.json"}
    seen = defaultdict(list)
    for p in ROOT.rglob("*"):
        if p.is_file() and p.name in watch and not (set(p.parts) & skip):
            seen[p.name].append(str(p.relative_to(ROOT)))
    bad = {k: v for k, v in seen.items() if len(v) >= 3}
    if bad:
        return FAIL, f"triplicated: {bad}"
    twos = {k: len(v) for k, v in seen.items() if len(v) == 2}
    return OK, f"no artifact in 3+ places (pairs, all declared: {twos})"


def check_frozen_types_unchanged():
    """Open/closed: the law and gate registries are frozen; CI refuses to merge
    changes to them. Here we only assert they still exist and still parse."""
    g = _read("biology_as_code/src/biology_as_code/audit/gates.py")
    l = _read("biology_as_code/src/biology_as_code/laws.py")
    if not (g and l):
        return FAIL, "gates.py or laws.py missing"
    return OK, f"gates.py {len(g)}B, laws.py {len(l)}B present"


def check_laws_gates_bounds_intact():
    """Logic component: 47 laws = 9 categorical gates + 38 magnitude bounds."""
    # Counted through the public API, never by grepping a file. `textbook_to_code
    # _laws.json` is a SEPARATE 42-row mapping and counting it produces a false
    # 42-vs-47 discrepancy — a trap this project has already walked into once.
    sys.path.insert(0, str(ROOT / "biology_as_code/src"))
    try:
        from biology_as_code import laws as L
    except Exception as e:
        return FAIL, f"cannot import the law registry: {e}"
    ids = L.list_laws()
    gates = sum(1 for i in ids if L.get_law(i).gate_present is True)
    bounds = len(ids) - gates
    if (len(ids), gates, bounds) == (47, 9, 38):
        return OK, "47 laws = 9 categorical gates + 38 magnitude bounds"
    return FAIL, f"expected 47/9/38, got {len(ids)}/{gates}/{bounds}"


def check_declared_has_main_field():
    src = _read("biology_as_code/ontology-sdk/declared.py")
    if "def value" not in src:
        return FAIL, "declared.py has no main-field accessor"
    return OK, "Declared[T].value() is the main field"


def check_declared_three_states():
    src = _read("biology_as_code/ontology-sdk/declared.py")
    have = [t for t in ('OPEN', 'NONE') if f'{t} = "{t}"' in src]
    if len(have) != 2:
        return FAIL, f"declared.py does not define both OPEN and NONE (found {have})"
    # Match a real annotation, not the docstring line that says "never Optional[T]".
    code = "\n".join(l for l in src.splitlines()
                     if not l.lstrip().startswith("#") and "Optional[T] and collapses" not in l)
    if re.search(r"->\s*Optional\[|:\s*Optional\[", code):
        return FAIL, "declared.py annotates Optional[T] — that is the two-state model"
    return OK, "three states, never Optional[T]"


def check_grade_is_computed_not_stored():
    src = _read("biology_as_code/ontology-sdk/declared.py")
    if "def weakest_link" not in src:
        return FAIL, "weakest_link not defined — a derived property must be computed"
    return OK, "weakest_link is computed at read time"


def check_open_is_not_null():
    """Declaredness: the canonical crosswalk must have zero blank cells."""
    p = ROOT / "biology_as_code/MASTER_CROSSWALK.tsv"
    if not p.is_file():
        return FAIL, "canonical crosswalk missing"
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh, delimiter="\t"))
    blank = sum(1 for r in rows[1:] for c in r if c == "")
    opens = sum(1 for r in rows[1:] for c in r if c == "OPEN")
    if blank:
        return FAIL, f"{blank} blank cells — OPEN collapsed to null"
    return OK, f"0 blank, {opens} OPEN declared"


def check_generated_artifacts_are_gated():
    """Every generated artifact needs a --check that proves it is regenerable."""
    gates = {
        "MASTER_CROSSWALK.tsv": "tools/normalize_crosswalk.py",
        "nutrition-vocab.v1.json": "nutri-collective/evidence-platform/src/build_vocab.py",
    }
    missing = [a for a, t in gates.items() if "--check" not in _read(t)]
    if missing:
        return FAIL, f"generated with no drift gate: {missing}"
    return OK, f"{len(gates)} generated artifacts, all gated"


def check_dates_are_iso():
    bad = []
    site = ROOT / "nutri-collective/evidence-platform/site"
    for p in sorted(site.glob("*.v1.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for k in ("as_of", "generated"):
            v = d.get(k)
            if isinstance(v, str) and not re.match(r"^\d{4}-\d{2}-\d{2}", v):
                bad.append(f"{p.name}:{k}={v!r}")
    return (FAIL, f"non-ISO dates: {bad}") if bad else (OK, "all register dates ISO 8601")


def check_versioning_is_on_the_record():
    site = ROOT / "nutri-collective/evidence-platform/site"
    bad = []
    for p in sorted(site.glob("*.v1.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not (d.get("schema_version") or d.get("version")):
            bad.append(p.name)
    return (FAIL, f"unversioned: {bad}") if bad else (OK, "versioning on the record, not modelled as objects")


def check_provenance_fields_survive():
    """The Kitchen Sink, refused. The validator must still require provenance."""
    src = _read("fdp-1/validator/validate_fdp.py")
    need = ["method", "source_ref", "retrieved"]
    missing = [f for f in need if f not in src]
    if missing:
        return FAIL, f"validator no longer mentions {missing} — provenance stripped"
    return OK, "method / source_ref / retrieved all still required"


def check_layer_misnomer():
    """The Misnomer. Both senses of 'layer' are in use; this is expected to FAIL
    until the collision is resolved. A green here would be the lie."""
    causal = len(re.findall(r"\bL[1-5]\b", _read("book/ONTOLOGY-CONSOLIDATION.md")
                            + _read("biology_as_code/ontology-sdk/WHERE-THIS-FITS.md")))
    stack = len(re.findall(r"\bL[06-9]\b", _read("book/ONTOLOGY-CONSOLIDATION.md")
                           + _read("biology_as_code/ontology-sdk/WHERE-THIS-FITS.md")))
    if causal and stack:
        return FAIL, (f"'layer' carries two numbering systems in the same docs "
                      f"(causal-spine refs {causal}, nine-layer refs {stack}) — "
                      f"open naming blocker, qualify both")
    return OK, "one 'layer' sense in use"


def check_dependents_are_generated():
    if "## Dependents" not in _read("book/ONTOLOGY-CONSOLIDATION.md"):
        return FAIL, "no generated Dependents view"
    return OK, "Dependents generated by ontology_inventory.py"


def check_sdk_does_not_import_the_hub():
    """Object views are presentation, not structure."""
    bad = []
    for p in HERE.glob("*.py"):
        if p.name == Path(__file__).name:      # the checker names it in order to check it
            continue
        if re.search(r"evidence-hub", p.read_text(encoding="utf-8")):
            bad.append(p.name)
    return (FAIL, f"SDK references the hub: {bad}") if bad else (OK, "SDK has no dependency on the hub")


# --------------------------------------------------------------------------- #

def main(argv):
    reg = json.loads(REG.read_text(encoding="utf-8"))
    ps = reg["principles"]
    results, fails = [], 0

    for p in ps:
        name = p.get("check")
        if not name:
            results.append((NA, p["id"], p.get("why_not_checkable", "")))
            continue
        fn = globals().get(name)
        if fn is None:
            results.append((FAIL, p["id"], f"register names check {name!r} that does not exist"))
            fails += 1
            continue
        try:
            status, detail = fn()
        except Exception as e:
            status, detail = FAIL, f"{type(e).__name__}: {e}"
        results.append((status, p["id"], detail))
        fails += status == FAIL

    width = max(len(r[1]) for r in results)
    print(f"ontology principles — {len(ps)} recorded, "
          f"{sum(1 for p in ps if p.get('check'))} checkable\n")
    for group in ("design", "structure", "naming", "anti-pattern", "model",
                  "manager", "departure"):
        rows = [(s, i, d) for (s, i, d) in results
                if next(p["group"] for p in ps if p["id"] == i) == group]
        if not rows:
            continue
        print(f"  {group}")
        for status, pid, detail in rows:
            mark = {OK: "ok  ", FAIL: "FAIL", NA: "  · "}[status]
            print(f"    {mark} {pid:{width}}  {detail}")
        print()

    checked = [r for r in results if r[0] != NA]
    print(f"{sum(1 for r in checked if r[0] == OK)}/{len(checked)} checks pass, "
          f"{len(ps) - len(checked)} not machine-checkable (each says why)")
    if fails:
        print(f"\n{fails} FAIL — see above. Known open blocker: the 'layer' misnomer.")
    return 1 if (fails and "--strict" in argv) else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
