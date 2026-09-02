#!/usr/bin/env python3
"""dump_pathway_nodes.py — every pathway node as one JSON row, for ontology resolution.

    python3 scripts/dump_pathway_nodes.py > /tmp/bac_pathway_nodes.json

The pathway modules carry node ids that are local slugs ("glucose"), which cannot be
joined to a claim carrying an OLS4-resolved accession. This dump is the input to
`services/assay/src/scripts/resolve_pathway_nodes.ts`, which asks EBI OLS4 for a ChEBI
accession per chemical node — exact label or synonym only, never a guess.

Read-only: nothing here modifies a pathway module.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from biology_as_code.pathways.registry import pathway_loaders  # noqa: E402


def rows() -> list[dict]:
    out: list[dict] = []
    for label, factory in pathway_loaders():
        registry = factory()
        try:
            pathways = list(registry.pathways.values())
        except AttributeError:
            pathways = list(registry.list_all())
        for pathway in pathways:
            for key, node in (getattr(pathway, "nodes", {}) or {}).items():
                node_type = getattr(node, "node_type", None)
                out.append(
                    {
                        "module": label,
                        "pathway": getattr(pathway, "name", "") or getattr(pathway, "id", ""),
                        "key": str(key),
                        "id": getattr(node, "id", None),
                        "name": getattr(node, "name", None),
                        "node_type": getattr(node_type, "value", None),
                    }
                )
    return out


if __name__ == "__main__":
    json.dump(rows(), sys.stdout, indent=1)
