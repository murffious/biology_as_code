"""
energy_accounting.py
=================================================================
Why energy is not a nutrient node, and what a score may do with it instead.

``nodes/`` models a nutrient as a pipeline scored against a reference intake.
Energy fails that shape at every joint:

1. It is a **cascade of subtractions** (gross → digestible → net), not a fraction.
2. It is a **balance**, not a target. Correctness is defined by the outcome, not
   by proximity to a reference value.
3. It **has no RDA and cannot have one.** Berdanier is explicit: no safety factor
   is possible, because an intake producing obesity in one person may be
   inadequate for another.
4. Storage cost is **substrate-dependent**. The same kilocalorie stored as fat
   costs more arriving as glucose than as preformed fat, so a single calorie
   figure cannot express what the body actually did with it.

So this is a sibling of the nutrient node, not an instance of it. The practical
output is :data:`SCORING_GUARD`: a score may act on macronutrient distribution
and on substrate storage cost, and must not act on an absolute kilocalorie target.

What is deliberately *not* here
-------------------------------
BMR equations (``body_composition_energy.py`` already implements Mifflin-St Jeor,
revised Harris-Benedict, Cunningham and Katch-McArdle) and the respiratory
quotient (``respiratory_quotient.py``). This module carries only what those did
not already cover.

Source and its errata
---------------------
Berdanier, Berdanier & Zempleni (2009), *Advanced Nutrition: Macronutrients,
Micronutrients, and Metabolism*, CRC Press, Ch. 1, pp. 1-19.

Chapter 1 contains five arithmetic errors, catalogued in
``docs/VALIDATION_LEDGER.md`` under "Berdanier Ch. 1 errata". Two of them
propagate into the numbers below, so the constants here are the corrected values
with the printed ones retained alongside for traceability. Everything in this
module is tier `gate`: secondary source, no primary read.
=================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

KJ_PER_KCAL = 4.184


# ---------------------------------------------------------------------------
# 1. The scoring guard — the load-bearing output of this module
# ---------------------------------------------------------------------------

SCORING_GUARD: dict[str, object] = {
    "has_rda": False,
    "can_have_rda": False,
    "response_shape": "balance",
    "monotonic_safe": False,
    "rationale": (
        "Berdanier p. 3: unlike other essential nutrients, no safety factor is "
        "possible in an energy recommendation, because an intake producing obesity "
        "in one person may be inadequate for another. Energy has an AMDR for "
        "macronutrient distribution but no reference intake for amount. A score "
        "may act on distribution and on substrate quality; it must not act on an "
        "absolute kcal target."
    ),
    "act_on": ["macronutrient_distribution", "substrate_storage_cost"],
    "do_not_act_on": ["absolute_kcal_target"],
}

#: Acceptable Macronutrient Distribution Ranges, percent of total energy.
#: Attributed by Berdanier (p. 3) to the Food and Nutrition Board; the citable
#: anchor is the IOM 2005 macronutrient DRI report (DOI 10.17226/10490), not the
#: textbook.
AMDR: dict[str, dict[str, tuple[int, int]]] = {
    "child_1_3": {"fat": (30, 40), "carbohydrate": (45, 65), "protein": (5, 20)},
    "child_4_18": {"fat": (25, 35), "carbohydrate": (45, 65), "protein": (10, 30)},
    "adult": {"fat": (20, 35), "carbohydrate": (45, 65), "protein": (10, 35)},
}


def amdr_verdict(life_stage: str, energy_fractions: dict[str, float]) -> dict[str, str]:
    """Classify each macronutrient's share of energy against its AMDR band.

    ``energy_fractions`` are fractions of total energy (0-1), keyed ``fat``,
    ``carbohydrate``, ``protein``. Returns ``below`` | ``within`` | ``above`` per
    macronutrient — a distribution judgement, which is the one energy judgement
    :data:`SCORING_GUARD` permits.
    """
    bands = AMDR.get(life_stage)
    if bands is None:
        raise ValueError(f"unknown life stage {life_stage!r}; expected one of {sorted(AMDR)}")

    out: dict[str, str] = {}
    for macro, (low, high) in bands.items():
        share = energy_fractions.get(macro)
        if share is None:
            continue
        percent = share * 100
        out[macro] = "below" if percent < low else "above" if percent > high else "within"
    return out


# ---------------------------------------------------------------------------
# 2. The energy cascade (Figure 1.3, p. 4)
# ---------------------------------------------------------------------------


@dataclass
class EnergyCascade:
    """Gross energy stepped down by successive measurable losses.

    ``GE`` (bomb calorimeter) minus excreta gives digestible energy; minus the
    heat increment gives net energy. What remains after basal and activity costs
    is the energy balance — the only free term, and the only quantity a food
    score can meaningfully act on.
    """

    gross_energy_kcal: float
    #: ~10% of GE for a mixed diet (Berdanier pp. 4-5).
    excreta_loss_fraction: float = 0.10
    #: NOT given as a number in Ch. 1. This default is a placeholder and must not
    #: be reported as sourced.
    heat_increment_fraction: float = 0.10

    @property
    def digestible_energy_kcal(self) -> float:
        return self.gross_energy_kcal * (1 - self.excreta_loss_fraction)

    @property
    def heat_increment_kcal(self) -> float:
        return self.digestible_energy_kcal * self.heat_increment_fraction

    @property
    def net_energy_kcal(self) -> float:
        return self.digestible_energy_kcal - self.heat_increment_kcal

    def energy_balance_kcal(self, basal_kcal: float, activity_kcal: float) -> float:
        """Net energy less basal and activity cost. Positive = stored."""
        return self.net_energy_kcal - basal_kcal - activity_kcal

    def as_dict(self) -> dict[str, float]:
        return {
            "GE": round(self.gross_energy_kcal, 1),
            "DE": round(self.digestible_energy_kcal, 1),
            "HI": round(self.heat_increment_kcal, 1),
            "NE": round(self.net_energy_kcal, 1),
        }


# ---------------------------------------------------------------------------
# 3. Storage-cost asymmetry (Table 1.4, pp. 10-11, corrected)
# ---------------------------------------------------------------------------

#: Heat of combustion of glucose, 2802.7 kJ/mol. Berdanier p. 11 prints
#: "294.8 kcal or 1238 kJ", low by a factor of 2.27 — see ERR-GLU-01. Every
#: efficiency percentage in Table 1.4 is built on the printed figure.
GLUCOSE_KCAL_PER_MOL = 669.87
GLUCOSE_KCAL_PER_MOL_AS_PRINTED = 294.8

#: 9.41 kcal/g x 807.3 g/mol. This one checks out.
TRIPALMITIN_KCAL_PER_MOL = 7597.0
ATP_KCAL_PER_BOND = 7.3

#: Table 1.3 uses pre-1990s P/O ratios (NADH=3, FADH2=2). Modern consensus is
#: 2.5 and 1.5, giving ~30 ATP via the glycerol-3-phosphate shuttle and ~32 via
#: malate-aspartate — see ERR-ATP-01.
ATP_PER_GLUCOSE_AS_PRINTED = 36
ATP_PER_GLUCOSE_CORRECTED = 31


def efficiency_de_novo_lipogenesis(
    atp_per_glucose: int = ATP_PER_GLUCOSE_CORRECTED,
    glucose_kcal: float = GLUCOSE_KCAL_PER_MOL,
) -> float:
    """Fraction of substrate energy retained in tripalmitin built from glucose.

    Berdanier's accounting: 12 glucose supply the carbon for 3 palmitoyl-CoA,
    0.5 glucose supplies the glycerol phosphate, and 49 ATP are consumed. The ATP
    must itself come from oxidising glucose, so its cost converts to a glucose
    cost at the prevailing yield.

    Framed as product over substrate, which is the only thermodynamically
    coherent form. Berdanier's printed framing subtracts the glucose cost *from*
    the tripalmitin value and only yields a positive number because her glucose
    constant is 2.3x too low; with the correct constant her expression goes
    negative, which is what exposed the error.
    """
    carbon_glucose = 12.5
    atp_needed = 49
    atp_glucose = atp_needed / atp_per_glucose
    total_kcal_in = (carbon_glucose + atp_glucose) * glucose_kcal
    return TRIPALMITIN_KCAL_PER_MOL / total_kcal_in


def efficiency_preformed_fat_storage() -> float:
    """Fraction retained when dietary fat is esterified and stored directly.

    Cost is 10 ATP (Table 1.4): 3 x 2 ATP to activate each palmitate to
    palmitoyl-CoA, plus 4 ATP for the glycerol phosphate.

    NOTE the scope. This is the *biochemical* cost of esterification and nothing
    else, so it returns ~99%. McGuire & Beerman put the whole-body cost of storing
    dietary fat nearer 5% (≈95% efficient), which additionally carries digestion,
    chylomicron assembly and transport. The two numbers are not in conflict, but
    they are not interchangeable either — do not quote this one as the dietary-fat
    storage efficiency. See the errata note in the validation ledger.
    """
    cost_kcal = 10 * ATP_KCAL_PER_BOND
    return (TRIPALMITIN_KCAL_PER_MOL - cost_kcal) / TRIPALMITIN_KCAL_PER_MOL


def storage_cost_asymmetry(atp_per_glucose: int = ATP_PER_GLUCOSE_CORRECTED) -> dict[str, float]:
    """Both storage routes and the ratio between them.

    The qualitative asymmetry is the part that survives the errata, and it in fact
    widens under correction: fewer ATP per glucose makes de novo lipogenesis look
    worse, not better. This is the substrate-quality signal
    :data:`SCORING_GUARD` permits a score to act on.
    """
    de_novo = efficiency_de_novo_lipogenesis(atp_per_glucose)
    preformed = efficiency_preformed_fat_storage()
    return {
        "de_novo_lipogenesis": round(de_novo, 4),
        "preformed_fat_biochemical": round(preformed, 4),
        "ratio": round(preformed / de_novo, 3),
    }


# ---------------------------------------------------------------------------
# 4. Postabsorptive onset — species scoping (p. 5)
# ---------------------------------------------------------------------------

#: Hours after the last meal at which the postabsorptive state begins.
#: The single most important scoping fact when reading animal metabolic data:
#: a 12-hour fast is postabsorptive in a human, still absorptive in a rat, and
#: nowhere near it in a pig.
POSTABSORPTIVE_ONSET_H: dict[str, tuple[int, int]] = {
    "human": (12, 14),
    "mouse": (10, 10),
    "rat": (17, 17),
    "guinea_pig": (22, 22),
    "rabbit": (60, 60),
    "pig": (96, 96),
    "ruminant": (120, 144),
}


def is_postabsorptive(hours_since_meal: float, species: str = "human") -> bool | None:
    """Whether a fast has reached the postabsorptive state for this species.

    Returns None inside the transition window, and for unknown species — an
    unknown clock is not a human clock.
    """
    window = POSTABSORPTIVE_ONSET_H.get(species)
    if window is None:
        return None
    low, high = window
    if hours_since_meal >= high:
        return True
    if hours_since_meal < low:
        return False
    return None


# ---------------------------------------------------------------------------
# 5. Starvation timeline (Figure 1.6, Figure 1.8, pp. 16-17)
# ---------------------------------------------------------------------------

STARVATION_TIMELINE: list[dict[str, object]] = [
    {"hours": (0, 12), "events": ["insulin_release_down"]},
    {"hours": (12, 18), "events": ["epinephrine_up", "glucagon_up", "growth_hormone_down"]},
    {"hours": (18, 24), "events": ["gluconeogenesis_measurable", "ketones_up",
                                   "growth_hormone_up"]},
    {"hours": (24, 36), "events": ["ketones_down", "tca_down", "proteolysis_down",
                                   "glucocorticoid_up"]},
    {"hours": (36, 48), "events": ["growth_hormone_up", "ketosis_declines_adaptation"]},
]

#: Figure 1.6, adapted from Cahill (1970). Percent of fuel by source in prolonged
#: starvation — carbohydrate contributes almost nothing, which is the point.
FUEL_SOURCE_IN_STARVATION_PCT = {
    "fat_adipose": 85.32,
    "protein_muscle": 14.50,
    "carbohydrate_muscle_liver": 0.18,
}

STARVATION_FACTS = {
    "glycogen_stores_g": 75,
    "glycogen_contribution_kcal_first_24h": 300,
    "cns_glucose_use_g_per_day_fed": 115,
    "brain_energy_from_ketones_fraction_at_40d": 0.65,
    "cahill_subject_maintenance_kcal_per_day": 2000,
    "cahill_subject_survival_days": 80,
}


__all__ = [
    "AMDR",
    "ATP_KCAL_PER_BOND",
    "ATP_PER_GLUCOSE_AS_PRINTED",
    "ATP_PER_GLUCOSE_CORRECTED",
    "FUEL_SOURCE_IN_STARVATION_PCT",
    "GLUCOSE_KCAL_PER_MOL",
    "GLUCOSE_KCAL_PER_MOL_AS_PRINTED",
    "KJ_PER_KCAL",
    "POSTABSORPTIVE_ONSET_H",
    "SCORING_GUARD",
    "STARVATION_FACTS",
    "STARVATION_TIMELINE",
    "TRIPALMITIN_KCAL_PER_MOL",
    "EnergyCascade",
    "amdr_verdict",
    "efficiency_de_novo_lipogenesis",
    "efficiency_preformed_fat_storage",
    "is_postabsorptive",
    "storage_cost_asymmetry",
]
