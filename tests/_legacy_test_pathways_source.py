"""
test_pathways.py
=================================================================
Minimal verification for KIBO metabolic pathway models.

Run:
    python test_pathways.py
=================================================================
"""

from __future__ import annotations

import sys
from typing import Any, Callable, List

from metabolic_pathways import get_metabolic_pathways_registry
from tca_cycle import get_tca_cycle_registry
from etc_oxphos import get_etc_oxphos_registry
from beta_oxidation import get_beta_oxidation_registry
from gluconeogenesis import get_gluconeogenesis_registry
from urea_cycle import get_urea_cycle_registry
from pentose_phosphate import get_pentose_phosphate_registry
from glycogen_metabolism import get_glycogen_metabolism_registry
from cholesterol_pathway import get_cholesterol_pathway_registry
from fatty_acid_synthesis import get_fatty_acid_synthesis_registry
from ketogenesis import get_ketogenesis_registry
from digestion_absorption_pathways import get_digestion_absorption_registry
from supporting_pathways import get_supporting_pathways_registry
from metabolic_mechanisms import get_metabolic_mechanism_registry
from nitrogen_balance import NitrogenBalance
from respiratory_quotient import RespiratoryQuotient
from fiber_rs_model import FiberRSModel, FiberProperties


def _pathways_from(reg: Any) -> List[Any]:
    if hasattr(reg, "list_all"):
        return list(reg.list_all())
    if hasattr(reg, "pathways"):
        return list(reg.pathways.values())
    return []


def test_glycolysis_energy_balance():
    pathway = get_metabolic_pathways_registry().get("glycolysis")
    summary = pathway.summary()
    assert summary["net_atp"] == 2, f"Expected +2 ATP, got {summary['net_atp']}"
    assert summary["net_nadh"] == 2, f"Expected +2 NADH, got {summary['net_nadh']}"
    print("✓ Glycolysis energy balance correct (+2 ATP, +2 NADH)")


def test_glycolysis_key_mechanisms_linked():
    pathway = get_metabolic_pathways_registry().get("glycolysis")
    linked_ids = {e.mechanism_id for e in pathway.edges if getattr(e, "mechanism_id", "")}
    required = {"hexokinase", "pfk1", "pyruvate_kinase"}
    missing = required - linked_ids
    assert not missing, f"Missing mechanism links: {missing}"
    print("✓ Glycolysis key mechanisms are formally linked")


def test_tca_energy_yield():
    pathway = get_tca_cycle_registry().get("tca_cycle")
    s = pathway.summary()
    assert s["nadh_per_acetyl_coa"] == 3
    assert s["fadh2_per_acetyl_coa"] == 1
    assert s["gtp_per_acetyl_coa"] == 1
    print("✓ TCA cycle energy yield correct (3 NADH + 1 FADH₂ + 1 GTP)")


def test_tca_all_steps_linked():
    pathway = get_tca_cycle_registry().get("tca_cycle")
    linked = [e for e in pathway.edges if getattr(e, "mechanism_id", "")]
    assert len(linked) == 8, f"Expected 8 linked edges, found {len(linked)}"
    print("✓ All 8 TCA steps are formally linked to mechanisms")


def test_etc_oxphos_p_ratios():
    pathway = get_etc_oxphos_registry().get("etc_oxphos")
    s = pathway.summary()
    assert s["atp_per_nadh"] == 2.5
    assert s["atp_per_fadh2"] == 1.5
    print("✓ ETC/OxPhos P/O ratios present (2.5 / 1.5)")


def test_beta_oxidation_cycle_yield():
    pathway = get_beta_oxidation_registry().get("beta_oxidation")
    s = pathway.summary()
    assert "NADH" in s["per_cycle"] and "FADH" in s["per_cycle"]
    print("✓ β-Oxidation per-cycle yield stated")


def test_cholesterol_hmgcr_linked():
    pathway = get_cholesterol_pathway_registry().get("cholesterol_biosynthesis")
    hmg_edges = [e for e in pathway.edges if getattr(e, "mechanism_id", "") == "hmg_coa_reductase"]
    assert len(hmg_edges) == 1, "HMG-CoA reductase edge missing or not linked"
    print("✓ HMG-CoA reductase is formally linked")


def test_urea_cycle_cost():
    pathway = get_urea_cycle_registry().get("urea_cycle")
    assert pathway.summary()["atp_per_urea"] == 4
    print("✓ Urea cycle ATP cost correct")


def test_gluconeogenesis_cost():
    pathway = get_gluconeogenesis_registry().get("gluconeogenesis")
    assert pathway.summary()["atp_equivalents_per_glucose"] == 6
    print("✓ Gluconeogenesis ATP cost correct")


def test_ppp_nadph():
    pathway = get_pentose_phosphate_registry().get("pentose_phosphate")
    assert pathway.summary()["nadph_per_g6p_oxidative"] == 2
    print("✓ PPP oxidative NADPH yield correct")


def test_fas_palmitate_costs():
    pathway = get_fatty_acid_synthesis_registry().get("fatty_acid_synthesis")
    s = pathway.summary()
    assert "14" in str(s.get("nadph_required", ""))
    assert "7" in str(s.get("atp_required", ""))
    print("✓ FAS NADPH/ATP teaching costs present")


def test_ketogenesis_products():
    pathway = get_ketogenesis_registry().get("ketogenesis")
    products = pathway.summary().get("main_products", "")
    assert "Acetoacetate" in products or "acetoacetate" in products.lower()
    print("✓ Ketogenesis main products present")


def test_glycogen_key_enzymes():
    pathway = get_glycogen_metabolism_registry().get("glycogen_metabolism")
    s = pathway.summary()
    assert "synthase" in s.get("synthesis_key_enzyme", "").lower()
    assert "phosphorylase" in s.get("breakdown_key_enzyme", "").lower()
    print("✓ Glycogen key enzymes named")


def test_digestion_absorption_suite():
    reg = get_digestion_absorption_registry()
    required = {
        "carb_digestion_absorption",
        "protein_digestion_absorption",
        "lipid_digestion_absorption",
        "brush_border_final_digestion",
        "enterohepatic_bile",
        "bile_acid_synthesis",
    }
    names = {p.name.lower() for p in reg.list_all()}
    missing = required - names
    assert not missing, f"Missing dig pathways: {missing}"
    carb = reg.get("carb_digestion_absorption")
    assert any(getattr(e, "mechanism_id", "") == "sglt1" for e in carb.edges)
    print("✓ Digestion/absorption suite complete (incl. bile + brush border)")


def test_supporting_pathways_suite():
    reg = get_supporting_pathways_registry()
    required = {
        "cori_glucose_alanine",
        "redox_shuttles",
        "fructose_galactose",
        "secondary_bile_acids",
        "prebiotic_probiotic",
        "fuel_selection_hierarchy",
    }
    names = {p.name.lower() for p in reg.list_all()}
    missing = required - names
    assert not missing, f"Missing supporting pathways: {missing}"
    print("✓ Supporting pathways suite present")


def test_all_pathways_have_nodes_and_edges():
    registries = [
        get_metabolic_pathways_registry(),
        get_tca_cycle_registry(),
        get_etc_oxphos_registry(),
        get_beta_oxidation_registry(),
        get_gluconeogenesis_registry(),
        get_urea_cycle_registry(),
        get_pentose_phosphate_registry(),
        get_glycogen_metabolism_registry(),
        get_cholesterol_pathway_registry(),
        get_fatty_acid_synthesis_registry(),
        get_ketogenesis_registry(),
        get_digestion_absorption_registry(),
        get_supporting_pathways_registry(),
    ]
    count = 0
    for reg in registries:
        for pathway in _pathways_from(reg):
            if pathway is None:
                continue
            assert len(pathway.nodes) > 0, f"{pathway.name} has no nodes"
            assert len(pathway.edges) > 0, f"{pathway.name} has no edges"
            for edge in pathway.edges:
                assert edge.from_node in pathway.nodes, f"{pathway.name}: {edge.from_node} missing"
                assert edge.to_node in pathway.nodes, f"{pathway.name}: {edge.to_node} missing"
            count += 1
    print(f"✓ All {count} pathways have valid nodes and connected edges")


def test_mechanism_registry_populated():
    reg = get_metabolic_mechanism_registry()
    required = [
        "hexokinase", "pfk1", "pyruvate_kinase",
        "hmg_coa_reductase", "citrate_synthase",
        "isocitrate_dehydrogenase", "pancreatic_lipase", "sglt1",
    ]
    for mid in required:
        assert reg.get(mid) is not None, f"Mechanism {mid} is missing from registry"
    print(f"✓ Mechanism registry contains {len(reg.list_all())} mechanisms (core set present)")


def test_nitrogen_balance_signs():
    pos = NitrogenBalance(intake_g=14.0, excretion_g=12.0)
    assert pos.calculate().startswith("positive")
    neg = NitrogenBalance(intake_g=8.0, excretion_g=12.0)
    assert neg.calculate().startswith("negative")
    eq = NitrogenBalance(intake_g=12.0, excretion_g=12.0)
    assert eq.calculate().startswith("equilibrium")
    print("✓ Nitrogen balance signs correct")


def test_respiratory_quotient_bounds():
    pure_carb = RespiratoryQuotient(co2_produced_ml=100, o2_consumed_ml=100)
    assert pure_carb.calculate() == 1.0
    pure_fat = RespiratoryQuotient(co2_produced_ml=70, o2_consumed_ml=100)
    assert abs(pure_fat.calculate() - 0.7) < 1e-9
    print("✓ RQ pure-carb / pure-fat bounds correct")


def test_colonic_medium_and_scfa_flow():
    m = FiberRSModel()
    med = m.project_colonic_medium(
        20.0,
        fermentable_fraction=0.7,
        fiber_properties=FiberProperties(viscosity=0.3, fermentability=0.7),
        rs_profile={"rs2": 0.4, "rs3": 0.3},
        residual_macros_g={"carbs": 2.0, "protein": 1.0, "fats": 0.5},
    )
    assert abs(med.fermentable_fiber_g - 14.0) < 1e-9
    scfa = m.simulate_fermentation(
        total_fiber_g=med.fermentable_fiber_g,
        rs_profile=med.rs_profile,
        viscosity=med.viscosity,
    )
    assert scfa["total_scfa_kcal"] > 0
    assert scfa["substrate_fiber_g"] == 14.0
    print("✓ Colonic medium → SCFA FLOW handoff correct")


def test_energy_routing_snapshot():
    from energy_routing import build_energy_routing_report

    r = build_energy_routing_report(60, 30, 15, fiber_g=12, quality_score=0.8)
    assert "glycolysis" in r["pathway_activity"]
    assert "ampk" in r["pathway_activity"]
    assert r["routing"]["primary_fuel_program"]
    print("✓ Energy routing snapshot present")


def test_colon_scfa_units_walk():
    from kibo_core.laws import walk_pathway
    from kibo_core.pathways import COLON_SCFA_PATHWAY, colon_scfa_context_from_engine

    ctx = colon_scfa_context_from_engine(
        fermentable_fraction=0.8, microbiome_diversity=0.9
    )
    res = walk_pathway(COLON_SCFA_PATHWAY, "colon.residue_arrival", context=ctx)
    assert res.yield_factor > 1.0
    assert "colon.fermentation" in res.path
    print("✓ Colon SCFA UNITS walk runs")


def test_additive_effect_hooks():
    from food_additives_registry import get_food_additives_registry

    out = get_food_additives_registry().effects_for_additives(["lecithin", "MSG"])
    assert out["matches"]
    assert out["unique_effect_tags"]
    print("✓ Food additive effect hooks resolve")


def test_engine_energy_routing_keys():
    from kibo_engine import KIBOEngine, FoodPayload
    import digestion_flow_simulator as dfs

    _orig = dfs.DigestiveFlowSimulator.simulate_full_transit

    def quiet(self, bolus, verbose=False, absorption_plan=None, **kwargs):
        return _orig(
            self, bolus, verbose=False, absorption_plan=absorption_plan, **kwargs
        )

    dfs.DigestiveFlowSimulator.simulate_full_transit = quiet
    try:
        eng = KIBOEngine()
        r = eng.simulate_payload(
            FoodPayload(
                name="routing test",
                macros_g={"carbs": 55, "protein": 25, "fats": 12},
                fiber_g=18,
                fermentable_fraction=0.75,
                additives=["polysorbate 80"],
            )
        )
        assert "energy_routing" in r
        assert "colon_scfa_units" in r
        assert r["colon_scfa_units"].get("magnitude_locked") is False
        assert "absorption_plan" in r
        assert "pathway_regulation" in r
        assert r.get("transit_capacity_driven") is True
        print("✓ Engine energy_routing + colon_scfa_units + capacity plan keys")
    finally:
        dfs.DigestiveFlowSimulator.simulate_full_transit = _orig


def run_all_tests() -> bool:
    print("=" * 60)
    print("KIBO PATHWAY MODEL VERIFICATION TESTS")
    print("=" * 60)
    tests: List[Callable[[], None]] = [
        test_glycolysis_energy_balance,
        test_glycolysis_key_mechanisms_linked,
        test_tca_energy_yield,
        test_tca_all_steps_linked,
        test_etc_oxphos_p_ratios,
        test_beta_oxidation_cycle_yield,
        test_cholesterol_hmgcr_linked,
        test_urea_cycle_cost,
        test_gluconeogenesis_cost,
        test_ppp_nadph,
        test_fas_palmitate_costs,
        test_ketogenesis_products,
        test_glycogen_key_enzymes,
        test_digestion_absorption_suite,
        test_supporting_pathways_suite,
        test_all_pathways_have_nodes_and_edges,
        test_mechanism_registry_populated,
        test_nitrogen_balance_signs,
        test_respiratory_quotient_bounds,
        test_colonic_medium_and_scfa_flow,
        test_energy_routing_snapshot,
        test_colon_scfa_units_walk,
        test_additive_effect_hooks,
        test_engine_energy_routing_keys,
    ]
    failed = 0
    for test in tests:
        try:
            test()
        except AssertionError as e:
            print(f"✗ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ {test.__name__}: ERROR {e}")
            failed += 1
    print("=" * 60)
    if failed == 0:
        print(f"ALL {len(tests)} TESTS PASSED")
    else:
        print(f"{failed} / {len(tests)} TEST(S) FAILED")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
