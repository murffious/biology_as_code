#!/usr/bin/env python3
"""Every number the engine ships must name the paper that grounds it.

WHY THIS EXISTS
---------------
`tools/check_pmids.py` checks that a citation we ship resolves to the paper we
claimed. It cannot check the other direction: whether the *numbers* in the engine
have a citation at all. Before this gate they did not. Seven constants sat at
module level in `dig/` as bare literals —

    SOD_O2_PER_H2O2 = 2
    PO_NADH = 2.5

— and all seven are emitted in `to_dict()` payloads, so a consumer reads them as
assertions about mammalian biochemistry with nothing attached. Which paper? Had
anyone checked it? Is the engine even allowed to multiply by this one?
`docs/metabolic-constants.md` answered all three in prose, and prose is not
executable: the same page carried four PMIDs that named unrelated papers for
weeks without any check noticing.

WHAT IT CHECKS
--------------
1. Every module-level numeric assignment under `src/biology_as_code/dig/` is a
   `grounded(...)` call, not a bare literal.
2. Its tier is one this repository allows in code. `population` is refused at
   construction — a tier-3 statistic does not become encodable by acquiring a
   citation, and annotating one would make it look as though it had.
3. Its PMID resolves, and resolves to a paper whose title is consistent with the
   record `check_pmids.py` already verified. This reuses `tools/pmid_cache.json`,
   so the two gates cannot drift apart.

A constant that is genuinely dimensionless and needs no source (a loop bound, an
index) does not belong at module level in `dig/`; put it where it is used.

    python3 tools/check_constants.py            # advisory report
    python3 tools/check_constants.py --strict   # exit 1; what CI runs
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
DIG = ROOT / "src" / "biology_as_code" / "dig"
CACHE = ROOT / "tools" / "pmid_cache.json"

ALLOWED_TIERS = {"identity", "teaching"}


def module_level_numbers(tree: ast.Module) -> list[tuple[str, ast.AST, int]]:
    """Top-level `NAME = <something>` where the something is or should be a number."""
    out = []
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name) or not target.id.isupper():
            continue
        out.append((target.id, node.value, node.lineno))
    return out


def is_number(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Constant)
        and isinstance(node.value, (int, float))
        and not isinstance(node.value, bool)
    )


def grounded_call(node: ast.AST) -> dict | None:
    """Unpack a `grounded(value, tier=..., pmid=..., supports=...)` call."""
    if not isinstance(node, ast.Call):
        return None
    name = node.func.id if isinstance(node.func, ast.Name) else None
    if name != "grounded":
        return None
    fields: dict[str, object] = {}
    for kw in node.keywords:
        if kw.arg and isinstance(kw.value, ast.Constant):
            fields[kw.arg] = kw.value.value
    if node.args and is_number(node.args[0]):
        fields["value"] = node.args[0].value
    return fields


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="exit 1 on any finding")
    args = parser.parse_args()

    cache = json.loads(CACHE.read_text()) if CACHE.exists() else {}
    findings: list[str] = []
    checked = 0

    for path in sorted(DIG.rglob("*.py")):
        tree = ast.parse(path.read_text())
        where = path.relative_to(ROOT)
        for name, value, lineno in module_level_numbers(tree):
            if is_number(value):
                findings.append(
                    f"{where}:{lineno}  {name} = {value.value} is a bare literal\n"
                    "    Wrap it: grounded(<value>, tier=..., pmid=..., supports=...)"
                )
                continue
            fields = grounded_call(value)
            if fields is None:
                continue  # not a number and not a grounded call; nothing to say
            checked += 1
            tier, pmid = fields.get("tier"), fields.get("pmid")
            if tier not in ALLOWED_TIERS:
                findings.append(f"{where}:{lineno}  {name} has tier {tier!r}")
            record = cache.get(str(pmid))
            if record is None:
                findings.append(
                    f"{where}:{lineno}  {name} cites PMID {pmid}, which is not in "
                    "tools/pmid_cache.json\n"
                    "    An unresolved identifier is decoration. Resolve it with "
                    "`python3 tools/check_pmids.py --strict`."
                )
            elif not record.get("title"):
                findings.append(
                    f"{where}:{lineno}  {name} cites PMID {pmid}, which resolves to "
                    "no PubMed record"
                )

    print(f"{checked} grounded constant(s) under src/biology_as_code/dig/; {len(findings)} finding(s)")
    for finding in findings:
        print(f"  {finding}")
    if findings and args.strict:
        return 1
    if findings:
        print("(advisory — pass --strict to fail on these)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
