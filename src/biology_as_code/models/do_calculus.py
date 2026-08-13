"""
do_calculus.py
=================================================================
Lightweight do-calculus support for the causal graph.

1. Explicit confounder / back-door nodes
2. Identifiability checker for queries of the form
   P(outcome | do(nutrient))

This is a practical, graph-based approximation of Pearl's
do-calculus rules, tailored to the layered nutrition DAG:
  NUTRIENT → MECHANISM → EFFECT → OUTCOME
with optional confounding edges.
=================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from biology_as_code.models.causal_inference import TIER_WEIGHT
from biology_as_code.models.causal_join_graph import CausalJoinGraph, get_causal_join_graph

# ---------------------------------------------------------------------------
# Confounder / back-door structures
# ---------------------------------------------------------------------------

class ConfounderType(Enum):
    LATENT = "latent"              # unobserved common cause
    OBSERVED = "observed"          # measured covariate
    GENETIC = "genetic"
    LIFESTYLE = "lifestyle"
    PHYSIOLOGICAL = "physiological"
    ABSORPTIVE = "absorptive"      # absorption capacity, IF status, etc.


@dataclass
class Confounder:
    """
    A common cause that opens a back-door path between a nutrient
    (or mechanism) and an outcome.
    """
    id: str
    label: str
    confounder_type: ConfounderType
    # Nodes this confounder influences (can include nutrients, mechanisms, effects, outcomes)
    affects: list[str] = field(default_factory=list)
    # If observed, it can be adjusted for (back-door admissible)
    observable: bool = False
    notes: str = ""


@dataclass
class BackDoorPath:
    """A path from treatment (nutrient) to outcome that begins with an arrow into the treatment."""
    treatment: str
    outcome: str
    path_nodes: list[str]          # including treatment and outcome
    confounders_on_path: list[str]
    blocked_by_adjustment: bool    # True if a known observable confounder set blocks it


# ---------------------------------------------------------------------------
# Identifiability result
# ---------------------------------------------------------------------------

class IdentifiabilityStatus(Enum):
    IDENTIFIABLE = "identifiable"                 # effect identifiable from graph alone
    IDENTIFIABLE_WITH_ADJUSTMENT = "identifiable_with_adjustment"
    NOT_IDENTIFIABLE = "not_identifiable"         # open back-door, no adjustment set
    NO_CAUSAL_PATH = "no_causal_path"
    QUALITATIVE_ONLY = "qualitative_only"         # path exists but only weak tiers


@dataclass
class IdentifiabilityResult:
    treatment: str                 # nutrient id
    outcome: str                   # outcome id
    status: IdentifiabilityStatus
    causal_paths_exist: bool
    back_door_paths: list[BackDoorPath]
    adjustment_set: list[str]      # observable confounders that block back-doors
    strongest_tier: str
    tier_weight: float
    explanation: str
    do_expression: str             # human-readable


# ---------------------------------------------------------------------------
# Registry of confounders relevant to nutrition causal claims
# ---------------------------------------------------------------------------

class ConfounderRegistry:
    def __init__(self):
        self.confounders: dict[str, Confounder] = {}
        self._build()

    def register(self, c: Confounder):
        self.confounders[c.id] = c

    def get(self, cid: str) -> Confounder | None:
        return self.confounders.get(cid)

    def affecting(self, node_id: str) -> list[Confounder]:
        return [c for c in self.confounders.values() if node_id in c.affects]

    def list_ids(self) -> list[str]:
        return sorted(self.confounders.keys())

    def _build(self):
        # Latent / physiological confounders that commonly open back-doors
        self.register(Confounder(
            id="conf.inflammation",
            label="Systemic inflammation",
            confounder_type=ConfounderType.PHYSIOLOGICAL,
            affects=[
                "chebi:iron", "chebi:vitamin_d", "out.iron_deficiency_anemia",
                "phys.barrier_integrity", "out.t2d", "phys.glucose_homeostasis",
            ],
            observable=False,
            notes="Inflammation alters nutrient status markers and disease risk independently.",
        ))
        self.register(Confounder(
            id="conf.absorption_capacity",
            label="Intestinal absorption capacity",
            confounder_type=ConfounderType.ABSORPTIVE,
            affects=[
                "chebi:cobalamin", "chebi:iron", "chebi:calcium", "chebi:folate",
                "mech.b12_if_complex", "mech.dmt1_iron", "mech.trpv6_calcium",
                "out.b12_deficiency", "out.iron_deficiency_anemia",
            ],
            observable=False,
            notes="IF status, mucosal integrity, PPI use, surgery, etc.",
        ))
        self.register(Confounder(
            id="conf.sun_exposure",
            label="UV / sun exposure",
            confounder_type=ConfounderType.LIFESTYLE,
            affects=["chebi:vitamin_d", "chebi:calcitriol", "out.vitamin_d_deficiency",
                     "out.rickets", "out.osteomalacia", "phys.bone_mineralization"],
            observable=True,
            notes="Major determinant of vitamin D status independent of dietary intake.",
        ))
        self.register(Confounder(
            id="conf.dietary_pattern",
            label="Overall dietary pattern / energy intake",
            confounder_type=ConfounderType.LIFESTYLE,
            affects=[
                "chebi:leucine", "chebi:glucose", "out.body_composition",
                "out.energy", "phys.mps", "phys.glucose_homeostasis",
            ],
            observable=True,
            notes="Nutrients travel together in foods; hard to isolate single-nutrient effects.",
        ))
        self.register(Confounder(
            id="conf.genetics_mthfr",
            label="MTHFR / one-carbon genetic variation",
            confounder_type=ConfounderType.GENETIC,
            affects=["chebi:folate", "mech.folate_1c", "out.neural_tube_defect",
                     "out.folate_deficiency_anemia"],
            observable=True,
            notes="Genetic variation modifies folate requirements and risk.",
        ))
        self.register(Confounder(
            id="conf.age_sex",
            label="Age and sex",
            confounder_type=ConfounderType.OBSERVED,
            affects=[
                "out.osteomalacia", "out.rickets", "out.iron_deficiency_anemia",
                "phys.bone_mineralization", "phys.erythropoiesis",
            ],
            observable=True,
            notes="Classic demographic confounders for many nutrient–outcome pairs.",
        ))
        self.register(Confounder(
            id="conf.ppi_use",
            label="Proton-pump inhibitor / hypochlorhydria",
            confounder_type=ConfounderType.PHYSIOLOGICAL,
            affects=[
                "chebi:cobalamin", "chebi:iron", "chebi:calcium",
                "mech.b12_if_complex", "out.b12_deficiency",
            ],
            observable=True,
            notes="Raises gastric pH → impairs mineral and B12 liberation.",
        ))
        self.register(Confounder(
            id="conf.kidney_function",
            label="Renal function (1α-hydroxylase capacity)",
            confounder_type=ConfounderType.PHYSIOLOGICAL,
            affects=["chebi:calcitriol", "mech.vdr_ligand_binding",
                     "phys.calcium_homeostasis", "out.osteomalacia"],
            observable=True,
            notes="Activation of vitamin D depends on adequate kidney function.",
        ))


def get_confounder_registry() -> ConfounderRegistry:
    return ConfounderRegistry()


# ---------------------------------------------------------------------------
# Identifiability checker
# ---------------------------------------------------------------------------

class IdentifiabilityChecker:
    """
    Lightweight identifiability checker for queries:
        P(outcome | do(nutrient))

    Uses the layered causal graph + explicit confounders.

    Approximation of do-calculus Rule 2 / back-door criterion:
      - Causal paths (nutrient → … → outcome) must exist
      - Back-door paths (via confounders) must be blocked by an
        observable adjustment set, or declared absent
    """

    def __init__(
        self,
        graph: CausalJoinGraph | None = None,
        confounders: ConfounderRegistry | None = None,
    ):
        self.graph = graph or get_causal_join_graph()
        self.confounders = confounders or get_confounder_registry()

    def check(self, treatment: str, outcome: str) -> IdentifiabilityResult:
        """
        Check whether P(outcome | do(treatment)) is identifiable
        under the current graph + confounder set.
        """
        # 1. Do causal (front-door direction) paths exist?
        paths = self.graph.downstream_of_nutrient(treatment)
        causal = [p for p in paths if p.outcome_id == outcome]
        causal_exist = len(causal) > 0

        strongest_tier = "open"
        best_w = 0.0
        for p in causal:
            w = TIER_WEIGHT.get(p.tier_hint, 0.1)
            if w > best_w:
                best_w = w
                strongest_tier = p.tier_hint

        if not causal_exist:
            return IdentifiabilityResult(
                treatment=treatment,
                outcome=outcome,
                status=IdentifiabilityStatus.NO_CAUSAL_PATH,
                causal_paths_exist=False,
                back_door_paths=[],
                adjustment_set=[],
                strongest_tier="open",
                tier_weight=0.0,
                explanation=f"No directed causal path from {treatment} to {outcome} in the graph.",
                do_expression=f"P({outcome} | do({treatment}))  — undefined (no path)",
            )

        # 2. Collect back-door structure via shared confounders
        back_doors = self._find_back_doors(treatment, outcome)
        observable_blockers = sorted({
            c for bd in back_doors for c in bd.confounders_on_path
            if self.confounders.get(c) and self.confounders.get(c).observable
        })
        unblocked = [bd for bd in back_doors if not bd.blocked_by_adjustment]

        # 3. Decide status
        if not back_doors:
            # No known back-door — identifiable if tier is strong enough
            if best_w >= 0.75:
                status = IdentifiabilityStatus.IDENTIFIABLE
                expl = (
                    f"Causal path(s) exist (strongest tier={strongest_tier}). "
                    f"No explicit back-door confounders registered. "
                    f"Treating P({outcome} | do({treatment})) as identifiable at the "
                    f"qualitative/tier level."
                )
            else:
                status = IdentifiabilityStatus.QUALITATIVE_ONLY
                expl = (
                    f"Causal path(s) exist but only at tier={strongest_tier}. "
                    f"Effect is directionally plausible but not law-grade identifiable."
                )
        elif not unblocked:
            status = IdentifiabilityStatus.IDENTIFIABLE_WITH_ADJUSTMENT
            expl = (
                f"Back-door paths exist but are blocked by observable adjustment set "
                f"{observable_blockers}. Effect identifiable after adjustment "
                f"(back-door criterion)."
            )
        else:
            status = IdentifiabilityStatus.NOT_IDENTIFIABLE
            latent = sorted({
                c for bd in unblocked for c in bd.confounders_on_path
                if self.confounders.get(c) and not self.confounders.get(c).observable
            })
            expl = (
                f"Open back-door path(s) remain via latent confounders {latent}. "
                f"P({outcome} | do({treatment})) is not identifiable from observational "
                f"data alone under the current graph."
            )

        return IdentifiabilityResult(
            treatment=treatment,
            outcome=outcome,
            status=status,
            causal_paths_exist=True,
            back_door_paths=back_doors,
            adjustment_set=observable_blockers,
            strongest_tier=strongest_tier,
            tier_weight=best_w,
            explanation=expl,
            do_expression=f"P({outcome} | do({treatment}))",
        )

    def _find_back_doors(self, treatment: str, outcome: str) -> list[BackDoorPath]:
        """
        Approximate back-door discovery:
        A confounder that affects both the treatment (or its mechanisms)
        and the outcome (or its upstream effects) opens a back-door.
        """
        # Nodes on the causal side of treatment
        treatment_side = {treatment}
        for m in self.graph.mechanisms_for_nutrient(treatment):
            treatment_side.add(m.node_id)
            for e in self.graph.effects_for_mechanism(m.node_id):
                treatment_side.add(e.node_id)

        # Nodes on the outcome side
        outcome_side = {outcome}
        o = self.graph.outcomes.get(outcome)
        if o:
            for eid in o.upstream_effects:
                outcome_side.add(eid)
                e = self.graph.effects.get(eid)
                if e:
                    for mid in e.upstream_mechanisms:
                        outcome_side.add(mid)

        back_doors: list[BackDoorPath] = []
        for conf in self.confounders.confounders.values():
            affects_treatment = bool(set(conf.affects) & treatment_side)
            affects_outcome = bool(set(conf.affects) & outcome_side)
            if affects_treatment and affects_outcome:
                blocked = conf.observable
                back_doors.append(BackDoorPath(
                    treatment=treatment,
                    outcome=outcome,
                    path_nodes=[treatment, conf.id, outcome],
                    confounders_on_path=[conf.id],
                    blocked_by_adjustment=blocked,
                ))
        return back_doors

    def report(self, treatment: str, outcome: str) -> dict[str, Any]:
        """JSON-serialisable identifiability report."""
        r = self.check(treatment, outcome)
        return {
            "do_expression": r.do_expression,
            "status": r.status.value,
            "causal_paths_exist": r.causal_paths_exist,
            "strongest_tier": r.strongest_tier,
            "tier_weight": r.tier_weight,
            "adjustment_set": r.adjustment_set,
            "back_door_count": len(r.back_door_paths),
            "back_doors": [
                {
                    "path": bd.path_nodes,
                    "confounders": bd.confounders_on_path,
                    "blocked": bd.blocked_by_adjustment,
                }
                for bd in r.back_door_paths
            ],
            "explanation": r.explanation,
        }


def get_identifiability_checker() -> IdentifiabilityChecker:
    return IdentifiabilityChecker()


# ---------------------------------------------------------------------------
# Demo
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    checker = get_identifiability_checker()
    conf = get_confounder_registry()

    print("=== Confounders registered ===")
    for cid in conf.list_ids():
        c = conf.get(cid)
        print(f"  {cid:30s} observable={c.observable}  type={c.confounder_type.value}")

    print("\n=== Identifiability: do(ascorbate) → scurvy ===")
    print(json.dumps(checker.report("chebi:ascorbate", "out.scurvy"), indent=2))

    print("\n=== Identifiability: do(vitamin_d) → osteomalacia ===")
    print(json.dumps(checker.report("chebi:vitamin_d", "out.osteomalacia"), indent=2))

    print("\n=== Identifiability: do(cobalamin) → b12_deficiency ===")
    print(json.dumps(checker.report("chebi:cobalamin", "out.b12_deficiency"), indent=2))

    print("\n=== Identifiability: do(leucine) → body_composition ===")
    print(json.dumps(checker.report("chebi:leucine", "out.body_composition"), indent=2))
