"""Reject the pasted yield tests; keep handoff + route identity."""

from __future__ import annotations

from biology_as_code.dig.chyme_handoff import handoff_from_declared
from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
from biology_as_code.dig.hepatic_routes import route_scfa


def test_pasted_approx_grams_are_not_emitted():
    result = process_fiber(10.0, FiberType.SOLUBLE)
    assert result.amounts["acetate"] is None
    assert result.amounts["propionate"] is None
    assert result.amounts["butyrate"] is None
    blob = str(result.to_dict())
    assert "2.4" not in blob
    assert "1.575" not in blob


def test_empty_handoff_is_unevaluable():
    chyme = handoff_from_declared(None)
    assert chyme.pool_state() == "UNEVALUABLE"
    assert chyme.ferment() == ()


def test_handoff_ferments_declared_rows():
    chyme = handoff_from_declared(
        [
            (8.0, FiberType.SOLUBLE, "demo.oats"),
            (0.0, FiberType.RESISTANT_STARCH, "demo.zero"),
        ]
    )
    rows = chyme.ferment()
    assert rows[0].state == "HOLDS"
    assert rows[1].state == "REFUTED"
    assert chyme.pool_state() == "REFUTED"


def test_missing_ontology_does_not_raise():
    chyme = handoff_from_declared([(5.0, None, "USDA-unknown")])
    rows = chyme.ferment()
    assert rows[0].state == "UNEVALUABLE"


def test_hepatic_routes_named_without_fractions():
    routed = route_scfa(process_fiber(6.0, FiberType.RESISTANT_STARCH))
    assert routed.state == "HOLDS"
    assert "succinyl_coa" in routed.sinks
    assert "ketogenesis_bhb" in routed.sinks
    assert "systemic_acetate" in routed.sinks
    assert all(v is None for v in routed.amounts.values())
    blob = str(routed.to_dict())
    assert "0.70" not in blob
    assert "0.85" not in blob
    assert "LAW-062" not in blob
    assert "LAW-063" not in blob


def test_closed_ferment_does_not_invent_hepatic_output():
    routed = route_scfa(process_fiber(0.0, FiberType.SOLUBLE))
    assert routed.state == "REFUTED"
    assert routed.sinks == ()
