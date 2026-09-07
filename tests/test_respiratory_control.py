from __future__ import annotations

import json

from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
from biology_as_code.dig.hepatic_routes import route_scfa
from biology_as_code.dig.mitochondrial_routes import oxidize
from biology_as_code.dig.respiratory_control import respire


def _mito():
    return oxidize(route_scfa(process_fiber(6.0, FiberType.SOLUBLE)))


def test_adp_present_is_state_3_not_a_yield():
    result = respire(_mito(), adp_declared=True)
    assert result.chance_state == "state_3"
    assert result.leak_direction == "low"
    assert result.amounts["atp"] is None
    blob = json.dumps(result.to_dict())
    assert "0.005" not in blob
    assert "0.04" not in blob
    assert "LAW-101" not in blob
    assert "500" not in blob


def test_adp_absent_is_state_4_direction():
    result = respire(_mito(), adp_declared=False)
    assert result.state == "REFUTED"
    assert result.chance_state == "state_4"
    assert result.leak_direction == "high"


def test_adp_silent_is_not_sedentary_default():
    result = respire(_mito(), adp_declared=None)
    assert result.state == "UNEVALUABLE"
    assert result.chance_state == "unknown"
