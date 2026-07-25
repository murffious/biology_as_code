"""
Assay — nutrition claim catalog & stress-test engine (local foundations).

Compose-don't-invent: normalize wild claims to the SCHEMA.md CanonicalClaim,
run the 8-attack gauntlet as a pure function, emit scoped restatements +
schema.org ClaimReview. LLM may extract later; scoring never invents grades.
"""

from .ids import compute_claim_id, supersede
from .pipeline import AssayResult, assay_claim
from .schema import (
    AtomicClaim,
    CanonicalClaim,
    VerdictLabel,
    validate_claim,
)
from .score import RUBRIC_VERSION, score

__all__ = [
    "AtomicClaim",
    "AssayResult",
    "CanonicalClaim",
    "RUBRIC_VERSION",
    "VerdictLabel",
    "assay_claim",
    "compute_claim_id",
    "score",
    "supersede",
    "validate_claim",
]

__version__ = "0.1.0"
