"""
kibo_engine.py
Main orchestrator for the KIBO Metabolic Simulator (v1.4 — unified).

Merges:
  A) Causal stack (pre-unify latest): signaling, gut–brain, digestive layers, causal inference
  B) Depth stack (archive package 2): minerals, enzymes, life-stage DRI, NEAT body composition,
     vitamin Engine API, fiber simulate_fermentation, hormonal update_from_meal

Pipeline for one food payload:
  protein quality → enzyme capacity → absorption plan (enzymes + dig edges) →
  GI transit → colonic medium (SI residual) → fiber/RS fermentation →
  vitamins → minerals → physiological_state + pathway_regulation →
  hormonal → energy routing → pathway network → DRI adequacy →
  gut–brain / causal / mechanism snapshot → report

Colonic medium / SCFA arithmetic is FLOW open-tier (not UNITS / LAW-SPEC).
"""

from __future__ import annotations

from biology_as_code.utils.logging import get_logger

log = get_logger(__name__)

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from biology_as_code.data.version_manifest import package_version, report_version_block
from biology_as_code.dig.digestion_capacity_routing import (
    build_absorption_plan,
    expected_residual_macros,
)
from biology_as_code.dig.digestion_flow_simulator import Bolus, DigestiveFlowSimulator
from biology_as_code.dig.digestive_definition_layer import get_digestive_definition_registry
from biology_as_code.dig.digestive_enzymes import DigestiveEnzymeSystem, GISite
from biology_as_code.dig.digestive_mechanism_layer import get_digestive_mechanism_registry

# Dig stack (GI residual, micros) — pathway graphs/mermaid live under repo pathways/ + glycolysis/
from biology_as_code.dig.fiber_rs_model import FiberProperties, FiberRSModel
from biology_as_code.dig.food_additives_registry import get_food_additives_registry
from biology_as_code.dig.mineral_interactions import MineralInteractionSystem
from biology_as_code.dig.protein_quality import (
    calculate_protein_quality,
)
from biology_as_code.dig.vitamin_absorption import VitaminAbsorptionEngine
from biology_as_code.models.causal_inference import InterventionLevel, get_causal_inference_engine

# ---------------------------------------------------------------------------
# Core
# ---------------------------------------------------------------------------
from biology_as_code.models.kibo_nutrition_ontology import KiboNutritionOntology
from biology_as_code.pathways.pathway_regulation import pathway_activity_snapshot
from biology_as_code.product_score import product_score_available, run_product_score_analysis
from biology_as_code.simulation.body_composition_energy import (
    ActivityLevel,
    AdaptiveThermogenesisModel,
    AdaptiveThermogenesisState,
    Anthropometrics,
    BodyCompositionEnergy,
    NEATProfile,
    OccupationActivity,
    Sex,
)
from biology_as_code.simulation.energy_routing import (
    build_energy_routing_report,
    physiological_state_from_meal,
)
from biology_as_code.simulation.hormonal_energy import HormonalEnergyController
from biology_as_code.simulation.hormonal_energy import MetabolicPhase as HEPhase
from biology_as_code.simulation.life_stage_dri import LifeStage as DRIStage
from biology_as_code.simulation.life_stage_dri import LifeStageDRISystem
from biology_as_code.simulation.metabolic_state import MetabolicState
from biology_as_code.simulation.organ_pathway_network import Organ, OrganPathwayNetwork

# Causal / systems stack
from biology_as_code.simulation.signaling_pathways import (
    get_gut_brain_axis,
    get_signaling_pathway_registry,
)


class LifecycleStage(StrEnum):
    INFANT = "infant"
    ADOLESCENT = "adolescent"
    ADULT = "adult"
    PREGNANT = "pregnant"
    LACTATING = "lactating"
    ELDERLY = "elderly"
    ATHLETE = "athlete"


@dataclass
class LifestyleFactors:
    activity_level: float = 1.0  # 1.0 sedentary → 2.0 elite
    stress_level: float = 0.3
    smoking: bool = False
    alcohol_units_per_day: float = 0.0
    sleep_hours: float = 7.5
    diet_pattern: str = "standard"


@dataclass
class FoodPayload:
    name: str
    nutrient_density_score: float = 0.7
    quality_score: float = 0.7
    macros_g: dict[str, float] = field(default_factory=dict)
    vitamins_mg: dict[str, float] = field(default_factory=dict)
    minerals_mg: dict[str, float] = field(default_factory=dict)
    fiber_g: float = 0.0
    fiber_properties: FiberProperties | None = None
    rs_profile: dict[str, float] = field(default_factory=lambda: {"rs2": 0.3, "rs3": 0.2})
    # Part 2: explicit fermentable share of fiber (0–1). None → resolve from
    # FiberProperties.fermentability or RS blend (see FiberRSModel.resolve_fermentable_fraction).
    fermentable_fraction: float | None = None
    protein_source: str | None = None
    anti_nutrients: float = 0.0
    # mineral-matrix meal context
    phytate_score: float = 0.0
    polyphenols: bool = False
    ascorbate_boost: bool = False
    animal_protein: bool = False
    heme_iron: bool = False
    additives: list[str] = field(default_factory=list)


@dataclass
class MicrobiomeProfile:
    diversity_score: float = 0.8
    scfa_production_factor: float = 1.0
    resistant_fraction: float = 0.05


class KIBOEngine:
    """Unified high-level controller: depth modules + causal / signaling stack."""

    # Prefer VERSION_MANIFEST.json; string kept for backward greps
    VERSION = package_version()

    def __init__(self):
        log.debug(f"Initializing KIBO Engine {self.VERSION} ...")

        # Body / NEAT
        self.body_comp = BodyCompositionEnergy()
        self.adaptive_state = AdaptiveThermogenesisState()
        self.adaptive_model = AdaptiveThermogenesisModel(self.body_comp.neat_model)

        # Core state
        self.ontology = KiboNutritionOntology()
        self.state = MetabolicState()
        self.state.load_vitamins()
        self.state.load_organ_laws()
        self.state.load_bound_conditions()

        # Digestion + depth
        self.digestion = DigestiveFlowSimulator(self.state)
        self.fiber_model = FiberRSModel()
        self.vitamin_abs = VitaminAbsorptionEngine()
        self.minerals = MineralInteractionSystem()
        self.enzymes = DigestiveEnzymeSystem()
        self.life_stage = LifeStageDRISystem()
        self.hormonal = HormonalEnergyController()
        self.pathway_net = OrganPathwayNetwork()

        # Causal / systems
        self.signaling = get_signaling_pathway_registry()
        self.gut_brain = get_gut_brain_axis()
        self.mechanisms = get_digestive_mechanism_registry()
        self.definitions = get_digestive_definition_registry()
        self.causal = get_causal_inference_engine()
        self.food_additives = get_food_additives_registry()

        # Profile
        self.lifecycle = LifecycleStage.ADULT
        self.dri_stage = DRIStage.MALE_19_50
        self.lifestyle = LifestyleFactors()
        self.microbiome = MicrobiomeProfile()
        # Last meal-derived PhysiologicalState (pathway_regulation input)
        self.physiological_state = None
        # Product meal score: optional proprietary plugin (default off unless installed)
        self.enable_product_score = False

        log.debug(
            "✅ Modules loaded: minerals, enzymes, capacity routing, DRI, NEAT, "
            "signaling, gut–brain, mechanisms, causal, pathway_regulation"
        )
        if product_score_available():
            log.debug(
                "  · proprietary product_score analyzer detected "
                "(call with enable_product_score=True to run)"
            )

    # ------------------------------------------------------------------
    # Profile
    # ------------------------------------------------------------------
    def apply_profile(
        self,
        lifecycle: LifecycleStage,
        lifestyle: LifestyleFactors,
        age_years: float = 30,
        sex: str = "male",
    ):
        """Apply lifecycle + lifestyle modifiers; resolve life-stage DRI."""
        self.lifecycle = lifecycle
        self.lifestyle = lifestyle

        pregnant = lifecycle == LifecycleStage.PREGNANT
        lactating = lifecycle == LifecycleStage.LACTATING
        athlete = lifecycle == LifecycleStage.ATHLETE
        if lifecycle == LifecycleStage.ELDERLY:
            age_years = max(age_years, 72)
        elif lifecycle == LifecycleStage.INFANT:
            age_years = 0.75
        elif lifecycle == LifecycleStage.ADOLESCENT:
            age_years = 15

        self.dri_stage = self.life_stage.resolve_stage(
            age_years, sex=sex, pregnant=pregnant, lactating=lactating, athlete=athlete
        )
        dri_profile = self.life_stage.get(self.dri_stage)

        if lifecycle == LifecycleStage.PREGNANT:
            for vid in ["folate", "b9", "iron", "c", "d", "calcium"]:
                if vid in self.state.vitamin_pool:
                    self.state.vitamin_pool[vid].adequacy = min(
                        1.0, self.state.vitamin_pool[vid].adequacy + 0.25
                    )
            self.hormonal.set_phase(HEPhase.FED)
        elif lifecycle == LifecycleStage.ATHLETE:
            self.state.energy_charge = min(1.0, self.state.energy_charge + 0.12)
            self.pathway_net.set_organ_capacity(Organ.MUSCLE, 1.25)
            self.pathway_net.set_organ_capacity(Organ.HEART, 1.20)
        elif lifecycle == LifecycleStage.ELDERLY:
            self.state.energy_charge *= 0.88
            for vid in self.state.vitamin_pool:
                self.state.vitamin_pool[vid].adequacy *= 0.92
            self.pathway_net.set_organ_capacity(Organ.GUT, 0.85)
            for k, v in dri_profile.absorption_modifiers.items():
                if k in self.state.vitamin_pool:
                    self.state.vitamin_pool[k].adequacy *= v

        if lifestyle.smoking and "c" in self.state.vitamin_pool:
            self.state.vitamin_pool["c"].adequacy *= 0.70
        if lifestyle.activity_level > 1.4:
            self.state.energy_charge = min(
                1.0, self.state.energy_charge + 0.08 * (lifestyle.activity_level - 1.0)
            )
            self.pathway_net.set_organ_capacity(
                Organ.MUSCLE, 1.0 + 0.15 * (lifestyle.activity_level - 1.0)
            )
        if lifestyle.stress_level > 0.6:
            self.state.inflammation_score = min(1.0, self.state.inflammation_score + 0.15)

        log.debug(
            f"✅ Profile: {lifecycle.value} | DRI={self.dri_stage.value} "
            f"| activity={lifestyle.activity_level}"
        )

    # ------------------------------------------------------------------
    # Causal / gut–brain views
    # ------------------------------------------------------------------
    def gut_brain_status(
        self, stress_level: float | None = None, inflammation: float | None = None
    ) -> dict[str, Any]:
        """Lightweight gut–brain axis state for reporting."""
        stress = self.lifestyle.stress_level if stress_level is None else stress_level
        inflam = self.state.inflammation_score if inflammation is None else inflammation
        barrier_stress = min(1.0, stress * 0.6 + inflam * 0.5)
        serotonin_shift = max(0.0, inflam * 0.7)

        return {
            "gut_brain_axis_pathways": self.gut_brain.summary(),
            "active_afferent_count": len(self.gut_brain.afferent_pathways),
            "active_efferent_count": len(self.gut_brain.efferent_pathways),
            "stress_barrier_impact": round(barrier_stress, 3),
            "tryptophan_kynurenine_shift": round(serotonin_shift, 3),
            "key_pathways_loaded": [
                "vagal_afferent_pathway",
                "vagal_efferent_pathway",
                "crf_stress_permeability_pathway",
                "tryptophan_serotonin_kynurenine_pathway",
                "incretin_pathway",
                "gpr109a_hdac_pathway",
            ],
            "notes": (
                "Higher stress/inflammation increases permeability "
                "and shifts tryptophan toward kynurenine."
            ),
        }

    def causal_snapshot(self, payload: FoodPayload | None = None) -> dict[str, Any]:
        """
        Brief causal-inference view after a meal (or baseline).
        Maps coarse nutrient adequacy → InterventionLevel for explain/summary.
        """
        snap: dict[str, Any] = {
            "engine": "causal_inference",
            "summary": self.causal.summary() if hasattr(self.causal, "summary") else {},
        }
        # Example interventions from current vitamin pool
        examples = {}
        for key in ("c", "b12", "d", "iron", "folate", "b9"):
            if key not in self.state.vitamin_pool:
                continue
            adeq = self.state.vitamin_pool[key].adequacy
            if adeq < 0.5:
                level = InterventionLevel.DEPLETED
            elif adeq < 0.75:
                level = InterventionLevel.LOW
            elif adeq < 1.05:
                level = InterventionLevel.ADEQUATE
            else:
                level = InterventionLevel.HIGH
            try:
                if hasattr(self.causal, "intervene"):
                    # nutrient id conventions may vary; best-effort
                    nid = "vitamin_c" if key == "c" else key
                    examples[key] = {
                        "adequacy": round(adeq, 3),
                        "level": level.value,
                        "result": str(self.causal.intervene(nid, level))[:200],
                    }
                else:
                    examples[key] = {"adequacy": round(adeq, 3), "level": level.value}
            except Exception as exc:
                examples[key] = {
                    "adequacy": round(adeq, 3),
                    "level": level.value,
                    "note": f"intervene skipped: {exc}",
                }
        snap["pool_interventions"] = examples
        if payload is not None:
            snap["payload"] = payload.name
            snap["fiber_g"] = payload.fiber_g
            snap["anti_nutrients"] = payload.anti_nutrients
        return snap

    def systems_layer_status(self) -> dict[str, Any]:
        """Registry sizes for digestive mechanisms / definitions / signaling."""
        out: dict[str, Any] = {}
        if hasattr(self.mechanisms, "summary"):
            out["digestive_mechanisms"] = self.mechanisms.summary()
        elif hasattr(self.mechanisms, "list_ids"):
            out["digestive_mechanisms"] = {"count": len(self.mechanisms.list_ids())}
        if hasattr(self.definitions, "summary"):
            out["digestive_definitions"] = self.definitions.summary()
        if hasattr(self.signaling, "summary"):
            out["signaling"] = self.signaling.summary()
        return out

    # ------------------------------------------------------------------
    # Full meal pipeline
    # ------------------------------------------------------------------
    def simulate_payload(
        self,
        payload: FoodPayload,
        *,
        enable_product_score: bool | None = None,
        host_context: dict[str, Any] | None = None,
        persona: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Full unified pipeline for one food payload.

        Product meal score is **optional** and only runs when proprietary
        analysis is installed **and** enable_product_score is True
        (or self.enable_product_score). Open dig path never requires it.
        """
        log.debug(f"\n=== Simulating payload: {payload.name} ===")
        report: dict[str, Any] = {
            "payload": payload.name,
            "engine_version": self.VERSION,
            "package_version": report_version_block(),
        }

        # 1. Protein quality
        if payload.protein_source:
            pq = calculate_protein_quality(payload.protein_source)
            report["protein_quality"] = {
                "pdcaas": pq.pdcaas,
                "diaas": pq.diaas,
                "limiting_aa": pq.limiting_amino_acid,
                "notes": pq.notes,
                "quality_category": pq.quality_category,
            }
            log.debug(
                f"  Protein quality ({payload.protein_source}): "
                f"DIAAS={pq.diaas:.3f}, limiting={pq.limiting_amino_acid}"
            )

        # 2. Enzyme capacity (duodenum + jejunum) + absorption plan
        enz_ctx = self._enzyme_context_for_payload(payload)
        report["enzyme_capacity"] = {
            "duodenum": self.enzymes.site_digestive_capacity(GISite.DUODENUM, enz_ctx),
            "jejunum": self.enzymes.site_digestive_capacity(GISite.JEJUNUM, enz_ctx),
        }
        abs_plan = build_absorption_plan(
            self.enzymes,
            macros_g=dict(payload.macros_g),
            enzyme_context=enz_ctx,
            quality_score=payload.quality_score,
        )
        report["absorption_plan"] = abs_plan.as_dict()
        log.debug(
            f"  Absorption plan (capacity): "
            f"CHO={abs_plan.total_carbs:.2f} PRO={abs_plan.total_protein:.2f} "
            f"FAT={abs_plan.total_fats:.2f} | edges={len(abs_plan.edge_trace)}"
        )

        # 3. GI transit (capacity-driven segment fractions)
        bolus = Bolus(
            macros_g=dict(payload.macros_g),
            vitamins_mg=dict(payload.vitamins_mg),
            fiber_g=payload.fiber_g,
            volume_ml=700.0,
            nutrient_density=payload.nutrient_density_score,
            quality_score=payload.quality_score,
        )
        events = self.digestion.simulate_full_transit(
            bolus, verbose=False, absorption_plan=abs_plan
        )
        report["transit_events"] = len(events)
        report["transit_capacity_driven"] = True
        absorbed_totals = self._sum_absorbed_macros(events)
        report["absorbed_macros_g"] = absorbed_totals

        # 3b. SI residual → colonic medium envelope (Part 3 filter on Part 2 packet)
        residual_macros = self._si_residual_macros(events, payload)
        planned_residual = expected_residual_macros(payload.macros_g or {}, abs_plan)
        report["residual_macros_g"] = residual_macros
        report["residual_macros_planned_g"] = planned_residual
        colonic_medium = self.fiber_model.project_colonic_medium(
            total_fiber_g=payload.fiber_g,
            fermentable_fraction=payload.fermentable_fraction,
            fiber_properties=payload.fiber_properties,
            rs_profile=payload.rs_profile,
            residual_macros_g=residual_macros,
        )
        report["colonic_medium"] = colonic_medium.as_dict()
        log.debug(
            f"  Absorbed macros g: {absorbed_totals} | residual SI: {residual_macros}"
        )
        log.debug(
            f"  Colonic medium: fermentable {colonic_medium.fermentable_fiber_g:.1f} g "
            f"of {colonic_medium.fiber_g:.1f} g fiber "
            f"(frac={colonic_medium.fermentable_fraction:.2f}); "
            f"residual macros={residual_macros}"
        )

        # 4. Fiber / RS fermentation on *fermentable* colon substrate (not raw packet fiber)
        if colonic_medium.fermentable_fiber_g > 0:
            rs_result = self.fiber_model.simulate_fermentation(
                total_fiber_g=colonic_medium.fermentable_fiber_g,
                rs_profile=colonic_medium.rs_profile,
                microbiome_diversity=self.microbiome.diversity_score,
                viscosity=colonic_medium.viscosity,
            )
            rs_result["colonic_medium"] = colonic_medium.as_dict()
            report["scfa"] = rs_result
            self.state.energy_charge = min(
                1.0, self.state.energy_charge + rs_result.get("total_scfa_kcal", 0) / 150
            )
            butyrate_frac = rs_result.get("butyrate_fraction", 0.15)
            anti_inflam = butyrate_frac * 1.4 * self.microbiome.diversity_score
            self.state.inflammation_score = max(
                0.0, self.state.inflammation_score - anti_inflam * 0.4
            )
            log.debug(
                f"  SCFA: {rs_result.get('total_scfa_kcal', 0):.1f} kcal | "
                f"butyrate fraction={butyrate_frac:.2f} "
                f"(from colonic fermentable substrate)"
            )

        # 5. Vitamin absorption
        abs_result = self.vitamin_abs.absorb(
            intake_mg=payload.vitamins_mg,
            food_matrix_quality=payload.quality_score,
            fiber_viscosity=(
                payload.fiber_properties.viscosity if payload.fiber_properties else 0.3
            ),
            current_pool={k: v.adequacy for k, v in self.state.vitamin_pool.items()},
            context={
                "dietary_fat_g": payload.macros_g.get("fats", 10),
                "bile_present": True,
            },
        )
        for vid, new_adeq in abs_result.get("updated_adequacy", {}).items():
            if vid in self.state.vitamin_pool:
                self.state.vitamin_pool[vid].adequacy = float(new_adeq)
        # Keep coenzyme factors aligned so apply_vitamin_modifiers is not a no-op
        if hasattr(self.state, "sync_coenzyme_from_adequacy"):
            self.state.sync_coenzyme_from_adequacy()
        report["vitamin_absorption"] = abs_result
        log.debug(
            f"  Vitamins | interactions: {abs_result.get('interactions_triggered', [])}"
        )

        # 6. Mineral interactions
        min_ctx = {
            "phytate_score": payload.phytate_score or payload.anti_nutrients,
            "polyphenols": payload.polyphenols,
            "ascorbate": payload.ascorbate_boost
            or payload.vitamins_mg.get("c", 0) > 30,
            "animal_protein": payload.animal_protein
            or (payload.protein_source in ("whey", "casein", "egg", "beef")),
            "heme_iron": payload.heme_iron,
            "stomach_acid": True,
            "vitamin_d": payload.vitamins_mg.get("d", 0) > 0.005,
        }
        if payload.minerals_mg:
            min_results = self.minerals.process_meal_minerals(
                payload.minerals_mg, min_ctx
            )
            report["mineral_absorption"] = {
                k: {
                    "absorbed": round(v.absorbed_amount, 3),
                    "fraction": round(v.absorbed_fraction, 3),
                    "limiting": v.limiting_factors,
                    "enhanced": v.enhanced_by,
                }
                for k, v in min_results.items()
            }
            log.debug(
                "  Minerals: "
                + ", ".join(
                    f"{k}={v.absorbed_fraction * 100:.0f}%"
                    for k, v in min_results.items()
                )
            )

        # 7. Physiological state + pathway_regulation (explicit engine wiring)
        phys = physiological_state_from_meal(
            carbs_g=payload.macros_g.get("carbs", 0),
            protein_g=payload.macros_g.get("protein", 0),
            fat_g=payload.macros_g.get("fats", 0),
            fiber_g=payload.fiber_g,
            quality_score=payload.quality_score,
        )
        # Soft host tilt from lifestyle stress / activity
        phys.host.stress_level = self.lifestyle.stress_level
        phys.inflammation = max(phys.inflammation, self.state.inflammation_score)
        if self.lifestyle.activity_level > 1.5:
            phys.hormones.epinephrine = max(
                phys.hormones.epinephrine, 0.4 + 0.3 * (self.lifestyle.activity_level - 1.0)
            )
        self.physiological_state = phys
        path_acts = pathway_activity_snapshot(phys)
        report["physiological_state"] = phys.summary()
        report["pathway_regulation"] = path_acts
        try:
            from biology_as_code.pathways.pathway_regulation import nutrient_sensing_snapshot
            report["nutrient_sensing"] = nutrient_sensing_snapshot(phys)
        except Exception as exc:
            log.debug("nutrient_sensing snapshot skipped: %s", exc)
        log.debug(
            f"  Pathway regulation: glycolysis={path_acts.get('glycolysis')} "
            f"β-ox={path_acts.get('beta_oxidation')} "
            f"ketogenesis={path_acts.get('ketogenesis')} "
            f"(I/G={phys.hormones.insulin_glucagon_ratio:.2f})"
        )

        # 7b. Hormonal / energy homeostasis
        he_report = self.hormonal.update_from_meal(
            carbs_g=payload.macros_g.get("carbs", 0),
            protein_g=payload.macros_g.get("protein", 0),
            fat_g=payload.macros_g.get("fats", 0),
            fiber_g=payload.fiber_g,
        )
        report["hormonal"] = he_report
        self.state.energy_charge = min(
            1.0, self.state.energy_charge * he_report.get("energy_multiplier", 1.0)
        )

        # 7c. Energy routing (reuses same phys state → pathway_regulation)
        routing = build_energy_routing_report(
            carbs_g=payload.macros_g.get("carbs", 0),
            protein_g=payload.macros_g.get("protein", 0),
            fat_g=payload.macros_g.get("fats", 0),
            fiber_g=payload.fiber_g,
            quality_score=payload.quality_score,
            state=phys,
        )
        report["energy_routing"] = routing
        log.debug(
            f"  Energy routing: {routing['routing'].get('primary_fuel_program')} | "
            f"glycolysis={routing['pathway_activity'].get('glycolysis')} "
            f"β-ox={routing['pathway_activity'].get('beta_oxidation')}"
        )

        # 8. Pathway network (scaled softly by regulation activities)
        vit_adeq = {k: v.adequacy for k, v in self.state.vitamin_pool.items()}
        self.pathway_net.apply_vitamin_cofactors(vit_adeq)
        self.pathway_net.apply_inflammation(self.state.inflammation_score)
        self._apply_regulation_to_pathway_net(path_acts)
        report["pathway_network"] = self.pathway_net.summary()

        # 9. Life-stage DRI adequacy
        intake_for_dri = {**payload.vitamins_mg, **payload.minerals_mg}
        report["dri_adequacy"] = self.life_stage.adequacy(
            self.dri_stage, intake_for_dri
        )

        # 10. Causal / gut–brain / systems layers
        report["gut_brain"] = self.gut_brain_status()
        report["systems_layers"] = self.systems_layer_status()
        report["causal"] = self.causal_snapshot(payload)

        if payload.additives:
            report["additive_effects"] = self.food_additives.effects_for_additives(
                payload.additives
            )
        else:
            report["additive_effects"] = {"matches": [], "unique_effect_tags": []}

        report["colon_scfa_units"] = self._colon_scfa_units_walk(
            fermentable_fraction=float(
                report.get("colonic_medium", {}).get("fermentable_fraction", 0.55)
            ),
            microbiome_diversity=self.microbiome.diversity_score,
        )

        # Claim-tier labels: which report fields are FLOW vs provisional UNITS
        report["claim_tiers"] = {
            "scfa": "flow",
            "colonic_medium": "flow",
            "absorption_plan": "flow",
            "pathway_regulation": "flow",
            "physiological_state": "flow",
            "energy_routing": "flow",
            "colon_scfa_units": "units_provisional",
            "additive_effects": "flow_qualitative",
            "product_score_analysis": "proprietary_optional",
            "notes": (
                "flow = teaching sim numbers; units_provisional = formal walk, "
                "magnitude not locked; product_score_analysis is patent-pending "
                "optional plugin (not open dig FLOW). "
                "use evidence_pubmed.pack_for_law for PMIDs"
            ),
        }

        # 11. Final state
        self.state.apply_vitamin_modifiers()
        self.state.enforce_bounds()
        report["final_energy_charge"] = round(self.state.energy_charge, 3)
        report["inflammation_score"] = round(self.state.inflammation_score, 3)
        report["deficiency_symptoms"] = self.state.get_deficiency_symptoms()
        report["lifecycle"] = self.lifecycle.value
        report["dri_stage"] = self.dri_stage.value

        # 12. Optional proprietary product meal-score analysis (patent pending)
        run_score = (
            self.enable_product_score
            if enable_product_score is None
            else enable_product_score
        )
        # Only attempt if explicitly enabled (avoids implying product score in open demos)
        report["product_score_analysis"] = run_product_score_analysis(
            payload=payload,
            depth_report=report,
            host_context=host_context
            or {
                "lifecycle": self.lifecycle.value,
                "lifestyle": {
                    "activity": self.lifestyle.activity_level,
                    "stress": self.lifestyle.stress_level,
                },
                "dri_stage": self.dri_stage.value,
            },
            persona=persona,
            enabled=bool(run_score),
        )
        psa = report["product_score_analysis"]
        if psa.get("available"):
            log.debug(
                f"  Product score (proprietary): {psa.get('product_score')} "
                f"status={psa.get('status')}"
            )
        elif run_score:
            log.debug(
                f"  Product score: unavailable ({psa.get('status')}) — "
                "open dig complete without patent module"
            )
        else:
            log.debug(
                "  Product meal score / Kibo-vars scorer: skipped "
                "(enable_product_score=False) — open dig + FLOW evals only"
            )

        log.debug(
            f"  Final energy_charge={report['final_energy_charge']} | "
            f"inflammation={report['inflammation_score']}"
        )
        return report

    def _colon_scfa_units_walk(
        self,
        *,
        fermentable_fraction: float,
        microbiome_diversity: float,
    ) -> dict[str, Any]:
        try:
            from biology_as_code.data.kibo_core.laws import walk_pathway
            from biology_as_code.data.kibo_core.pathways import (
                COLON_SCFA_PATHWAY,
                colon_scfa_context_from_engine,
            )

            ctx = colon_scfa_context_from_engine(
                fermentable_fraction=fermentable_fraction,
                microbiome_diversity=microbiome_diversity,
            )
            result = walk_pathway(
                COLON_SCFA_PATHWAY,
                "colon.residue_arrival",
                context=ctx,
            )
            return {
                "tier": "UNITS_skeleton",
                "magnitude_locked": False,
                "yield_factor": round(result.yield_factor, 4),
                "path": list(result.path),
                "context": ctx,
            }
        except Exception as exc:
            return {
                "tier": "UNITS_skeleton",
                "error": str(exc),
                "magnitude_locked": False,
            }

    # ------------------------------------------------------------------
    # Body composition convenience
    # ------------------------------------------------------------------
    def body_energy_report(
        self,
        sex: str = "male",
        age: float = 30,
        weight_kg: float = 80,
        height_cm: float = 178,
        body_fat_percent: float | None = None,
        activity: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE,
        occupation: OccupationActivity = OccupationActivity.DESK,
    ) -> dict[str, Any]:
        """Chapter 8: BMR / TDEE / NEAT / adaptive summary."""
        sx = Sex.MALE if sex.lower().startswith("m") else Sex.FEMALE
        anthro = Anthropometrics(
            sex=sx,
            age_years=age,
            weight_kg=weight_kg,
            height_cm=height_cm,
            body_fat_percent=body_fat_percent,
        )
        self.body_comp.set_neat_profile(
            NEATProfile(
                occupation=occupation, steps_per_day=7000, fidgeting_score=0.45
            )
        )
        return self.body_comp.full_report(anthro, activity)

    def _enzyme_context_for_payload(self, payload: FoodPayload) -> dict[str, Any]:
        """Default healthy enzyme context; overridable via payload attributes later."""
        fats = float((payload.macros_g or {}).get("fats") or 0)
        ctx: dict[str, Any] = {
            "bile_salts": 0.85 if fats > 5 else 0.5,
            "colipase": True,
            "trypsin_active": True,
            "pancreatic_capacity": 1.0,
            "zn_adequate": True,
            "lactase_persistent": True,
            "cl_present": True,
            "ca_present": True,
            "ppi": False,
        }
        # Optional host/meal overrides on FoodPayload (soft API)
        for key in (
            "bile_salts",
            "colipase",
            "trypsin_active",
            "pancreatic_capacity",
            "zn_adequate",
            "lactase_persistent",
            "ppi",
        ):
            if hasattr(payload, key):
                val = getattr(payload, key)
                if val is not None:
                    ctx[key] = val
        return ctx

    def _apply_regulation_to_pathway_net(self, path_acts: dict[str, float]) -> None:
        """Soft organ capacity tilt from pathway_regulation activities (FLOW)."""
        try:
            glycol = float(path_acts.get("glycolysis") or 0.5)
            box = float(path_acts.get("beta_oxidation") or 0.5)
            # Muscle / liver respond to fuel program
            self.pathway_net.set_organ_capacity(
                Organ.MUSCLE, 0.85 + 0.35 * max(glycol, box)
            )
            self.pathway_net.set_organ_capacity(
                Organ.LIVER, 0.85 + 0.30 * float(path_acts.get("gluconeogenesis") or 0.3)
            )
            self.pathway_net.set_organ_capacity(
                Organ.ADIPOSE,
                0.8 + 0.4 * float(path_acts.get("fatty_acid_synthesis") or 0.2),
            )
        except Exception as exc:
            log.debug("pathway-net regulation tilt skipped: %s", exc)

    @staticmethod
    def _sum_absorbed_macros(events: list[Any]) -> dict[str, float]:
        totals = {"carbs": 0.0, "protein": 0.0, "fats": 0.0}
        for ev in events or []:
            absd = getattr(ev, "absorbed", None) or {}
            for k in totals:
                if k in absd:
                    totals[k] += float(absd[k] or 0)
        return {k: round(v, 3) for k, v in totals.items()}

    @staticmethod
    def _si_residual_macros(
        events: list[Any], payload: FoodPayload
    ) -> dict[str, float]:
        """
        Macros remaining after small intestine (ileum remaining_bolus if present).
        Fiber is handled separately on the packet (mostly not SI-absorbed).
        """
        for ev in reversed(events or []):
            seg = getattr(ev, "segment", None)
            name = getattr(seg, "value", str(seg) if seg is not None else "")
            if name == "Ileum" or name == "ILEUM":
                rem = getattr(ev, "remaining_bolus", None) or {}
                return {
                    "carbs": round(float(rem.get("carbs", 0.0)), 3),
                    "protein": round(float(rem.get("protein", 0.0)), 3),
                    "fats": round(float(rem.get("fats", 0.0)), 3),
                }
        # Fallback: rough SI strip if history missing
        m = payload.macros_g or {}
        return {
            "carbs": float(m.get("carbs", 0.0)) * 0.15,
            "protein": float(m.get("protein", 0.0)) * 0.20,
            "fats": float(m.get("fats", 0.0)) * 0.15,
        }

    # ------------------------------------------------------------------
    # Demo
    # ------------------------------------------------------------------
    def run_quick_demo(self):
        """Two contrasting payloads exercising minerals + causal + SCFA."""
        self.apply_profile(
            LifecycleStage.ATHLETE,
            LifestyleFactors(activity_level=1.7, stress_level=0.4),
            age_years=28,
            sex="male",
        )

        high = FoodPayload(
            name="High-RS whole-food athlete meal",
            nutrient_density_score=0.92,
            quality_score=0.95,
            macros_g={"carbs": 65, "protein": 40, "fats": 18},
            vitamins_mg={"c": 140, "b1": 1.8, "folate": 0.4, "d": 0.02},
            minerals_mg={"fe": 12, "zn": 14, "ca": 350, "mg": 280, "cu": 1.0},
            fiber_g=35,
            rs_profile={"rs2": 0.45, "rs3": 0.35},
            fermentable_fraction=0.80,
            fiber_properties=FiberProperties(
                viscosity=0.35, fermentability=0.80, solubility=0.2
            ),
            protein_source="whey",
            animal_protein=True,
            ascorbate_boost=True,
            phytate_score=0.15,
        )
        low = FoodPayload(
            name="Ultra-processed low-fiber meal",
            nutrient_density_score=0.25,
            quality_score=0.20,
            macros_g={"carbs": 85, "protein": 12, "fats": 28},
            vitamins_mg={"c": 8},
            minerals_mg={"fe": 4, "zn": 3, "ca": 80, "mg": 40, "cu": 0.3},
            fiber_g=4,
            rs_profile={"rs2": 0.05, "rs3": 0.02},
            fermentable_fraction=0.35,
            fiber_properties=FiberProperties(
                viscosity=0.1, fermentability=0.35, solubility=0.4
            ),
            protein_source="wheat",
            anti_nutrients=0.55,
            phytate_score=0.7,
            polyphenols=True,
        )

        log.debug("\n" + "=" * 60)
        r1 = self.simulate_payload(high)
        log.debug("\n" + "=" * 60)
        r2 = self.simulate_payload(low)

        log.debug("\n" + "=" * 60)
        log.debug("Body composition / NEAT snapshot")
        log.debug(
            self.body_energy_report(
                sex="male",
                age=28,
                weight_kg=82,
                height_cm=180,
                body_fat_percent=12,
                activity=ActivityLevel.VERY_ACTIVE,
            )
        )
        return r1, r2


if __name__ == "__main__":
    engine = KIBOEngine()
    engine.run_quick_demo()
