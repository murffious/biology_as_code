"""
Map topic nodes → simulation slots.

Representation model (like typed ECS components):

  cargo          → relative amounts on MetabolicState / Walk context
  modifier       → boolean or float context flags (phytate, tannin, …)
  signal         → RegulatorySignals 0–2 scale
  mechanism      → phase enzyme/transporter hooks
  process        → named pathway process ids
  compartment    → geography / phase seat
  endpoint       → L5 outcome (open tier; not auto-diagnosed)
  measurement    → lexicon only (not sim physics)
  host_context   → Part 4 config
  payload_food   → L1 food identity hints
  lexicon        → vocabulary only
"""

from __future__ import annotations

from typing import Any

from .registry import TopicNode, TopicRegistry, load_topics

SIM_ROLE_TYPES: dict[str, str] = {
    "cargo": "Quantity on the payload / absorbed pool",
    "modifier": "Same-meal or matrix factor changing a bound",
    "signal": "Hormone / peptide / neural tone on state",
    "mechanism": "Enzyme or transporter active in a phase",
    "process": "Named metabolic or GI process",
    "compartment": "Organ / tissue geography",
    "endpoint": "Disease or wellness pole (claim-tiered)",
    "measurement": "Assessment method — not physics",
    "host_context": "Life stage / population config",
    "payload_food": "Food item / form identity",
    "lexicon": "Named vocabulary without sim slot yet",
}

# High-value defaults wired into MetabolicState-compatible context keys
CORE_CONTEXT_DEFAULTS: dict[str, Any] = {
    # modifiers (bool)
    "ascorbate_same_meal": False,
    "tannin": False,
    "phytate": False,
    "meat_fish_factor": False,
    "hepcidin_block": False,
    # signals (0–2)
    "signal.insulin": 1.0,
    "signal.glucagon": 0.3,
    "signal.cortisol": 0.4,
    "signal.cck": 0.0,
    "signal.ghrelin": 0.3,
    "signal.leptin": 1.0,
    "signal.glp1": 0.0,
    # cargo relatives
    "cargo.iron": 1.0,
    "cargo.zinc": 1.0,
    "cargo.calcium": 1.0,
    "cargo.glucose": 0.0,
    "cargo.fiber": 0.0,
}


def topics_for_system(system: str, reg: TopicRegistry | None = None) -> list[TopicNode]:
    reg = reg or load_topics()
    return reg.by_system(system)


def topics_linked_to_law(law_id: str, reg: TopicRegistry | None = None) -> list[TopicNode]:
    reg = reg or load_topics()
    return reg.linked_to_law(law_id)


def build_sim_context_template(
    reg: TopicRegistry | None = None,
    *,
    include_all_sim_ready: bool = False,
) -> dict[str, Any]:
    """
    Build a default context dict for MetabolicState / WalkState.

    By default only CORE keys; optionally expand with all sim_ready field_hints
    (large — for ontology-complete experiments).
    """
    ctx = dict(CORE_CONTEXT_DEFAULTS)
    if include_all_sim_ready:
        reg = reg or load_topics()
        for t in reg.sim_ready():
            key = t.field_hint
            if key in ctx:
                continue
            if t.sim_role in ("modifier",):
                ctx[key] = False
            elif t.sim_role == "signal" or t.sim_role == "cargo":
                ctx[key] = 0.0
            else:
                ctx[key] = None
    return ctx


def topic_to_sim_spec(node: TopicNode) -> dict[str, Any]:
    """Single topic → simulation specification card."""
    return {
        "id": node.id,
        "label": node.label,
        "role": node.sim_role,
        "role_meaning": SIM_ROLE_TYPES.get(node.sim_role, ""),
        "systems": list(node.systems),
        "chain_layer": node.chain_layer,
        "field": node.field_hint,
        "repr": node.sim_repr,
        "laws": list(node.law_links),
        "status": node.status,
        "executable_hint": bool(node.law_links)
        and node.sim_role in ("cargo", "modifier", "signal", "mechanism", "process"),
    }
