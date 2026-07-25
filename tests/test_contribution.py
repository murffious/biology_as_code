"""
CI gate for crowd-sourced contributions.

Because CI runs the whole suite, adding a file under ``examples/contributions/``
is itself validated here. The tests assert the fail-closed invariants directly:
a magnitude without a source is REFUSED, an unsourced claim is NEEDS_SOURCE, a
resolved + sourced contribution is ACCEPTED, a non-existent target is REFUSED,
and garbage never raises.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from biology_as_code.contrib import validate_contribution

CONTRIB_DIR = Path(__file__).resolve().parents[1] / "examples" / "contributions"

# Expected verdict for each shipped example, keyed by its id.
EXPECTED = {
    "contrib.evidence-unlu-2005-law020": "ACCEPTED",
    "contrib.evidence-scfa-energy-law026": "NEEDS_SOURCE",
    "contrib.badmagnitude-iron-law004": "REFUSE",
}


def _contribution_files() -> list[Path]:
    return sorted(CONTRIB_DIR.glob("*.json"))


def test_examples_present():
    assert _contribution_files(), "no example contributions found under examples/contributions/"


@pytest.mark.parametrize("path", _contribution_files(), ids=lambda p: p.stem)
def test_example_matches_expected_verdict(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    assert data["id"] in EXPECTED, f"example {data['id']!r} has no expected verdict listed"
    result = validate_contribution(data)
    assert result.verdict == EXPECTED[data["id"]], (result.verdict, result.reasons)


def test_magnitude_without_source_is_refused():
    result = validate_contribution(
        {
            "id": "contrib.t-magnitude",
            "type": "gate_bound",
            "target": {"kind": "law", "ref": "LAW-004"},
            "payload": {"claimed": "2x"},
            "asserts_magnitude": True,
        }
    )
    assert result.verdict == "REFUSE"


def test_unsourced_evidence_needs_source():
    result = validate_contribution(
        {
            "id": "contrib.t-nosource",
            "type": "evidence",
            "target": {"kind": "law", "ref": "LAW-020"},
            "payload": {"law": "LAW-020"},
        }
    )
    assert result.verdict == "NEEDS_SOURCE"
    assert result.strength == 0


def test_sourced_on_target_is_accepted():
    result = validate_contribution(
        {
            "id": "contrib.t-ok",
            "type": "evidence",
            "target": {"kind": "law", "ref": "LAW-020"},
            "payload": {"law": "LAW-020"},
            "source": {"kind": "pubmed", "pmid": "15735074"},
        }
    )
    assert result.verdict == "ACCEPTED"
    assert result.strength >= 3
    assert result.provenance.get("url") == "https://pubmed.ncbi.nlm.nih.gov/15735074/"


def test_nonexistent_law_target_is_refused():
    result = validate_contribution(
        {
            "id": "contrib.t-notarget",
            "type": "evidence",
            "target": {"kind": "law", "ref": "LAW-999"},
            "payload": {"law": "LAW-999"},
            "source": {"kind": "pubmed", "pmid": "15735074"},
        }
    )
    assert result.verdict == "REFUSE"


def test_pubmed_source_without_valid_pmid_is_not_accepted():
    result = validate_contribution(
        {
            "id": "contrib.t-badpmid",
            "type": "evidence",
            "target": {"kind": "law", "ref": "LAW-020"},
            "payload": {"law": "LAW-020"},
            "source": {"kind": "pubmed", "pmid": "not-a-pmid"},
        }
    )
    assert result.verdict == "NEEDS_SOURCE"


def test_garbage_never_raises():
    for junk in ({}, {"id": "x"}, {"nope": 1}, [], "string", None):
        result = validate_contribution(junk)
        assert result.verdict == "REFUSE"
