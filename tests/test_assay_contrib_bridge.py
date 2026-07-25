"""
The claims agent feeding the contribution gate — Door B end to end.

An assay verdict becomes a `type: "claim"` contribution. Fail-closed still holds:
the agent's own claim is NEEDS_SOURCE until a primary source is attached.
"""

from __future__ import annotations

from biology_as_code.agents.assay.pipeline import assay_claim
from biology_as_code.contrib import validate_contribution
from biology_as_code.contrib.from_assay import (
    assay_result_to_contribution,
    contribute_assay_result,
)


def test_bridge_dict_is_well_formed():
    result = assay_claim("Creatine increases strength.")
    contribution = assay_result_to_contribution(result)
    assert contribution["id"].startswith("contrib.claim-")
    assert contribution["type"] == "claim"
    assert contribution["target"]["kind"] == "claim"
    assert contribution["payload"]["verdict"] in {"CONFIRMED", "PLAUSIBLE", "BUSTED"}
    # A well-formed claim is never REFUSE'd for being malformed.
    assert validate_contribution(contribution).verdict in {"ACCEPTED", "NEEDS_SOURCE"}


def test_agent_claim_without_source_needs_source():
    result = assay_claim("Creatine increases strength.")
    gated = contribute_assay_result(result)
    assert gated.verdict == "NEEDS_SOURCE"  # the agent cannot auto-accept itself
    assert gated.strength == 0


def test_agent_claim_with_source_is_accepted():
    result = assay_claim("Creatine increases strength.")
    gated = contribute_assay_result(result, source={"kind": "pubmed", "pmid": "22855911"})
    assert gated.verdict == "ACCEPTED"
    assert gated.provenance.get("url") == "https://pubmed.ncbi.nlm.nih.gov/22855911/"


def test_busted_claim_still_gates_cleanly():
    result = assay_claim("Spirulina removes heavy metals from your brain.")
    gated = contribute_assay_result(result)
    assert gated.verdict == "NEEDS_SOURCE"
