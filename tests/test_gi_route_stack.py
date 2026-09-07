"""Robust but small suite for the colon → hepatic → mito → defense stack.

These modules are teaching-FLOW. Tests lock constitution behaviour, not grams.
"""

from __future__ import annotations

import json

import pytest

from biology_as_code.dig.antioxidant_routes import defend
from biology_as_code.dig.chyme_handoff import handoff_from_declared
from biology_as_code.dig.colon_fermentation import FiberType, process_fiber
from biology_as_code.dig.hepatic_routes import route_scfa
from biology_as_code.dig.mitochondrial_routes import oxidize

STATES = frozenset({"HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"})
BANNED = (
    "LAW-048",
    "LAW-062",
    "LAW-063",
    "LAW-081",
    "LAW-082",
    "LAW-104",
    "LAW-105",
    "0.40",
    "0.35",
    "0.70",
    "0.85",
    "0.02",
    "moles_atp",
    "moles_superoxide",
)


def _walk(amount, kind, gsh=True):
    ferment = process_fiber(amount, kind)
    hepatic = route_scfa(ferment)
    mito = oxidize(hepatic)
    defense = defend(mito, gsh_declared=gsh)
    return ferment, hepatic, mito, defense


@pytest.mark.parametrize(
    ("amount", "kind", "gsh", "ferment_state"),
    [
        (None, None, None, "UNEVALUABLE"),
        (None, FiberType.SOLUBLE, True, "UNEVALUABLE"),
        (8.0, None, True, "UNEVALUABLE"),
        (0.0, FiberType.SOLUBLE, True, "REFUTED"),
        (-1.0, FiberType.SOLUBLE, True, "REFUSE"),
        (8.0, FiberType.SOLUBLE, True, "HOLDS"),
        (8.0, FiberType.RESISTANT_STARCH, False, "HOLDS"),
        (8.0, "cellulose", True, "UNEVALUABLE"),
        (True, FiberType.SOLUBLE, True, "UNEVALUABLE"),  # bool is not a mass
    ],
)
def test_process_fiber_never_raises_and_stays_in_vocabulary(amount, kind, gsh, ferment_state):
    ferment, hepatic, mito, defense = _walk(amount, kind, gsh)
    assert ferment.state == ferment_state
    for row in (ferment, hepatic, mito, defense):
        assert row.state in STATES
        payload = row.to_dict()
        json.dumps(payload)
        blob = json.dumps(payload)
        for token in BANNED:
            assert token not in blob, token
        for value in payload.get("amounts", {}).values():
            assert value is None


def test_stack_does_not_raise_on_garbage():
    process_fiber("ten grams", "soluble_fiber")
    handoff_from_declared([(None, None, None), (0, "soluble_fiber", "x")])


def test_positive_fiber_opens_named_paths():
    ferment, hepatic, mito, defense = _walk(5.0, FiberType.SOLUBLE, True)
    assert ferment.products
    assert "succinyl_coa" in hepatic.sinks or "tca_cycle" in hepatic.sinks
    assert mito.po_identity == {"nadh": 2.5, "fadh2": 1.5}
    assert defense.stoichiometry == {"sod_o2_per_h2o2": 2, "gpx_gsh_per_h2o2": 2}
    assert defense.state == "HOLDS"


def test_zero_fiber_closes_the_whole_stack():
    ferment, hepatic, mito, defense = _walk(0.0, FiberType.RESISTANT_STARCH, True)
    assert ferment.state == hepatic.state == mito.state == defense.state == "REFUTED"
    assert hepatic.sinks == mito.sinks == defense.sinks == ()


def test_gsh_silence_does_not_claim_neutralization():
    _, _, mito, _ = _walk(5.0, FiberType.SOLUBLE, True)
    silent = defend(mito, gsh_declared=None)
    assert silent.state == "UNEVALUABLE"
    assert silent.gate == "unknown"


def test_handoff_worst_state_wins():
    chyme = handoff_from_declared(
        [
            (4.0, FiberType.SOLUBLE, "a"),
            (None, FiberType.SOLUBLE, "b"),
        ]
    )
    assert chyme.pool_state() == "UNEVALUABLE"
