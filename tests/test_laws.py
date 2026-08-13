"""LAW-SPEC law cards public API (feature #4)."""

from __future__ import annotations


def test_list_laws_and_systems():
    from biology_as_code import list_laws
    from biology_as_code.laws import list_systems

    ids = list_laws()
    assert len(ids) >= 47
    assert "LAW-004" in ids
    systems = list_systems()
    assert "Assimilation" in systems
    assert len(systems) <= 7  # the seven functional systems


def test_get_law_accepts_flexible_ids():
    from biology_as_code import get_law

    a = get_law("LAW-004")
    assert a is not None
    # int and lowercase forms resolve to the same record
    assert get_law(4).id == "LAW-004"
    assert get_law("law-004").id == "LAW-004"
    assert get_law("nope") is None


def test_law_card_shape_is_law_spec():
    from biology_as_code import law_card

    card = law_card("LAW-004")
    assert card is not None
    # LAW-SPEC fields present
    for key in ("id", "system", "organ", "subsystem", "statement", "gate", "bound",
                "conditions", "relation", "executable"):
        assert key in card, f"missing card field {key}"
    assert card["id"] == "LAW-004"
    assert set(card["gate"]) == {"present", "text"}
    assert isinstance(card["gate"]["present"], bool)
    assert set(card["relation"]) == {"type", "expression"}
    assert law_card("nope") is None


def test_laws_by_system():
    from biology_as_code.laws import laws_by_system

    assim = laws_by_system("assimilation")  # case-insensitive
    assert assim
    assert all(law.system_name.lower() == "assimilation" for law in assim)


def test_bhb_signaling_pathway_registered():
    """Feature #1: BHB signaling (not just fuel) — HDAC / NLRP3 / GPR109A."""
    from biology_as_code.simulation.signaling_pathways import (
        PathwayCategory,
        get_signaling_pathway_registry,
    )

    p = get_signaling_pathway_registry().get("bhb_signaling")
    assert p is not None
    assert p.category == PathwayCategory.METABOLIC
    assert "beta_hydroxybutyrate" in p.transmitters
    blob = " ".join(p.sensors + p.effects).lower()
    assert "hdac" in blob
    assert "nlrp3" in blob
    assert "gpr109a" in blob
    # sources tracked per project convention
    assert "pmc" in p.notes.lower() or "pmid" in p.notes.lower()
