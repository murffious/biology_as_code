"""
Claims-agent (assay) foundations — schema, ids, golden scoring, pipeline.

Migrated from claims_agent/assay/tests/test_assay.py. This is the two-engine
golden contract (Python assay must agree with its TypeScript twin on verdicts and
bare-16-hex claim ids); wiring it into biology_as_code's suite keeps that contract
enforced in CI.
"""

from __future__ import annotations

from biology_as_code.agents.assay.atomize import atomize
from biology_as_code.agents.assay.fixtures.golden import GOLDEN
from biology_as_code.agents.assay.ids import compute_claim_id, supersede
from biology_as_code.agents.assay.pipeline import assay_claim
from biology_as_code.agents.assay.schema import validate_claim
from biology_as_code.agents.assay.score import EvidenceSet, score


def test_claim_id_deterministic():
    a = compute_claim_id("spirulina", "removes", "heavy metals", site="brain")
    b = compute_claim_id("Spirulina", "Removes", "Heavy Metals", site="Brain")
    assert a == b
    assert not a.startswith("assay:claim/")  # bare hex (TS parity)
    assert len(a) == 16
    assert all(c in "0123456789abcdef" for c in a)


def test_claim_id_differs_on_outcome():
    a = compute_claim_id("creatine", "increases", "strength")
    b = compute_claim_id("creatine", "increases", "endurance")
    assert a != b


def test_supersede_increments():
    prev = {"claim_id": "a" * 16, "version": 1, "verdict": {"rubric_version": "1.0.0"}}
    nxt = supersede(prev, rubric_version="1.1.0")
    assert nxt["version"] == 2
    assert nxt["supersedes"] == "a" * 16
    assert nxt["verdict"]["rubric_version"] == "1.1.0"
    assert prev["version"] == 1  # immutable


def test_validate_rejects_missing_claim_id():
    errs = validate_claim({"atomic_claims": [{"predicate": "x", "outcome": {"surface": "y"}}]})
    assert any("claim_id" in e for e in errs)


def test_validate_accepts_pipeline_output():
    r = assay_claim(GOLDEN["creatine-strength"]["raw_text"])
    assert validate_claim(r.claim.to_dict()) == []


def test_golden_verdicts():
    for fid, g in GOLDEN.items():
        ar = atomize(g["raw_text"])
        evidence = EvidenceSet.from_dict(g["evidence"])
        verdict, _attacks, _c = score(evidence, ar.atoms)
        assert verdict.label == g["expected_verdict"], f"{fid}: {verdict.label}"
        if "expected_survived_min" in g:
            assert verdict.survived >= g["expected_survived_min"], fid
        if "expected_survived_max" in g:
            assert verdict.survived <= g["expected_survived_max"], fid


def test_monotonicity_rebuttal_never_raises_confidence():
    ar = atomize(GOLDEN["flavonoids-cvd"]["raw_text"])
    base = EvidenceSet.from_dict(GOLDEN["flavonoids-cvd"]["evidence"])
    more = EvidenceSet.from_dict(
        {**GOLDEN["flavonoids-cvd"]["evidence"], "rebuttals": base.rebuttals + 2}
    )
    _, _, c0 = score(base, ar.atoms)
    _, _, c1 = score(more, ar.atoms)
    assert c1 <= c0


def test_spirulina_pipeline_busted():
    r = assay_claim(GOLDEN["spirulina-brain-metals"]["raw_text"])
    assert r.claim.verdict.label == "BUSTED"
    assert r.matched_fixture == "spirulina-brain-metals"
    assert len(r.claim.atomic_claims) == 4
    assert any(a.claim_type == "superlative" for a in r.claim.atomic_claims)
    assert r.jsonld["schema:ClaimReview"]["reviewRating"]["alternateName"] == "Busted"


def test_creatine_confirmed():
    r = assay_claim(GOLDEN["creatine-strength"]["raw_text"])
    assert r.claim.verdict.label == "CONFIRMED"
    assert r.claim.verdict.survived >= 7


def test_unknown_fail_closed():
    r = assay_claim("Quantum kale permanently rewires your DNA for immortality.")
    assert r.claim.verdict.label == "BUSTED"
    assert r.matched_fixture is None
