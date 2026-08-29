"""Exposure→system→outcome edges with separate L3 walks.

Stops pooling 'UPF → T2D' as one construct. Each row is one mechanism.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from biology_as_code.systems.states import EvalState


@dataclass(frozen=True)
class Edge:
    edge_id: str
    exposure: str
    system_id: str
    l3_gate: str
    outcome: str
    state: EvalState
    grade: str
    next_study: str
    citations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "edge_id": self.edge_id,
            "exposure": self.exposure,
            "system_id": self.system_id,
            "l3_gate": self.l3_gate,
            "outcome": self.outcome,
            "state": self.state.value,
            "grade": self.grade,
            "next_study": self.next_study,
            "citations": list(self.citations),
        }


def _e(**kwargs) -> Edge:
    return Edge(**kwargs)


DEFAULT_EDGES: tuple[Edge, ...] = (
    _e(
        edge_id="upf.digestive.eating_rate.energy_intake",
        exposure="NOVA-4 UPF pattern",
        system_id="digestive",
        l3_gate="eating_rate",
        outcome="ad libitum energy intake",
        state=EvalState.HOLDS,
        grade="moderate (n=20 inpatient crossover)",
        next_study="Replicate Hall eating-rate measurement in UPDATE-like free living with chew/video rate.",
        citations=("PMID:31105044",),
    ),
    _e(
        edge_id="upf.endocrine.incretin.intake",
        exposure="NOVA-4 UPF pattern",
        system_id="endocrine",
        l3_gate="incretin_distal_contact",
        outcome="blunted GLP-1/PYY → higher intake",
        state=EvalState.OPEN,
        grade="not locked in humans on matched UPF vs unprocessed",
        next_study="Matched UPF vs unprocessed meal-stimulated GLP-1 and PYY with eating-rate covariate.",
        citations=("PMID:31105044",),
    ),
    _e(
        edge_id="upf.endocrine.gi.t2d",
        exposure="NOVA-4 UPF pattern",
        system_id="endocrine",
        l3_gate="insulin_gi_fii",
        outcome="type 2 diabetes",
        state=EvalState.REFUTED,
        grade="construct mismatch",
        next_study="Do not use GI/GL as the UPF pathway. 2024 NOVA×GI analysis found no higher mean GI in UPF.",
        citations=("PMC11600077",),
    ),
    _e(
        edge_id="upf.cardio.energy_surplus.weight",
        exposure="NOVA-4 UPF pattern",
        system_id="cardiovascular",
        l3_gate="energy_surplus_bp",
        outcome="weight / energy surplus",
        state=EvalState.HOLDS,
        grade="moderate (Hall; supported directionally by UPDATE)",
        next_study="Hard BP and ApoB on the same matched design.",
        citations=("PMID:31105044",),
    ),
    _e(
        edge_id="upf.cardio.observational.cvd",
        exposure="NOVA-4 UPF pattern",
        system_id="cardiovascular",
        l3_gate="unspecified",
        outcome="CVD mortality",
        state=EvalState.OPEN,
        grade="very low–moderate observational (Lane umbrella 2024 class)",
        next_study="Do not pool until L3 is named. Split Na / energy surplus / residual confounding.",
        citations=("Lane et al. 2024 umbrella review",),
    ),
    _e(
        edge_id="upf.immune.emulsifier.barrier",
        exposure="dietary emulsifiers (CMC, P80)",
        system_id="immune",
        l3_gate="emulsifier_mucus",
        outcome="barrier / low-grade inflammation",
        state=EvalState.OPEN,
        grade="strong mouse; thin human",
        next_study="Human crossover with declared emulsifier dose, mucus/calprotectin, eating-rate held constant.",
        citations=("Chassaing 2015 Nature",),
    ),
    _e(
        edge_id="upf.nervous.reward.intake",
        exposure="HPF nutrient pairs and/or UPF texture",
        system_id="nervous",
        l3_gate="eating_rate_reward",
        outcome="ad libitum intake",
        state=EvalState.OPEN,
        grade="mechanism plausible; not isolated in Hall",
        next_study="Code Hall menus on Fazzino HPF pairs and test whether pair count predicts residual intake after eating rate.",
        citations=("PMID:31689013", "PMID:31105044"),
    ),
    _e(
        edge_id="upf.nervous.mnp.dementia",
        exposure="dietary UPF",
        system_id="nervous",
        l3_gate="diet_to_brain_mnp",
        outcome="dementia / brain MNPs",
        state=EvalState.REFUSE,
        grade="not a dietary-exposure walk",
        next_study="Do not treat tissue Py-GC-MS MNP reports as a diet trial endpoint.",
        citations=("companion review §4",),
    ),
)


class EdgeLedger:
    def __init__(self, edges: tuple[Edge, ...] = DEFAULT_EDGES) -> None:
        self.edges = edges

    def by_state(self, state: EvalState) -> tuple[Edge, ...]:
        return tuple(e for e in self.edges if e.state is state)

    def by_system(self, system_id: str) -> tuple[Edge, ...]:
        return tuple(e for e in self.edges if e.system_id == system_id)

    def next_studies(self) -> tuple[str, ...]:
        return tuple(e.next_study for e in self.edges if e.state in {EvalState.OPEN, EvalState.UNEVALUABLE})


def default_ledger() -> EdgeLedger:
    return EdgeLedger()


def next_studies() -> tuple[str, ...]:
    return default_ledger().next_studies()
