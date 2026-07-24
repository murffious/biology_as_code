"""
causal_inference.py
=================================================================
Causal Inference Engine over the KIBO multi-layer graph

  NUTRIENT/COMPOUND → L3 Mechanism → L4 Effect → L5 Outcome

Algorithms:
  - downstream / upstream
  - intervene (do-operator style)
  - counterfactual
  - root_causes
  - explain
  - tier-aware path scoring
=================================================================
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from biology_as_code.models.causal_join_graph import CausalJoinGraph, get_causal_join_graph
from biology_as_code.models.causal_join_graph import CausalPath as GraphPath

TIER_WEIGHT = {
    "law_possible": 1.0,
    "law_truncated": 0.75,
    "law_truncated_or_evidence": 0.65,
    "evidence": 0.45,
    "open": 0.15,
}


class InterventionLevel(Enum):
    DEPLETED = "depleted"
    LOW = "low"
    ADEQUATE = "adequate"
    HIGH = "high"


@dataclass
class InterventionResult:
    nutrient_id: str
    level: InterventionLevel
    affected_disease_outcomes: list[dict[str, Any]] = field(default_factory=list)
    affected_wellness_outcomes: list[dict[str, Any]] = field(default_factory=list)
    summary: str = ""


@dataclass
class CounterfactualResult:
    outcome_id: str
    outcome_label: str
    intervened_nutrient: str
    intervention_level: InterventionLevel
    would_still_occur: bool | None
    confidence: float
    reasoning: str


@dataclass
class RootCause:
    nutrient_id: str
    nutrient_label: str
    score: float
    tier: str
    mechanisms: list[str]
    effects: list[str]
    reasoning: str


class CausalInferenceEngine:
    def __init__(self, graph: CausalJoinGraph | None = None):
        self.graph = graph or get_causal_join_graph()
        self.nutrients = self.graph.nutrients
        self.mechanisms = self.graph.mechanisms
        self.effects = self.graph.effects
        self.outcomes = self.graph.outcomes

    # ------------------------------------------------------------------
    def downstream(self, nutrient_id: str) -> dict[str, Any]:
        paths = self.graph.downstream_of_nutrient(nutrient_id)
        return {
            "nutrient_id": nutrient_id,
            "path_count": len(paths),
            "scored_outcomes": self._score_paths(paths),
            "raw": self.graph.query_downstream(nutrient_id),
        }

    def upstream(self, outcome_id: str) -> dict[str, Any]:
        return self.graph.upstream_of_outcome(outcome_id)

    # ------------------------------------------------------------------
    def intervene(self, nutrient_id: str, level: InterventionLevel) -> InterventionResult:
        paths = self.graph.downstream_of_nutrient(nutrient_id)
        n = self.nutrients.get(nutrient_id)
        label = n.label if n else nutrient_id

        disease_hits: list[dict[str, Any]] = []
        wellness_hits: list[dict[str, Any]] = []

        for p in paths:
            weight = TIER_WEIGHT.get(p.tier_hint, 0.3)
            entry = {
                "outcome_id": p.outcome_id,
                "label": p.outcome_label,
                "tier": p.tier_hint,
                "weight": weight,
                "via_mechanism": p.mechanism_id,
                "via_effect": p.effect_id,
            }
            if p.outcome_pole == "disease":
                if level == InterventionLevel.DEPLETED:
                    entry["predicted_direction"] = "increased_risk"
                    entry["impact"] = weight
                elif level in (InterventionLevel.ADEQUATE, InterventionLevel.HIGH):
                    entry["predicted_direction"] = "decreased_risk"
                    entry["impact"] = weight
                else:
                    entry["predicted_direction"] = "mild_modulation"
                    entry["impact"] = weight * 0.4
                disease_hits.append(entry)
            else:
                if level in (InterventionLevel.ADEQUATE, InterventionLevel.HIGH):
                    entry["predicted_direction"] = "supported"
                    entry["impact"] = weight
                elif level == InterventionLevel.DEPLETED:
                    entry["predicted_direction"] = "undermined"
                    entry["impact"] = weight
                else:
                    entry["predicted_direction"] = "mild_modulation"
                    entry["impact"] = weight * 0.4
                wellness_hits.append(entry)

        disease_hits.sort(key=lambda x: -x["impact"])
        wellness_hits.sort(key=lambda x: -x["impact"])

        return InterventionResult(
            nutrient_id=nutrient_id,
            level=level,
            affected_disease_outcomes=disease_hits,
            affected_wellness_outcomes=wellness_hits,
            summary=(
                f"Intervention do({label} = {level.value}): "
                f"{len(disease_hits)} disease and {len(wellness_hits)} wellness outcomes downstream."
            ),
        )

    # ------------------------------------------------------------------
    def counterfactual(
        self,
        outcome_id: str,
        nutrient_id: str,
        level: InterventionLevel = InterventionLevel.ADEQUATE,
    ) -> CounterfactualResult:
        o = self.outcomes.get(outcome_id)
        if not o:
            return CounterfactualResult(
                outcome_id=outcome_id, outcome_label="unknown",
                intervened_nutrient=nutrient_id, intervention_level=level,
                would_still_occur=None, confidence=0.0,
                reasoning="Unknown outcome ID",
            )

        up = self.graph.upstream_of_outcome(outcome_id)
        nutrient_ids = {n["id"] for n in up.get("nutrients", [])}

        if nutrient_id not in nutrient_ids:
            return CounterfactualResult(
                outcome_id=outcome_id, outcome_label=o.label,
                intervened_nutrient=nutrient_id, intervention_level=level,
                would_still_occur=True, confidence=0.7,
                reasoning=(
                    f"{nutrient_id} has no recorded causal path to {o.label}; "
                    "intervention would not block the outcome under current graph."
                ),
            )

        paths = self.graph.downstream_of_nutrient(nutrient_id)
        relevant = [p for p in paths if p.outcome_id == outcome_id]
        best_weight = 0.0
        best_tier = "open"
        for p in relevant:
            w = TIER_WEIGHT.get(p.tier_hint, 0.1)
            if w > best_weight:
                best_weight = w
                best_tier = p.tier_hint

        if o.pole == "disease":
            if level in (InterventionLevel.ADEQUATE, InterventionLevel.HIGH):
                if best_weight >= 0.75:
                    return CounterfactualResult(
                        outcome_id=outcome_id, outcome_label=o.label,
                        intervened_nutrient=nutrient_id, intervention_level=level,
                        would_still_occur=False, confidence=best_weight,
                        reasoning=(
                            f"Setting {nutrient_id} to {level.value} blocks a {best_tier} "
                            f"causal path to {o.label}. Deficiency disease not expected."
                        ),
                    )
                return CounterfactualResult(
                    outcome_id=outcome_id, outcome_label=o.label,
                    intervened_nutrient=nutrient_id, intervention_level=level,
                    would_still_occur=None, confidence=best_weight,
                    reasoning=(
                        f"Only {best_tier}-tier paths link {nutrient_id} to {o.label}. "
                        "Intervention may help but is not a hard block."
                    ),
                )
            return CounterfactualResult(
                outcome_id=outcome_id, outcome_label=o.label,
                intervened_nutrient=nutrient_id, intervention_level=level,
                would_still_occur=True, confidence=best_weight,
                reasoning=(
                    f"Keeping {nutrient_id} depleted preserves causal conditions "
                    f"for {o.label} (tier={best_tier})."
                ),
            )

        # wellness
        if level in (InterventionLevel.ADEQUATE, InterventionLevel.HIGH):
            return CounterfactualResult(
                outcome_id=outcome_id, outcome_label=o.label,
                intervened_nutrient=nutrient_id, intervention_level=level,
                would_still_occur=True, confidence=best_weight,
                reasoning=f"Adequate/high {nutrient_id} supports wellness outcome {o.label}.",
            )
        return CounterfactualResult(
            outcome_id=outcome_id, outcome_label=o.label,
            intervened_nutrient=nutrient_id, intervention_level=level,
            would_still_occur=False, confidence=best_weight,
            reasoning=f"Depleting {nutrient_id} undermines wellness outcome {o.label}.",
        )

    # ------------------------------------------------------------------
    def root_causes(self, outcome_id: str, top_k: int = 5) -> list[RootCause]:
        up = self.graph.upstream_of_outcome(outcome_id)
        o = self.outcomes.get(outcome_id)
        if not o:
            return []

        nutrient_mechs: dict[str, set[str]] = defaultdict(set)
        nutrient_effects: dict[str, set[str]] = defaultdict(set)

        for e in up.get("effects", []):
            eid = e["id"]
            effect_obj = self.effects.get(eid)
            if not effect_obj:
                continue
            for mid in effect_obj.upstream_mechanisms:
                m = self.mechanisms.get(mid)
                if not m:
                    continue
                for pid in m.participants:
                    nutrient_mechs[pid].add(mid)
                    nutrient_effects[pid].add(eid)

        ranked: list[RootCause] = []
        for nid, mechs in nutrient_mechs.items():
            n = self.nutrients.get(nid)
            label = n.label if n else nid
            tier = o.tier_hint
            base = TIER_WEIGHT.get(tier, 0.3)
            score = min(1.0, base + 0.05 * max(0, len(mechs) - 1))
            ranked.append(RootCause(
                nutrient_id=nid,
                nutrient_label=label,
                score=round(score, 3),
                tier=tier,
                mechanisms=sorted(mechs),
                effects=sorted(nutrient_effects[nid]),
                reasoning=(
                    f"{label} participates in {len(mechs)} mechanism(s) "
                    f"upstream of {o.label} (tier={tier})."
                ),
            ))
        ranked.sort(key=lambda r: -r.score)
        return ranked[:top_k]

    # ------------------------------------------------------------------
    def explain(self, nutrient_id: str, outcome_id: str) -> dict[str, Any]:
        paths = self.graph.downstream_of_nutrient(nutrient_id)
        relevant = [p for p in paths if p.outcome_id == outcome_id]
        if not relevant:
            return {
                "related": False,
                "nutrient_id": nutrient_id,
                "outcome_id": outcome_id,
                "message": "No causal path found in the current graph.",
            }
        best = max(relevant, key=lambda p: TIER_WEIGHT.get(p.tier_hint, 0))
        duals = self.graph.dual_pole(outcome_id)
        return {
            "related": True,
            "nutrient_id": nutrient_id,
            "outcome_id": outcome_id,
            "path_count": len(relevant),
            "strongest_path": {
                "mechanism": best.mechanism_id,
                "mechanism_label": best.mechanism_label,
                "effect": best.effect_id,
                "effect_label": best.effect_label,
                "tier": best.tier_hint,
                "score": TIER_WEIGHT.get(best.tier_hint, 0.3),
            },
            "dual_outcomes": [{"id": d.node_id, "label": d.label} for d in duals if d],
            "narrative": (
                f"{best.nutrient_label} acts via [{best.mechanism_label}] "
                f"producing [{best.effect_label}], which is linked to "
                f"[{best.outcome_label}] (tier={best.tier_hint})."
            ),
        }

    # ------------------------------------------------------------------
    def _score_paths(self, paths: list[GraphPath]) -> list[dict[str, Any]]:
        by_outcome: dict[str, list[GraphPath]] = defaultdict(list)
        for p in paths:
            by_outcome[p.outcome_id].append(p)
        scored = []
        for oid, plist in by_outcome.items():
            best = max(plist, key=lambda p: TIER_WEIGHT.get(p.tier_hint, 0))
            scored.append({
                "outcome_id": oid,
                "label": best.outcome_label,
                "pole": best.outcome_pole,
                "tier": best.tier_hint,
                "score": TIER_WEIGHT.get(best.tier_hint, 0.3),
                "path_count": len(plist),
                "example_mechanism": best.mechanism_id,
                "example_effect": best.effect_id,
            })
        scored.sort(key=lambda x: -x["score"])
        return scored

    def summary(self) -> dict[str, Any]:
        return {
            "graph": self.graph.summary(),
            "algorithms": [
                "downstream", "upstream", "intervene",
                "counterfactual", "root_causes", "explain",
            ],
        }


def get_causal_inference_engine() -> CausalInferenceEngine:
    return CausalInferenceEngine()


if __name__ == "__main__":
    eng = get_causal_inference_engine()
    print("=== Causal Inference Engine ===")
    print(eng.summary())

    print("\n--- Intervene: deplete ascorbate ---")
    r = eng.intervene("chebi:ascorbate", InterventionLevel.DEPLETED)
    print(r.summary)
    for d in r.affected_disease_outcomes[:3]:
        print(f"  DISEASE {d['predicted_direction']}: {d['label']} (impact={d['impact']:.2f})")

    print("\n--- Counterfactual: scurvy if ascorbate adequate? ---")
    cf = eng.counterfactual("out.scurvy", "chebi:ascorbate", InterventionLevel.ADEQUATE)
    print(f"  would_still_occur={cf.would_still_occur}  confidence={cf.confidence:.2f}")
    print(f"  {cf.reasoning}")

    print("\n--- Root causes of scurvy ---")
    for rc in eng.root_causes("out.scurvy"):
        print(f"  {rc.score:.2f}  {rc.nutrient_label}  ({rc.tier})")

    print("\n--- Explain ascorbate → scurvy ---")
    ex = eng.explain("chebi:ascorbate", "out.scurvy")
    print(" ", ex.get("narrative") or ex.get("message"))
