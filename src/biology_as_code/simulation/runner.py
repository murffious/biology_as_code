"""
High-level meal run API — wraps MealEngine without renaming it.

Product meal score stays off unless enable_external_score=True and private plugin present.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class MealRunResult:
    """Structured result of one meal compile (not a product meal score object)."""

    report: dict[str, Any]
    payload_name: str = ""
    absorbed_macros_g: dict[str, float] = field(default_factory=dict)
    residual_macros_g: dict[str, float] = field(default_factory=dict)
    pathway_regulation: dict[str, float] = field(default_factory=dict)
    external_scorer_available: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "payload_name": self.payload_name,
            "absorbed_macros_g": self.absorbed_macros_g,
            "residual_macros_g": self.residual_macros_g,
            "pathway_regulation": self.pathway_regulation,
            "external_scorer_available": self.external_scorer_available,
            "report": self.report,
        }


def simulate_meal(
    payload: Any = None,
    *,
    name: str = "meal",
    carbs_g: float = 0.0,
    protein_g: float = 0.0,
    fats_g: float = 0.0,
    fiber_g: float = 0.0,
    quality_score: float = 0.7,
    enable_external_score: bool = False,
    engine: Any = None,
) -> MealRunResult:
    """
    Run open dig on a FoodPayload or macro kwargs.

    Parameters
    ----------
    payload : FoodPayload, optional
        If omitted, build from macro kwargs.
    enable_external_score : bool
        Patent-pending plugin; default False.
    """
    from biology_as_code.simulation.meal_engine import FoodPayload, MealEngine

    if payload is None:
        # Clamp degenerate input: negative/NaN grams are not physical. Treat
        # them as absent (0.0) rather than propagating negative "grams".
        def _clean(x: float) -> float:
            try:
                x = float(x)
            except (TypeError, ValueError):
                return 0.0
            return x if x > 0.0 else 0.0  # also maps NaN -> 0.0

        payload = FoodPayload(
            name=name,
            macros_g={
                "carbs": _clean(carbs_g),
                "protein": _clean(protein_g),
                "fats": _clean(fats_g),
            },
            fiber_g=_clean(fiber_g),
            quality_score=quality_score,
        )
    eng = engine or MealEngine()
    report = eng.simulate_payload(
        payload, enable_external_score=enable_external_score
    )
    psa = report.get("external_score_analysis") or {}
    return MealRunResult(
        report=report,
        payload_name=getattr(payload, "name", name),
        absorbed_macros_g=dict(report.get("absorbed_macros_g") or {}),
        residual_macros_g=dict(report.get("residual_macros_g") or {}),
        pathway_regulation=dict(report.get("pathway_regulation") or {}),
        external_scorer_available=bool(psa.get("available")),
    )
