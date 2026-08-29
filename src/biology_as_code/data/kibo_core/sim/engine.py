"""Orchestrator for the compartmental phase pipeline."""

from __future__ import annotations

from .phases import DEFAULT_PHASES, Phase
from .state import MetabolicState


class MetabolicSimulator:
    """
    Runs a sequence of Phase.process(state) → state.

    Matches scientific compartmental modeling: one state object, modular stages.
    """

    def __init__(self, phases: list[Phase] | None = None) -> None:
        self.phases = list(phases) if phases is not None else list(DEFAULT_PHASES)

    def run(self, initial: MetabolicState) -> MetabolicState:
        state = initial
        state.note(f"Simulator start — {len(self.phases)} phases")
        for phase in self.phases:
            state = phase.process(state)
        state.note("Simulator complete")
        state.claim_tier = "open"
        return state

    def summary(self, state: MetabolicState) -> dict:
        return {
            "claim_tier": state.claim_tier,
            "micelle_gate_open": state.micelle_gate_open,
            "absorbed_fat": state.absorbed_fat,
            "absorbed_carb": state.absorbed_carb,
            "absorbed_protein": state.absorbed_protein,
            "iron_bioavailability_factor": state.iron_bioavailability_factor,
            "zinc_bioavailability_factor": state.zinc_bioavailability_factor,
            "scfa_mmol": state.scfa_mmol,
            "beta_hb_mmol": state.beta_hb_mmol,
            "atp_units": state.atp_units,
            "flow_score": state.flow_score,
            "laws_cited": list(state.laws_cited),
            "refuse": list(state.refuse),
            "messages": list(state.messages),
        }
