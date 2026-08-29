"""
unified_facade.py
=================
Single entry that joins product **depth** (`kibo_engine`) with **LAW-linked**
GI / core FLOW (`bridge.bridge_engine`).

- Depth: enzyme capacity → absorption plan → transit residual → SCFA →
  vitamins/minerals → pathway_regulation → DRI / causal
- Bridge: SEGMENT_MAP laws, L-FAT-1 micelle gate, kibo_core.sim, iron walk

Does not invent a third meal model — composes the two existing stacks.
Tier: FLOW open teaching; not clinical software.
"""

from __future__ import annotations

from typing import Any

from biology_as_code.product_score import run_product_score_analysis
from biology_as_code.simulation.kibo_engine import (
    FoodPayload as DepthPayload,
)
from biology_as_code.simulation.kibo_engine import (
    KIBOEngine,
)
from biology_as_code.simulation.kibo_engine import (
    LifecycleStage as DepthLifecycle,
)
from biology_as_code.simulation.kibo_engine import (
    LifestyleFactors as DepthLifestyle,
)


def _bridge_imports():
    """Lazy import so depth-only users never require bridge path quirks."""
    from biology_as_code.bridge.bridge_engine import (  # type: ignore
        BridgedKIBOEngine,
    )
    from biology_as_code.bridge.bridge_engine import (
        FoodPayload as BridgePayload,
    )
    from biology_as_code.bridge.bridge_engine import (
        LifecycleStage as BridgeLifecycle,
    )
    from biology_as_code.bridge.bridge_engine import (
        LifestyleFactors as BridgeLifestyle,
    )

    return BridgedKIBOEngine, BridgePayload, BridgeLifecycle, BridgeLifestyle


def depth_to_bridge_payload(payload: DepthPayload):
    BridgedKIBOEngine, BridgePayload, _, _ = _bridge_imports()
    del BridgedKIBOEngine
    minerals = getattr(payload, "minerals_mg", None) or {}
    vitamins = dict(payload.vitamins_mg or {})
    # Bridge historically folds some minerals into vitamins_mg for iron walk
    for k in ("iron", "zinc", "calcium", "magnesium"):
        if k in minerals and k not in vitamins:
            vitamins[k] = minerals[k]
    return BridgePayload(
        name=payload.name,
        nutrient_density_score=payload.nutrient_density_score,
        quality_score=payload.quality_score,
        macros_g=dict(payload.macros_g or {}),
        vitamins_mg=vitamins,
        fiber_g=float(payload.fiber_g or 0),
        anti_nutrients=float(getattr(payload, "anti_nutrients", 0) or 0),
        rs_breakdown=dict(getattr(payload, "rs_profile", None) or {"rs2": 0.3, "rs3": 0.2}),
        ascorbate_same_meal=bool(getattr(payload, "ascorbate_boost", False))
        or float(vitamins.get("c") or 0) >= 30,
        tannin_same_meal=bool(getattr(payload, "polyphenols", False)),
    )


def _lifecycle_bridge(stage: DepthLifecycle):
    _, _, BridgeLifecycle, _ = _bridge_imports()
    try:
        return BridgeLifecycle(stage.value)
    except Exception:
        return BridgeLifecycle.ADULT


class UnifiedKIBOFacade:
    """
    Product facade: depth meal pipeline + bridge LAW GI events.

    Usage::

        facade = UnifiedKIBOFacade()
        facade.apply_profile(DepthLifecycle.ADULT, DepthLifestyle(), age_years=30, sex="male")
        report = facade.simulate_payload(DepthPayload(...))
        # report["depth"], report["bridge"], report["merged"]
    """

    def __init__(
        self,
        *,
        run_bridge: bool = True,
        bridge_verbose: bool = False,
        enable_product_score: bool = False,
    ):
        self.depth = KIBOEngine()
        self.run_bridge = run_bridge
        self.bridge_verbose = bridge_verbose
        # Patent-pending product meal score — off by default for open demos
        self.enable_product_score = enable_product_score
        self.depth.enable_product_score = enable_product_score
        self.bridge = None
        if run_bridge:
            BridgedKIBOEngine, _, _, _ = _bridge_imports()
            self.bridge = BridgedKIBOEngine()

    def apply_profile(
        self,
        lifecycle: DepthLifecycle,
        lifestyle: DepthLifestyle,
        age_years: float = 30,
        sex: str = "male",
    ) -> None:
        self.depth.apply_profile(lifecycle, lifestyle, age_years=age_years, sex=sex)
        if self.bridge is not None:
            _, _, _, BridgeLifestyle = _bridge_imports()
            self.bridge.apply_profile(
                _lifecycle_bridge(lifecycle),
                BridgeLifestyle(
                    activity_level=lifestyle.activity_level,
                    stress_level=lifestyle.stress_level,
                    smoking=lifestyle.smoking,
                    alcohol_units_per_day=lifestyle.alcohol_units_per_day,
                    sleep_hours=lifestyle.sleep_hours,
                    diet_pattern=lifestyle.diet_pattern,
                ),
            )

    def simulate_payload(
        self,
        payload: DepthPayload,
        *,
        include_bridge: bool | None = None,
        enable_product_score: bool | None = None,
        host_context: dict[str, Any] | None = None,
        persona: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run depth always; bridge unless include_bridge=False or run_bridge=False.

        Product meal score: optional proprietary plugin (patent pending).
        Off by default; set enable_product_score=True only when private analyzer installed.
        """
        do_bridge = self.run_bridge if include_bridge is None else include_bridge
        run_score = (
            self.enable_product_score
            if enable_product_score is None
            else enable_product_score
        )
        depth_report = self.depth.simulate_payload(
            payload,
            enable_product_score=False,  # facade owns optional product score once
            host_context=host_context,
            persona=persona,
        )

        bridge_report: dict[str, Any] | None = None
        if do_bridge and self.bridge is not None:
            b_payload = depth_to_bridge_payload(payload)
            bridge_report = self.bridge.simulate_payload(
                b_payload, verbose=self.bridge_verbose
            )

        # Label teaching meter from core_sim (not product score)
        flow_meter = None
        if bridge_report and isinstance(bridge_report.get("core_sim"), dict):
            flow_meter = bridge_report["core_sim"].get("flow_score")

        product_score_analysis = run_product_score_analysis(
            payload=payload,
            depth_report=depth_report,
            bridge_report=bridge_report,
            host_context=host_context,
            persona=persona,
            enabled=bool(run_score),
        )
        depth_report["product_score_analysis"] = product_score_analysis

        merged = self._merge(depth_report, bridge_report)
        merged["flow_teaching_meter"] = flow_meter
        merged["product_score_analysis"] = product_score_analysis
        merged["product_score"] = (
            product_score_analysis.get("product_score")
            if product_score_analysis.get("available")
            else None
        )
        return {
            "facade": "UnifiedKIBOFacade",
            "depth": depth_report,
            "bridge": bridge_report,
            "merged": merged,
            "product_score_analysis": product_score_analysis,
            "claim_tier": "open",
            "notes": (
                "depth = enzyme plan + residual + pathway_regulation + minerals/DRI; "
                "bridge = LAW-tagged GI narrative + kibo_core.sim + iron walk; "
                "flow_teaching_meter = open-tier core_sim.flow_score (NOT product meal score); "
                "product_score_analysis = optional patent-pending plugin; "
                "merged = selected join fields for product consumers."
            ),
        }

    @staticmethod
    def _merge(
        depth: dict[str, Any], bridge: dict[str, Any] | None
    ) -> dict[str, Any]:
        out: dict[str, Any] = {
            "payload": depth.get("payload"),
            "engine_version": depth.get("engine_version"),
            "absorbed_macros_g": depth.get("absorbed_macros_g"),
            "residual_macros_g": depth.get("residual_macros_g"),
            "absorption_plan_totals": (depth.get("absorption_plan") or {}).get("totals"),
            "pathway_regulation": depth.get("pathway_regulation"),
            "physiological_state": depth.get("physiological_state"),
            "scfa": depth.get("scfa"),
            "mineral_absorption": depth.get("mineral_absorption"),
            "hormonal": depth.get("hormonal"),
            "energy_routing_primary": (
                (depth.get("energy_routing") or {}).get("routing") or {}
            ).get("primary_fuel_program"),
            "final_energy_charge": depth.get("final_energy_charge"),
            "claim_tiers": depth.get("claim_tiers"),
            "product_score_analysis": depth.get("product_score_analysis"),
        }
        if bridge:
            out["micelle_gate_open"] = bridge.get("micelle_gate_open")
            out["laws_cited"] = bridge.get("laws_cited")
            out["narrative_events"] = bridge.get("narrative_events")
            out["iron_walk_yield"] = bridge.get("iron_walk_yield")
            out["core_sim"] = bridge.get("core_sim")
            # Explicit rename: teaching meter ≠ product score
            cs = bridge.get("core_sim") or {}
            if isinstance(cs, dict) and "flow_score" in cs:
                out["flow_teaching_meter"] = cs.get("flow_score")
            out["bridge_energy_charge"] = bridge.get("energy_charge")
            out["refuse"] = bridge.get("refuse")
        return out


# Friendly aliases for product importers
FoodPayload = DepthPayload
LifecycleStage = DepthLifecycle
LifestyleFactors = DepthLifestyle
KIBOFacade = UnifiedKIBOFacade


def demo() -> dict[str, Any]:
    facade = UnifiedKIBOFacade(bridge_verbose=False)
    facade.apply_profile(
        DepthLifecycle.ATHLETE,
        DepthLifestyle(activity_level=1.7, stress_level=0.35),
        age_years=28,
        sex="male",
    )
    meal = DepthPayload(
        name="Facade demo mixed meal",
        quality_score=0.85,
        nutrient_density_score=0.88,
        macros_g={"carbs": 55, "protein": 35, "fats": 18},
        vitamins_mg={"c": 90, "d": 0.015, "b12": 0.002},
        minerals_mg={"fe": 10, "zn": 12, "ca": 300},
        fiber_g=22,
        protein_source="whey",
        animal_protein=True,
        ascorbate_boost=True,
        phytate_score=0.2,
    )
    report = facade.simulate_payload(meal)
    m = report["merged"]
    print("\n=== Unified facade merged summary ===")
    print("  absorbed:", m.get("absorbed_macros_g"))
    print("  residual:", m.get("residual_macros_g"))
    print("  plan totals:", m.get("absorption_plan_totals"))
    print("  pathway_regulation:", m.get("pathway_regulation"))
    print("  micelle_gate:", m.get("micelle_gate_open"))
    print("  laws_cited (first 10):", (m.get("laws_cited") or [])[:10])
    print("  iron_walk_yield:", m.get("iron_walk_yield"))
    print("  primary fuel:", m.get("energy_routing_primary"))
    return report


if __name__ == "__main__":
    demo()
