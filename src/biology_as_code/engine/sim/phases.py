"""
Seven-phase digestive path — maps to book kingdoms (K1–K7).

FLOW coefficients are teaching defaults (open tier). Law ids cited when a
phase touches a known constitution row.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from .rules_redox import apply_l2_redox_competition
from .state import MetabolicState


class Phase(ABC):
    kingdom: str = "K?"
    system: str = ""

    @abstractmethod
    def process(self, state: MetabolicState) -> MetabolicState:
        ...


class MouthPhase(Phase):
    """K1 Ingestion — surface-area / cephalic priming (message only)."""

    kingdom = "K1"
    system = "Assimilation"

    def process(self, state: MetabolicState) -> MetabolicState:
        state.current_phase = "mouth"
        state.kingdom = self.kingdom
        state.system = self.system
        state.note("K1 mouth: surface-area prep + cephalic priming (teaching)")
        return state


class StomachPhase(Phase):
    """K2 Acid reactor — pH gate not fully simulated (STUB-A-03)."""

    kingdom = "K2"
    system = "Assimilation"

    def process(self, state: MetabolicState) -> MetabolicState:
        state.current_phase = "stomach"
        state.kingdom = self.kingdom
        state.system = self.system
        state.note("K2 stomach: acid/pepsin path (STUB-A-03 pH gate not locked)")
        return state


class SmallIntestinePhase(Phase):
    """
    K3–K4 emulsion + assimilation.

    Micelle gate: fat_g > 0 → open for fat-soluble teaching path (L-FAT-1 / LAW-020).
    Macro absorption fractions are FLOW prototypes, not LAW-SPEC locked.
    L2 redox competition applied here (DMT1 / non-haem Fe family).
    """

    kingdom = "K4"
    system = "Assimilation"

    def process(self, state: MetabolicState) -> MetabolicState:
        state.current_phase = "small_intestine"
        state.kingdom = self.kingdom
        state.system = self.system

        # L-FAT-1 style micelle gate (categorical teaching)
        state.micelle_gate_open = state.fat_g > 0 or state.mct_g > 0
        if state.micelle_gate_open:
            state.cite("L-FAT-1", "LAW-020", "LAW-016")
            state.note("K3/K4: micelle gate OPEN (fat co-present) — L-FAT-1 / LAW-020")
            # FLOW fat absorption prototype
            state.absorbed_fat = round((state.fat_g + state.mct_g) * 0.95, 2)
        else:
            state.cite("L-FAT-1")
            state.note(
                "K3/K4: micelle gate CLOSED (no fat) — fat-soluble cargo absorption absent"
            )
            state.absorbed_fat = 0.0

        # Macro FLOW prototypes (open tier — not locked bounds)
        state.absorbed_carb = round(state.carb_g * 0.9, 2)
        state.absorbed_protein = round(state.protein_g * 0.92, 2)
        state.note(
            "Macro absorption fractions 0.9/0.92/0.95 are FLOW prototypes (open tier)"
        )

        # Micronutrient L2 rule
        apply_l2_redox_competition(state)
        return state


class LiverPhase(Phase):
    """Hepatic handling + ketogenesis teaching + bile recycle prior (LAW-039)."""

    kingdom = "K7"
    system = "Biotransformation"

    def process(self, state: MetabolicState) -> MetabolicState:
        state.current_phase = "liver"
        state.kingdom = self.kingdom
        state.system = self.system
        state.cite("LAW-039", "LAW-021")
        # FLOW ketogenesis sketch — NOT a locked law
        state.beta_hb_mmol = round(
            state.absorbed_fat * 0.05 + state.mct_g * 0.12, 2
        )
        state.note(
            f"Liver FLOW: βHB≈{state.beta_hb_mmol} mmol teaching units "
            f"(not locked ketogenesis law); bile recycle prior {state.bile_recycling_efficiency}"
        )
        if not state.fed and state.hours_since_meal >= 12:
            state.beta_hb_mmol = round(state.beta_hb_mmol + 0.3, 2)
            state.note("Fasted ≥12h: mild ketogenesis bump (teaching)")
        return state


class PeripheralTissuesPhase(Phase):
    """
    Energy use — ATP teaching units.

    REFUSES locked 3.5 ATP factor as law (FLOW_VS_UNITS / colon SCFA honesty).
    """

    kingdom = "K7"
    system = "Energy"

    def process(self, state: MetabolicState) -> MetabolicState:
        state.current_phase = "peripheral_tissues"
        state.kingdom = self.kingdom
        state.system = self.system
        # Deliberately simple open-tier teaching score — not clinical
        state.atp_units = round(
            state.beta_hb_mmol * 10.0
            + state.absorbed_carb * 15.0
            + state.scfa_mmol * 2.0,
            1,
        )
        if "use_3.5_atp_factor_as_locked_bound" not in state.refuse:
            state.refuse.append("use_3.5_atp_factor_as_locked_bound")
        state.note(
            f"Energy FLOW: atp_units={state.atp_units} (teaching; refuse locked 3.5 factor)"
        )
        # soft heuristic: reward micelle open + reasonable macros
        score = 50.0
        if state.micelle_gate_open:
            score += 15
        if state.ascorbate_same_meal and state.iron_rel > 0:
            score += 5
        if state.fiber_g >= 20:
            score += 5
        if state.beta_hb_mmol > 0.5:
            score += 5
        state.flow_score = min(100.0, score)
        return state


class LargeIntestinePhase(Phase):
    """K5 Fermentation — LAW-025/026 cited; SCFA coeff open (FLOW_VS_UNITS)."""

    kingdom = "K5"
    system = "Energy"

    def process(self, state: MetabolicState) -> MetabolicState:
        state.current_phase = "large_intestine"
        state.kingdom = self.kingdom
        state.system = self.system
        state.cite("LAW-025", "LAW-026")
        # Prototype: not all fiber fermentable; 0.6 is FLOW not LAW-026 lock
        state.scfa_mmol = round(state.fiber_g * 0.6, 2)
        state.note(
            f"K5 colon: SCFA≈{state.scfa_mmol} (fiber×0.6 FLOW prototype; "
            f"LAW-026 bound not locked)"
        )
        if "scfa_0.6_as_locked_law" not in state.refuse:
            state.refuse.append("scfa_0.6_as_locked_law")
        return state


class RectumExcretionPhase(Phase):
    kingdom = "K7"
    system = "Assimilation"

    def process(self, state: MetabolicState) -> MetabolicState:
        state.current_phase = "rectum_excretion"
        state.kingdom = "K_end"
        state.note("Excretion: residual payload leaves the model")
        return state


# Order mirrors teaching loop: mouth→stomach→SI→colon→liver/periphery→exit
# Liver/peripheral after SI so absorbed macros exist; colon can run after SI.
DEFAULT_PHASES: list[Phase] = [
    MouthPhase(),
    StomachPhase(),
    SmallIntestinePhase(),
    LargeIntestinePhase(),
    LiverPhase(),
    PeripheralTissuesPhase(),
    RectumExcretionPhase(),
]
