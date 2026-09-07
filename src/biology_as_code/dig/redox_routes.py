"""PPP → NADPH → glutathione reductase teaching routes.

Pastes named the right coupling:

- oxidative PPP: G6P + 2 NADP+ + H2O → Ru5P + 2 NADPH + CO2
- GR: GSSG + NADPH + H+ → 2 GSH + NADP+
- no NADPH, no GSH regeneration

They then mutated mmol pools and minted LAW-083 / LAW-092. Those pools are
host seats. Silent seats are UNEVALUABLE. Declared-empty seats close the gate.
Deponte 2013 and Stanton 2012 support enzyme identity, not meal-level ledgers.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from biology_as_code.dig.antioxidant_routes import DefenseResult
from biology_as_code.grounding import grounded

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]

PPP_NADPH_PER_G6P = grounded(
    2,
    tier="identity",
    pmid="22431005",
    supports="the oxidative PPP yields two NADPH per glucose-6-phosphate",
)
GR_GSH_PER_GSSG = grounded(
    2,
    tier="identity",
    pmid="23036594",
    supports="glutathione reductase returns two GSH per GSSG",
)
GR_NADPH_PER_GSSG = grounded(
    1,
    tier="identity",
    pmid="23036594",
    supports="glutathione reductase consumes one NADPH per GSSG",
)


class RedoxSink(StrEnum):
    G6P = "g6p"
    G6PD = "g6pd"
    PPP_OXIDATIVE = "ppp_oxidative"
    RU5P = "ribulose_5_phosphate"
    CO2 = "co2"
    NADP = "nadp"
    NADPH = "nadph"
    GR = "glutathione_reductase"
    GSH = "gsh"
    GSSG = "gssg"
    GLYCOLYSIS = "glycolysis"


TEACHING_SOURCES = {
    "stanton_2012": {
        "citation": (
            "Stanton RC. Glucose-6-phosphate dehydrogenase, NADPH, and cell survival. "
            "IUBMB Life. 2012;64(5):362-9."
        ),
        "pmid": "22431005",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/22431005/",
        "supports": "G6PD / PPP as a source of NADPH",
        "does_not_support": "a hexose-pool ledger or RER from a meal fiber field",
        "verified": "2026-09-07",
    },
    "deponte_2013": {
        "citation": (
            "Deponte M. Glutathione catalysis and the reaction mechanisms of "
            "glutathione-dependent enzymes. Biochim Biophys Acta. 2013;1830(5):3217-66."
        ),
        "pmid": "23036594",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/23036594/",
        "supports": "GR reduces GSSG with NADPH; 1 GSSG → 2 GSH",
        "does_not_support": "pasted ledger math",
        "verified": "2026-09-07",
        "note": (
            "The pasted card used 23380721 and an earlier fix used 23380711; both "
            "name unrelated papers. The Deponte review is 23036594."
        ),
    },
}


@dataclass(frozen=True, slots=True)
class RedoxResult:
    state: ConstitutionState
    gate: Literal["open", "closed", "unknown"]
    sinks: tuple[str, ...]
    stoichiometry: dict[str, int]
    amounts: dict[str, None]
    note: str
    provenance: tuple[dict[str, str], ...]

    def to_dict(self) -> dict:
        return {
            "state": self.state,
            "gate": self.gate,
            "sinks": list(self.sinks),
            "stoichiometry": self.stoichiometry,
            "amounts": self.amounts,
            "note": self.note,
            "provenance": list(self.provenance),
        }


def regenerate(
    defense: DefenseResult,
    *,
    g6p_declared: bool | None,
    nadph_declared: bool | None,
) -> RedoxResult:
    """Name PPP/GR paths. Host carbon and NADPH seats are fail-closed."""
    stoich = {
        "ppp_nadph_per_g6p": PPP_NADPH_PER_G6P,
        "gr_gsh_per_gssg": GR_GSH_PER_GSSG,
        "gr_nadph_per_gssg": GR_NADPH_PER_GSSG,
    }
    provenance = (TEACHING_SOURCES["stanton_2012"], TEACHING_SOURCES["deponte_2013"])

    if defense.state not in {"HOLDS", "REFUTED"}:
        return RedoxResult(
            state=defense.state,
            gate="unknown",
            sinks=(),
            stoichiometry={},
            amounts={},
            note="no GR/PPP walk without a defense evaluation",
            provenance=(),
        )

    if g6p_declared is None or nadph_declared is None:
        return RedoxResult(
            state="UNEVALUABLE",
            gate="unknown",
            sinks=(RedoxSink.PPP_OXIDATIVE.value, RedoxSink.GR.value),
            stoichiometry=stoich,
            amounts={},
            note="G6P or NADPH seat undeclared — not a zero pool",
            provenance=provenance,
        )

    if g6p_declared is False or nadph_declared is False:
        return RedoxResult(
            state="REFUTED",
            gate="closed",
            sinks=(RedoxSink.GSSG.value, RedoxSink.GLYCOLYSIS.value),
            stoichiometry=stoich,
            amounts={RedoxSink.GSSG.value: None},
            note="no NADPH regeneration; GSSG is not silently reduced; G6P may stay in glycolysis",
            provenance=provenance,
        )

    sinks = tuple(s.value for s in RedoxSink)
    return RedoxResult(
        state="HOLDS",
        gate="open",
        sinks=sinks,
        stoichiometry=stoich,
        amounts={s: None for s in sinks},
        note="PPP and GR paths open; pool sizes stay OPEN",
        provenance=provenance,
    )
