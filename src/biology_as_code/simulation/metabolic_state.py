"""
metabolic_state.py
Core MetabolicState controller for KIBO.
Includes hormonal profiles, energy charge, pathway signals,
vitamin status, organ laws, and bound conditions.
"""

from biology_as_code.utils.logging import get_logger

log = get_logger(__name__)

from dataclasses import dataclass, field
from enum import Enum


class MetabolicPhase(Enum):
    FED = "fed"
    FASTING = "fasting"
    EXERCISE = "exercise"


@dataclass
class VitaminStatus:
    adequacy: float = 1.0          # 0.0 – 1.0
    coenzyme_factor: float = 1.0
    deficiency_impact: float = 0.0


@dataclass
class OrganLaw:
    organ: str
    description: str
    lever: str
    limit: float = 1.0
    affected_pathways: list[str] = field(default_factory=list)


@dataclass
class BoundCondition:
    variable: str
    min_val: float = 0.0
    max_val: float = 1.0
    soft: bool = True


@dataclass
class MetabolicState:
    phase: MetabolicPhase = MetabolicPhase.FED
    hormonal_profile: dict[str, float] = field(default_factory=dict)
    energy_charge: float = 1.0
    pathway_signals: dict[str, float] = field(default_factory=dict)
    vitamin_pool: dict[str, VitaminStatus] = field(default_factory=dict)
    organ_laws: dict[str, OrganLaw] = field(default_factory=dict)
    bound_conditions: dict[str, BoundCondition] = field(default_factory=dict)
    inflammation_score: float = 0.2

    def load_vitamins(self, path: str | None = None):
        """Load a simple vitamin registry. Expandable from vitamins.json."""
        core_vitamins = [
            "c", "b1", "b2", "b3", "b6", "b9", "b12", "a", "d", "e", "k",
            "iron", "zinc", "calcium", "folate"
        ]
        for v in core_vitamins:
            self.vitamin_pool[v] = VitaminStatus(adequacy=1.0)
        log.debug(f"✅ Loaded {len(self.vitamin_pool)} vitamins into MetabolicState")

    def load_organ_laws(self):
        self.organ_laws = {
            "liver": OrganLaw("liver", "detox + vitamin metabolism", "detox_rate", 0.95, ["tca", "gluconeogenesis"]),
            "kidney": OrganLaw("kidney", "excretion + electrolyte balance", "excretion_rate", 0.9, ["mineral_balance"]),
            "gut": OrganLaw("gut", "absorption + barrier integrity", "absorption_efficiency", 0.85, ["nutrient_uptake"]),
            "heart": OrganLaw("heart", "circulation demand", "cardiac_output", 1.0, ["oxygen_delivery"]),
            "pancreas": OrganLaw("pancreas", "enzyme + hormone secretion", "enzyme_output", 0.95, ["digestion"]),
        }
        log.debug("✅ Loaded organ/system laws")

    def load_bound_conditions(self):
        self.bound_conditions = {
            "energy_charge": BoundCondition("energy_charge", 0.0, 1.0, soft=False),
            "vitamin_adequacy": BoundCondition("vitamin_adequacy", 0.0, 1.0, soft=True),
            "inflammation_score": BoundCondition("inflammation_score", 0.0, 1.0, soft=True),
        }
        log.debug("✅ Loaded bound conditions")

    def enforce_bounds(self):
        for var, bound in self.bound_conditions.items():
            if var == "energy_charge":
                self.energy_charge = max(bound.min_val, min(bound.max_val, self.energy_charge))
            if var == "inflammation_score":
                self.inflammation_score = max(bound.min_val, min(bound.max_val, self.inflammation_score))

    def apply_organ_laws(self):
        for law in self.organ_laws.values():
            for p in law.affected_pathways:
                if p in self.pathway_signals:
                    self.pathway_signals[p] *= law.limit

    def sync_coenzyme_from_adequacy(self) -> None:
        """Keep coenzyme_factor in lockstep with adequacy (teaching FLOW model)."""
        for status in self.vitamin_pool.values():
            status.coenzyme_factor = max(0.5, min(1.0, float(status.adequacy)))
            status.deficiency_impact = max(0.0, 1.0 - float(status.adequacy))

    def apply_vitamin_modifiers(self):
        """
        Apply vitamin adequacy → coenzyme factors → pathway/energy soft gates.

        Previously coenzyme_factor could stay at 1.0 while adequacy was updated
        elsewhere, making this a silent no-op. We always resync first.
        """
        self.sync_coenzyme_from_adequacy()
        # Aggregate B-vitamin coenzyme pressure (mean of B-family factors)
        b_factors = [
            st.coenzyme_factor
            for vid, st in self.vitamin_pool.items()
            if vid.startswith("b") or vid in ("folate", "b9")
        ]
        if b_factors:
            b_mean = sum(b_factors) / len(b_factors)
            current = self.pathway_signals.get("tca", 1.0)
            self.pathway_signals["tca"] = current * b_mean
            self.energy_charge *= max(0.7, b_mean)
        if "c" in self.vitamin_pool:
            c_f = self.vitamin_pool["c"].coenzyme_factor
            current = self.pathway_signals.get("antioxidant", 1.0)
            self.pathway_signals["antioxidant"] = current * c_f
        self.apply_organ_laws()
        self.enforce_bounds()

    def update_vitamin_status(self, daily_intake: dict[str, float]):
        for vid, status in self.vitamin_pool.items():
            intake = daily_intake.get(vid, 0.0)
            # Simple model – replace with real DRI lookup later
            status.adequacy = min(1.0, max(0.0, intake / 0.1 + status.adequacy * 0.5))
        self.sync_coenzyme_from_adequacy()

    def get_deficiency_symptoms(self) -> dict[str, list[str]]:
        symptoms = {}
        for vid, status in self.vitamin_pool.items():
            if status.adequacy < 0.55:
                if vid == "c":
                    symptoms[vid] = ["bleeding gums", "poor wound healing", "fatigue", "bruising"]
                elif vid == "b1":
                    symptoms[vid] = ["neuropathy", "muscle weakness", "heart failure symptoms"]
                elif vid in ("b9", "folate"):
                    symptoms[vid] = ["megaloblastic anemia", "fatigue"]
                elif vid == "b12":
                    symptoms[vid] = ["neurological damage", "megaloblastic anemia"]
                elif vid == "iron":
                    symptoms[vid] = ["fatigue", "pallor", "shortness of breath"]
                else:
                    symptoms[vid] = ["general fatigue / subclinical deficiency"]
        return symptoms

    def advance_time(self, hours: int = 1):
        # Simple depletion model
        for status in self.vitamin_pool.values():
            status.adequacy = max(0.0, status.adequacy - 0.015 * hours)
            status.coenzyme_factor = max(0.5, status.adequacy)
        if self.phase == MetabolicPhase.FASTING:
            self.energy_charge = max(0.4, self.energy_charge - 0.02 * hours)
        elif self.phase == MetabolicPhase.EXERCISE:
            self.energy_charge = max(0.3, self.energy_charge - 0.05 * hours)
        self.apply_vitamin_modifiers()
        self.enforce_bounds()

    def start_exercise(self):
        self.phase = MetabolicPhase.EXERCISE
        self.energy_charge *= 0.85
        if "heart" in self.organ_laws:
            self.organ_laws["heart"].limit = 1.15
        self.enforce_bounds()


if __name__ == "__main__":
    state = MetabolicState()
    state.load_vitamins()
    state.load_organ_laws()
    state.load_bound_conditions()
    print("Energy charge:", state.energy_charge)
    print("Deficiency symptoms:", state.get_deficiency_symptoms())
