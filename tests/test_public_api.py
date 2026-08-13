"""Smoke tests for public package API (no product score required)."""

from __future__ import annotations


def test_version():
    import biology_as_code as bac

    assert bac.__version__


def test_list_pathways():
    from biology_as_code import get_pathway, list_pathways

    names = list_pathways()
    assert "glycolysis" in [n.lower() for n in names] or any("glycolysis" in n.lower() for n in names)
    g = get_pathway("glycolysis")
    assert g is not None
    assert len(g.nodes) >= 1
    assert len(g.edges) >= 1


def test_simulate_meal_open():
    from biology_as_code import simulate_meal

    r = simulate_meal(carbs_g=40, protein_g=20, fats_g=12, fiber_g=15, enable_external_score=False)
    assert r.absorbed_macros_g
    assert r.external_scorer_available is False
    assert "pathway_regulation" in r.report or r.pathway_regulation


def test_scenarios():
    from biology_as_code import fed, overnight_fast, pathway_activities

    a = pathway_activities(fed())
    b = pathway_activities(overnight_fast())
    assert a["glycolysis"] > b["glycolysis"] or a.get("glycolysis", 0) >= 0.5
