"""Pasted mitochondrial_engine.py must not land as a calculator."""

from __future__ import annotations

from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
from biology_as_code.dig.hepatic_routes import route_scfa
from biology_as_code.dig.mitochondrial_routes import PO_FADH2, PO_NADH, oxidize


def _open_hepatic():
    return route_scfa(process_fiber(6.0, FiberType.SOLUBLE))


def test_po_identity_is_teaching_not_applied_to_mass():
    result = oxidize(_open_hepatic())
    assert result.state == "HOLDS"
    assert result.po_identity == {"nadh": PO_NADH, "fadh2": PO_FADH2}
    assert result.po_identity["nadh"] == 2.5
    assert result.po_identity["fadh2"] == 1.5
    assert result.amounts["atp"] is None
    assert result.amounts["superoxide"] is None


def test_no_invented_leak_formula():
    blob = str(oxidize(_open_hepatic()).to_dict())
    assert "0.02" not in blob
    assert "1.5" in blob  # P/O FADH2 identity is allowed
    assert "**" not in blob
    assert "LAW-104" not in blob
    assert "LAW-105" not in blob
    assert "moles_atp" not in blob


def test_closed_upstream_does_not_mint_atp():
    result = oxidize(route_scfa(process_fiber(0.0, FiberType.SOLUBLE)))
    assert result.state == "REFUTED"
    assert result.sinks == ()
    assert result.po_identity == {}
