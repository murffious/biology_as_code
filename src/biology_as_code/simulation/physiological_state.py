"""
physiological_state.py
=================================================================
Central Physiological State for the engine

This is the single source of truth for system-wide variables that
pathways, mechanisms, and user scenarios can read.

It is deliberately designed to map onto the Internet-of-Body
17-factor taxonomy (L1 Host State, L2 Food, L3 Ingestion, L4 Clinical).

Design goals:
  - Clean, typed, and documented
  - Easy to set from wearables / food logs / CGM / manual input
  - Ready to drive pathway activity functions later
  - Sensible defaults for a healthy adult in the fed state
=================================================================
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class NutritionalPhase(Enum):
    """High-level metabolic context."""
    FED = "fed"                       # Recently eaten
    POST_ABSORPTIVE = "post_absorptive"  # 3–6 h after meal
    FASTING = "fasting"               # Overnight / 12–24 h
    PROLONGED_FASTING = "prolonged_fasting"  # >24–36 h
    EXERCISE = "exercise"
    RECOVERY = "recovery"


class TissueContext(Enum):
    LIVER = "liver"
    MUSCLE = "muscle"
    ADIPOSE = "adipose"
    BRAIN = "brain"
    WHOLE_BODY = "whole_body"


@dataclass
class HostState:
    """
    L1 – Host State variables
    Most of these can be derived or approximated from wearables today.
    """
    # Sleep & recovery
    sleep_hours_last_night: float = 7.5
    sleep_quality: float = 0.8          # 0–1
    hrv_rmssd: float | None = None   # ms, if available
    resting_hr: float | None = None  # bpm

    # Stress & autonomic
    stress_level: float = 0.3           # 0–1 (higher = more stressed)
    perceived_stress: float = 0.3       # self-report or derived

    # Activity
    steps_today: int = 0
    active_minutes_today: int = 0
    recent_exercise_intensity: float = 0.0  # 0–1

    # Body composition / hydration (coarse)
    hydration_status: float = 0.8       # 0–1
    body_fat_percent: float | None = None
    muscle_mass_kg: float | None = None


@dataclass
class HormonalState:
    """
    Core endocrine signals that drive pathway switching.
    Values are relative (1.0 = typical baseline) unless noted.
    """
    insulin: float = 1.0
    glucagon: float = 1.0
    epinephrine: float = 0.2
    cortisol: float = 1.0
    growth_hormone: float = 1.0
    thyroid_t3: float = 1.0             # optional refinement

    @property
    def insulin_glucagon_ratio(self) -> float:
        if self.glucagon <= 0:
            return 10.0
        return self.insulin / self.glucagon


@dataclass
class EnergyState:
    """Cellular and whole-body energy status."""
    atp: float = 5.0                    # relative or mM-scale
    adp: float = 0.5
    amp: float = 0.1
    phosphocreatine: float = 1.0        # muscle

    @property
    def energy_charge(self) -> float:
        """Atkinson energy charge: (ATP + 0.5*ADP) / (ATP+ADP+AMP)"""
        total = self.atp + self.adp + self.amp
        if total <= 0:
            return 0.0
        return (self.atp + 0.5 * self.adp) / total

    @property
    def ampk_activation(self) -> float:
        """Rough proxy: higher when energy charge is low."""
        ec = self.energy_charge
        if ec >= 0.9:
            return 0.1
        if ec <= 0.7:
            return 1.0
        return 1.0 - (ec - 0.7) / 0.2


@dataclass
class SubstratePools:
    """
    Key circulating and storage metabolites.
    These are the main variables pathways consume or produce.
    """
    # Circulating
    blood_glucose_mmol: float = 5.0     # ~90 mg/dL
    free_fatty_acids: float = 0.4       # mmol/L range
    blood_amino_acids: float = 1.0      # relative
    ketone_bodies: float = 0.1          # mmol/L (acetoacetate + βHB)
    lactate: float = 1.0                # mmol/L
    glycerol: float = 0.1

    # Storage
    glycogen_liver: float = 100.0       # relative or grams
    glycogen_muscle: float = 300.0
    adipose_tg: float = 1.0             # relative store

    # Important regulatory intermediates
    malonyl_coa: float = 0.5            # high in fed state → blocks CPT-I
    acetyl_coa_mito: float = 1.0
    citrate_cyto: float = 1.0


@dataclass
class FoodContext:
    """
    L2 – Information about the most recent meal / current substrate load.
    In a real system this would be populated by food logging + AI vision.
    """
    last_meal_timestamp: datetime | None = None
    last_meal_calories: float = 0.0
    last_meal_carb_g: float = 0.0
    last_meal_fat_g: float = 0.0
    last_meal_protein_g: float = 0.0
    last_meal_fiber_g: float = 0.0
    last_meal_nova_class: int = 1       # 1=unprocessed … 4=ultra-processed
    glycemic_load_estimate: float = 0.0
    is_ultra_processed: bool = False


@dataclass
class IngestionContext:
    """
    L3 – How the food was eaten (currently the weakest sensing layer).
    """
    meal_duration_minutes: float | None = None
    eating_speed: float = 0.5           # 0=very slow, 1=very fast
    food_order_score: float = 0.5       # 0=poor order, 1=optimal (veg/protein first)
    mastication_quality: float = 0.5    # 0–1
    meal_timing_circadian: float = 0.5  # 0=badly timed, 1=well timed
    hydrated_with_meal: bool = True


@dataclass
class ClinicalContext:
    """
    L4 – Medications, supplements, and acute substances.
    """
    medications: list[str] = field(default_factory=list)   # e.g. ["metformin", "atorvastatin"]
    supplements: list[str] = field(default_factory=list)
    alcohol_recent: float = 0.0         # 0–1 relative load
    tobacco_recent: float = 0.0
    statin_onboard: bool = False
    metformin_onboard: bool = False


@dataclass
class PhysiologicalState:
    """
    Master state object for the entire engine.

    Pathways and mechanisms should eventually query this object
    instead of relying only on static regulation notes.
    """
    # Core context
    phase: NutritionalPhase = NutritionalPhase.FED
    tissue: TissueContext = TissueContext.WHOLE_BODY
    timestamp: datetime = field(default_factory=datetime.now)

    # Layered state
    host: HostState = field(default_factory=HostState)
    hormones: HormonalState = field(default_factory=HormonalState)
    energy: EnergyState = field(default_factory=EnergyState)
    substrates: SubstratePools = field(default_factory=SubstratePools)
    food: FoodContext = field(default_factory=FoodContext)
    ingestion: IngestionContext = field(default_factory=IngestionContext)
    clinical: ClinicalContext = field(default_factory=ClinicalContext)

    # Derived / convenience flags
    inflammation: float = 0.2           # 0–1
    insulin_sensitivity: float = 1.0    # 1.0 = normal

    # ------------------------------------------------------------------
    # Helper methods
    # ------------------------------------------------------------------
    def is_fed(self) -> bool:
        return self.phase in (NutritionalPhase.FED, NutritionalPhase.POST_ABSORPTIVE)

    def is_fasting(self) -> bool:
        return self.phase in (NutritionalPhase.FASTING, NutritionalPhase.PROLONGED_FASTING)

    def is_exercising(self) -> bool:
        return self.phase == NutritionalPhase.EXERCISE

    def summary(self) -> dict:
        return {
            "phase": self.phase.value,
            "tissue": self.tissue.value,
            "insulin": round(self.hormones.insulin, 2),
            "glucagon": round(self.hormones.glucagon, 2),
            "insulin_glucagon_ratio": round(self.hormones.insulin_glucagon_ratio, 2),
            "energy_charge": round(self.energy.energy_charge, 3),
            "ampk_proxy": round(self.energy.ampk_activation, 2),
            "blood_glucose": self.substrates.blood_glucose_mmol,
            "ketones": self.substrates.ketone_bodies,
            "malonyl_coa": self.substrates.malonyl_coa,
            "inflammation": self.inflammation,
        }


# ----------------------------------------------------------------------
# Scenario factories – easy way to set realistic user states
# ----------------------------------------------------------------------

def create_fed_state() -> PhysiologicalState:
    """Typical state 1–2 hours after a mixed meal."""
    state = PhysiologicalState(phase=NutritionalPhase.FED)
    state.hormones.insulin = 2.5
    state.hormones.glucagon = 0.6
    state.substrates.blood_glucose_mmol = 6.5
    state.substrates.malonyl_coa = 1.2
    state.substrates.glycogen_liver = 110.0
    state.energy.atp = 5.2
    state.energy.amp = 0.08
    return state


def create_overnight_fast_state() -> PhysiologicalState:
    """~12–14 h overnight fast."""
    state = PhysiologicalState(phase=NutritionalPhase.FASTING)
    state.hormones.insulin = 0.5
    state.hormones.glucagon = 1.8
    state.substrates.blood_glucose_mmol = 4.6
    state.substrates.free_fatty_acids = 0.7
    state.substrates.ketone_bodies = 0.3
    state.substrates.malonyl_coa = 0.2
    state.substrates.glycogen_liver = 40.0
    return state


def create_prolonged_fast_state() -> PhysiologicalState:
    """>36 h fasting – high ketones, low insulin."""
    state = PhysiologicalState(phase=NutritionalPhase.PROLONGED_FASTING)
    state.hormones.insulin = 0.25
    state.hormones.glucagon = 2.5
    state.substrates.blood_glucose_mmol = 3.8
    state.substrates.free_fatty_acids = 1.1
    state.substrates.ketone_bodies = 3.5
    state.substrates.malonyl_coa = 0.1
    state.substrates.glycogen_liver = 5.0
    return state


def create_exercise_state() -> PhysiologicalState:
    """Moderate-to-vigorous exercise."""
    state = PhysiologicalState(phase=NutritionalPhase.EXERCISE)
    state.hormones.insulin = 0.4
    state.hormones.glucagon = 1.6
    state.hormones.epinephrine = 2.5
    state.energy.atp = 4.0
    state.energy.amp = 0.4
    state.substrates.blood_glucose_mmol = 4.8
    state.substrates.lactate = 4.0
    state.substrates.malonyl_coa = 0.15
    return state


if __name__ == "__main__":
    print("=" * 65)
    print("PHYSIOLOGICAL STATE – SCENARIO EXAMPLES")
    print("=" * 65)

    scenarios = {
        "Fed (1–2 h after meal)": create_fed_state(),
        "Overnight Fast (~12–14 h)": create_overnight_fast_state(),
        "Prolonged Fast (>36 h)": create_prolonged_fast_state(),
        "Exercise": create_exercise_state(),
    }

    for name, state in scenarios.items():
        print(f"\n--- {name} ---")
        for k, v in state.summary().items():
            print(f"  {k:25}: {v}")
