"""
mineral_interactions.py
Minerals, trace elements, and nutrient–nutrient interaction matrix.

Grounded in Handbook of Nutrition and Food + Advanced Nutrition and Human
Metabolism mineral chapters: competitive absorption, antinutrients, and
classic pairs (Zn–Cu, Ca–Fe, phytate–Zn/Fe, ascorbate–non-heme Fe, etc.).

On ``typical_bioavailability``
------------------------------
These floats are meal-realistic defaults with no citation, no dose and no cohort
attached. ``nodes/bounds.py`` carries the same quantity as sourced, dose-scoped
priors, and the two disagree for several minerals — see
:func:`absorption_prior` and ``reconcile_with_registry``. The disagreements are
mostly scope, not error: zinc absorbs at ~0.70 from a 3 mg dose with nothing
competing, and at ~0.30 across a mixed diet. Both are true of zinc; only one is
true of a meal.

The floats are deliberately left alone here. Changing them would silently move
every simulation result, and the choice of which condition a default should model
is a modelling decision that belongs in a reviewed diff, not in a data import.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class MineralFamily(Enum):
    MACROMINERAL = "macromineral"
    TRACE = "trace_mineral"
    ULTRATRACE = "ultratrace"


@dataclass
class MineralSpec:
    """Canonical mineral with absorption and interaction metadata."""
    id: str
    name: str
    symbol: str
    family: MineralFamily
    #: Meal-realistic default, 0–1. Unsourced by construction — for the sourced,
    #: dose-scoped prior call :func:`absorption_prior` with this mineral's id.
    typical_bioavailability: float
    primary_site: str
    transporters: list[str] = field(default_factory=list)
    dri_adult_mg: float = 0.0  # adult RDA/AI-ish reference (mg/day; µg as noted)
    unit: str = "mg"
    deficiency_signs: list[str] = field(default_factory=list)
    notes: str = ""


@dataclass
class InteractionRule:
    """
    One directed or mutual interaction affecting absorption or utilization.
    factor < 1.0 = inhibition; > 1.0 = enhancement of *target* absorption.
    """
    actor: str           # nutrient or antinutrient id
    target: str          # mineral id affected
    factor: float
    mechanism: str
    bidirectional: bool = False
    threshold_note: str = ""


@dataclass
class MineralAbsorptionResult:
    mineral_id: str
    intake: float
    absorbed_fraction: float
    absorbed_amount: float
    limiting_factors: list[str] = field(default_factory=list)
    enhanced_by: list[str] = field(default_factory=list)
    interactions_applied: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Registry – macrominerals + key trace elements from textbook tables
# ---------------------------------------------------------------------------

MINERAL_REGISTRY: dict[str, MineralSpec] = {
    "ca": MineralSpec(
        id="ca", name="Calcium", symbol="Ca", family=MineralFamily.MACROMINERAL,
        typical_bioavailability=0.30, primary_site="duodenum/jejunum (TRPV6, PMCA)",
        transporters=["TRPV6", "Calbindin-D9k", "PMCA1b", "NCX1"],
        dri_adult_mg=1000, deficiency_signs=["osteopenia", "tetany risk"],
        notes="Saturable active transport + paracellular passive path",
    ),
    "mg": MineralSpec(
        id="mg", name="Magnesium", symbol="Mg", family=MineralFamily.MACROMINERAL,
        typical_bioavailability=0.40, primary_site="distal jejunum/ileum (TRPM6)",
        transporters=["TRPM6", "TRPM7"], dri_adult_mg=400,
        deficiency_signs=["cramps", "arrhythmia risk", "hypokalemia co-occurrence"],
    ),
    "p": MineralSpec(
        id="p", name="Phosphorus", symbol="P", family=MineralFamily.MACROMINERAL,
        typical_bioavailability=0.70, primary_site="jejunum (NaPi-IIb)",
        transporters=["NaPi-IIb"], dri_adult_mg=700,
        deficiency_signs=["weakness", "bone demineralization"],
    ),
    "k": MineralSpec(
        id="k", name="Potassium", symbol="K", family=MineralFamily.MACROMINERAL,
        typical_bioavailability=0.90, primary_site="small intestine",
        transporters=["passive + Na/K-ATPase dependent"], dri_adult_mg=3400,
        deficiency_signs=["hypokalemia", "muscle weakness", "arrhythmia"],
    ),
    "na": MineralSpec(
        id="na", name="Sodium", symbol="Na", family=MineralFamily.MACROMINERAL,
        typical_bioavailability=0.95, primary_site="small intestine (SGLT1/NHE3 coupled)",
        transporters=["SGLT1", "NHE3", "ENaC"], dri_adult_mg=1500,
        deficiency_signs=["hyponatremia", "cramps"],
    ),
    "fe": MineralSpec(
        id="fe", name="Iron", symbol="Fe", family=MineralFamily.TRACE,
        typical_bioavailability=0.10, primary_site="duodenum (DMT1, ferroportin)",
        transporters=["DMT1", "DCYTB", "Ferroportin", "Hephaestin"],
        dri_adult_mg=8,  # adult male; female higher
        deficiency_signs=["microcytic anemia", "fatigue", "pica"],
        notes="Heme ~15–35% absorption; non-heme highly variable",
    ),
    "zn": MineralSpec(
        id="zn", name="Zinc", symbol="Zn", family=MineralFamily.TRACE,
        typical_bioavailability=0.30, primary_site="jejunum (ZIP4)",
        transporters=["ZIP4", "ZnT1"], dri_adult_mg=11,
        deficiency_signs=["acrodermatitis", "impaired immunity", "hypogonadism"],
    ),
    "cu": MineralSpec(
        id="cu", name="Copper", symbol="Cu", family=MineralFamily.TRACE,
        typical_bioavailability=0.50, primary_site="stomach/duodenum (CTR1)",
        transporters=["CTR1", "ATP7A"], dri_adult_mg=0.9,
        deficiency_signs=["anemia", "neuropathy", "neutropenia"],
    ),
    "se": MineralSpec(
        id="se", name="Selenium", symbol="Se", family=MineralFamily.TRACE,
        typical_bioavailability=0.70, primary_site="duodenum/jejunum",
        transporters=["amino acid transporters (selenomethionine)"],
        dri_adult_mg=0.055, unit="mg",
        deficiency_signs=["Keshan-like risk", "thyroid dysfunction"],
    ),
    "i": MineralSpec(
        id="i", name="Iodine", symbol="I", family=MineralFamily.TRACE,
        typical_bioavailability=0.90, primary_site="stomach/small intestine",
        transporters=["NIS (thyroid trapping)"], dri_adult_mg=0.150,
        deficiency_signs=["goiter", "hypothyroidism", "cretinism risk"],
    ),
    "mn": MineralSpec(
        id="mn", name="Manganese", symbol="Mn", family=MineralFamily.TRACE,
        typical_bioavailability=0.05, primary_site="small intestine",
        transporters=["DMT1 (shared)"], dri_adult_mg=2.3,
        deficiency_signs=["rare; bone/lipid metabolism issues"],
    ),
    "cr": MineralSpec(
        id="cr", name="Chromium", symbol="Cr", family=MineralFamily.TRACE,
        typical_bioavailability=0.02, primary_site="small intestine",
        transporters=["unclear"], dri_adult_mg=0.035,
        deficiency_signs=["impaired glucose tolerance (rare)"],
    ),
    "mo": MineralSpec(
        id="mo", name="Molybdenum", symbol="Mo", family=MineralFamily.TRACE,
        typical_bioavailability=0.80, primary_site="stomach/small intestine",
        transporters=["shared anion carriers"], dri_adult_mg=0.045,
        deficiency_signs=["sulfite oxidase deficiency picture (rare)"],
    ),
    "f": MineralSpec(
        id="f", name="Fluoride", symbol="F", family=MineralFamily.TRACE,
        typical_bioavailability=0.80, primary_site="stomach",
        transporters=["passive"], dri_adult_mg=4.0,
        deficiency_signs=["dental caries risk"],
    ),
}


# ---------------------------------------------------------------------------
# Interaction matrix (classic handbook pairs)
# ---------------------------------------------------------------------------

INTERACTION_RULES: list[InteractionRule] = [
    # Competitive divalent cations
    InteractionRule("zn", "cu", 0.55, "ZIP/CTR competition; chronic high Zn induces MT sequestering Cu", True),
    InteractionRule("cu", "zn", 0.70, "Mutual absorption competition at high doses", True),
    InteractionRule("ca", "fe", 0.65, "Ca inhibits heme and non-heme Fe absorption (meal-level)"),
    InteractionRule("ca", "zn", 0.75, "High Ca can reduce Zn absorption"),
    InteractionRule("fe", "zn", 0.70, "High non-heme Fe competes with Zn (especially supplements)"),
    InteractionRule("zn", "fe", 0.75, "High Zn can reduce Fe absorption"),
    InteractionRule("mg", "ca", 0.85, "High Mg may modestly reduce Ca absorption"),
    InteractionRule("mn", "fe", 0.70, "Mn and Fe share DMT1"),
    InteractionRule("fe", "mn", 0.65, "High Fe reduces Mn absorption via DMT1"),

    # Antinutrients
    InteractionRule("phytate", "zn", 0.45, "Phytate chelates Zn; molar phytate:Zn ratio critical"),
    InteractionRule("phytate", "fe", 0.50, "Phytate binds non-heme Fe"),
    InteractionRule("phytate", "ca", 0.70, "Phytate–Ca complexes"),
    InteractionRule("phytate", "mg", 0.75, "Phytate reduces Mg bioavailability"),
    InteractionRule("oxalate", "ca", 0.40, "Oxalate precipitates Ca (spinach, rhubarb)"),
    InteractionRule("polyphenols", "fe", 0.55, "Tea/coffee polyphenols inhibit non-heme Fe"),
    InteractionRule("tannins", "fe", 0.50, "Tannins chelate non-heme Fe"),
    InteractionRule("fiber_insoluble", "zn", 0.85, "High insoluble fiber modestly reduces Zn"),
    InteractionRule("fiber_insoluble", "fe", 0.88, "Bulking may reduce contact time"),

    # Enhancers
    InteractionRule("ascorbate", "fe", 1.80, "Vitamin C reduces Fe3+→Fe2+; keeps non-heme Fe soluble"),
    InteractionRule("heme_iron", "fe", 1.50, "Heme pathway (HCP1) bypasses many inhibitors", threshold_note="use when heme_fe present"),
    InteractionRule("animal_protein", "fe", 1.25, "Meat factor enhances non-heme Fe"),
    InteractionRule("animal_protein", "zn", 1.20, "Animal protein improves Zn bioavailability"),
    InteractionRule("organic_acids", "fe", 1.15, "Citric/lactic acids enhance non-heme Fe"),
    InteractionRule("vitamin_d", "ca", 1.40, "1,25-(OH)2D induces TRPV6/calbindin"),
    InteractionRule("lactose", "ca", 1.15, "Lactose modestly enhances Ca absorption"),
    InteractionRule("fructose", "cu", 0.80, "High fructose may impair Cu status (utilization)"),

    # Vitamin–mineral utilization (not always lumen absorption)
    InteractionRule("vitamin_c", "fe", 1.60, "Alias of ascorbate enhancer for meal context keys"),
    InteractionRule("retinol", "fe", 1.10, "Vitamin A supports mobilization/utilization of Fe stores"),
    InteractionRule("riboflavin", "fe", 1.10, "B2 needed for efficient Fe mobilization"),
]


class MineralInteractionSystem:
    """
    Compute mineral absorption fractions given co-ingested minerals,
    antinutrients, and enhancers in the same meal context.
    """

    def __init__(self):
        self.minerals = MINERAL_REGISTRY
        self.rules = INTERACTION_RULES
        # index rules by target for speed
        self._by_target: dict[str, list[InteractionRule]] = {}
        for rule in self.rules:
            self._by_target.setdefault(rule.target, []).append(rule)
            if rule.bidirectional:
                # reverse already listed separately for Zn/Cu; skip auto-reverse
                pass

    def get_mineral(self, mineral_id: str) -> MineralSpec | None:
        return self.minerals.get(mineral_id.lower())

    def interaction_matrix_summary(self) -> list[dict[str, Any]]:
        """Flat table for docs / UI."""
        rows = []
        for r in self.rules:
            rows.append({
                "actor": r.actor,
                "target": r.target,
                "factor": r.factor,
                "effect": "enhances" if r.factor > 1.0 else "inhibits",
                "mechanism": r.mechanism,
            })
        return rows

    def calculate_absorption(
        self,
        mineral_id: str,
        intake: float,
        context: dict[str, Any] | None = None,
    ) -> MineralAbsorptionResult:
        """
        context keys may include:
          - co-ingested mineral amounts: ca, fe, zn, ... (mg)
          - flags: phytate, oxalate, polyphenols, tannins, ascorbate, vitamin_c,
                   animal_protein, heme_iron, vitamin_d, lactose, organic_acids
          - phytate_score / polyphenol_score floats 0–1 for graded effects
          - stomach_acid: bool
          - hepcidin_high: bool (systemic block on Fe export)
        """
        context = context or {}
        mid = mineral_id.lower()
        spec = self.minerals.get(mid)
        if not spec:
            return MineralAbsorptionResult(mid, intake, 0.0, 0.0, ["unknown_mineral"])

        base = spec.typical_bioavailability
        limiting: list[str] = []
        enhanced: list[str] = []
        applied: list[str] = []

        # Dose saturation (simplified: high bolus → lower fractional absorption)
        dri = max(spec.dri_adult_mg, 0.001)
        if intake > dri * 2:
            sat = max(0.45, 1.0 - (intake / dri - 2) * 0.12)
            base *= sat
            limiting.append("dose_saturation")

        # Stomach acid needed for Fe, Ca solubilization
        if mid in ("fe", "ca", "mg") and not context.get("stomach_acid", True):
            base *= 0.55
            limiting.append("low_stomach_acid")

        # Systemic iron regulation
        if mid == "fe" and context.get("hepcidin_high", False):
            base *= 0.40
            limiting.append("hepcidin_block_ferroportin")

        # Heme vs non-heme iron baseline
        if mid == "fe":
            if context.get("heme_iron") or context.get("heme_fe_fraction", 0) > 0.3:
                base = max(base, 0.22)
                enhanced.append("heme_pathway")
            else:
                # non-heme more inhibitor-sensitive baseline already low
                pass

        # Apply interaction rules
        for rule in self._by_target.get(mid, []):
            actor_present = self._actor_present(rule.actor, context, mid)
            if not actor_present:
                continue

            graded = self._graded_strength(rule.actor, context)
            # interpolate factor toward 1.0 when graded is weak
            effective_factor = 1.0 + (rule.factor - 1.0) * graded
            base *= effective_factor
            label = f"{rule.actor}→{rule.target}×{effective_factor:.2f}"
            applied.append(label)
            if effective_factor < 1.0:
                limiting.append(rule.actor)
            elif effective_factor > 1.0:
                enhanced.append(rule.actor)

        # High co-mineral competition: if both high doses of Zn and Cu
        if mid == "cu" and context.get("zn", 0) > 40:
            base *= 0.50
            limiting.append("pharmacologic_zinc")
            applied.append("zn_high_dose_copper_block")

        absorbed_fraction = max(0.02, min(0.98, base))
        return MineralAbsorptionResult(
            mineral_id=mid,
            intake=intake,
            absorbed_fraction=absorbed_fraction,
            absorbed_amount=intake * absorbed_fraction,
            limiting_factors=limiting,
            enhanced_by=enhanced,
            interactions_applied=applied,
        )

    def process_meal_minerals(
        self,
        mineral_intakes: dict[str, float],
        context: dict[str, Any] | None = None,
    ) -> dict[str, MineralAbsorptionResult]:
        """Process a meal mineral map; auto-inject co-intakes into context."""
        context = dict(context or {})
        for mid, amount in mineral_intakes.items():
            context.setdefault(mid.lower(), amount)
        results = {}
        for mid, amount in mineral_intakes.items():
            results[mid.lower()] = self.calculate_absorption(mid, amount, context)
        return results

    def pairwise_risk(self, a: str, b: str) -> dict[str, Any]:
        """Lookup mutual interaction notes for two minerals."""
        a, b = a.lower(), b.lower()
        hits = [
            r for r in self.rules
            if (r.actor == a and r.target == b) or (r.actor == b and r.target == a)
        ]
        return {
            "pair": [a, b],
            "rules": [
                {"actor": r.actor, "target": r.target, "factor": r.factor, "mechanism": r.mechanism}
                for r in hits
            ],
            "risk": "high" if any(r.factor <= 0.6 for r in hits) else ("moderate" if hits else "low"),
        }

    @staticmethod
    def _actor_present(actor: str, context: dict[str, Any], target: str) -> bool:
        # mineral co-intake above a mild threshold
        if actor in MINERAL_REGISTRY:
            amount = float(context.get(actor, 0) or 0)
            if actor == target:
                return False
            # presence if absolute amount or flag
            if amount > 0:
                # only apply competition if co-mineral is non-trivial
                dri = MINERAL_REGISTRY[actor].dri_adult_mg
                return amount >= max(dri * 0.25, 0.01) or context.get(f"high_{actor}", False)
            return bool(context.get(f"has_{actor}") or context.get(f"high_{actor}"))

        # antinutrient / enhancer flags or scores
        if context.get(actor) or context.get(f"has_{actor}"):
            return True
        score_key = f"{actor}_score"
        if float(context.get(score_key, 0) or 0) > 0.05:
            return True
        # aliases
        aliases = {
            "ascorbate": ["vitamin_c", "c", "vit_c"],
            "vitamin_c": ["ascorbate", "c", "vit_c"],
            "vitamin_d": ["d", "vit_d"],
            "polyphenols": ["tea", "coffee", "polyphenol_score"],
            "phytate": ["phytic_acid", "phytate_score"],
        }
        for alt in aliases.get(actor, []):
            if context.get(alt) or float(context.get(alt, 0) or 0) > 0:
                return True
        return False

    @staticmethod
    def _graded_strength(actor: str, context: dict[str, Any]) -> float:
        """Return 0–1 strength for graded inhibitors/enhancers."""
        score_keys = [f"{actor}_score", actor]
        for k in score_keys:
            val = context.get(k)
            if isinstance(val, (int, float)) and not isinstance(val, bool):
                if actor in MINERAL_REGISTRY:
                    dri = MINERAL_REGISTRY[actor].dri_adult_mg
                    # scale: 1× DRI ~ 0.5 strength, 3× DRI ~ 1.0
                    return max(0.2, min(1.0, float(val) / max(dri * 2, 0.01)))
                return max(0.2, min(1.0, float(val)))
        return 1.0  # boolean presence → full rule strength


# ---------------------------------------------------------------------------
# Sourced priors — the bridge to nodes/bounds.py
# ---------------------------------------------------------------------------


def absorption_prior(mineral_id: str) -> Any | None:
    """The sourced, dose-scoped absorption prior for a mineral, or None.

    Returns an ``AbsorptionBound`` carrying the fraction *as the source stated
    it* — which may be a one-sided bound, a range, a cohort split, or a
    dose-response curve rather than a number. Unlike
    :attr:`MineralSpec.typical_bioavailability` it never flattens to a float,
    because for copper the honest answer is a curve and for calcium it is two
    cohorts.

    Returns None when the seed has no entry (iron, phosphorus, potassium and
    sodium are all registry-only today), and imports lazily so the mineral module
    keeps working without PyYAML installed.
    """
    try:
        from biology_as_code.nodes.bounds import bounds_by_mineral
    except ImportError:
        return None
    return bounds_by_mineral().get(mineral_id)


def unsourced_minerals() -> list[str]:
    """Registry ids whose bioavailability float has no counterpart in the seed.

    These are the numbers with nothing behind them at all. Worth knowing, because
    iron is on the list and iron is the one the interaction rules lean on hardest.
    """
    seeded = set()
    try:
        from biology_as_code.nodes.bounds import bounds_by_mineral

        seeded = set(bounds_by_mineral())
    except ImportError:
        pass
    return sorted(set(MINERAL_REGISTRY) - seeded)


if __name__ == "__main__":
    sys = MineralInteractionSystem()

    print("=== Mineral Interaction Matrix (sample) ===")
    for row in sys.interaction_matrix_summary()[:8]:
        print(f"  {row['actor']:16} → {row['target']:4}  {row['effect']:9} ×{row['factor']:.2f}  ({row['mechanism'][:50]})")

    print("\n=== Meal: plant-based + tea + vitamin C ===")
    ctx = {
        "phytate_score": 0.8,
        "polyphenols": True,
        "ascorbate": True,
        "animal_protein": False,
        "stomach_acid": True,
        "zn": 15,
        "ca": 400,
    }
    intakes = {"fe": 14, "zn": 12, "ca": 400, "cu": 1.2, "mg": 320}
    for mid, res in sys.process_meal_minerals(intakes, ctx).items():
        print(f"{mid.upper():3}: {res.absorbed_amount:.3f} absorbed "
              f"({res.absorbed_fraction*100:.1f}%)  "
              f"limit={res.limiting_factors} enh={res.enhanced_by}")

    print("\n=== Pairwise Zn–Cu ===")
    print(sys.pairwise_risk("zn", "cu"))
