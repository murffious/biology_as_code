"""Pasted antioxidant_defense.py must not become a GSH ledger."""

from __future__ import annotations

from biology_as_code.dig.antioxidant_routes import defend
from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
from biology_as_code.dig.hepatic_routes import route_scfa
from biology_as_code.dig.mitochondrial_routes import oxidize


def _mito():
    return oxidize(route_scfa(process_fiber(6.0, FiberType.SOLUBLE)))


def test_gsh_silent_is_unevaluable():
    result = defend(_mito(), gsh_declared=None)
    assert result.state == "UNEVALUABLE"
    assert result.gate == "unknown"
    assert "hydrogen_peroxide" in result.sinks
    assert result.amounts == {}


def test_gsh_closed_does_not_drop_h2o2():
    result = defend(_mito(), gsh_declared=False)
    assert result.state == "REFUTED"
    assert result.gate == "closed"
    assert "hydrogen_peroxide" in result.sinks
    assert "oxidative_stress" in result.sinks
    assert result.amounts["hydrogen_peroxide"] is None


def test_gsh_open_holds_path_not_mmol():
    result = defend(_mito(), gsh_declared=True)
    assert result.state == "HOLDS"
    assert result.stoichiometry == {"sod_o2_per_h2o2": 2, "gpx_gsh_per_h2o2": 2}
    assert result.amounts["gsh"] is None
    blob = str(result.to_dict())
    assert "LAW-081" not in blob
    assert "LAW-082" not in blob
    assert "mmol" not in blob


def test_closed_mito_does_not_invent_defense():
    result = defend(oxidize(route_scfa(process_fiber(0.0, FiberType.SOLUBLE))), gsh_declared=True)
    assert result.state == "REFUTED"
    assert result.sinks == ()
