"""
Enforces the LAW-026 magnitude policy as a test rather than as prose.

`LAW026_PROMOTION_DECISION.md` (2026-07-21) records a deliberate decision: the
colonic fermentation energy magnitude stays a provisional, unlocked band, because
EV-041 (PMID 33995299) documents interindividual and substrate heterogeneity large
enough to forbid a point estimate. The decision closes with the line that a single
demo coefficient must never be treated as LAW-SPEC truth, and that choosing not to
go there is a feature.

A policy that lives only in a Markdown file gets "finished" by the next person who
reads an unlocked field as an unfinished one. These tests make the decision
executable: locking the band, or promoting its midpoint into a bound, turns CI red
and forces whoever does it to delete a test that explains why they should not.

The one legitimate route to locking it is spelled out in the decision document —
primary human metabolizable-energy evidence with explicit kJ/g. When that lands,
update the decision document first, then these tests.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

PKG_DATA = (
    Path(__file__).resolve().parents[1] / "src" / "biology_as_code" / "data" / "kibo_core" / "data"
)
SKELETON = PKG_DATA / "base_unit_colon_fermentation.skeleton.json"
DECISION = PKG_DATA / "LAW026_PROMOTION_DECISION.md"

# PMIDs the decision document names as the supporting pack.
REQUIRED_PMIDS = {"38441170", "10702589", "33995299"}
HUMAN_ME_CANDIDATE = "40403748"


def skeleton() -> dict:
    return json.loads(SKELETON.read_text(encoding="utf-8"))


def energy_band() -> dict:
    return skeleton()["priors"]["energy_kcal_per_g_fermentable"]


def test_decision_document_exists_and_states_the_policy():
    text = DECISION.read_text(encoding="utf-8")
    assert "magnitude_locked: false" in text or "magnitude_locked` : false" in text or (
        "never a hard single coefficient" in text
    )


def test_energy_band_is_not_locked():
    """The load-bearing assertion. Flipping this to True requires primary human ME evidence."""
    assert energy_band()["locked"] is False, (
        "LAW-026 energy magnitude was locked. See LAW026_PROMOTION_DECISION.md — this "
        "requires primary human metabolizable-energy evidence with explicit kJ/g, and "
        "the decision document must be updated first."
    )


def test_priors_and_bounds_agree_that_magnitude_is_unlocked():
    data = skeleton()
    assert data["priors"]["magnitude_locked"] is False
    assert data["bounds_and_conditions"]["magnitude_locked"] is False


def test_band_remains_a_range_not_a_point():
    band = energy_band()
    assert band["low"] < band["mid"] < band["high"], "band collapsed toward a point estimate"
    assert band["low"] == 1.5 and band["high"] == 2.5, (
        "band edges changed; if intentional, record the evidence in the decision document"
    )


def test_bound_kind_stays_a_soft_prior():
    bounds = skeleton()["bounds_and_conditions"]
    assert bounds["bound_kind"] == "soft_prior_range", (
        "bound_kind hardened; a soft prior is not a law bound"
    )
    assert bounds["risks_of_deviation"], "the risk note must survive; it is the reason for the policy"


def test_the_flow_midpoint_is_labelled_as_demo_only():
    """2.0 kcal/g may be used for demos. It may not be presented as the value."""
    band = energy_band()
    assert band["flow_demo_midpoint"] == band["mid"]
    assert "demo" in band["note"].lower()


def test_band_carries_its_basis():
    """An unlocked prior with no stated basis is indistinguishable from a guess."""
    basis = energy_band()["basis"]
    assert len(basis) > 80, "basis string too thin to justify the prior"
    assert "FAO" in basis or "Livesey" in basis


@pytest.mark.parametrize("pmid", sorted(REQUIRED_PMIDS))
def test_supporting_pmids_stay_attached(pmid: str):
    refs = {str(source.get("ref")) for source in skeleton()["sources"]}
    assert pmid in refs, f"PMID {pmid} dropped from the LAW-026 source pack"


def test_the_anti_overlock_evidence_is_still_cited():
    """EV-041 is the reason the band cannot be locked; losing it loses the argument."""
    sources = skeleton()["sources"]
    ev041 = [s for s in sources if str(s.get("ref")) == "33995299"]
    assert ev041, "EV-041 (PMID 33995299) missing"
    assert "overlock" in (ev041[0].get("note") or "").lower()


def test_human_me_candidate_is_still_marked_pending():
    """PMID 40403748 is the one route to a lock. It must stay visible as pending."""
    sources = skeleton()["sources"]
    candidate = [s for s in sources if str(s.get("ref")) == HUMAN_ME_CANDIDATE]
    assert candidate, f"PMID {HUMAN_ME_CANDIDATE} dropped; it is the only human-ME link"
    note = (candidate[0].get("note") or "").lower()
    assert "pending" in note or "full-text" in note, (
        "human-ME candidate no longer marked pending; if it was read, record the outcome "
        "in LAW026_PROMOTION_DECISION.md"
    )


def test_law026_is_registered_as_shape_not_magnitude():
    laws = {law["id"]: law for law in skeleton()["laws"]}
    assert "LAW-026" in laws
    note = laws["LAW-026"]["note"].lower()
    assert "shape" in note and "not locked" in note
