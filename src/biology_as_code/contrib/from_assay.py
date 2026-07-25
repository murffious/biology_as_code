"""
Bridge: an assay claim verdict -> a fail-closed contribution.

The claims agent proposes; the contribution gate disposes. :func:`assay_claim`
produces a deterministic verdict (BUSTED / PLAUSIBLE / CONFIRMED) for a health
claim; this turns that into a ``type: "claim"`` contribution for the reference
corpus and (optionally) runs it through :func:`validate_contribution`.

Without a primary ``source``, the gate returns ``NEEDS_SOURCE`` — the agent can
never auto-accept its own claims. Attach a harvested PMID and the same claim can
be ``ACCEPTED``. This is Door B in one function: LLM extracts, the deterministic
gauntlet scores, the fail-closed gate admits.
"""

from __future__ import annotations

import re
from typing import Any

from biology_as_code.agents.assay.pipeline import AssayResult, assay_to_public_dict
from biology_as_code.contrib.validator import ContributionResult, validate_contribution


def assay_result_to_contribution(
    result: AssayResult,
    *,
    source: dict[str, Any] | None = None,
    contributor: str = "assay-agent",
) -> dict[str, Any]:
    """Serialise an assay result as a contribution dict. Does not gate it."""
    pub = assay_to_public_dict(result)
    verdict = pub.get("verdict") or {}
    slug = re.sub(r"[^a-z0-9]+", "-", str(pub["claim_id"]).lower()).strip("-") or "claim"
    contribution: dict[str, Any] = {
        "id": f"contrib.claim-{slug}",
        "type": "claim",
        "target": {"kind": "claim", "ref": str(pub["claim_id"])},
        "payload": {
            "verdict": verdict.get("label"),
            "rubric_version": verdict.get("rubric_version"),
            "confidence": pub.get("confidence"),
            "scoped_restatement": pub.get("scoped_restatement"),
            "matched_fixture": pub.get("matched_fixture"),
        },
        "contributor": contributor,
        "asserts_magnitude": False,  # a verdict is not a magnitude
    }
    if source:
        contribution["source"] = source
    return contribution


def contribute_assay_result(
    result: AssayResult,
    *,
    source: dict[str, Any] | None = None,
    contributor: str = "assay-agent",
) -> ContributionResult:
    """Produce a contribution from an assay result and gate it fail-closed."""
    return validate_contribution(
        assay_result_to_contribution(result, source=source, contributor=contributor)
    )
