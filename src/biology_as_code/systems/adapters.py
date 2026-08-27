"""System adapters.

Each adapter returns one WalkResult per system. It may only use fields the
meal declared. Parked systems return UNEVALUABLE with the parking reason.
"""

from __future__ import annotations

from biology_as_code.systems.anatomy import BODY_SYSTEMS, SystemSpec
from biology_as_code.systems.meal import MealObservation
from biology_as_code.systems.states import EvalState, WalkResult


def _uneval(system: SystemSpec, reason: str, missing: tuple[str, ...] = ()) -> WalkResult:
    return WalkResult(
        state=EvalState.UNEVALUABLE,
        system_id=system.id,
        gate_id=None,
        reason=reason,
        l3_named=False,
        missing_fields=missing,
    )


def _refuse(system: SystemSpec, gate_id: str, reason: str, cites: tuple[str, ...] = ()) -> WalkResult:
    return WalkResult(
        state=EvalState.REFUSE,
        system_id=system.id,
        gate_id=gate_id,
        reason=reason,
        l3_named=True,
        citations=cites,
    )


def _open(system: SystemSpec, gate_id: str, reason: str, missing: tuple[str, ...] = (), cites: tuple[str, ...] = ()) -> WalkResult:
    return WalkResult(
        state=EvalState.OPEN,
        system_id=system.id,
        gate_id=gate_id,
        reason=reason,
        l3_named=True,
        missing_fields=missing,
        citations=cites,
    )


def _holds(
    system: SystemSpec,
    gate_id: str,
    reason: str,
    declared: tuple[str, ...] = (),
    cites: tuple[str, ...] = (),
) -> WalkResult:
    return WalkResult(
        state=EvalState.HOLDS,
        system_id=system.id,
        gate_id=gate_id,
        reason=reason,
        l3_named=True,
        declared_fields=declared,
        citations=cites,
    )


def adapt_digestive(meal: MealObservation, spec: SystemSpec) -> WalkResult:
    if meal.declares("lipid_vehicle_g") and meal.declares("fat_soluble_cargo"):
        if float(meal.get("lipid_vehicle_g") or 0) <= 0 and bool(meal.get("fat_soluble_cargo")):
            return WalkResult(
                state=EvalState.REFUTED,
                system_id=spec.id,
                gate_id="micelle_fat_vehicle",
                reason="Fat-soluble cargo declared with lipid vehicle ≤ 0 g — absorption path absent, not reduced (LAW-020 shape).",
                l3_named=True,
                declared_fields=("lipid_vehicle_g", "fat_soluble_cargo"),
            )
    if meal.declares("eating_rate_kcal_min"):
        rate = float(meal.get("eating_rate_kcal_min"))
        return _holds(
            spec,
            "eating_rate",
            f"Eating rate declared at {rate} kcal/min. Digestive oro-sensory gate is evaluable.",
            declared=("eating_rate_kcal_min",),
            cites=("PMID:31105044",),
        )
    if meal.declares("matrix"):
        matrix = str(meal.get("matrix"))
        if matrix == "unknown":
            return _open(spec, "matrix_disintegration", "Matrix tagged unknown — disintegration gate not locked.")
        return _holds(
            spec,
            "matrix_disintegration",
            f"Matrix declared '{matrix}'. Disintegration gate is in scope; magnitude is not asserted.",
            declared=("matrix",),
        )
    if meal.declares("fiber_g"):
        return _open(
            spec,
            "transit_fiber",
            "Fiber mass declared; transit effect still needs host and form (viscous vs fragmented).",
            missing=("fiber_form", "transit_time_h"),
        )
    return _uneval(
        spec,
        "No digestive L3 field declared (matrix, eating_rate, lipid vehicle, fiber).",
        missing=("matrix", "eating_rate_kcal_min", "lipid_vehicle_g", "fiber_g"),
    )


def adapt_endocrine(meal: MealObservation, spec: SystemSpec) -> WalkResult:
    if meal.declares("glp1_iAUC") or meal.declares("incretin_measured"):
        return _holds(
            spec,
            "incretin_distal_contact",
            "Incretin measurement declared on this meal/trial — distal-contact gate evaluable.",
            declared=tuple(k for k in ("glp1_iAUC", "incretin_measured") if meal.declares(k)),
        )
    if meal.declares("gi") and meal.declares("available_carb_g"):
        return _open(
            spec,
            "insulin_gi_fii",
            "GI declared. Insulin is not settled: GI ≠ food insulin index (dairy/protein still invisible).",
            missing=("fii",),
            cites=("Holt 1997 Am J Clin Nutr",),
        )
    if meal.declares("available_carb_g") or meal.declares("added_sugar_g"):
        return _open(
            spec,
            "insulin_gi_fii",
            "Carbohydrate cargo declared without GI or FII — endocrine magnitude OPEN.",
            missing=("gi", "fii"),
        )
    return _uneval(
        spec,
        "No endocrine cargo or incretin field declared.",
        missing=("gi", "available_carb_g", "glp1_iAUC"),
    )


def adapt_cardiovascular(meal: MealObservation, spec: SystemSpec) -> WalkResult:
    if meal.declares("sodium_mg"):
        na = float(meal.get("sodium_mg"))
        return _holds(
            spec,
            "sodium_load",
            f"Sodium declared at {na} mg. Load gate is in scope; BP magnitude is not asserted from the meal alone.",
            declared=("sodium_mg",),
        )
    if meal.declares("energy_kcal") and meal.declares("eating_rate_kcal_min"):
        return _open(
            spec,
            "energy_surplus_bp",
            "Energy + eating rate declared. Surplus→weight→BP is a multi-day L5 walk, not a single-meal close.",
            missing=("weight_change_kg", "sbp_delta"),
            cites=("PMID:31105044",),
        )
    if meal.declares("fat_g"):
        return _open(
            spec,
            "apob_sat_fat",
            "Total fat declared without fatty-acid class or ApoB — cardiovascular lipid walk OPEN.",
            missing=("sfa_g", "apob"),
        )
    return _uneval(
        spec,
        "No cardiovascular gate field declared (sodium, energy+rate, fat class).",
        missing=("sodium_mg", "energy_kcal", "fat_g"),
    )


def adapt_immune(meal: MealObservation, spec: SystemSpec) -> WalkResult:
    if meal.declares("emulsifiers_declared") and bool(meal.get("emulsifiers_declared")):
        return _open(
            spec,
            "emulsifier_mucus",
            "Emulsifiers declared present. Mouse mucus/TLR walks exist; human end-to-end on this meal is not locked.",
            missing=("mucus_assay", "calprotectin"),
            cites=("Chassaing 2015 Nature", "Naimi 2021 Gut"),
        )
    if meal.declares("fiber_g"):
        return _open(
            spec,
            "fiber_scfa_barrier",
            "Fiber mass declared. SCFA/barrier effect needs microbiota + fiber form.",
            missing=("scfa_mmol", "fiber_form"),
        )
    return _uneval(
        spec,
        "No immune-gate field declared (emulsifiers, fiber).",
        missing=("emulsifiers_declared", "fiber_g"),
    )


def adapt_nervous(meal: MealObservation, spec: SystemSpec) -> WalkResult:
    # Explicit refusal: diet → brain microplastics is not a meal walk.
    notes = meal.get("notes") or ""
    if isinstance(notes, str) and "microplastic" in notes.lower():
        return _refuse(
            spec,
            "diet_to_brain_mnp",
            "Diet-to-brain microplastic walk refused. Tissue MNP reports are not dietary-exposure measurements.",
            cites=("Nihart 2025 contested; see companion review §4",),
        )
    hpf_flags = tuple(
        k
        for k in ("hpf_fat_sodium", "hpf_fat_sugar", "hpf_carb_sodium")
        if meal.declares(k) and bool(meal.get(k))
    )
    if hpf_flags or meal.declares("eating_rate_kcal_min"):
        declared = hpf_flags + (("eating_rate_kcal_min",) if meal.declares("eating_rate_kcal_min") else ())
        return _holds(
            spec,
            "eating_rate_reward",
            "HPF pair and/or eating rate declared. Reward/oro-sensory gate is in scope; addiction language is not licensed.",
            declared=declared,
            cites=("PMID:31689013", "PMID:31105044"),
        )
    if meal.declares("gi"):
        return _open(
            spec,
            "glycemic_swing_sleep",
            "GI declared; sleep/glycemic-swing walk needs nocturnal glucose, not a 2-h iAUC.",
            missing=("nocturnal_glucose",),
        )
    return _uneval(
        spec,
        "No nervous-gate field declared (HPF pairs, eating rate).",
        missing=("hpf_fat_sodium", "eating_rate_kcal_min"),
    )


ADAPTERS = {
    "digestive": adapt_digestive,
    "endocrine": adapt_endocrine,
    "cardiovascular": adapt_cardiovascular,
    "immune": adapt_immune,
    "nervous": adapt_nervous,
}


def adapt_system(system_id: str, meal: MealObservation) -> WalkResult:
    spec = next(s for s in BODY_SYSTEMS if s.id == system_id)
    if not spec.shipped:
        return _uneval(spec, spec.why)
    return ADAPTERS[system_id](meal, spec)
