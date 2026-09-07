"""Every number the engine emits must name the paper that grounds it.

`tools/check_constants.py` run inside the normal suite. It is a test and not only
a CI step for the same reason as `test_shipped_pmids_resolve.py`: these constants
travel out in `to_dict()` payloads, so an ungrounded one is an unsourced claim
about mammalian biochemistry, not a style problem.
"""

from __future__ import annotations

import json
import pathlib
import subprocess
import sys

import pytest

from biology_as_code.dig import antioxidant_routes, mitochondrial_routes, redox_routes
from biology_as_code.grounding import GroundedFloat, GroundedInt, grounded, sources_for

ROOT = pathlib.Path(__file__).resolve().parent.parent


def test_gate_passes():
    result = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "check_constants.py"), "--strict"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    assert result.returncode == 0, result.stdout + result.stderr


@pytest.mark.parametrize(
    "module", [antioxidant_routes, mitochondrial_routes, redox_routes]
)
def test_every_module_reports_its_sources(module):
    sources = sources_for(module)
    assert sources, module.__name__
    for name, row in sources.items():
        assert row["pmid"].isdigit(), name
        assert row["tier"] in {"identity", "teaching"}, name
        assert row["supports"].strip(), name


def test_grounded_is_a_drop_in_number():
    """Arithmetic, equality and JSON must be unchanged, or this is a rewrite."""
    two = grounded(2, tier="identity", pmid="5389100", supports="SOD 2:1")
    half = grounded(2.5, tier="teaching", pmid="15620362", supports="P/O")
    assert two == 2 and half == 2.5
    assert two * 3 == 6
    assert isinstance(two, int) and isinstance(half, float)
    assert json.loads(json.dumps({"a": two, "b": half})) == {"a": 2, "b": 2.5}


def test_a_population_statistic_may_not_be_encoded():
    """Tier 3 does not become encodable by acquiring a citation."""
    with pytest.raises(ValueError, match="must stay OPEN"):
        grounded(0.6, tier="population", pmid="8633856", supports="60:20:20 SCFA ratio")


def test_the_payload_shape_did_not_change():
    """Grounding is carried beside the payload, never interleaved into it."""
    from biology_as_code.dig.antioxidant_routes import defend
    from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
    from biology_as_code.dig.hepatic_routes import route_scfa
    from biology_as_code.dig.mitochondrial_routes import oxidize

    payload = defend(oxidize(route_scfa(process_fiber(8.0, FiberType.SOLUBLE))), gsh_declared=True).to_dict()
    assert payload["stoichiometry"] == {"sod_o2_per_h2o2": 2, "gpx_gsh_per_h2o2": 2}
    assert json.loads(json.dumps(payload))["stoichiometry"]["sod_o2_per_h2o2"] == 2


def test_grounded_types_are_exported():
    assert issubclass(GroundedInt, int) and issubclass(GroundedFloat, float)
