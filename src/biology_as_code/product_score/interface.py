"""
Contracts for optional proprietary product meal-score analysis.

Open tree implements only the protocol + unavailable stub.
Patent-pending algorithms live outside this file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass
class ProductScoreRequest:
    """Inputs the proprietary analyzer may use (all optional)."""

    payload: Any = None
    depth_report: dict[str, Any] | None = None
    bridge_report: dict[str, Any] | None = None
    host_context: dict[str, Any] | None = None
    persona: dict[str, Any] | None = None
    extras: dict[str, Any] = field(default_factory=dict)


@dataclass
class ProductScoreResult:
    """
    Output shell for **product meal score** and/or **Kibo-vars product scorer**.

    When ``available`` is False, proprietary product scoring was not run.
    Open dig may still have FLOW evals, claim verdicts, and teaching meters —
    those must **not** be stuffed into ``product_score``.
    """

    available: bool
    status: str
    product_score: float | None = None
    kibo_vars_score: dict[str, Any] | None = None
    axes: dict[str, Any] | None = None
    composite: dict[str, Any] | None = None
    honesty: str = "proprietary"
    patent_note: str = (
        "Product MEAL score and Kibo-vars product scorer are optional "
        "patent-pending modules. Open dig FLOW evals and claim evaluation "
        "do not require this plugin."
    )
    detail: dict[str, Any] = field(default_factory=dict)
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "available": self.available,
            "status": self.status,
            "product_score": self.product_score,
            "kibo_vars_score": self.kibo_vars_score,
            "axes": self.axes,
            "composite": self.composite,
            "honesty": self.honesty,
            "patent_note": self.patent_note,
            "detail": self.detail,
            "error": self.error,
            "schema": "kibo.ProductScoreAnalysis/v1",
            "excludes_open_flow": (
                "Does not replace dig residual, SCFA, minerals, pathway_regulation, "
                "or claim support|partial|refuse."
            ),
        }


@runtime_checkable
class ProductScoreAnalyzer(Protocol):
    """Proprietary plugin implements ``analyze``."""

    def analyze(self, request: ProductScoreRequest) -> ProductScoreResult: ...
