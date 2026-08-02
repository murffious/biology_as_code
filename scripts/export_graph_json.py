#!/usr/bin/env python3
"""
Export registry pathways as JSON graphs for web consumption.

The HTML cascade diagrams hand-copy graph facts — which metabolite feeds which,
what catalyses the step, which vitamin the step cannot run without — that already
exist as tested Python pathway packs. Hand-copied facts drift from the code that
tests them, and the diagram is the copy nobody re-checks.

So: the FACTS ship from here, the LAYOUT stays hand-authored. That split is the
whole design, and it is why this exporter deliberately emits **no x/y anywhere**.
A renderer keys its own coordinate file by `node.id` and joins the two. If
coordinates ever appear in this output, the hand-tuned layout becomes something a
generator overwrites, and the split is gone.

Sits beside `export_pathway_packs.py` (mermaid, for humans reading the repo) and
shares its `collect_pathways()` registry walk, so a pathway wired into
`registry.pathway_loaders()` gets both without further wiring.

  cd biology_as_code
  PYTHONPATH=src python3 scripts/export_graph_json.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from export_pathway_packs import collect_pathways  # noqa: E402

from biology_as_code.pathways._types import (  # noqa: E402
    edge_enzyme,
    edge_nutrients,
    edge_yields,
)

OUT = ROOT / "src" / "biology_as_code" / "pathways" / "packs"

#: Schema tags, versioned so a web client can refuse a shape it does not know.
GRAPH_SCHEMA = "biology-as-code/pathway-graph@1"
INDEX_SCHEMA = "biology-as-code/pathway-graph-index@1"

GENERATOR = "scripts/export_graph_json.py"

#: Keys a renderer must NOT find here — see the module docstring. Asserted by
#: `tests/test_graph_json_export.py`; listed once so both sides agree.
FORBIDDEN_KEYS = frozenset({"x", "y", "cx", "cy", "left", "top", "position", "coords"})


def _node_kind(node: Any) -> str:
    """Metabolic role as a plain string.

    Three shapes reach here: a `PathwayNodeType` enum (shared `_types` nodes), a
    bare string, and `RegulatoryNode.role` (nutrient_sensing never migrated).
    Read like `edge_enzyme` does — by getattr, so no module has to move first.
    """
    value = getattr(node, "node_type", None)
    if value is None:
        value = getattr(node, "role", "") or ""
    return str(getattr(value, "value", value) or "")


def _certification(pathway: Any) -> str:
    """Where this graph sits on the gate lattice in `biology_as_code.nodes`.

    Teaching topology drawn from a textbook map is a secondary source, so a cited
    pathway is a `prior` and an uncited one is only a `candidate`. Nothing here
    reaches `bound`: that would require reading the primary literature for every
    edge, which no pathway module claims to have done. Emitting the honest lower
    tier keeps a web client from rendering a wall chart as settled fact.
    """
    return "prior" if (getattr(pathway, "references", None) or []) else "candidate"


def node_to_json(node: Any) -> Dict[str, Any]:
    """One node. Identity, display text and biology — no geometry."""
    return {
        "id": str(getattr(node, "id", "")),
        "label": getattr(node, "name", None) or str(getattr(node, "id", "")),
        "kind": _node_kind(node),
        "compartment": str(getattr(node, "compartment", "") or ""),
        "notes": str(getattr(node, "notes", "") or ""),
    }


def edge_to_json(edge: Any) -> Dict[str, Any]:
    """One edge, via the shared accessors so no legacy field name is dropped.

    `yields` is already sign-normalised by `edge_yields()` (positive = produced),
    which matters because the raw redox fields carry the opposite sign to the
    phosphate fields — a client reading `nadh_cost` directly would print
    "NADH-1" on the step that makes NADH.
    """
    return {
        "from": str(getattr(edge, "from_node", "")),
        "to": str(getattr(edge, "to_node", "")),
        "enzyme": edge_enzyme(edge),
        "cofactors": edge_nutrients(edge),
        "yields": [{"species": species, "delta": delta} for species, delta in edge_yields(edge)],
        "mechanism_id": str(getattr(edge, "mechanism_id", "") or ""),
        "notes": str(getattr(edge, "notes", "") or ""),
    }


def pathway_to_json(pathway: Any, module: str, pack_id: str) -> Dict[str, Any]:
    """One pathway as a web-ready document."""
    nodes = getattr(pathway, "nodes", {}) or {}
    edges = getattr(pathway, "edges", []) or []
    references = list(getattr(pathway, "references", None) or [])

    deps: Dict[str, List[str]] = {}
    if hasattr(pathway, "nutrient_dependencies"):
        deps = {k: list(v) for k, v in pathway.nutrient_dependencies().items()}
    net: Dict[str, int] = {}
    if hasattr(pathway, "net_yields"):
        net = dict(pathway.net_yields())

    return {
        "schema": GRAPH_SCHEMA,
        "id": pack_id,
        "name": str(getattr(pathway, "name", pack_id)),
        "description": str(getattr(pathway, "description", "") or ""),
        "provenance": {
            "module": module,
            "generator": GENERATOR,
            "certification": _certification(pathway),
            "references": references,
        },
        # Declaration order, not sorted: the modules list metabolites along the
        # chain, which is the order a reader expects and a layout file follows.
        "nodes": [node_to_json(n) for n in nodes.values()],
        "edges": [edge_to_json(e) for e in edges],
        # Derived views the graph cannot answer by inspection: which steps a
        # single shortfall stops, and what the whole chain nets out to.
        "nutrient_dependencies": {k: deps[k] for k in sorted(deps)},
        "net_yields": {k: net[k] for k in sorted(net)},
    }


def index_to_json(documents: List[Dict[str, Any]]) -> Dict[str, Any]:
    """The combined index: one fetch tells a client what exists and where.

    `nutrient_index` is the cross-pathway roll-up — vitamin B6 lands in both
    tryptophan→niacin and carnitine synthesis, so one shortfall shows up twice.
    A per-pathway file cannot show that; a client should not have to load all
    forty to find out.
    """
    nutrient_index: Dict[str, List[str]] = {}
    for doc in documents:
        for nutrient, steps in doc["nutrient_dependencies"].items():
            nutrient_index.setdefault(nutrient, []).extend(
                f"{doc['id']}::{step}" for step in steps
            )

    return {
        "schema": INDEX_SCHEMA,
        "generator": GENERATOR,
        "count": len(documents),
        "pathways": [
            {
                "id": doc["id"],
                "name": doc["name"],
                "description": doc["description"],
                "module": doc["provenance"]["module"],
                "certification": doc["provenance"]["certification"],
                "nodes": len(doc["nodes"]),
                "edges": len(doc["edges"]),
                "cofactors": sorted(doc["nutrient_dependencies"]),
                "graph": f"{doc['id']}/graph.json",
            }
            for doc in sorted(documents, key=lambda d: d["id"])
        ],
        "nutrient_index": {k: sorted(v) for k, v in sorted(nutrient_index.items())},
    }


def dumps(document: Dict[str, Any]) -> str:
    """Stable text for one document.

    No timestamp and no host path: the packs directory is under a golden-digest
    test, so a re-run that changed nothing must produce byte-identical files.
    `ensure_ascii=False` keeps ε-N-trimethyl-L-lysine and γ-butyrobetaine
    readable in the file rather than escaped.
    """
    return json.dumps(document, indent=2, ensure_ascii=False) + "\n"


def build_all() -> List[Dict[str, Any]]:
    """Every registry pathway as a JSON document, without writing anything."""
    return [
        pathway_to_json(pathway, module, pack_id)
        for pack_id, module, pathway in collect_pathways()
    ]


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    documents = build_all()
    for doc in documents:
        pack = OUT / doc["id"]
        pack.mkdir(parents=True, exist_ok=True)
        (pack / "graph.json").write_text(dumps(doc), encoding="utf-8")
        print(f"  wrote packs/{doc['id']}/graph.json  (n={len(doc['nodes'])} e={len(doc['edges'])})")

    index = index_to_json(documents)
    (OUT / "graph-index.json").write_text(dumps(index), encoding="utf-8")
    print(
        f"graph-index.json — {index['count']} graphs, "
        f"{len(index['nutrient_index'])} cofactor nutrients"
    )


if __name__ == "__main__":
    main()
