#!/usr/bin/env python3
"""
Export structured pathway packs: mermaid + tests.md + INDEX.

Gold style: glycolysis/ (hand-authored at repo root).
Auto packs: pathways/<id>/ from live biology_as_code registries.

  cd biology_as_code
  PYTHONPATH=src python3 scripts/export_pathway_packs.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Callable, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

OUT = ROOT / "pathways"
GOLD = ROOT / "glycolysis"


def _safe_id(name: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return s or "pathway"


def _node_label(node: Any) -> str:
    return getattr(node, "name", None) or getattr(node, "id", str(node))


def _edge_label(edge: Any) -> str:
    parts = []
    mid = getattr(edge, "mechanism_id", "") or ""
    enz = getattr(edge, "enzyme", "") or getattr(edge, "process", "") or ""
    if mid:
        parts.append(mid)
    elif enz:
        parts.append(str(enz)[:40])
    atp = getattr(edge, "atp_cost", None)
    nadh = getattr(edge, "nadh_cost", None)
    if atp:
        parts.append(f"ATP{atp:+g}" if isinstance(atp, (int, float)) else f"ATP={atp}")
    if nadh:
        parts.append(f"NADH{nadh:+g}" if isinstance(nadh, (int, float)) else f"NADH={nadh}")
    return "<br/>".join(parts) if parts else "step"


def pathway_to_mermaid(pathway: Any) -> str:
    lines = [
        "flowchart TD",
        f"  %% Auto-generated from registry pathway: {getattr(pathway, 'name', '?')}",
        f"  %% Do not hand-edit; re-run scripts/export_pathway_packs.py",
    ]
    for ref in getattr(pathway, "references", None) or []:
        lines.append(f"  %% Source: {ref}")
    nodes = getattr(pathway, "nodes", {}) or {}
    edges = getattr(pathway, "edges", []) or []

    for nid, node in nodes.items():
        label = _node_label(node).replace('"', "'")
        sid = re.sub(r"[^A-Za-z0-9_]", "_", str(nid))
        lines.append(f'  {sid}["{label}"]')

    for edge in edges:
        a = re.sub(r"[^A-Za-z0-9_]", "_", str(getattr(edge, "from_node", "")))
        b = re.sub(r"[^A-Za-z0-9_]", "_", str(getattr(edge, "to_node", "")))
        lab = _edge_label(edge).replace('"', "'")
        lines.append(f'  {a} -->|"{lab}"| {b}')

    return "\n".join(lines) + "\n"


def write_tests_md(pathway: Any, module: str, pack_id: str) -> str:
    name = getattr(pathway, "name", pack_id)
    desc = getattr(pathway, "description", "") or ""
    nodes = getattr(pathway, "nodes", {}) or {}
    edges = getattr(pathway, "edges", []) or []
    summary = pathway.summary() if hasattr(pathway, "summary") else {}
    mech = [
        getattr(e, "mechanism_id", "")
        for e in edges
        if getattr(e, "mechanism_id", "")
    ]
    mech = [m for m in mech if m]

    lines = [
        f"# Structured tests — `{name}`",
        "",
        f"**Module:** `{module}`  ",
        f"**Pack id:** `{pack_id}`  ",
        f"**Description:** {desc}",
        "",
        "## Graph size",
        "",
        "| Metric | Value |",
        "|--------|------:|",
        f"| Nodes | {len(nodes)} |",
        f"| Edges | {len(edges)} |",
    ]
    if summary:
        for k, v in summary.items():
            if k in ("name", "description", "nodes", "edges"):
                continue
            lines.append(f"| `{k}` | {v} |")
    lines += [
        "",
        "## Structural checklist",
        "",
        "- [ ] `nodes >= 1` and `edges >= 1`",
        "- [ ] Every edge `from_node` / `to_node` exists in `nodes`",
        "- [ ] No empty node ids",
        "- [ ] Mermaid renders (`pathway.mermaid`)",
        "",
        "## Mechanism links",
        "",
        f"Edges with `mechanism_id`: **{len(mech)}** / {len(edges)}",
        "",
    ]
    if mech:
        lines.append("```")
        for m in sorted(set(mech)):
            lines.append(f"  {m}")
        lines.append("```")
    else:
        lines.append("_No mechanism_id links (topology-only teaching graph)._")
    refs = getattr(pathway, "references", None) or []
    if refs:
        lines += ["", "## Sources", ""]
        for r in refs:
            lines.append(f"- {r}")
    lines += [
        "",
        "## Biochemical invariants (document here)",
        "",
        "Hand-fill like root `glycolysis/tests.md` when auditing against pathway mermaid packs:",
        "",
        "| Invariant | Expected | Status |",
        "|-----------|----------|--------|",
        "| Energy / stoichiometry | _(TBD for this path)_ | Open |",
        "| Irreversible / regulated steps | _(TBD)_ | Open |",
        "",
        "## Automated tests",
        "",
        "```bash",
        "PYTHONPATH=src python3 tests/test_pathway_packs.py",
        "# or: pytest tests/test_pathway_packs.py -q",
        "```",
        "",
        "Gold audit style: `glycolysis/tests.md`.",
        "",
    ]
    return "\n".join(lines)


def write_readme(pathway: Any, module: str, pack_id: str) -> str:
    name = getattr(pathway, "name", pack_id)
    desc = getattr(pathway, "description", "") or "Teaching pathway graph."
    return "\n".join(
        [
            f"# {name}",
            "",
            desc,
            "",
            f"- **Python module:** `{module}`",
            f"- **Graph:** `pathway.mermaid` (auto)",
            f"- **Tests:** `tests.md` + `tests/test_pathway_packs.py`",
            f"- **Gold template:** repo root `glycolysis/`",
            "",
            "Tier: FLOW teaching. Not product meal score / Kibo-vars product scorer.",
            "",
        ]
    )


def collect_pathways() -> List[Tuple[str, str, Any]]:
    """Return list of (pack_id, module_path, pathway_obj)."""
    from biology_as_code.pathways.metabolic_pathways import get_metabolic_pathways_registry
    from biology_as_code.pathways.tca_cycle import get_tca_cycle_registry
    from biology_as_code.pathways.etc_oxphos import get_etc_oxphos_registry
    from biology_as_code.pathways.beta_oxidation import get_beta_oxidation_registry
    from biology_as_code.pathways.gluconeogenesis import get_gluconeogenesis_registry
    from biology_as_code.pathways.urea_cycle import get_urea_cycle_registry
    from biology_as_code.pathways.pentose_phosphate import get_pentose_phosphate_registry
    from biology_as_code.pathways.glycogen_metabolism import get_glycogen_metabolism_registry
    from biology_as_code.pathways.cholesterol_pathway import get_cholesterol_pathway_registry
    from biology_as_code.pathways.fatty_acid_synthesis import get_fatty_acid_synthesis_registry
    from biology_as_code.pathways.ketogenesis import get_ketogenesis_registry
    from biology_as_code.pathways.ketolysis import get_ketolysis_registry
    from biology_as_code.pathways.digestion_absorption_pathways import (
        get_digestion_absorption_registry,
    )
    from biology_as_code.pathways.supporting_pathways import get_supporting_pathways_registry

    loaders: List[Tuple[str, Callable]] = [
        ("biology_as_code.pathways.metabolic_pathways", get_metabolic_pathways_registry),
        ("biology_as_code.pathways.tca_cycle", get_tca_cycle_registry),
        ("biology_as_code.pathways.etc_oxphos", get_etc_oxphos_registry),
        ("biology_as_code.pathways.beta_oxidation", get_beta_oxidation_registry),
        ("biology_as_code.pathways.gluconeogenesis", get_gluconeogenesis_registry),
        ("biology_as_code.pathways.urea_cycle", get_urea_cycle_registry),
        ("biology_as_code.pathways.pentose_phosphate", get_pentose_phosphate_registry),
        ("biology_as_code.pathways.glycogen_metabolism", get_glycogen_metabolism_registry),
        ("biology_as_code.pathways.cholesterol_pathway", get_cholesterol_pathway_registry),
        ("biology_as_code.pathways.fatty_acid_synthesis", get_fatty_acid_synthesis_registry),
        ("biology_as_code.pathways.ketogenesis", get_ketogenesis_registry),
        ("biology_as_code.pathways.ketolysis", get_ketolysis_registry),
        ("biology_as_code.pathways.digestion_absorption_pathways", get_digestion_absorption_registry),
        ("biology_as_code.pathways.supporting_pathways", get_supporting_pathways_registry),
    ]

    out: List[Tuple[str, str, Any]] = []
    for module, getter in loaders:
        reg = getter()
        paths = reg.list_all() if hasattr(reg, "list_all") else list(reg.pathways.values())
        for p in paths:
            pid = _safe_id(getattr(p, "name", "pathway"))
            out.append((pid, module, p))
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for pack_id, module, pathway in collect_pathways():
        d = OUT / pack_id
        d.mkdir(parents=True, exist_ok=True)
        (d / "pathway.mermaid").write_text(pathway_to_mermaid(pathway), encoding="utf-8")
        (d / "tests.md").write_text(
            write_tests_md(pathway, module, pack_id), encoding="utf-8"
        )
        (d / "README.md").write_text(
            write_readme(pathway, module, pack_id), encoding="utf-8"
        )
        n = len(getattr(pathway, "nodes", {}) or {})
        e = len(getattr(pathway, "edges", []) or [])
        rows.append((pack_id, module, n, e, getattr(pathway, "name", pack_id)))
        print(f"  wrote pathways/{pack_id}/  (n={n} e={e})")

    lines = [
        "# Pathway packs index",
        "",
        "Auto-generated by `scripts/export_pathway_packs.py`.",
        "",
        f"Gold hand pack: [`../glycolysis/`](../glycolysis/) (exists={GOLD.is_dir()})",
        "",
        "| Pack | Module | Nodes | Edges |",
        "|------|--------|------:|------:|",
    ]
    for pack_id, module, n, e, _name in sorted(rows):
        lines.append(f"| [`{pack_id}`](./{pack_id}/) | `{module}` | {n} | {e} |")
    lines += [
        "",
        f"**Total:** {len(rows)} graphs",
        "",
    ]
    (OUT / "INDEX.md").write_text("\n".join(lines), encoding="utf-8")

    # top-level pathways README
    (OUT / "README.md").write_text(
        "\n".join(
            [
                "# Pathway packs — mermaid + structured tests",
                "",
                "**Gold template:** [`../glycolysis/`](../glycolysis/)",
                "",
                "Auto packs for every teaching pathway graph in `biology_as_code.pathways`.",
                "",
                "## Layout",
                "",
                "```text",
                "pathways/<pathway_id>/",
                "  README.md",
                "  pathway.mermaid",
                "  tests.md",
                "glycolysis/                 # hand-authored gold pack (repo root)",
                "scripts/export_pathway_packs.py",
                "tests/test_pathway_packs.py",
                "```",
                "",
                "## Regenerate",
                "",
                "```bash",
                "cd biology_as_code",
                "PYTHONPATH=src python3 scripts/export_pathway_packs.py",
                "PYTHONPATH=src python3 tests/test_pathway_packs.py",
                "```",
                "",
                "See [INDEX.md](./INDEX.md).",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(f"INDEX.md — {len(rows)} packs")


if __name__ == "__main__":
    main()
