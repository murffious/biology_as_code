"""Hepatic / systemic *routes* for SCFA — teaching graph, not clearance fractions.

The pasted hepatic_metabolism.py correctly named distinct fates:

- acetate → peripheral acetyl-CoA / TCA (much of it escapes first-pass)
- propionate → hepatic succinyl-CoA / gluconeogenesis
- butyrate → colonocyte fuel; remainder can be ketogenic (BHB)

It then invented 0.70 / 0.90 / 0.85 splits and minted LAW-062 / LAW-063.
Those percentages are bound/evidence. den Besten 2013 and Stilling 2016
support route identity, not a universal clearance table.

Amounts stay OPEN. No new law ids.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from biology_as_code.dig.colon_fermentation import FermentResult, SCFAType

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]


class RouteSink(StrEnum):
    SYSTEMIC_ACETATE = "systemic_acetate"
    ACETYL_COA = "acetyl_coa"
    SUCCINYL_COA = "succinyl_coa"
    GLUCONEOGENESIS = "gluconeogenesis"
    COLONOCYTE_FUEL = "colonocyte_fuel"
    KETOGENESIS_BHB = "ketogenesis_bhb"
    TCA_CYCLE = "tca_cycle"


ROUTES: dict[SCFAType, tuple[RouteSink, ...]] = {
    SCFAType.ACETATE: (
        RouteSink.SYSTEMIC_ACETATE,
        RouteSink.ACETYL_COA,
        RouteSink.TCA_CYCLE,
    ),
    SCFAType.PROPIONATE: (
        RouteSink.SUCCINYL_COA,
        RouteSink.GLUCONEOGENESIS,
        RouteSink.TCA_CYCLE,
    ),
    SCFAType.BUTYRATE: (
        RouteSink.COLONOCYTE_FUEL,
        RouteSink.KETOGENESIS_BHB,
        RouteSink.ACETYL_COA,
        RouteSink.TCA_CYCLE,
    ),
}

TEACHING_SOURCES = {
    "den_besten_2013": {
        "citation": (
            "den Besten G, et al. The role of short-chain fatty acids in the "
            "interplay between diet, gut microbiota, and host energy metabolism."
        ),
        "pmid": "24347302",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/24347302/",
        "supports": "distinct SCFA fates (acetate/propionate/butyrate)",
        "does_not_support": "0.70/0.90/0.85 clearance fractions as law",
        "note": (
            "Pasted LAW-062 pointed at PMID 24023713; den Besten energy-metabolism "
            "review is 24347302. Identity citation only until a card exists."
        ),
    },
    "stilling_2016": {
        "citation": (
            "Stilling RM, et al. The neuropharmacology of butyrate: "
            "The bread and butter of the microbiota-gut-brain axis?"
        ),
        "pmid": "26859755",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/26859755/",
        "supports": "butyrate as a biologically active colon-derived SCFA",
        "does_not_support": "1 mol butyrate → 0.85 mol BHB as law",
        "note": "Pasted LAW-063 used PMID 26859528; Stilling butyrate review is 26859755.",
    },
}


@dataclass(frozen=True, slots=True)
class RouteResult:
    state: ConstitutionState
    sinks: tuple[str, ...]
    amounts: dict[str, None]
    note: str
    provenance: tuple[dict[str, str], ...]

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "sinks": list(self.sinks),
            "amounts": self.amounts,
            "note": self.note,
            "provenance": list(self.provenance),
        }


def route_scfa(ferment: FermentResult) -> RouteResult:
    if ferment.state != "HOLDS":
        return RouteResult(
            state=ferment.state,
            sinks=(),
            amounts={},
            note="no hepatic routing without an open fermentation gate",
            provenance=(),
        )
    sinks: list[str] = []
    for product in ferment.products:
        sinks.extend(s.value for s in ROUTES[product])
    unique = tuple(dict.fromkeys(sinks))
    return RouteResult(
        state="HOLDS",
        sinks=unique,
        amounts={sink: None for sink in unique},
        note="routes named; clearance fractions stay OPEN",
        provenance=(
            TEACHING_SOURCES["den_besten_2013"],
            TEACHING_SOURCES["stilling_2016"],
        ),
    )
