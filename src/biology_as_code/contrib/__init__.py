"""
Crowd-sourced contributions, gated fail-closed.

The public surface is one function and its result type. A contribution is
validated the same way a claim is audited — structurally against
``schemas/contribution.schema.json`` and then against the constitution's policy
(a magnitude needs primary evidence, a target must resolve, unsourced stays
``OPEN``). Merging an ``ACCEPTED`` contribution is what grows the register.

    from biology_as_code.contrib import validate_contribution

    r = validate_contribution({
        "id": "contrib.evidence-unlu-2005-law020",
        "type": "evidence",
        "target": {"kind": "law", "ref": "LAW-020"},
        "payload": {"law": "LAW-020"},
        "source": {"kind": "pubmed", "pmid": "15735074"},
    })
    r.verdict   # 'ACCEPTED'
"""

from __future__ import annotations

from biology_as_code.contrib.validator import ContributionResult, validate_contribution

__all__ = ["ContributionResult", "validate_contribution"]
