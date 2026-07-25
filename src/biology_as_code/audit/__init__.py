"""
Fail-closed claim auditor — feed it a claim, get a provenance-backed verdict.

    from biology_as_code import Claim, audit_claim
    from biology_as_code.packets import get_packet

    claim = Claim(
        id="claim.spinach_vitA_no_fat",
        surface_claim="Fat-free spinach salad prevents vitamin A deficiency",
        verb_class="disease_claim",
        nutrient="beta_carotene",
    )
    audit_claim(claim, get_packet("ex.spinach_salad.zero_fat")).verdict
    # 'Busted'  — gate closed at L3, no lipid phase declared

The auditor never invents a number and never defaults to a pass. When a packet is
silent about a required co-factor the verdict is ``UNEVALUABLE``, not ``fail`` —
silence is not a zero. See :mod:`biology_as_code.audit.auditor` for the verdict
lattice and :mod:`biology_as_code.audit.gates` for the rule table.
"""

from biology_as_code.audit.auditor import (
    BoundFinding,
    Claim,
    ClaimAudit,
    audit_claim,
    audit_packet_coverage,
)
from biology_as_code.audit.gates import (
    BOUND_RULES,
    GATE_RULES,
    BoundRule,
    GateRule,
    all_law_refs,
    bounds_for,
    gates_for,
    known_nutrients,
)

__all__ = [
    "BOUND_RULES",
    "GATE_RULES",
    "BoundFinding",
    "BoundRule",
    "Claim",
    "ClaimAudit",
    "GateRule",
    "all_law_refs",
    "audit_claim",
    "audit_packet_coverage",
    "bounds_for",
    "gates_for",
    "known_nutrients",
]
