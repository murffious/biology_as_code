"""Pasted GR / PPP calculators must not land."""

from __future__ import annotations

from biology_as_code.dig.antioxidant_routes import defend
from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
from biology_as_code.dig.hepatic_routes import route_scfa
from biology_as_code.dig.mitochondrial_routes import oxidize
from biology_as_code.dig.redox_routes import regenerate


def _defense(gsh=True):
    return defend(
        oxidize(route_scfa(process_fiber(6.0, FiberType.SOLUBLE))),
        gsh_declared=gsh,
    )


def test_silent_seats_are_unevaluable():
    result = regenerate(_defense(), g6p_declared=None, nadph_declared=True)
    assert result.state == "UNEVALUABLE"
    assert result.gate == "unknown"
    assert result.amounts == {}


def test_empty_nadph_closes_regeneration():
    result = regenerate(_defense(), g6p_declared=True, nadph_declared=False)
    assert result.state == "REFUTED"
    assert result.gate == "closed"
    assert "gssg" in result.sinks
    assert result.amounts["gssg"] is None


def test_open_seats_hold_identity_not_mmol():
    result = regenerate(_defense(), g6p_declared=True, nadph_declared=True)
    assert result.state == "HOLDS"
    assert result.stoichiometry["ppp_nadph_per_g6p"] == 2
    assert result.stoichiometry["gr_gsh_per_gssg"] == 2
    blob = str(result.to_dict())
    assert "LAW-083" not in blob
    assert "LAW-092" not in blob
    assert "mmol" not in blob
    assert all(v is None for v in result.amounts.values())


def test_unevaluable_defense_does_not_invent_ppp():
    silent_def = defend(
        oxidize(route_scfa(process_fiber(None, None))),
        gsh_declared=True,
    )
    result = regenerate(silent_def, g6p_declared=True, nadph_declared=True)
    assert result.state == "UNEVALUABLE"
    assert result.sinks == ()
