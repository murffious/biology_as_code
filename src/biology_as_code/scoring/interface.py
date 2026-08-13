"""
Contract for an optional, out-of-tree scorer.

The open tree implements the protocol and an unavailable stub, nothing else.
No scoring weights, axis cutoffs, tier boundaries or composite formulas live in
this repository, and none may be added — a scorer is somebody else's software
that this package agrees to call.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

SCHEMA_ID = "bac.ExternalScoreAnalysis/v1"


@dataclass
class ScoreRequest:
    """Inputs a scorer may read. Every field is optional."""

    payload: Any = None
    depth_report: dict[str, Any] | None = None
    bridge_report: dict[str, Any] | None = None
    host_context: dict[str, Any] | None = None
    persona: dict[str, Any] | None = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class ScoreResult:
    """
    Output shell for whatever composite an external scorer computes.

    When ``available`` is False no external scoring ran. Open-tree FLOW evals,
    claim verdicts and teaching meters are still produced by the engine — they
    must **not** be copied into ``product_score`` or ``vendor_scores`` to make
    a result look scored.

    ``product_score`` is the scorer's single headline number, whatever it
    means to that scorer; ``vendor_scores`` carries any additional named
    values it wants to return. Both are opaque to this package.
    """

    available: bool
    status: str
    product_score: float | None = None
    vendor_scores: dict[str, Any] | None = None
    axes: dict[str, Any] | None = None
    composite: dict[str, Any] | None = None
    honesty: str = "external"
    provenance_note: str = (
        "Score produced by an external plugin outside this repository. "
        "Open-tier FLOW evaluation and claim adjudication do not require it "
        "and are not derived from it."
    )
    detail: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "status": self.status,
            "product_score": self.product_score,
            "vendor_scores": self.vendor_scores,
            "axes": self.axes,
            "composite": self.composite,
            "honesty": self.honesty,
            "provenance_note": self.provenance_note,
            "detail": self.detail,
            "error": self.error,
            "schema": SCHEMA_ID,
            "excludes_open_flow": (
                "Does not replace dig residual, SCFA, minerals, pathway_regulation, "
                "or claim support|partial|refuse."
            ),
        }


@runtime_checkable
class ScorerPlugin(Protocol):
    """An external scorer implements exactly this."""

    def analyze(self, request: ScoreRequest) -> ScoreResult: ...
