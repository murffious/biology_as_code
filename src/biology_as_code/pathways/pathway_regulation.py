"""
pathway_regulation.py
=================================================================
Executable regulation rules that connect PhysiologicalState
to pathway / mechanism activity.

This is the first wiring layer that turns static educational
graphs into a state-responsive system.

Activity is returned as a float in [0.0, 1.0] where:
  0.0 = fully suppressed
  1.0 = fully active
=================================================================
"""


from biology_as_code.simulation.physiological_state import NutritionalPhase, PhysiologicalState


def clamp(value: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, value))


# ----------------------------------------------------------------------
# Core hormonal drivers
# ----------------------------------------------------------------------

def insulin_signal(state: PhysiologicalState) -> float:
    """Normalized insulin drive (higher = more storage mode)."""
    return clamp(state.hormones.insulin / 3.0)  # 3.0 ≈ strong fed response


def glucagon_signal(state: PhysiologicalState) -> float:
    """Normalized glucagon drive (higher = more mobilization)."""
    return clamp(state.hormones.glucagon / 3.0)


def epinephrine_signal(state: PhysiologicalState) -> float:
    return clamp(state.hormones.epinephrine / 3.0)


def energy_stress_signal(state: PhysiologicalState) -> float:
    """High when energy charge is low (AMPK-like)."""
    return state.energy.ampk_activation


# ----------------------------------------------------------------------
# Glycolysis vs Gluconeogenesis (first real reciprocal pair)
# ----------------------------------------------------------------------

def glycolysis_activity(state: PhysiologicalState) -> float:
    """
    Glycolysis is favored by:
      - High insulin
      - Fed state
    Suppressed by high glucagon.
    """
    insulin = insulin_signal(state)
    glucagon = glucagon_signal(state)
    fed = 1.0 if state.is_fed() else 0.3

    activity = (0.55 * insulin) + (0.25 * fed) + (0.20 * (1.0 - glucagon))
    return clamp(activity)


def gluconeogenesis_activity(state: PhysiologicalState) -> float:
    """
    Gluconeogenesis is favored by:
      - High glucagon
      - Low insulin
      - Fasting / prolonged fasting
    """
    insulin = insulin_signal(state)
    glucagon = glucagon_signal(state)
    fasting = 1.0 if state.is_fasting() else 0.2

    activity = (0.45 * glucagon) + (0.35 * (1.0 - insulin)) + (0.20 * fasting)
    return clamp(activity)


# ----------------------------------------------------------------------
# Glycogen metabolism
# ----------------------------------------------------------------------

def glycogenesis_activity(state: PhysiologicalState) -> float:
    """Active when insulin is high and glucose is available."""
    insulin = insulin_signal(state)
    glucose_ok = 1.0 if state.substrates.blood_glucose_mmol > 5.0 else 0.4
    return clamp(0.7 * insulin + 0.3 * glucose_ok)


def glycogenolysis_activity(state: PhysiologicalState) -> float:
    """Active under glucagon / epinephrine or low glucose."""
    glucagon = glucagon_signal(state)
    epi = epinephrine_signal(state)
    low_glucose = 1.0 if state.substrates.blood_glucose_mmol < 4.5 else 0.3
    return clamp(0.4 * glucagon + 0.35 * epi + 0.25 * low_glucose)


# ----------------------------------------------------------------------
# Fat metabolism (ACC vs CPT-I logic)
# ----------------------------------------------------------------------

def fatty_acid_synthesis_activity(state: PhysiologicalState) -> float:
    """
    Driven by insulin.
    Suppressed by AMPK (energy stress) and glucagon.
    """
    insulin = insulin_signal(state)
    energy_stress = energy_stress_signal(state)
    glucagon = glucagon_signal(state)

    activity = (0.6 * insulin) - (0.3 * energy_stress) - (0.2 * glucagon)
    return clamp(activity)


def beta_oxidation_activity(state: PhysiologicalState) -> float:
    """
    Active when malonyl-CoA is low (CPT-I released) and 
    energy is needed or fasting is present.
    """
    malonyl_block = clamp(state.substrates.malonyl_coa / 1.5)
    fasting = 1.0 if state.is_fasting() else 0.3
    energy_stress = energy_stress_signal(state)
    glucagon = glucagon_signal(state)

    activity = (0.4 * (1.0 - malonyl_block)) + (0.3 * fasting) + (0.2 * energy_stress) + (0.1 * glucagon)
    return clamp(activity)


def ketogenesis_activity(state: PhysiologicalState) -> float:
    """Strongly activated in prolonged fasting / very low insulin."""
    insulin = insulin_signal(state)
    fasting_depth = 0.0
    if state.phase == NutritionalPhase.PROLONGED_FASTING:
        fasting_depth = 1.0
    elif state.phase == NutritionalPhase.FASTING:
        fasting_depth = 0.5

    activity = (0.5 * (1.0 - insulin)) + (0.5 * fasting_depth)
    return clamp(activity)


def ampk_activity(state: PhysiologicalState) -> float:
    """AMPK-like proxy: energy stress + low insulin / fasting."""
    stress = energy_stress_signal(state)
    insulin = insulin_signal(state)
    fasting = 1.0 if state.is_fasting() else 0.25
    return clamp(0.5 * stress + 0.3 * (1.0 - insulin) + 0.2 * fasting)


def mtor_activity(state: PhysiologicalState) -> float:
    """mTOR-like proxy: insulin + amino acids + energy available."""
    insulin = insulin_signal(state)
    aa = clamp(state.substrates.blood_amino_acids / 2.0)
    energy_ok = 1.0 - energy_stress_signal(state)
    return clamp(0.45 * insulin + 0.3 * aa + 0.25 * energy_ok)


def srebp_lipogenic_activity(state: PhysiologicalState) -> float:
    """SREBP-1c-like lipogenic drive proxy."""
    insulin = insulin_signal(state)
    ampk = ampk_activity(state)
    fed = 1.0 if state.is_fed() else 0.2
    return clamp(0.5 * insulin + 0.3 * fed - 0.4 * ampk)


# ----------------------------------------------------------------------
# Multi-node nutrient-sensing graphs, executed from state
# ----------------------------------------------------------------------

def nutrient_sensing_snapshot(state: PhysiologicalState) -> dict:
    """Run the AMPK / mTORC1 / SREBP graphs on the current state.

    Turns the declarative networks in ``pathways.nutrient_sensing`` into a
    state-responsive computation: AMPK feeds mTORC1 and SREBP, mTORC1 feeds SREBP
    (so the AMPK ⊣ mTORC1 ⊣ SREBP cross-talk is explicit). Returns per-node
    activations plus the three headline regulator levels.
    """
    from biology_as_code.pathways.nutrient_sensing import (
        evaluate_network,
        get_nutrient_sensing_registry,
    )

    reg = get_nutrient_sensing_registry()
    insulin = insulin_signal(state)
    amino_acids = clamp(state.substrates.blood_amino_acids / 2.0)
    # Seed the AMPK sensor node from the validated scalar proxy, then let the graph
    # propagate the downstream consequences (ACC, mTORC1, ULK1, SREBP, PGC-1α).
    ampk = ampk_activity(state)

    ampk_net = evaluate_network(reg.get("ampk_network"), {"ampk": ampk})

    mtorc1_net = evaluate_network(
        reg.get("mtorc1_network"),
        {"amino_acids": amino_acids, "insulin_igf": insulin, "ampk": ampk},
    )
    mtorc1 = mtorc1_net["mtorc1"]

    srebp_net = evaluate_network(
        reg.get("srebp_network"),
        {"insulin": insulin, "mtorc1": mtorc1, "ampk": ampk, "sterols": 0.5},
    )

    def _round(d: dict) -> dict:
        return {k: round(v, 3) for k, v in d.items()}

    return {
        "regulators": {
            "ampk": round(ampk, 3),
            "mtorc1": round(mtorc1, 3),
            "srebp1c": round(srebp_net["srebp1c"], 3),
        },
        "ampk_network": _round(ampk_net),
        "mtorc1_network": _round(mtorc1_net),
        "srebp_network": _round(srebp_net),
    }


# ----------------------------------------------------------------------
# Convenience: get a full activity snapshot
# ----------------------------------------------------------------------

def iron_absorption_activity(state: PhysiologicalState) -> float:
    """
    Non-haem iron absorption proxy: higher when not inflamed (low hepcidin drive).
    Inflammation raises hepcidin → ferroportin block → lower absorption activity.
    """
    inflam = clamp(getattr(state, "inflammation", 0.2))
    # mild fed boost (duodenal exposure / meal context teaching)
    fed = 1.0 if state.is_fed() else 0.55
    activity = (0.75 * (1.0 - inflam)) + (0.25 * fed)
    return clamp(activity)


def glucose_epithelial_transport_activity(state: PhysiologicalState) -> float:
    """Apical SGLT1 path more relevant post-meal (fed / high insulin proxy)."""
    insulin = insulin_signal(state)
    fed = 1.0 if state.is_fed() else 0.35
    return clamp(0.55 * fed + 0.45 * insulin)


def scfa_colonic_production_activity(state: PhysiologicalState) -> float:
    """
    Colonic fermentation is relatively constitutive; slightly higher in fasting
    teaching states when upper-GI carbohydrate load is low (more substrate reaches colon).
    """
    fasting = 1.0 if state.is_fasting() else 0.6
    return clamp(0.5 + 0.3 * fasting)


def pathway_activity_snapshot(state: PhysiologicalState) -> dict[str, float]:
    """Return current activity levels for the major regulated pathways."""
    return {
        "glycolysis": round(glycolysis_activity(state), 3),
        "gluconeogenesis": round(gluconeogenesis_activity(state), 3),
        "glycogenesis": round(glycogenesis_activity(state), 3),
        "glycogenolysis": round(glycogenolysis_activity(state), 3),
        "fatty_acid_synthesis": round(fatty_acid_synthesis_activity(state), 3),
        "beta_oxidation": round(beta_oxidation_activity(state), 3),
        "ketogenesis": round(ketogenesis_activity(state), 3),
        "ampk": round(ampk_activity(state), 3),
        "mtor": round(mtor_activity(state), 3),
        "srebp_lipogenic": round(srebp_lipogenic_activity(state), 3),
        # Meal-critical queue (tier B)
        "iron_absorption": round(iron_absorption_activity(state), 3),
        "glucose_epithelial_transport": round(glucose_epithelial_transport_activity(state), 3),
        "scfa_colonic_production": round(scfa_colonic_production_activity(state), 3),
    }


if __name__ == "__main__":
    from biology_as_code.simulation.physiological_state import (
        create_exercise_state,
        create_fed_state,
        create_overnight_fast_state,
        create_prolonged_fast_state,
    )

    scenarios = {
        "Fed": create_fed_state(),
        "Overnight Fast": create_overnight_fast_state(),
        "Prolonged Fast": create_prolonged_fast_state(),
        "Exercise": create_exercise_state(),
    }

    print("=" * 70)
    print("EXECUTABLE PATHWAY REGULATION – ACTIVITY SNAPSHOTS")
    print("=" * 70)

    for name, state in scenarios.items():
        print(f"\n--- {name} ---")
        print(f"  Insulin/Glucagon ratio: {state.hormones.insulin_glucagon_ratio:.2f}")
        print(f"  Energy charge:          {state.energy.energy_charge:.3f}")
        print(f"  Malonyl-CoA:            {state.substrates.malonyl_coa:.2f}")
        print("  Pathway activities:")
        for pathway, activity in pathway_activity_snapshot(state).items():
            bar = "█" * int(activity * 20) + "░" * (20 - int(activity * 20))
            print(f"    {pathway:22} {activity:4.2f}  {bar}")