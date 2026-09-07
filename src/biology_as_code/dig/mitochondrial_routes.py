"""Mitochondrial teaching routes — ATP and ROS as named paths, not computed moles.

The pasted mitochondrial_engine.py got the *names* right:

- acetyl-CoA enters TCA
- NADH / FADH2 feed ETC
- accepted teaching P/O is ~2.5 (NADH) and ~1.5 (FADH2)
- Complexes I and III can leak superoxide
- high substrate vs demand raises leak *directionally*

It then treated those as calculators: 10 ATP per mass unit, 2% base leak,
``load_ratio ** 1.5``, minted LAW-104 / LAW-105. Roadmap already says glycolysis /
TCA / ETC P/O are teaching invariants — not meal-level mole tallies.

Brand 2010 supports *sites* of superoxide production. Rich 2003 supports ETC
machinery. Neither licenses a nutrition-score ROS formula.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from biology_as_code.dig.hepatic_routes import RouteResult, RouteSink

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]

# Teaching P/O identity (not applied to meal grams).
PO_NADH = 2.5
PO_FADH2 = 1.5


class MitoSink(StrEnum):
    TCA_CYCLE = "tca_cycle"
    NADH = "nadh"
    FADH2 = "fadh2"
    ETC_OXPHOS = "etc_oxphos"
    ATP = "atp"
    SUPEROXIDE = "superoxide"
    OXIDATIVE_STRESS = "oxidative_stress"


TEACHING_SOURCES = {
    "rich_2003": {
        "citation": (
            "Rich PR. The molecular machinery of Keilin's respiratory chain. "
            "Biochem Soc Trans. 2003;31(Pt 6):1095-105."
        ),
        "pmid": "14641005",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/14641005/",
        "supports": "ETC as the respiratory chain that oxidizes NADH/FADH2",
        "does_not_support": "10 ATP per incoming mass unit of a NutrientState",
        "verified": "2026-09-07",
        "note": "The pasted card used 14668792, which resolves to no PubMed record.",
    },
    "brand_2010": {
        "citation": (
            "Brand MD. The sites and topology of mitochondrial superoxide production. "
            "Exp Gerontol. 2010;45(7-8):466-72."
        ),
        "pmid": "20064600",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/20064600/",
        "supports": "superoxide can form at defined ETC sites (incl. I and III)",
        "does_not_support": "a fixed base-leak constant or an exponential load term as law",
        "verified": "2026-09-07",
        "note": "The pasted card used 20463404, which names an unrelated Alzheimer paper.",
    },
}


@dataclass(frozen=True, slots=True)
class MitoResult:
    state: ConstitutionState
    sinks: tuple[str, ...]
    po_identity: dict[str, float]
    amounts: dict[str, None]
    note: str
    provenance: tuple[dict[str, str], ...]

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "sinks": list(self.sinks),
            "po_identity": self.po_identity,
            "amounts": self.amounts,
            "note": self.note,
            "provenance": list(self.provenance),
        }


def oxidize(hepatic: RouteResult) -> MitoResult:
    """Name the oxidative paths if hepatic routing HOLDS. Never emit ROS grams."""
    if hepatic.state != "HOLDS":
        return MitoResult(
            state=hepatic.state,
            sinks=(),
            po_identity={},
            amounts={},
            note="no mitochondrial walk without an open hepatic route",
            provenance=(),
        )

    needs_tca = RouteSink.TCA_CYCLE.value in hepatic.sinks or RouteSink.ACETYL_COA.value in hepatic.sinks
    if not needs_tca:
        return MitoResult(
            state="UNEVALUABLE",
            sinks=(),
            po_identity={},
            amounts={},
            note="hepatic sinks did not declare a TCA/acetyl-CoA seat",
            provenance=(),
        )

    sinks = tuple(s.value for s in MitoSink)
    return MitoResult(
        state="HOLDS",
        sinks=sinks,
        po_identity={"nadh": PO_NADH, "fadh2": PO_FADH2},
        amounts={s: None for s in sinks},
        note=(
            "P/O 2.5/1.5 is teaching identity; ATP moles and superoxide grams stay OPEN. "
            "High substrate vs demand raises leak directionally — no exponential table."
        ),
        provenance=(TEACHING_SOURCES["rich_2003"], TEACHING_SOURCES["brand_2010"]),
    )
