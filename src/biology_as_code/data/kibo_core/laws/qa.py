"""CLI / importable QA for law registry + pathways."""

from __future__ import annotations

import json
import sys

from biology_as_code.data.kibo_core.pathways.nonhaem_iron import NONHAEM_IRON_PATHWAY

from .atomic import binding_qa, walk_bindings
from .registry import load_default_registry
from .walk import collect_reachable, walk_pathway


def qa_pathways() -> dict:
    errors: list[str] = []
    warns: list[str] = []
    nodes = NONHAEM_IRON_PATHWAY
    # all next targets exist
    for n in nodes.values():
        for nxt in n.next_pathways:
            if nxt not in nodes:
                errors.append(f"dangling next {n.id} → {nxt}")
        for mod in (*n.inhibitors, *n.enhancers):
            if not mod.law_id.startswith("LAW-"):
                warns.append(f"{mod.id} law_id {mod.law_id}")
            if mod.requires_context is None:
                errors.append(f"{mod.id} missing requires_context")
    # reachable from start
    reach = collect_reachable(nodes, "fe.meal_payload")
    if "fe.blood_transferrin" not in reach:
        errors.append("blood terminus not reachable from meal_payload")
    # no cycles in first-path spine
    seen = set()
    cur = "fe.meal_payload"
    while cur:
        if cur in seen:
            errors.append(f"cycle on spine at {cur}")
            break
        seen.add(cur)
        nxts = nodes[cur].next_pathways
        cur = nxts[0] if nxts else ""
    return {"ok": not errors, "errors": errors, "warns": warns, "nodes": len(nodes), "reachable": len(reach)}


def main() -> int:
    reg = load_default_registry()
    r = reg.qa()
    p = qa_pathways()
    b = binding_qa()
    out = {"registry": r, "pathways": p, "atomic_bindings": b}
    print(json.dumps(out, indent=2))
    # demo walk
    demo = walk_pathway(
        NONHAEM_IRON_PATHWAY,
        "fe.meal_payload",
        context={"ascorbate_same_meal": True, "tannin": True},
        cargo="nonhaem_Fe",
    )
    print("demo_walk", json.dumps(demo.as_dict(), indent=2))
    # nutrient bindings moving down the system
    stack = walk_bindings()
    slim = [
        {
            "order": u["order"],
            "stage": u["stage_id"],
            "system": u["system"],
            "nutrients": [x.get("ref") for x in u["bindings"]],
            "next": u["next_pathways"],
        }
        for u in stack
    ]
    print("bindings_down_system", json.dumps(slim, indent=2))
    return 0 if r["ok"] and p["ok"] and b["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
