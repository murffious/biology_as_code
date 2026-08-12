"""
Build the graph from the repository's own registers.

Sources, in order of authority:

  1. ``engine.laws.registry``   — the 47 system-bound laws
  2. ``examples/contributions/*.json``  — accepted evidence contributions
  3. ``examples/claims/*.json``         — adjudicated claim fixtures
  4. ``examples/claims/food_health_claims_500.json`` — 500 foods, their claims,
     the bioactives said to drive them, and an evidence grade per claim

Nothing is invented here. Where a register leaves a magnitude open, the graph
leaves it open too — the loader has no fallback values, by design.
"""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

from biology_as_code.graph.store import GraphStore

# Repo root: src/biology_as_code/graph/build.py -> up 4
_REPO = Path(__file__).resolve().parents[3]
EXAMPLES = _REPO / "examples"

#: Surface relation words in the law register mapped to the closed ENUM.
_REL_ALIASES = {
    "OPENS_GATE": "OPENS_GATE",
    "CLOSES_GATE": "CLOSES_GATE",
    "EXPANDS_BOUND": "EXPANDS_BOUND",
    "NARROWS_BOUND": "NARROWS_BOUND",
    "COMPETES_WITH": "COMPETES_WITH",
    "PART_OF": "PART_OF",
    "NEEDS_RESOLUTION": "NEEDS_RESOLUTION",
    "MALFORMED_MECHANISM": "MALFORMED_MECHANISM",
}


def build(path: str | Path = ":memory:", *, include_foods: bool = True) -> GraphStore:
    """Construct the full graph. Returns an open store."""
    g = GraphStore.open(path)
    load_laws(g)
    load_contributions(g)
    load_claim_fixtures(g)
    if include_foods:
        load_food_claims(g)
    g.commit()
    return g


# ------------------------------------------------------------------ laws

def load_laws(g: GraphStore) -> int:
    """The 47-law register, with systems, organs, gates and bounds split out."""
    from biology_as_code.engine.laws.registry import load_system_bound_registry

    reg = load_system_bound_registry()
    n = 0
    for law in reg.all():
        rec = asdict(law) if is_dataclass(law) else dict(law)
        law_id = rec["id"]

        g.add_node(
            law_id,
            "Law",
            rec.get("law_statement") or law_id,
            system=rec.get("system_name"),
            organ=rec.get("organ"),
            subsystem=rec.get("subsystem"),
            status=rec.get("status"),
            gate_present=bool(rec.get("gate_present")),
            # gate_text carries the law's condition vocabulary and is what the
            # Court reads to decide whether a claim's stated absence closes it.
            gate_text=rec.get("gate_text") or "",
            bound_text=rec.get("bound_text") or "",
            conditions=rec.get("conditions_text") or "",
            executable=bool(rec.get("executable")),
            relation_expression=rec.get("relation_expression") or "",
        )
        n += 1

        # seat: system and organ
        if sys_name := (rec.get("system_name") or "").strip():
            sid = f"system:{_slug(sys_name)}"
            g.add_node(sid, "System", sys_name)
            g.add_edge(law_id, "SEATED_IN", sid)

        if organ := (rec.get("organ") or "").strip():
            oid = f"organ:{_slug(organ)}"
            g.add_node(oid, "Organ", organ)
            g.add_edge(law_id, "LOCATED_AT", oid)

        # gate is categorical; bound is a magnitude. never the same node.
        if rec.get("gate_present") and (gate_text := (rec.get("gate_text") or "").strip()):
            gid = f"gate:{law_id}"
            g.add_node(gid, "Gate", gate_text, law=law_id, categorical=True)
            g.add_edge(law_id, "HAS_GATE", gid)

        if bound_text := (rec.get("bound_text") or "").strip():
            bid = f"bound:{law_id}"
            g.add_node(
                bid,
                "Bound",
                bound_text,
                law=law_id,
                condition=rec.get("conditions_text") or "",
                sourced=False,   # set true when a contribution attaches
            )
            # structural, not a magnitude assertion: the register states the
            # bound as text. The magnitude claim arrives with a contribution.
            g.add_edge(law_id, "HAS_BOUND", bid)

        # typed relation declared by the law itself
        rel = _REL_ALIASES.get((rec.get("relation_type") or "").strip().upper())
        if rel and (expr := (rec.get("relation_expression") or "").strip()):
            g.add_edge(law_id, rel, law_id, expression=expr, self_declared=True)

    # cross-references between laws
    for law in reg.all():
        rec = asdict(law) if is_dataclass(law) else dict(law)
        for ref in _law_refs(rec.get("related_to") or ""):
            if g.get_node(ref) and ref != rec["id"]:
                g.add_edge(rec["id"], "NEEDS_RESOLUTION", ref, kind="cross_reference")
    return n


def _law_refs(text: str) -> list[str]:
    import re
    return sorted({f"LAW-{m:0>3}" for m in re.findall(r"LAW-(\d{1,3})", text or "")})


# --------------------------------------------------------- contributions

def load_contributions(g: GraphStore) -> int:
    """Accepted evidence contributions, and the sources they cite."""
    d = EXAMPLES / "contributions"
    if not d.is_dir():
        return 0
    n = 0
    for f in sorted(d.glob("*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        cid = rec.get("id") or f.stem
        target = rec.get("target") or {}
        strength = rec.get("strength")

        g.add_node(
            cid,
            "Contribution",
            rec.get("notes") or cid,
            type=rec.get("type"),
            target_kind=target.get("kind"),
            target_ref=target.get("ref"),
            asserts_magnitude=bool(rec.get("asserts_magnitude")),
            submitted=rec.get("submitted"),
            contributor=rec.get("contributor"),
            strength=strength,
            signoffs=len(rec.get("signoffs") or []),
        )
        n += 1

        # the source it cites
        src = rec.get("source") or {}
        if src:
            key = src.get("pmid") or src.get("doi") or src.get("citation") or "unknown"
            sid = f"source:{_slug(str(key))[:64]}"
            g.add_node(
                sid,
                "Source",
                src.get("citation") or str(key),
                kind=src.get("kind"),
                pmid=src.get("pmid"),
                doi=src.get("doi"),
                url=src.get("url"),
                # a textbook is not a primary source; the model reads this
                primary=src.get("kind") in {"pubmed", "doi"},
            )
            g.add_edge(cid, "CITES", sid)

        # attach to its target
        ref = (target.get("ref") or "").strip().upper()
        if target.get("kind") == "law" and g.get_node(ref):
            g.add_edge(
                ref,
                "EVIDENCED_BY",
                cid,
                asserts_magnitude=bool(rec.get("asserts_magnitude")),
                evidence=cid,
                strength=strength,
            )
            if bound := g.get_node(f"bound:{ref}"):
                props = dict(bound.props)
                props["sourced"] = True
                g.add_node(bound.id, "Bound", bound.name, **props)
    return n


# ---------------------------------------------------------- claim fixtures

def load_claim_fixtures(g: GraphStore) -> int:
    """The adjudicated Court fixtures — the model's gold labels."""
    d = EXAMPLES / "claims"
    if not d.is_dir():
        return 0
    n = 0
    for f in sorted(d.glob("claim_*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        cid = rec.get("id") or f.stem
        rosetta = rec.get("rosetta") or {}
        g.add_node(
            cid,
            "Claim",
            rec.get("surface_claim") or cid,
            kingdom=rec.get("kingdom"),
            gate_check=rec.get("gate_check"),
            gate_note=rec.get("gate_note"),
            verdict=rec.get("verdict"),
            integrity=rec.get("integrity"),
            surface_verb=rosetta.get("surface_verb"),
            verb_class=rosetta.get("class"),
            relation_enum=rosetta.get("relation_enum"),
            atomized=rec.get("atomized") or [],
            closed_through=(rec.get("l1_to_l5") or {}).get("closed_through"),
            gold=True,
        )
        n += 1
        rel = _REL_ALIASES.get((rosetta.get("relation_enum") or "").strip().upper())
        if rel == "MALFORMED_MECHANISM":
            g.add_edge(cid, "MALFORMED_MECHANISM", cid, reason=rec.get("gate_note") or "")
    return n


# ------------------------------------------------------------- food claims

def load_food_claims(g: GraphStore) -> int:
    """
    500 foods with the claims made about them, the bioactives credited, and a
    per-claim evidence grade. This is the model's training and evaluation set.
    """
    f = EXAMPLES / "claims" / "food_health_claims_500.json"
    if not f.is_file():
        return 0
    doc = json.loads(f.read_text(encoding="utf-8"))
    n = 0

    for outcome_id, label in _outcome_taxonomy(doc).items():
        g.add_node(f"outcome:{outcome_id}", "Outcome", label, code=outcome_id)

    for food in doc.get("foods") or []:
        fid = f"food:{food['id']}"
        g.add_node(
            fid,
            "Food",
            food.get("name") or food["id"],
            group=food.get("group"),
            nova_class=food.get("nova_class"),
            verdict=food.get("verdict"),
            serving=food.get("typical_serving"),
        )

        for benefit in food.get("benefits") or []:
            claim_id = f"claim:{food['id']}:{benefit.get('claim_id', 'NA')}"
            g.add_node(
                claim_id,
                "Claim",
                benefit.get("statement") or benefit.get("claim") or claim_id,
                food=food["id"],
                outcome=benefit.get("claim_id"),
                evidence_grade=benefit.get("evidence_grade"),
                drivers=benefit.get("primary_drivers") or [],
                gold=False,
            )
            n += 1
            g.add_edge(fid, "CLAIMS", claim_id)

            if oc := benefit.get("claim_id"):
                if g.get_node(f"outcome:{oc}"):
                    g.add_edge(claim_id, "TARGETS", f"outcome:{oc}")

            for driver in benefit.get("primary_drivers") or []:
                did = f"compound:{_slug(driver)}"
                g.add_node(did, "Compound", driver)
                g.add_edge(claim_id, "DRIVEN_BY", did)
                g.add_edge(fid, "CONTAINS", did)
    return n


def _outcome_taxonomy(doc: dict[str, Any]) -> dict[str, str]:
    tax = doc.get("claim_taxonomy") or {}
    if isinstance(tax, dict):
        out = {}
        for k, v in tax.items():
            out[k] = v if isinstance(v, str) else (v.get("label") or v.get("claim") or k)
        return out
    if isinstance(tax, list):
        return {t.get("id", str(i)): t.get("label") or t.get("claim") or str(i)
                for i, t in enumerate(tax)}
    return {}


def _slug(text: str) -> str:
    import re
    return re.sub(r"[^a-z0-9]+", "_", (text or "").lower()).strip("_")


__all__ = ["build", "load_laws", "load_contributions", "load_claim_fixtures",
           "load_food_claims"]
