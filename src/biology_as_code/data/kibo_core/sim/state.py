"""Central state that flows through every digestive/metabolic phase."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MetabolicState:
    """
    Compartmental state object (systems-biology style).

    Inputs = meal payload + host/runtime context.
    Outputs accumulate as phases run.
    micronutrients = soft L2 pool factors (relative 0–1+), not mg clinical doses.
    """

    # —— Meal payload (L1/L2 teaching inputs) ——
    fat_g: float = 0.0
    carb_g: float = 0.0
    protein_g: float = 0.0
    mct_g: float = 0.0
    fiber_g: float = 0.0
    # relative meal units (not mg) for competition / redox demos
    iron_rel: float = 1.0
    zinc_rel: float = 1.0
    calcium_rel: float = 1.0
    ascorbate_same_meal: bool = False
    tannin_same_meal: bool = False
    phytate_matrix: bool = False

    # —— Runtime (Part 4 dual lens — soft) ——
    hours_since_meal: float = 0.0
    hour_of_day: float = 12.0
    chronotype: str = "intermediate"
    jet_lag_hours: float = 0.0
    fed: bool = True

    # —— Phase outputs ——
    absorbed_fat: float = 0.0
    absorbed_carb: float = 0.0
    absorbed_protein: float = 0.0
    iron_bioavailability_factor: float = 1.0
    zinc_bioavailability_factor: float = 1.0
    beta_hb_mmol: float = 0.0
    atp_units: float = 0.0  # FLOW teaching units — not locked ATP law
    scfa_mmol: float = 0.0  # FLOW teaching — LAW-026 magnitude not locked
    bile_recycling_efficiency: float = 0.95  # LAW-039 family, provisional
    micelle_gate_open: bool = False
    kibo_score: float = 50.0

    # —— Trace ——
    current_phase: str = "start"
    kingdom: str = "K0"
    system: str = ""
    messages: list[str] = field(default_factory=list)
    laws_cited: list[str] = field(default_factory=list)
    refuse: list[str] = field(default_factory=list)
    claim_tier: str = "open"
    meta: dict[str, Any] = field(default_factory=dict)

    def cite(self, *law_ids: str) -> None:
        for lid in law_ids:
            if lid and lid not in self.laws_cited:
                self.laws_cited.append(lid)

    def note(self, msg: str) -> None:
        self.messages.append(msg)
