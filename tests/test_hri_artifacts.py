"""
The HRI draft's claims about *this repository*, pinned.

`design/hri_v1/` is a pre-Stage-2 proposal — no engine code implements it. But
the spec asserts things about the engine that are checkable today, and this
branch has already demonstrated what happens to an unchecked cross-artifact
claim: a relation type was added to one vocabulary, three others were missed,
and every test stayed green (see `test_graph_relation_vocabulary.py`).

So these tests do not evaluate whether HRI is a good design. They check that
what it says about the code is true, and that the example obeys the rules the
spec states — which makes the drop-in load-bearing rather than inert.
"""

from __future__ import annotations

import json
import typing
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
HRI_DIR = REPO_ROOT / "design" / "hri_v1"
SCHEMA_PATH = HRI_DIR / "HRIRecord.schema.json"
EXAMPLE_PATH = HRI_DIR / "example_juice_vs_orange.hri.json"

BANDS = ["adverse", "low", "provisional", "moderate", "high"]


def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def example() -> dict:
    return json.loads(EXAMPLE_PATH.read_text(encoding="utf-8"))


def _cells(record: dict) -> dict[tuple[str, str], dict]:
    return {
        (system, clock): cell
        for system, row in record["matrix"].items()
        for clock, cell in row.items()
    }


# --- the spec's claim about the engine ----------------------------------------


def test_the_matrix_reuses_the_engine_seven_system_enum_verbatim():
    """
    The spec says "systems reuse the engine's existing SevenSystem enum
    verbatim". Checked in both directions — a subset check would let the engine
    grow a system that HRI silently cannot score.
    """
    from biology_as_code.engine.laws.models import SevenSystem

    engine_systems = set(typing.get_args(SevenSystem))
    hri_systems = set(schema()["properties"]["matrix"]["propertyNames"]["enum"])

    assert hri_systems == engine_systems, (
        f"only in engine: {sorted(engine_systems - hri_systems)}; "
        f"only in HRI: {sorted(hri_systems - engine_systems)}"
    )


def test_the_hri_clock_axis_is_disjoint_from_the_engine_clock_enum():
    """
    D-HRI-1, pinned as a fact rather than left as an assumption.

    HRI clocks (`acute`/`adaptive`/`parameter`) type the horizon of a *response*;
    `engine.clocks.Clock` types how fast a *state variable* changes. Different
    axes, zero shared values — but `adaptive` and `adaptation` sit one letter
    apart, which is exactly how the LAW-039 vocabulary bug looked.

    If someone later unifies them, this test fails and the unification is a
    deliberate decision instead of a half-holding assumption.
    """
    from biology_as_code.engine.clocks import Clock as EngineClock

    hri_clocks = set(
        schema()["properties"]["matrix"]["patternProperties"][".*"]["propertyNames"]["enum"]
    )
    engine_clocks = {c.value for c in EngineClock}

    assert hri_clocks == {"acute", "adaptive", "parameter"}
    assert not (hri_clocks & engine_clocks), (
        "the HRI response-horizon axis and the engine state-rate axis now share "
        f"values {sorted(hri_clocks & engine_clocks)} — decide whether they are one "
        "vocabulary or two, and update design/hri_v1/README.md D-HRI-1"
    )


# --- the example obeys the rules the spec states ------------------------------


def test_the_example_carries_every_required_field():
    record, required = example(), schema()["required"]
    missing = [field for field in required if field not in record]
    assert not missing, missing


def test_the_example_floor_cell_is_the_actual_minimum_over_covered_critical_cells():
    """
    The Liebig rule, verified rather than asserted. If someone edits a subscore
    and forgets `floor_cell`, this catches it.
    """
    record = example()
    cells = _cells(record)
    critical = {(c["system"], c["clock"]) for c in record["critical_staves"]}
    covered = {
        key: cell["subscore"]
        for key, cell in cells.items()
        if key in critical and "subscore" in cell
    }
    assert covered, "no covered critical cell carries a subscore"

    expected = min(covered, key=covered.get)
    actual = (record["floor_cell"]["system"], record["floor_cell"]["clock"])
    assert actual == expected, (
        f"floor_cell says {actual} but the minimum over covered critical cells is "
        f"{expected} (subscores: {covered})"
    )


def test_the_floor_cell_exists_in_the_matrix():
    record = example()
    floor = (record["floor_cell"]["system"], record["floor_cell"]["clock"])
    assert floor in _cells(record), f"floor_cell {floor} is not present in the matrix"


def test_the_example_never_averages_its_way_above_its_floor():
    """
    The anti-Goodhart invariant. Six good systems must not lift a jammed one:
    the band may not sit above the floor cell's own class.
    """
    record = example()
    floor_cell = _cells(record)[
        (record["floor_cell"]["system"], record["floor_cell"]["clock"])
    ]
    assert floor_cell["class"] == "adverse"
    assert BANDS.index(record["score_band"]) <= BANDS.index("low"), (
        "score_band rose above the floor cell's class — that is the averaging hole"
    )


def test_unmeasured_cells_stay_unknown_rather_than_becoming_neutral():
    """Fail-closed: missing data never quietly becomes a pass."""
    record = example()
    for key, cell in _cells(record).items():
        if cell["method"] == "prior":
            assert cell["class"] == "unknown", (
                f"{key} was inferred from a prior but is classed {cell['class']!r}; "
                "an unmeasured cell must stay unknown"
            )


# --- coverage-tier caps -------------------------------------------------------


def test_tier_and_band_caps_hold_for_the_example():
    record = example()
    tier, band = record["coverage_tier"], record["score_band"]

    if tier == 0:
        assert BANDS.index(band) <= BANDS.index("provisional"), (
            "Tier 0 is input-axis prior only and may not exceed 'provisional'"
        )
    if band == "high":
        cells = _cells(record)
        for key in (("Energy", "acute"), ("Communication", "acute")):
            assert cells.get(key, {}).get("method") == "measured", (
                f"top band requires measured {key}; a modeled cell cannot earn it"
            )


def test_a_modeled_record_declares_its_model_and_its_conformance_reference():
    """Calibration is a licence: a modeled record must say which model, and where green."""
    record = example()
    if any(cell["method"] == "modeled" for cell in _cells(record).values()):
        assert record.get("model_version"), "modeled cells require model_version"
        assert record.get("conformance_ref"), (
            "modeled cells require conformance_ref — Tier 1 is licensed by the ward suite"
        )


def test_every_record_carries_a_review_date():
    """The anti-1941 field. Nothing in this system persists unreviewed."""
    assert example().get("review_by")


# --- the dependency the example is honest about -------------------------------


def test_the_satiety_protocol_the_example_references_is_still_not_executable():
    """
    `Communication.acute` cites `SatietyResponse/1.0`, which does not exist as
    runnable code — the example marks it `modeled`, correctly.

    When Satiety becomes executable this test fails, which is the signal to
    revisit the example and the README's dependency list rather than leaving a
    stale reference in place.
    """
    from biology_as_code.responses import ResponseNotExecutable, Sample, SatietyResponse

    with pytest.raises(ResponseNotExecutable):
        SatietyResponse().compute([Sample(0, 1.0)])

    refs = [
        ref
        for cell in _cells(example()).values()
        for ref in cell.get("response_refs", [])
    ]
    assert any(ref.startswith("SatietyResponse/") for ref in refs)
