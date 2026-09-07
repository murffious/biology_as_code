"""Respiratory control as an ADP seat — last unused idea from the ETC paste.

What we *used* from the pasted series (after review), as teaching identity:

- colon: fiber → acetate / propionate / butyrate names (Macfarlane 2003)
- chyme: unabsorbed fiber must be handed off, not dropped
- hepatic: distinct SCFA fates
- mito: TCA → NADH/FADH2 → ETC; P/O 2.5 / 1.5; superoxide at I/III
- defense: SOD then GPx; 2 O2•- / H2O2; 2 GSH / H2O2
- redox: PPP 2 NADPH / G6P; GR 1 GSSG + 1 NADPH → 2 GSH
- this file: ADP present → State 3; ADP absent → State 4 leak *direction*

What we did not use from any paste: yield tables, mmol ledgers, minted LAW-ids,
min(pool, pool) meal engines, pytest.approx gram tests, simulate_meal rewires.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from biology_as_code.dig.mitochondrial_routes import MitoResult

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]
ChanceState = Literal["state_3", "state_4", "unknown"]

TEACHING_SOURCES = {
    "mitchell_1961": {
        "citation": (
            "Mitchell P. Coupling of phosphorylation to electron and hydrogen "
            "transfer by a chemi-osmotic type of mechanism. Nature. 1961;191:144-8."
        ),
        "pmid": "13771349",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/13771349/",
        "supports": "ADP phosphorylation is coupled to electron transfer",
        "does_not_support": "an ADP-capped ATP ledger as a meal law",
        "verified": "2026-09-07",
    },
    "murphy_2009": {
        "citation": (
            "Murphy MP. How mitochondria produce reactive oxygen species. "
            "Biochem J. 2009;417(1):1-13."
        ),
        "pmid": "19061483",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/19061483/",
        "supports": "ROS rise when the chain is reduced / potential is high",
        "does_not_support": "a leak percentage attached to a meal field",
        "verified": "2026-09-07",
        "note": (
            "The pasted card used 19028888 and an earlier fix used 19052988; both "
            "name unrelated papers. The Biochem J review is 19061483."
        ),
    },
}


@dataclass(frozen=True, slots=True)
class ControlResult:
    state: ConstitutionState
    chance_state: ChanceState
    leak_direction: Literal["low", "high", "unknown"]
    amounts: dict[str, None]
    note: str
    provenance: tuple[dict[str, str], ...]

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "chance_state": self.chance_state,
            "leak_direction": self.leak_direction,
            "amounts": self.amounts,
            "note": self.note,
            "provenance": list(self.provenance),
        }


def respire(mito: MitoResult, *, adp_declared: bool | None) -> ControlResult:
    """State 3 vs State 4 from the ADP seat. No leak percentages."""
    provenance = (TEACHING_SOURCES["mitchell_1961"], TEACHING_SOURCES["murphy_2009"])
    if mito.state != "HOLDS":
        return ControlResult(
            state=mito.state,
            chance_state="unknown",
            leak_direction="unknown",
            amounts={},
            note="no respiratory-control walk without an open ETC path",
            provenance=(),
        )
    if adp_declared is None:
        return ControlResult(
            state="UNEVALUABLE",
            chance_state="unknown",
            leak_direction="unknown",
            amounts={},
            note="ADP seat undeclared — not a sedentary default",
            provenance=provenance,
        )
    if adp_declared is False:
        return ControlResult(
            state="REFUTED",
            chance_state="state_4",
            leak_direction="high",
            amounts={"atp": None, "superoxide": None},
            note="ADP seat empty; State 4 direction; leak magnitude stays OPEN",
            provenance=provenance,
        )
    return ControlResult(
        state="HOLDS",
        chance_state="state_3",
        leak_direction="low",
        amounts={"atp": None, "superoxide": None},
        note="ADP seat present; State 3 direction; still not 0.5% of anything",
        provenance=provenance,
    )
