"""Meal-critical tier-B graphs (iron, B12, glucose transport, SCFA)."""

from __future__ import annotations

import re

MEAL_CRITICAL = (
    "iron_absorption",
    "cobalamin_absorption",
    "glucose_epithelial_transport",
    "scfa_colonic_production",
)


def test_meal_critical_discoverable():
    from biology_as_code import get_pathway, list_pathways

    names = {n.lower() for n in list_pathways()}
    for name in MEAL_CRITICAL:
        assert name in names, f"missing {name}"
        p = get_pathway(name)
        assert p is not None
        assert len(p.nodes) >= 4
        assert len(p.edges) >= 3


def test_iron_absorption_mechanisms_and_control_point():
    from biology_as_code import get_pathway
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    p = get_pathway("iron_absorption")
    assert "dmt1" in {e.mechanism_id for e in p.edges}
    assert "ferroportin" in {e.mechanism_id for e in p.edges}
    assert "hepcidin" in p.nodes
    assert p.summary().get("control_point") == "ferroportin / hepcidin"
    reg = get_metabolic_mechanism_registry()
    for mid in ("dmt1", "ferroportin", "hepcidin_ferroportin", "duodenal_cytochrome_b"):
        assert reg.get(mid) is not None, mid


def test_cobalamin_requires_intrinsic_factor():
    from biology_as_code import get_pathway

    p = get_pathway("cobalamin_absorption")
    assert "intrinsic_factor" in p.nodes
    assert any(e.mechanism_id == "intrinsic_factor" for e in p.edges)
    assert p.summary().get("obligatory_partner") == "intrinsic_factor"
    assert "if_b12_complex" in p.nodes


def test_glucose_epithelial_sglt1_glut2():
    from biology_as_code import get_pathway

    p = get_pathway("glucose_epithelial_transport")
    mids = {e.mechanism_id for e in p.edges if e.mechanism_id}
    assert "sglt1" in mids
    assert "glut2" in mids
    assert "glucose_lumen" in p.nodes
    assert "glucose_portal" in p.nodes


def test_scfa_three_products():
    from biology_as_code import get_pathway

    p = get_pathway("scfa_colonic_production")
    for scfa in ("acetate", "propionate", "butyrate"):
        assert scfa in p.nodes
    assert any(e.mechanism_id == "colonic_fermentation" for e in p.edges)


def test_iron_absorption_regulation_inflammation_lowers_activity():
    from biology_as_code.pathways.pathway_regulation import iron_absorption_activity
    from biology_as_code.simulation.physiological_state import (
        create_fed_state,
    )

    low = create_fed_state()
    low.inflammation = 0.1
    high = create_fed_state()
    high.inflammation = 0.9
    assert iron_absorption_activity(low) > iron_absorption_activity(high)


def test_pathway_snapshot_includes_meal_critical_keys():
    from biology_as_code import fed, pathway_activities

    a = pathway_activities(fed())
    for key in ("iron_absorption", "glucose_epithelial_transport", "scfa_colonic_production"):
        assert key in a
        assert 0.0 <= a[key] <= 1.0


def test_mechanism_ids_resolve_for_meal_critical():
    from biology_as_code import get_pathway
    from biology_as_code.pathways.metabolic_mechanisms import get_metabolic_mechanism_registry

    known = {m.id for m in get_metabolic_mechanism_registry().list_all()}
    for name in MEAL_CRITICAL:
        p = get_pathway(name)
        for e in p.edges:
            if e.mechanism_id:
                assert e.mechanism_id in known, f"{name}: {e.mechanism_id}"


def test_meal_critical_sources_are_traceable():
    """Convention: new pathway/mermaid artifacts cite PMIDs/URLs, not just prose.

    The exporter renders `references` into `%% Source:` (mermaid) and `## Sources`
    (tests.md), so every meal-critical graph must carry traceable citations.
    """
    from biology_as_code import get_pathway

    pmid_or_url = re.compile(r"PMID\s*\d{5,9}|https?://", re.IGNORECASE)
    for name in MEAL_CRITICAL:
        p = get_pathway(name)
        refs = getattr(p, "references", None) or []
        assert refs, f"{name}: no references"
        traceable = [r for r in refs if pmid_or_url.search(r)]
        assert len(traceable) >= 2, (
            f"{name}: expected >=2 PMID/URL-backed references, got "
            f"{len(traceable)} of {len(refs)}"
        )
