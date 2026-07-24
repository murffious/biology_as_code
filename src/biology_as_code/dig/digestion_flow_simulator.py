
"""
digestion_flow_simulator.py
Chronological GI tract simulation from mouth → rectum.
Uses textbook terminology (enzymes, hormones, absorption sites, microbiota, SCFA).

When ``absorption_plan`` (from digestion_capacity_routing) is set, macro
absorption fractions are driven by enzyme capacity + dig-pathway edges
instead of fixed teaching defaults.
"""

import copy
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from biology_as_code.dig.digestion_capacity_routing import MacroAbsorptionPlan


class GI_Segment(Enum):
    MOUTH = "Mouth"
    ESOPHAGUS = "Esophagus"
    STOMACH = "Stomach"
    DUODENUM = "Duodenum"
    JEJUNUM = "Jejunum"
    ILEUM = "Ileum"
    COLON = "Colon"
    RECTUM = "Rectum"


# Legacy fixed sequential fractions (fraction of *remaining* bolus) when no plan.
_LEGACY_FRAC: dict[str, dict[str, float]] = {
    "Mouth": {"carbs": 0.05},
    "Stomach": {"protein": 0.08},
    "Duodenum": {"fats": 0.35, "carbs": 0.25},
    "Jejunum": {"carbs": 0.50, "protein": 0.55},
    "Ileum": {"fats": 0.40},
}


@dataclass
class Bolus:
    """Represents the food mass moving through the GI tract."""
    macros_g: dict[str, float] = field(default_factory=dict)  # carbs, protein, fats
    vitamins_mg: dict[str, float] = field(default_factory=dict)
    fiber_g: float = 0.0
    volume_ml: float = 500.0
    nutrient_density: float = 1.0
    quality_score: float = 1.0


@dataclass
class DigestiveEvent:
    segment: GI_Segment
    terminology_used: list[str]
    laws_fired: list[str]
    interacting_systems: list[str]
    absorbed: dict[str, float]
    remaining_bolus: dict[str, float]
    note: str = ""
    scfa_produced: dict[str, float] = field(default_factory=dict)
    capacity_driven: bool = False


class DigestiveFlowSimulator:
    """
    Simulates the entire digestive process chronologically.
    Each segment fires specific physiological laws and interacts with other systems.
    """

    def __init__(self, metabolic_state=None):
        self.metabolic_state = metabolic_state
        self.segments = list(GI_Segment)
        self.history: list[DigestiveEvent] = []
        self.absorption_plan: MacroAbsorptionPlan | None = None

    def set_absorption_plan(self, plan: Optional["MacroAbsorptionPlan"]) -> None:
        """Optional capacity-driven plan for the next (and subsequent) transits."""
        self.absorption_plan = plan

    def _macro_frac(self, segment: GI_Segment, macro: str) -> float:
        """Sequential fraction of remaining bolus for this macro at segment."""
        label = segment.value
        plan = self.absorption_plan
        if plan is not None:
            seq = plan.sequential_for(macro, label)
            if seq is not None:
                return float(seq)
            return 0.0
        return float(_LEGACY_FRAC.get(label, {}).get(macro, 0.0))

    def _apply_macro_absorption(
        self, segment: GI_Segment, bolus: Bolus, macros: list[str]
    ) -> dict[str, float]:
        absorbed: dict[str, float] = {}
        for m in macros:
            frac = self._macro_frac(segment, m)
            if frac <= 0:
                continue
            avail = float(bolus.macros_g.get(m, 0) or 0)
            take = avail * frac
            if take <= 0:
                continue
            absorbed[m] = take
            bolus.macros_g[m] = max(0.0, avail - take)
        return absorbed

    def process_segment(self, segment: GI_Segment, bolus: Bolus) -> DigestiveEvent:
        event = DigestiveEvent(
            segment=segment,
            terminology_used=[],
            laws_fired=[],
            interacting_systems=[],
            absorbed={},
            remaining_bolus={},
            capacity_driven=self.absorption_plan is not None,
        )

        if segment == GI_Segment.MOUTH:
            event.terminology_used = [
                "mastication", "salivary amylase", "lingual lipase", "bolus formation"
            ]
            event.laws_fired = ["salivary_secretion_law"]
            event.interacting_systems = ["nervous system", "salivary glands"]
            event.absorbed = self._apply_macro_absorption(
                segment, bolus, ["carbs", "fats", "protein"]
            )
            event.note = (
                "Mechanical breakdown + initial starch digestion"
                + (" [capacity plan]" if event.capacity_driven else "")
            )

        elif segment == GI_Segment.ESOPHAGUS:
            event.terminology_used = ["peristalsis", "swallowing", "lower esophageal sphincter"]
            event.laws_fired = ["peristalsis_law"]
            event.interacting_systems = ["smooth muscle", "enteric nervous system"]
            event.note = "Transit only – no significant digestion or absorption"

        elif segment == GI_Segment.STOMACH:
            event.terminology_used = [
                "gastric acid", "pepsin", "gastrin", "churning",
                "intrinsic factor", "gastric lipase",
            ]
            event.laws_fired = ["gastric_acid_law", "pepsinogen_activation_law"]
            event.interacting_systems = ["endocrine system", "gastric mucosa", "parietal cells"]
            event.absorbed = self._apply_macro_absorption(
                segment, bolus, ["protein", "fats", "carbs"]
            )
            event.note = "Acid denaturation + protein digestion begins" + (
                " [capacity plan]" if event.capacity_driven else ""
            )

        elif segment == GI_Segment.DUODENUM:
            event.terminology_used = [
                "CCK", "secretin", "pancreatic enzymes", "bile salts",
                "micelle formation", "pancreatic lipase", "colipase", "trypsin",
            ]
            event.laws_fired = [
                "pancreatic_enzyme_law", "bile_release_law", "enterohepatic_circulation"
            ]
            event.interacting_systems = ["pancreas", "liver", "gallbladder", "endocrine"]
            event.absorbed = self._apply_macro_absorption(
                segment, bolus, ["fats", "carbs", "protein"]
            )
            if getattr(self.metabolic_state, "vitamin_pool", None) is not None:
                for v in ["a", "d", "e", "k"]:
                    if v in self.metabolic_state.vitamin_pool:
                        self.metabolic_state.vitamin_pool[v].adequacy = min(
                            1.0,
                            self.metabolic_state.vitamin_pool[v].adequacy
                            + 0.15 * bolus.quality_score,
                        )
            event.note = "Major fat emulsification + enzyme cascade begins" + (
                " [capacity plan]" if event.capacity_driven else ""
            )

        elif segment == GI_Segment.JEJUNUM:
            event.terminology_used = [
                "brush border enzymes", "lactase", "maltase", "sucrase",
                "villi", "enterocytes", "amino acid transporters", "peptide transporters",
            ]
            event.laws_fired = ["brush_border_law", "active_transport_law"]
            event.interacting_systems = ["intestinal mucosa", "circulatory system"]
            event.absorbed = self._apply_macro_absorption(
                segment, bolus, ["carbs", "protein", "fats"]
            )
            if getattr(self.metabolic_state, "vitamin_pool", None) is not None:
                for v in ["c", "b1", "b2", "b3", "b6", "folate"]:
                    if v in self.metabolic_state.vitamin_pool:
                        self.metabolic_state.vitamin_pool[v].adequacy = min(
                            1.0,
                            self.metabolic_state.vitamin_pool[v].adequacy
                            + 0.20 * bolus.nutrient_density,
                        )
            event.note = "Primary site of carbohydrate and protein absorption" + (
                " [capacity plan]" if event.capacity_driven else ""
            )

        elif segment == GI_Segment.ILEUM:
            event.terminology_used = [
                "bile acid reabsorption", "B12-intrinsic factor complex",
                "ileocecal valve", "enterohepatic circulation",
            ]
            event.laws_fired = ["bile_acid_reabsorption_law", "b12_absorption_law"]
            event.interacting_systems = ["liver", "ileal mucosa"]
            event.absorbed = self._apply_macro_absorption(
                segment, bolus, ["fats", "protein", "carbs"]
            )
            event.absorbed["bile_acids"] = 0.95
            if (
                getattr(self.metabolic_state, "vitamin_pool", None) is not None
                and "b12" in self.metabolic_state.vitamin_pool
            ):
                self.metabolic_state.vitamin_pool["b12"].adequacy = min(
                    1.0, self.metabolic_state.vitamin_pool["b12"].adequacy + 0.25
                )
            event.note = "B12 and remaining bile acids absorbed" + (
                " [capacity plan]" if event.capacity_driven else ""
            )

        elif segment == GI_Segment.COLON:
            event.terminology_used = [
                "gut microbiota", "fermentation", "short-chain fatty acids",
                "acetate", "propionate", "butyrate", "PYY", "GLP-1",
                "resistant starch", "prebiotics",
            ]
            event.laws_fired = ["microbiota_fermentation_law", "scfa_production_law"]
            event.interacting_systems = ["microbiota", "immune system", "endocrine"]

            fermented = bolus.fiber_g * 0.70 * bolus.quality_score
            acetate = fermented * 0.60 * 2.0
            propionate = fermented * 0.25 * 2.0
            butyrate = fermented * 0.15 * 2.5

            event.scfa_produced = {
                "acetate_kcal": acetate,
                "propionate_kcal": propionate,
                "butyrate_kcal": butyrate,
                "total_scfa_kcal": acetate + propionate + butyrate,
            }
            event.absorbed = {"scfa_energy": acetate + propionate + butyrate}

            if (
                self.metabolic_state
                and hasattr(self.metabolic_state, "energy_charge")
                and hasattr(self.metabolic_state, "hormonal_profile")
            ):
                scfa_boost = (acetate + propionate + butyrate) / 100.0
                self.metabolic_state.energy_charge = min(
                    1.0, self.metabolic_state.energy_charge + scfa_boost
                )
                self.metabolic_state.hormonal_profile["glp1"] = (
                    self.metabolic_state.hormonal_profile.get("glp1", 0)
                    + 0.3 * bolus.quality_score
                )
                self.metabolic_state.hormonal_profile["pyy"] = (
                    self.metabolic_state.hormonal_profile.get("pyy", 0)
                    + 0.25 * bolus.quality_score
                )

            event.note = (
                f"Microbial fermentation of fiber → SCFA "
                f"({acetate + propionate + butyrate:.1f} kcal)"
            )

        elif segment == GI_Segment.RECTUM:
            event.terminology_used = ["water reabsorption", "defecation", "fecal bulk"]
            event.laws_fired = ["final_water_balance_law"]
            event.interacting_systems = ["large intestine mucosa"]
            event.note = "Waste elimination complete – remaining unabsorbed material excreted"

        event.remaining_bolus = {
            "carbs": bolus.macros_g.get("carbs", 0),
            "protein": bolus.macros_g.get("protein", 0),
            "fats": bolus.macros_g.get("fats", 0),
            "fiber": bolus.fiber_g,
        }

        if self.metabolic_state and hasattr(self.metabolic_state, "apply_vitamin_modifiers"):
            self.metabolic_state.apply_vitamin_modifiers()

        return event

    def simulate_full_transit(
        self,
        bolus: Bolus,
        verbose: bool = True,
        absorption_plan: Optional["MacroAbsorptionPlan"] = None,
    ) -> list[DigestiveEvent]:
        """Run the complete chronological simulation from mouth to rectum."""
        if absorption_plan is not None:
            self.absorption_plan = absorption_plan
        self.history = []
        current_bolus = copy.deepcopy(bolus)

        mode = "capacity plan" if self.absorption_plan is not None else "legacy fractions"
        if verbose:
            print("=" * 60)
            print(f"DIGESTIVE FLOW SIMULATION: Mouth → Rectum ({mode})")
            print("=" * 60)

        for segment in self.segments:
            event = self.process_segment(segment, current_bolus)
            self.history.append(event)

            if verbose:
                print(f"\n[{segment.value}]")
                print(f"  Laws fired: {', '.join(event.laws_fired)}")
                print(f"  Systems interacting: {', '.join(event.interacting_systems)}")
                terms = event.terminology_used[:5]
                print(
                    f"  Terminology: {', '.join(terms)}"
                    f"{'...' if len(event.terminology_used) > 5 else ''}"
                )
                if event.absorbed:
                    print(f"  Absorbed: {event.absorbed}")
                if event.scfa_produced:
                    print(f"  SCFA: {event.scfa_produced}")
                print(f"  Note: {event.note}")

        if verbose:
            print("\n" + "=" * 60)
            print("TRANSIT COMPLETE")
            print("=" * 60)

        return self.history
