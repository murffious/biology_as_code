#!/usr/bin/env python3
"""
Structured tests for pathway packs under pathways/ + gold glycolysis/.

  PYTHONPATH=src python3 tests/test_pathway_packs.py
  pytest tests/test_pathway_packs.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

PATHWAYS = ROOT / "pathways"
# Hand-authored gold glycolysis variants (archived under the auto pack).
GLYCOLYSIS_GOLD = ROOT / "pathways" / "glycolysis" / "glycolysis_extra"


def _collect() -> List[Tuple[str, str, Any]]:
    # Import from export script to stay DRY
    sys.path.insert(0, str(ROOT / "scripts"))
    from export_pathway_packs import collect_pathways  # type: ignore

    return collect_pathways()


def test_all_pathway_packs_structural():
    paths = _collect()
    assert paths, "no pathways collected"
    for pack_id, _module, pathway in paths:
        nodes = getattr(pathway, "nodes", {}) or {}
        edges = getattr(pathway, "edges", []) or []
        assert len(nodes) >= 1, f"{pack_id}: expected nodes"
        assert len(edges) >= 1, f"{pack_id}: expected edges"
        for e in edges:
            a = getattr(e, "from_node", None)
            b = getattr(e, "to_node", None)
            assert a in nodes, f"{pack_id}: missing from_node {a}"
            assert b in nodes, f"{pack_id}: missing to_node {b}"
        d = PATHWAYS / pack_id
        if d.is_dir():
            assert (d / "pathway.mermaid").is_file(), f"{pack_id}: missing mermaid"
            assert (d / "tests.md").is_file(), f"{pack_id}: missing tests.md"
    print(f"✓ Structural OK for {len(paths)} pathway graphs")


def test_glycolysis_gold_folder():
    assert GLYCOLYSIS_GOLD.is_dir()
    assert (GLYCOLYSIS_GOLD / "glycolysis.mermaid").is_file()
    assert (GLYCOLYSIS_GOLD / "tests.md").is_file()
    print("✓ Gold glycolysis/ pack present (mermaid + tests.md)")


def test_glycolysis_invariants():
    from biology_as_code.pathways.metabolic_pathways import get_metabolic_pathways_registry

    p = get_metabolic_pathways_registry().get("glycolysis")
    s = p.summary()
    assert s["net_atp"] == 2
    assert s["net_nadh"] == 2
    linked = {e.mechanism_id for e in p.edges if getattr(e, "mechanism_id", "")}
    for req in ("hexokinase", "pfk1", "pyruvate_kinase"):
        assert req in linked, f"missing {req}"
    print("✓ Glycolysis invariants (+2 ATP / +2 NADH; HK/PFK1/PK linked)")


def test_tca_invariants():
    from biology_as_code.pathways.tca_cycle import get_tca_cycle_registry

    p = get_tca_cycle_registry().get("tca_cycle")
    s = p.summary()
    assert s.get("nadh_per_acetyl_coa") == 3
    assert s.get("fadh2_per_acetyl_coa") == 1
    assert s.get("gtp_per_acetyl_coa") == 1
    linked = [e for e in p.edges if getattr(e, "mechanism_id", "")]
    assert len(linked) == 8
    print("✓ TCA invariants (3 NADH + 1 FADH₂ + 1 GTP; 8 linked steps)")


def test_etc_p_ratios():
    from biology_as_code.pathways.etc_oxphos import get_etc_oxphos_registry

    s = get_etc_oxphos_registry().get("etc_oxphos").summary()
    assert s["atp_per_nadh"] == 2.5
    assert s["atp_per_fadh2"] == 1.5
    print("✓ ETC P/O ratios (2.5 / 1.5)")


def test_mechanism_ids_resolve_when_set():
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    reg = get_metabolic_mechanism_registry()
    known = set()
    if hasattr(reg, "list_all"):
        for m in reg.list_all():
            known.add(getattr(m, "id", None) or getattr(m, "name", ""))
    elif hasattr(reg, "mechanisms"):
        known = set(reg.mechanisms.keys())

    paths = _collect()
    missing = []
    for pack_id, _, pathway in paths:
        for e in getattr(pathway, "edges", []) or []:
            mid = getattr(e, "mechanism_id", "") or ""
            if mid and known and mid not in known:
                missing.append((pack_id, mid))
    core_missing = [
        m
        for m in missing
        if m[0] in ("glycolysis", "tca_cycle", "beta_oxidation", "gluconeogenesis")
    ]
    assert len(core_missing) == 0, f"core mechanism ids missing: {core_missing[:10]}"
    print(f"✓ Core mechanism_ids resolve (checked {len(paths)} graphs)")


def test_mermaid_nonempty_when_exported():
    if not PATHWAYS.is_dir():
        print("⊘ pathways/ missing — run scripts/export_pathway_packs.py")
        return
    packs = [
        p
        for p in PATHWAYS.iterdir()
        if p.is_dir() and (p / "pathway.mermaid").is_file()
    ]
    assert packs, "no pathway packs found; run export_pathway_packs.py"
    for p in packs:
        text = (p / "pathway.mermaid").read_text(encoding="utf-8")
        assert "flowchart" in text
        assert "-->" in text or "---" in text
    print(f"✓ Mermaid non-empty for {len(packs)} packs")


def run_all() -> bool:
    tests = [
        test_glycolysis_gold_folder,
        test_all_pathway_packs_structural,
        test_glycolysis_invariants,
        test_tca_invariants,
        test_etc_p_ratios,
        test_mechanism_ids_resolve_when_set,
        test_mermaid_nonempty_when_exported,
    ]
    failed = 0
    print("=" * 60)
    print("PATHWAY PACKS — STRUCTURED TESTS")
    print("=" * 60)
    for t in tests:
        try:
            t()
        except Exception as exc:
            failed += 1
            print(f"✗ {t.__name__}: {exc}")
    print("=" * 60)
    if failed:
        print(f"{failed} FAILED")
        return False
    print("ALL PATHWAY PACK TESTS PASSED")
    return True


if __name__ == "__main__":
    sys.exit(0 if run_all() else 1)
