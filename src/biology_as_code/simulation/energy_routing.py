"""
energy_routing.py
=================================================================
Post-meal energy-routing snapshot for kibo_engine.

Joins:
  - PhysiologicalState + pathway_regulation activities (incl. AMPK/mTOR proxies)
  - Static pathway graph summaries (glycolysis, TCA, ETC, β-ox, fuel hierarchy)
  - Dominant fuel program label (glucose / fat / ketone bias)

Tier: teaching FLOW (not LAW-SPEC magnitudes).
=================================================================
"""
from __future__ import annotations

from typing import Any

from biology_as_code.pathways.pathway_regulation import pathway_activity_snapshot
from biology_as_code.simulation.physiological_state import (
    NutritionalPhase,
    PhysiologicalState,
    create_fed_state,
    create_overnight_fast_state,
)


def physiological_state_from_meal(
    carbs_g: float,
    protein_g: float,
    fat_g: float,
    fiber_g: float = 0.0,
    *,
    quality_score: float = 0.7,
) -> PhysiologicalState:
    """
    Coarse fed-state estimate from macronutrient load.
    High carb → stronger insulin bias; high fat+low carb → flatter insulin.
    """
    state = create_fed_state()
    total = max(carbs_g + protein_g + fat_g, 1.0)
    carb_frac = carbs_g / total
    fat_frac = fat_g / total

    # Insulin / glucagon tilt from carb load (teaching only)
    state.hormones.insulin = max(0.4, min(3.5, 0.8 + 2.4 * carb_frac + 0.3 * (protein_g / total)))
    state.hormones.glucagon = max(0.3, min(2.5, 1.6 - 1.1 * carb_frac + 0.4 * fat_frac))
    state.substrates.blood_glucose_mmol = max(4.2, min(9.0, 4.8 + 0.04 * carbs_g))
    state.substrates.malonyl_coa = max(0.15, min(1.6, 0.3 + 0.9 * carb_frac))
    state.food.last_meal_carb_g = carbs_g
    state.food.last_meal_fat_g = fat_g
    state.food.last_meal_protein_g = protein_g
    state.food.last_meal_fiber_g = fiber_g
    state.food.glycemic_load_estimate = carbs_g * (1.0 - 0.3 * min(1.0, fiber_g / max(carbs_g, 1.0)))
    state.food.is_ultra_processed = quality_score < 0.4
    state.phase = NutritionalPhase.FED
    return state


def _pathway_graph_summaries() -> dict[str, Any]:
    """Pull static teaching summaries from pathway modules (import-safe)."""
    out: dict[str, Any] = {}
    try:
        from biology_as_code.pathways.metabolic_pathways import get_metabolic_pathways_registry

        g = get_metabolic_pathways_registry().get("glycolysis")
        if g:
            out["glycolysis"] = g.summary()
    except Exception as e:
        out["glycolysis"] = {"error": str(e)}
    try:
        from biology_as_code.pathways.tca_cycle import get_tca_cycle_registry

        t = get_tca_cycle_registry().get("tca_cycle")
        if t:
            out["tca_cycle"] = t.summary()
    except Exception as e:
        out["tca_cycle"] = {"error": str(e)}
    try:
        from biology_as_code.pathways.etc_oxphos import get_etc_oxphos_registry

        e = get_etc_oxphos_registry().get("etc_oxphos")
        if e:
            out["etc_oxphos"] = e.summary()
    except Exception as e:
        out["etc_oxphos"] = {"error": str(e)}
    try:
        from biology_as_code.pathways.beta_oxidation import get_beta_oxidation_registry

        b = get_beta_oxidation_registry().get("beta_oxidation")
        if b:
            out["beta_oxidation"] = b.summary()
    except Exception as e:
        out["beta_oxidation"] = {"error": str(e)}
    try:
        from biology_as_code.pathways.supporting_pathways import get_supporting_pathways_registry

        s = get_supporting_pathways_registry().get("fuel_selection_hierarchy")
        if s:
            out["fuel_selection_hierarchy"] = s.summary()
    except Exception as e:
        out["fuel_selection_hierarchy"] = {"error": str(e)}
    return out


def dominant_routing(activities: dict[str, float]) -> dict[str, Any]:
    """Name the dominant catabolic / anabolic tilt from activity snapshot."""
    glycol = activities.get("glycolysis", 0.0)
    box = activities.get("beta_oxidation", 0.0)
    keto = activities.get("ketogenesis", 0.0)
    gng = activities.get("gluconeogenesis", 0.0)
    fas = activities.get("fatty_acid_synthesis", 0.0)

    if glycol >= box and glycol >= keto:
        primary = "glucose_oxidation_storage"
    elif box >= keto:
        primary = "fatty_acid_oxidation"
    else:
        primary = "ketone_bias"

    secondary = "gluconeogenesis" if gng > 0.45 else "low_gng"
    lipogenic = fas > 0.5
    return {
        "primary_fuel_program": primary,
        "gluconeogenesis_bias": secondary,
        "lipogenesis_favored": lipogenic,
        "insulin_like_activity": round(glycol, 3),
        "fat_oxidation_activity": round(box, 3),
    }


def build_energy_routing_report(
    carbs_g: float,
    protein_g: float,
    fat_g: float,
    fiber_g: float = 0.0,
    *,
    quality_score: float = 0.7,
    state: PhysiologicalState | None = None,
) -> dict[str, Any]:
    """Full engine-facing energy routing block."""
    phys = state or physiological_state_from_meal(
        carbs_g, protein_g, fat_g, fiber_g, quality_score=quality_score
    )
    activities = pathway_activity_snapshot(phys)
    routing = dominant_routing(activities)
    graphs = _pathway_graph_summaries()

    chain = [
        {
            "step": 1,
            "label": "Absorbed CHO → glycolysis",
            "graph": "glycolysis",
            "activity": activities.get("glycolysis"),
            "teaching": graphs.get("glycolysis", {}),
        },
        {
            "step": 2,
            "label": "Acetyl-CoA → TCA",
            "graph": "tca_cycle",
            "activity": None,
            "teaching": graphs.get("tca_cycle", {}),
        },
        {
            "step": 3,
            "label": "NADH/FADH₂ → ETC / OxPhos",
            "graph": "etc_oxphos",
            "activity": None,
            "teaching": graphs.get("etc_oxphos", {}),
        },
        {
            "step": 4,
            "label": "Fatty acids → β-oxidation (if fat program active)",
            "graph": "beta_oxidation",
            "activity": activities.get("beta_oxidation"),
            "teaching": graphs.get("beta_oxidation", {}),
        },
    ]

    return {
        "tier": "FLOW_open",
        "physiological_phase": phys.phase.value,
        "hormones": {
            "insulin": round(phys.hormones.insulin, 3),
            "glucagon": round(phys.hormones.glucagon, 3),
            "ig_ratio": round(phys.hormones.insulin / max(phys.hormones.glucagon, 0.01), 3),
        },
        "pathway_activity": activities,
        "routing": routing,
        "energy_chain": chain,
        "fuel_selection_graph": graphs.get("fuel_selection_hierarchy", {}),
        "notes": (
            "Activities from pathway_regulation on meal-derived PhysiologicalState; "
            "graph summaries are static pathway models [7]. Not UNITS/LAW-SPEC."
        ),
    }


def fasting_contrast_snapshot() -> dict[str, Any]:
    """Optional compare block for demos."""
    fed = pathway_activity_snapshot(create_fed_state())
    fast = pathway_activity_snapshot(create_overnight_fast_state())
    return {"fed": fed, "overnight_fast": fast}
