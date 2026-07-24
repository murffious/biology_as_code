"""
Run a meal through the declarative digestion machines end-to-end.

This makes the machine registry the **single source of truth** for the digestion
sequence: ``digestion_stage_ids()`` reads the ordered stages from the registry
(not a hard-coded list), and ``run_digestion()`` walks ``process.full-digest``
and traces each stage it chains, returning the whole inspectable path.

The numeric FLOW models (``build_absorption_plan``, ``DigestiveFlowSimulator``)
still compute gram-level absorption; this is the structural/teaching layer that
now defines the stage order they follow.
"""

from __future__ import annotations

from typing import Any

from biology_as_code.machines.executor import trace
from biology_as_code.machines.loader import load_registry

_DEFAULT_HOST = {
    "host.ready": 1,
    "host.acidCapacity": 1.0,
    "host.bileCapacity": 1.0,
    "host.alcohol": False,
    "host.insulinResistance": 0.0,
    "host.lactaseLow": False,
    "host.villousAtrophy": False,
    "host.postSurgical": False,
}
_DEFAULT_INTAKE = {"intake.food": 1, "intake.hydration": 1, "intake.supplement": 0}


def digestion_stage_ids() -> list[str]:
    """The canonical ordered digestion stage ids — SSOT from the machine registry."""
    return [m["id"] for m in load_registry().get("machines", []) if m.get("kind") == "stage"]


def meal_to_context(
    *,
    carbs_g: float = 0.0,
    protein_g: float = 0.0,
    fats_g: float = 0.0,
    fiber_g: float = 0.0,
    fructose_g: float = 0.0,
    matrix_integrity: float = 0.8,
    food_quality: float = 0.7,
    host: dict[str, Any] | None = None,
    intake: dict[str, Any] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Map a meal (+ optional host/intake) into the machine context namespace.

    Negative macros are clamped to 0 (a meal can't hold negative grams).
    """

    def _pos(x: float) -> float:
        try:
            x = float(x)
        except (TypeError, ValueError):
            return 0.0
        return x if x > 0.0 else 0.0

    ctx: dict[str, Any] = {
        # teaching proxy: treat available carbohydrate as glucose-equivalent
        "meal.glucoseG": _pos(carbs_g),
        "meal.proteinG": _pos(protein_g),
        "meal.fatG": _pos(fats_g),
        "meal.fiberG": _pos(fiber_g),
        "meal.fructoseG": _pos(fructose_g),
        "meal.matrixIntegrity": float(matrix_integrity),
        "meal.foodQuality": float(food_quality),
    }
    ctx.update(_DEFAULT_HOST)
    ctx.update(_DEFAULT_INTAKE)
    if host:
        ctx.update(host)
    if intake:
        ctx.update(intake)
    if extra:
        ctx.update(extra)
    return ctx


def run_digestion(
    context: dict[str, Any] | None = None,
    *,
    process: str = "process.full-digest",
    **meal: Any,
) -> dict[str, Any]:
    """Walk the digestion process and trace every stage it chains.

    Pass either a ready ``context`` dict or meal kwargs (``carbs_g=...`` etc.).
    Returns ``{process, stages, context, final_states, firedEdgeCases}``.
    """
    if context is None:
        context = meal_to_context(**meal)

    proc = trace(process, context)
    stage_traces: list[dict[str, Any]] = []
    for step in proc["path"]:
        for emit in step.get("emits", []) or []:
            if isinstance(emit, str) and emit.startswith("stage:"):
                stage_traces.append(trace(emit.split(":", 1)[1], context))

    return {
        "process": proc,
        "stages": stage_traces,
        "context": context,
        "final_states": {s["machine"]: s["final"] for s in stage_traces},
        "firedEdgeCases": [ec for s in stage_traces for ec in s["firedEdgeCases"]],
    }
