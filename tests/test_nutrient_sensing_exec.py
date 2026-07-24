"""Executable nutrient-sensing: evaluate_network + state-driven snapshot."""

from __future__ import annotations


def test_evaluate_network_signs_and_bounds():
    from biology_as_code.pathways.nutrient_sensing import (
        evaluate_network,
        get_nutrient_sensing_registry,
    )

    net = get_nutrient_sensing_registry().get("ampk_network")
    # strong energy stress -> AMPK high -> mTORC1 inhibited (low)
    hi = evaluate_network(net, {"amp_adp_atp": 1.0, "lkb1": 1.0, "camkk2": 0.5})
    lo = evaluate_network(net, {"amp_adp_atp": 0.0, "lkb1": 0.2, "camkk2": 0.0})
    assert 0.0 <= hi["ampk"] <= 1.0
    assert hi["ampk"] > lo["ampk"]
    # AMPK inhibits mTORC1: higher AMPK -> lower mTORC1 node
    assert hi["mtorc1"] < lo["mtorc1"]
    # AMPK activates ULK1 (autophagy): higher AMPK -> higher ULK1
    assert hi["ulk1"] > lo["ulk1"]


def test_nutrient_sensing_snapshot_flips_fed_vs_fasted():
    from biology_as_code import fed, overnight_fast
    from biology_as_code.pathways.pathway_regulation import nutrient_sensing_snapshot

    f = nutrient_sensing_snapshot(fed())["regulators"]
    x = nutrient_sensing_snapshot(overnight_fast())["regulators"]
    # fed: mTORC1/SREBP high, AMPK low.  fasted: the reverse.
    assert x["ampk"] > f["ampk"]
    assert f["mtorc1"] > x["mtorc1"]
    assert f["srebp1c"] > x["srebp1c"]


def test_snapshot_shape():
    from biology_as_code import fed
    from biology_as_code.pathways.pathway_regulation import nutrient_sensing_snapshot

    s = nutrient_sensing_snapshot(fed())
    assert set(s) == {"regulators", "ampk_network", "mtorc1_network", "srebp_network"}
    assert set(s["regulators"]) == {"ampk", "mtorc1", "srebp1c"}
    assert all(0.0 <= v <= 1.0 for v in s["ampk_network"].values())


def test_engine_report_includes_nutrient_sensing():
    from biology_as_code import simulate_meal

    r = simulate_meal(carbs_g=40, protein_g=20, fats_g=12, fiber_g=10)
    assert "nutrient_sensing" in r.report
    assert "regulators" in r.report["nutrient_sensing"]
    # flat pathway_regulation stays flat floats (engine unbroken)
    assert all(isinstance(v, (int, float)) for v in r.report["pathway_regulation"].values())


def test_shipped_mermaid_renders_signed_edges():
    from biology_as_code import get_pathway
    from biology_as_code.visualization.graphs import pathway_to_mermaid

    m = pathway_to_mermaid(get_pathway("ampk_network"))
    assert "flowchart" in m and "-->" in m
    assert "inhibits" in m or "activates" in m
    # and it still works for a metabolic pathway (ketolysis)
    mk = pathway_to_mermaid(get_pathway("ketolysis"))
    assert "flowchart" in mk and "BDH1" in mk
