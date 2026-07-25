"""
The digest() engine — how the body handles a standardized food, under conditions.
"""

from __future__ import annotations

from biology_as_code.digestion import Conditions, digest, packet_to_context
from biology_as_code.packets import get_packet
from biology_as_code.packets.loader import FoodPacket


def _handling(trace, nutrient):
    return next(h for h in trace.handling if h.nutrient == nutrient)


def test_fat_soluble_gate_closed_without_fat():
    t = digest("ex.spinach_salad.zero_fat")
    h = _handling(t, "beta_carotene")
    assert h.gate == "closed"
    assert "LAW-020" in h.law_refs


def test_fat_soluble_gate_open_with_oil():
    assert _handling(digest("ex.spinach_salad.with_oil"), "beta_carotene").gate == "open"


def test_iron_bound_expands_with_ascorbate():
    h = _handling(digest("ex.lentils.with_ascorbate"), "nonhaem_iron")
    assert h.gate == "none"  # iron is a bound story, not a categorical gate
    assert any(b.direction == "EXPANDS_BOUND" for b in h.bounds)
    assert "LAW-004" in h.law_refs


def test_iron_bound_narrows_with_tea():
    h = _handling(digest("ex.lentils.with_tea"), "nonhaem_iron")
    assert any(b.direction == "NARROWS_BOUND" for b in h.bounds)
    assert "LAW-006" in h.law_refs


def test_same_food_different_conditions():
    """The whole thesis: same packet, a Partner-seat condition changes the handling."""
    base = _handling(digest("ex.lentils.with_ascorbate"), "nonhaem_iron")
    with_tea = _handling(
        digest("ex.lentils.with_ascorbate", Conditions(partners={"tea_tannins": True})),
        "nonhaem_iron",
    )
    assert {b.direction for b in base.bounds} == {"EXPANDS_BOUND"}
    assert {b.direction for b in with_tea.bounds} == {"EXPANDS_BOUND", "NARROWS_BOUND"}


def test_path_walks_all_stages():
    t = digest("ex.spinach_salad.zero_fat")
    for stage in ("oral", "stomach", "duodenum", "jejunum", "portal", "systemic", "cell", "colon"):
        assert stage in t.path
    assert t.status == "ok"


def test_events_include_stage_emits():
    assert any(e.startswith("stage:") for e in digest("ex.spinach_salad.zero_fat").events)


def test_fail_closed_when_fat_undeclared():
    # fat-soluble cargo, but nothing declared about lipid -> UNEVALUABLE, never a zero.
    packet = FoodPacket.from_dict(
        {
            "id": "ex.test.retinol_only",
            "identity": {"common_name": "test food"},
            "cargo": [{"nutrient": "vitamin_a"}],
        }
    )
    assert _handling(digest(packet), "vitamin_a").gate == "unevaluable"
    assert "meal.fatG" not in packet_to_context(packet)  # silence is not a zero


def test_accepts_packet_object_and_id():
    a = digest("ex.spinach_salad.zero_fat")
    b = digest(get_packet("ex.spinach_salad.zero_fat"))
    assert a.summary == b.summary


def test_trace_serialises():
    d = digest("ex.lentils.with_tea").to_dict()
    assert d["handling"] and d["path"] and "summary" in d and "events" in d
