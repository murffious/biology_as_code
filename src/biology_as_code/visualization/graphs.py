"""Pathway graph → mermaid (teaching visuals, not product score charts)."""

from __future__ import annotations

import re
from typing import Any


def pathway_to_mermaid(pathway: Any) -> str:
    lines = [
        "flowchart TD",
        f"  %% {getattr(pathway, 'name', 'pathway')}",
    ]
    nodes = getattr(pathway, "nodes", {}) or {}
    for nid, node in nodes.items():
        label = getattr(node, "name", None) or nid
        label = str(label).replace('"', "'")
        sid = re.sub(r"[^A-Za-z0-9_]", "_", str(nid))
        lines.append(f'  {sid}["{label}"]')
    for e in getattr(pathway, "edges", []) or []:
        a = re.sub(r"[^A-Za-z0-9_]", "_", str(getattr(e, "from_node", "")))
        b = re.sub(r"[^A-Za-z0-9_]", "_", str(getattr(e, "to_node", "")))
        lab = getattr(e, "mechanism_id", None) or getattr(e, "enzyme", None) or getattr(e, "process", "") or ""
        lab = str(lab).replace('"', "'")[:48]
        lines.append(f'  {a} -->|"{lab}"| {b}')
    return "\n".join(lines) + "\n"
