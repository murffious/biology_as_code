#!/usr/bin/env python3
"""
Pathway integration gate — run before merging a new/changed teaching graph.

Checks that every registry pathway is fully wired:

  • discoverable via list_pathways / get_pathway
  • pack dir under pathways/packs/<id>/ with mermaid + tests.md + README
  • mermaid is non-empty (flowchart + edge)
  • graph structure: edges endpoints ∈ nodes
  • mechanism_id values resolve when set
  • COVERAGE.md mentions the pathway name
  • no orphan pack folders (except gold extras dirs)

Usage:
  cd biology_as_code
  PYTHONPATH=src python3 scripts/check_pathway_integration.py
  PYTHONPATH=src python3 scripts/check_pathway_integration.py --pathway bcaa_catabolism
  PYTHONPATH=src python3 scripts/check_pathway_integration.py --json

Exit 0 = integrated. Exit 1 = gaps (print report).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PACKS = ROOT / "src" / "biology_as_code" / "pathways" / "packs"
COVERAGE = PACKS / "COVERAGE.md"

# Directories under packs/ that are not pathway packs
NON_PACK_DIRS = frozenset()
# Nested gold extras live inside a pack (e.g. glycolysis/glycolysis_extra) — not top-level


def _safe_id(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s or "pathway"


def _mechanism_ids() -> set[str]:
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    reg = get_metabolic_mechanism_registry()
    if hasattr(reg, "list_all"):
        return {getattr(m, "id", "") for m in reg.list_all() if getattr(m, "id", "")}
    return set(getattr(reg, "mechanisms", {}).keys())


def _check_one(name: str, pathway: Any, known_mechs: set[str]) -> list[str]:
    """Return list of problem strings (empty = OK)."""
    problems: list[str] = []
    pack_id = _safe_id(name)
    pack = PACKS / pack_id

    nodes = getattr(pathway, "nodes", {}) or {}
    edges = getattr(pathway, "edges", []) or []

    if len(nodes) < 1:
        problems.append("graph has no nodes")
    if len(edges) < 1:
        problems.append("graph has no edges")

    for i, e in enumerate(edges):
        a = getattr(e, "from_node", None)
        b = getattr(e, "to_node", None)
        if a not in nodes:
            problems.append(f"edge[{i}] from_node {a!r} missing from nodes")
        if b not in nodes:
            problems.append(f"edge[{i}] to_node {b!r} missing from nodes")
        mid = getattr(e, "mechanism_id", "") or ""
        if mid and known_mechs and mid not in known_mechs:
            problems.append(f"edge[{i}] unknown mechanism_id {mid!r}")

    if not pack.is_dir():
        problems.append(f"missing pack dir packs/{pack_id}/ — run export_pathway_packs.py")
        return problems

    mermaid = pack / "pathway.mermaid"
    tests_md = pack / "tests.md"
    readme = pack / "README.md"
    if not mermaid.is_file():
        problems.append(f"missing {pack_id}/pathway.mermaid")
    else:
        text = mermaid.read_text(encoding="utf-8")
        if "flowchart" not in text.lower() and "graph " not in text.lower():
            problems.append(f"{pack_id}/pathway.mermaid: no flowchart/graph directive")
        if "-->" not in text and "---" not in text:
            problems.append(f"{pack_id}/pathway.mermaid: no edges")
        if len(text.strip()) < 40:
            problems.append(f"{pack_id}/pathway.mermaid: suspiciously short")
    if not tests_md.is_file():
        problems.append(f"missing {pack_id}/tests.md")
    if not readme.is_file():
        problems.append(f"missing {pack_id}/README.md")

    if COVERAGE.is_file():
        cov = COVERAGE.read_text(encoding="utf-8")
        # Accept name or pack path mention
        if name not in cov and pack_id not in cov:
            problems.append(f"not mentioned in packs/COVERAGE.md (add a table row)")
    else:
        problems.append("packs/COVERAGE.md missing")

    return problems


def run_checks(only: str | None = None) -> dict[str, Any]:
    from biology_as_code import get_pathway, list_pathways

    names = list_pathways()
    known_mechs = _mechanism_ids()
    report: dict[str, Any] = {
        "registry_count": len(names),
        "ok": [],
        "failed": {},
        "orphan_packs": [],
        "missing_packs": [],
    }

    name_set = {n for n in names}
    lower_map = {n.lower(): n for n in names}

    targets = names
    if only:
        key = only.strip().lower()
        if key not in lower_map and only not in name_set:
            report["failed"][only] = [f"not in list_pathways() — wire registry.pathway_loaders()"]
            report["pass"] = False
            return report
        targets = [lower_map.get(key, only)]

    for name in targets:
        p = get_pathway(name)
        if p is None:
            report["failed"][name] = ["get_pathway returned None"]
            continue
        probs = _check_one(name, p, known_mechs)
        if probs:
            report["failed"][name] = probs
        else:
            report["ok"].append(name)

    # Orphan / missing pack scan (full suite only)
    if only is None and PACKS.is_dir():
        registry_ids = {_safe_id(n) for n in names}
        pack_dirs = {
            d.name
            for d in PACKS.iterdir()
            if d.is_dir() and not d.name.startswith("_") and d.name not in NON_PACK_DIRS
        }
        # ignore nested only; top-level dirs should match packs
        report["orphan_packs"] = sorted(pack_dirs - registry_ids)
        report["missing_packs"] = sorted(registry_ids - pack_dirs)

        for oid in report["orphan_packs"]:
            report["failed"].setdefault(f"[orphan pack] {oid}", []).append(
                "pack folder has no registry pathway — delete or register a graph"
            )
        for mid in report["missing_packs"]:
            if mid not in { _safe_id(n) for n in report["failed"] }:
                report["failed"].setdefault(mid, []).append(
                    "registry pathway has no pack — run export_pathway_packs.py"
                )

    report["pass"] = len(report["failed"]) == 0
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate pathway integration (registry ↔ packs).")
    parser.add_argument(
        "--pathway", "-p",
        action="append",
        dest="pathways",
        help="Check only this pathway name (repeatable). Default: all.",
    )
    parser.add_argument("--json", action="store_true", help="Machine-readable report.")
    args = parser.parse_args(argv)

    if args.pathways:
        # merge multi-pathway runs
        combined: dict[str, Any] = {
            "registry_count": 0,
            "ok": [],
            "failed": {},
            "orphan_packs": [],
            "missing_packs": [],
            "pass": True,
        }
        for name in args.pathways:
            part = run_checks(only=name)
            combined["registry_count"] = part["registry_count"]
            combined["ok"].extend(part["ok"])
            combined["failed"].update(part["failed"])
        combined["pass"] = len(combined["failed"]) == 0
        report = combined
    else:
        report = run_checks(only=None)

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("=" * 60)
        print("PATHWAY INTEGRATION CHECK")
        print("=" * 60)
        print(f"Registry pathways: {report['registry_count']}")
        print(f"OK: {len(report['ok'])}")
        if report["orphan_packs"]:
            print(f"Orphan packs: {', '.join(report['orphan_packs'])}")
        if report["missing_packs"]:
            print(f"Missing packs: {', '.join(report['missing_packs'])}")
        if report["failed"]:
            print()
            print("FAILURES:")
            for name, probs in sorted(report["failed"].items()):
                print(f"  ✗ {name}")
                for pr in probs:
                    print(f"      - {pr}")
            print()
            print("Fix: docs/python/ADD_PATHWAY.md")
            print("Then: PYTHONPATH=src python3 scripts/export_pathway_packs.py")
        else:
            print()
            print("ALL CHECKS PASSED — graphs, mermaid packs, mechanisms, COVERAGE aligned.")
        print("=" * 60)

    return 0 if report["pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
