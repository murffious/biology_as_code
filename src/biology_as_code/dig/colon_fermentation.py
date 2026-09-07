"""Colonic fermentation teaching machine — issue #15, constitution-corrected.

Issue #15 proposed converting fiber grams into acetate/propionate/butyrate
grams with fixed yields (0.40 / 0.35) and molar ratios. Those magnitudes are
host-, microbiota-, and transit-dependent. Shipping them as law would violate
**empty beats fake** and **gate ≠ bound**.

What this module *does* assert, with a real citation:

- Soluble fiber and resistant starch that reach the colon are fermentation
  substrates (gate: substrate present).
- The characteristic products are acetate, propionate, and butyrate (SCFA).
- Product *amounts* stay OPEN unless a later evidence layer supplies them.

What it does not do:

- Invent % conversion or a 60:20:20 table as science.
- Mint a LAW-048 card (no card exists in the register).
- Raise on missing input (missing → UNEVALUABLE, not an exception).
- Wire into simulate_meal or the product score.

Teaching source for product identity, not for yields:
Macfarlane S, Macfarlane GT. Regulation of short-chain fatty acid production.
Proc Nutr Soc. 2003;62(1):67-72. PMID 12740060.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]

MACFARLANE_2003 = {
    "citation": (
        "Macfarlane S, Macfarlane GT. Regulation of short-chain fatty acid "
        "production. Proc Nutr Soc. 2003;62(1):67-72."
    ),
    "pmid": "12740060",
    "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/12740060/",
    "supports": "SCFA product identity (acetate, propionate, butyrate)",
    "does_not_support": "fixed mass-conversion yields or a universal molar ratio",
    "verified": "2026-09-07",
}


class FiberType(StrEnum):
    SOLUBLE = "soluble_fiber"
    RESISTANT_STARCH = "resistant_starch"


class SCFAType(StrEnum):
    ACETATE = "acetate"
    PROPIONATE = "propionate"
    BUTYRATE = "butyrate"


SCFA_PRODUCTS: tuple[SCFAType, ...] = (
    SCFAType.ACETATE,
    SCFAType.PROPIONATE,
    SCFAType.BUTYRATE,
)

DOWNSTREAM_TEACHING = {
    SCFAType.ACETATE: ("tca_cycle",),
    SCFAType.PROPIONATE: ("tca_cycle", "gluconeogenesis"),
    SCFAType.BUTYRATE: ("tca_cycle", "ketogenesis"),
}


@dataclass(frozen=True, slots=True)
class FermentResult:
    """Fail-closed result. Amounts are never invented."""

    state: ConstitutionState
    gate: Literal["open", "closed", "unknown"]
    fiber_type: FiberType | None
    substrate_declared: bool
    products: tuple[SCFAType, ...]
    amounts: dict[str, None]
    note: str
    provenance: dict[str, str]

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "gate": self.gate,
            "fiber_type": None if self.fiber_type is None else str(self.fiber_type),
            "substrate_declared": self.substrate_declared,
            "products": [str(p) for p in self.products],
            "amounts": self.amounts,
            "note": self.note,
            "provenance": self.provenance,
        }


def process_fiber(
    fiber_amount: float | None,
    fiber_type: FiberType | str | None,
) -> FermentResult:
    """Map a declared colon substrate to SCFA *paths*, not SCFA grams.

    * ``None`` amount or type → UNEVALUABLE (silence is not zero).
    * declared ``0`` → gate closed, REFUTED (no substrate, no fermentation).
    * declared ``> 0`` with a known type → gate open, HOLDS that products exist;
      amounts stay ``None`` (OPEN magnitude).
    """
    parsed_type = _parse_type(fiber_type)
    provenance = {
        "pmid": MACFARLANE_2003["pmid"],
        "pubmed_url": MACFARLANE_2003["pubmed_url"],
        "supports": MACFARLANE_2003["supports"],
    }

    if fiber_amount is None or parsed_type is None:
        return FermentResult(
            state="UNEVALUABLE",
            gate="unknown",
            fiber_type=parsed_type,
            substrate_declared=fiber_amount is not None,
            products=(),
            amounts={},
            note="fiber amount or type undeclared — not a zero yield",
            provenance=provenance,
        )

    if not isinstance(fiber_amount, (int, float)) or isinstance(fiber_amount, bool):
        return FermentResult(
            state="UNEVALUABLE",
            gate="unknown",
            fiber_type=parsed_type,
            substrate_declared=False,
            products=(),
            amounts={},
            note="fiber amount is not a number",
            provenance=provenance,
        )

    if fiber_amount < 0:
        return FermentResult(
            state="REFUSE",
            gate="unknown",
            fiber_type=parsed_type,
            substrate_declared=True,
            products=(),
            amounts={},
            note="negative fiber is a category error, not a yield",
            provenance=provenance,
        )

    if fiber_amount == 0:
        return FermentResult(
            state="REFUTED",
            gate="closed",
            fiber_type=parsed_type,
            substrate_declared=True,
            products=(),
            amounts={},
            note="declared zero colon substrate — fermentation path absent, not reduced",
            provenance=provenance,
        )

    return FermentResult(
        state="HOLDS",
        gate="open",
        fiber_type=parsed_type,
        substrate_declared=True,
        products=SCFA_PRODUCTS,
        amounts={p.value: None for p in SCFA_PRODUCTS},
        note=(
            "substrate present; acetate/propionate/butyrate paths exist; "
            "mass conversion stays OPEN (no fixed yield table)"
        ),
        provenance=provenance,
    )


def _parse_type(fiber_type: FiberType | str | None) -> FiberType | None:
    if fiber_type is None:
        return None
    if isinstance(fiber_type, FiberType):
        return fiber_type
    try:
        return FiberType(fiber_type)
    except ValueError:
        return None
