"""Pasted test_pentose_phosphate_pathway.py and test_redox_integration.py.

Those files prove a calculator. These prove the constitution reading of the
same two stories: recovery seats declared vs glucose seat empty.
"""

from __future__ import annotations

import json

from biology_as_code.dig.antioxidant_routes import defend
from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
from biology_as_code.dig.hepatic_routes import route_scfa
from biology_as_code.dig.mitochondrial_routes import oxidize
from biology_as_code.dig.redox_routes import regenerate

BANNED = (
    "LAW-082",
    "LAW-083",
    "LAW-092",
    "unneutralized_h2o2_mmol",
    "g6p_mmol",
    "nadph_mmol",
)


def _defense():
    return defend(
        oxidize(route_scfa(process_fiber(6.0, FiberType.SOLUBLE))),
        gsh_declared=True,
    )


def test_golden_path_is_open_seats_not_a_10_mmol_recovery():
    """Pasted 'full cellular recovery via glucose' without inventing 10/5/0."""
    result = regenerate(_defense(), g6p_declared=True, nadph_declared=True)
    assert result.state == "HOLDS"
    assert result.gate == "open"
    assert "ppp_oxidative" in result.sinks
    assert "glutathione_reductase" in result.sinks
    assert result.stoichiometry["ppp_nadph_per_g6p"] == 2
    assert result.stoichiometry["gr_gsh_per_gssg"] == 2
    assert all(v is None for v in result.amounts.values())
    blob = json.dumps(result.to_dict())
    for token in BANNED:
        assert token not in blob
    assert "10.0" not in blob
    assert "5.0" not in blob


def test_starvation_path_is_empty_g6p_seat_not_1_mmol_damage():
    """Pasted 'glucose starvation causes oxidative damage' as a closed carbon seat."""
    result = regenerate(_defense(), g6p_declared=False, nadph_declared=True)
    assert result.state == "REFUTED"
    assert result.gate == "closed"
    assert "gssg" in result.sinks
    assert "glycolysis" in result.sinks
    assert result.amounts["gssg"] is None
    blob = json.dumps(result.to_dict())
    assert "1.0" not in blob
    assert "spillover" not in blob.lower()
    assert "LAW-082" not in blob


def test_nadp_bottleneck_is_named_not_computed_as_45_left_over():
    """Pasted G6PD-inhibition test used min(50, 10/2)=5. We only name the seat."""
    result = regenerate(_defense(), g6p_declared=True, nadph_declared=False)
    assert result.state == "REFUTED"
    assert "gssg" in result.sinks
    blob = json.dumps(result.to_dict())
    assert "45.0" not in blob
    assert "110.0" not in blob
