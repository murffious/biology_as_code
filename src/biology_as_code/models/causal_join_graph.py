"""
causal_join_graph.py
=================================================================
Causal Join Graph
Walks the full chain:

  FOOD / NUTRIENT → Layer 3 Mechanism → Layer 4 Effect → Layer 5 Outcome

Enables queries such as:
  “What outcomes are downstream of ascorbate?”
  “What mechanisms lead to scurvy?”
  “Show the dual wellness pole of a disease outcome.”
=================================================================
"""

from dataclasses import dataclass
from typing import Any

from biology_as_code.models.biochemical_mechanisms import (
    BiochemicalMechanism,
    get_biochemical_mechanism_registry,
)
from biology_as_code.models.nutrient_compound import get_nutrient_compound_registry
from biology_as_code.simulation.health_outcomes import HealthOutcome, get_health_outcome_registry
from biology_as_code.simulation.physiological_effects import (
    PhysiologicalEffect,
    get_physiological_effect_registry,
)


@dataclass
class CausalPath:
    """One complete path from nutrient to outcome."""
    nutrient_id: str
    nutrient_label: str
    mechanism_id: str
    mechanism_label: str
    effect_id: str
    effect_label: str
    outcome_id: str
    outcome_label: str
    outcome_pole: str
    tier_hint: str


class CausalJoinGraph:
    """
    In-memory join graph over Layers Nutrient → 3 → 4 → 5.
    """

    def __init__(self):
        self.nutrients = get_nutrient_compound_registry()
        self.mechanisms = get_biochemical_mechanism_registry()
        self.effects = get_physiological_effect_registry()
        self.outcomes = get_health_outcome_registry()

    # ------------------------------------------------------------------
    # Core walks
    # ------------------------------------------------------------------
    def mechanisms_for_nutrient(self, nutrient_id: str) -> list[BiochemicalMechanism]:
        n = self.nutrients.get(nutrient_id)
        if not n:
            # also try reverse lookup via participant lists
            return self.mechanisms.by_participant(nutrient_id)
        result = []
        for mid in n.participates_in:
            m = self.mechanisms.get(mid)
            if m:
                result.append(m)
        return result

    def effects_for_mechanism(self, mech_id: str) -> list[PhysiologicalEffect]:
        return self.effects.by_mechanism(mech_id)

    def outcomes_for_effect(self, effect_id: str) -> list[HealthOutcome]:
        return self.outcomes.by_effect(effect_id)

    def downstream_of_nutrient(self, nutrient_id: str) -> list[CausalPath]:
        """Full walk: nutrient → mechanisms → effects → outcomes."""
        paths: list[CausalPath] = []
        n = self.nutrients.get(nutrient_id)
        nutrient_label = n.label if n else nutrient_id

        for mech in self.mechanisms_for_nutrient(nutrient_id):
            for effect in self.effects_for_mechanism(mech.node_id):
                for outcome in self.outcomes_for_effect(effect.node_id):
                    paths.append(CausalPath(
                        nutrient_id=nutrient_id,
                        nutrient_label=nutrient_label,
                        mechanism_id=mech.node_id,
                        mechanism_label=mech.label,
                        effect_id=effect.node_id,
                        effect_label=effect.label,
                        outcome_id=outcome.node_id,
                        outcome_label=outcome.label,
                        outcome_pole=outcome.pole,
                        tier_hint=outcome.tier_hint,
                    ))
        return paths

    def upstream_of_outcome(self, outcome_id: str) -> dict[str, Any]:
        """Reverse walk: outcome → effects → mechanisms → nutrients."""
        o = self.outcomes.get(outcome_id)
        if not o:
            return {"error": f"Unknown outcome {outcome_id}"}

        result = {
            "outcome": {"id": o.node_id, "label": o.label, "pole": o.pole, "tier": o.tier_hint},
            "effects": [],
            "mechanisms": [],
            "nutrients": [],
        }
        seen_mech: set[str] = set()
        seen_nut: set[str] = set()

        for eid in o.upstream_effects:
            e = self.effects.get(eid)
            if not e:
                continue
            result["effects"].append({"id": e.node_id, "label": e.label})
            for mid in e.upstream_mechanisms:
                if mid in seen_mech:
                    continue
                seen_mech.add(mid)
                m = self.mechanisms.get(mid)
                if not m:
                    continue
                result["mechanisms"].append({"id": m.node_id, "label": m.label})
                for pid in m.participants:
                    if pid in seen_nut:
                        continue
                    seen_nut.add(pid)
                    n = self.nutrients.get(pid)
                    result["nutrients"].append({
                        "id": pid,
                        "label": n.label if n else pid
                    })
        return result

    def dual_pole(self, outcome_id: str) -> list[HealthOutcome]:
        """Return wellness duals of a disease (or vice-versa)."""
        o = self.outcomes.get(outcome_id)
        if not o:
            return []
        if o.pole == "disease":
            return self.outcomes.duals_of(outcome_id)
        # if wellness, find the disease nodes it is dual_of
        return [self.outcomes.get(d) for d in o.dual_of if self.outcomes.get(d)]

    # ------------------------------------------------------------------
    # Convenience query API
    # ------------------------------------------------------------------
    def query_downstream(self, nutrient_id: str) -> dict[str, Any]:
        """Human-friendly downstream report for a nutrient."""
        paths = self.downstream_of_nutrient(nutrient_id)
        disease = [p for p in paths if p.outcome_pole == "disease"]
        wellness = [p for p in paths if p.outcome_pole == "wellness"]
        return {
            "nutrient": nutrient_id,
            "path_count": len(paths),
            "disease_outcomes": [
                {"id": p.outcome_id, "label": p.outcome_label, "tier": p.tier_hint,
                 "via_mechanism": p.mechanism_id, "via_effect": p.effect_id}
                for p in disease
            ],
            "wellness_outcomes": [
                {"id": p.outcome_id, "label": p.outcome_label, "tier": p.tier_hint,
                 "via_mechanism": p.mechanism_id, "via_effect": p.effect_id}
                for p in wellness
            ],
        }

    def query_upstream(self, outcome_id: str) -> dict[str, Any]:
        return self.upstream_of_outcome(outcome_id)

    def summary(self) -> dict[str, int]:
        return {
            "nutrients": self.nutrients.summary()["total"],
            "mechanisms_L3": self.mechanisms.summary()["total"],
            "effects_L4": self.effects.summary()["total"],
            "outcomes_L5": self.outcomes.summary()["total"],
        }


def get_causal_join_graph() -> CausalJoinGraph:
    return CausalJoinGraph()


if __name__ == "__main__":
    g = get_causal_join_graph()
    print("=== Causal Join Graph ===")
    print(g.summary())
    print("\n--- Downstream of ascorbate ---")
    import json
    print(json.dumps(g.query_downstream("chebi:ascorbate"), indent=2))
    print("\n--- Upstream of scurvy ---")
    print(json.dumps(g.query_upstream("out.scurvy"), indent=2))
    print("\n--- Dual of scurvy ---")
    for d in g.dual_pole("out.scurvy"):
        print(f"  {d.node_id}: {d.label}")
