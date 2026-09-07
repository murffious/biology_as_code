"""SOD → GPx teaching routes. Stoichiometry is identity, not a GSH ledger.

The pasted antioxidant_defense.py named the right path:

- SOD: 2 O2•- + 2 H+ → H2O2 + O2
- GPx: H2O2 + 2 GSH → 2 H2O + GSSG
- undeclared/depleted GSH must not silently drop H2O2

It then required superoxide mmol from the mitochondrial paste and mutated a
host GSH pool. Those magnitudes were never declared. McCord & Fridovich 1969
and Lubos 2011 support enzyme identity, not a meal-level redox score.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Literal

from biology_as_code.dig.mitochondrial_routes import MitoResult
from biology_as_code.grounding import grounded

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]

# Identity only — never multiplied by a meal mass.
SOD_O2_PER_H2O2 = grounded(
    2,
    tier="identity",
    pmid="5389100",
    supports="SOD dismutates two superoxide anions per hydrogen peroxide",
)
GPX_GSH_PER_H2O2 = grounded(
    2,
    tier="identity",
    pmid="21087145",
    supports="GPx oxidises two GSH per hydrogen peroxide reduced",
)


class DefenseSink(StrEnum):
    SUPEROXIDE = "superoxide"
    SOD = "sod"
    HYDROGEN_PEROXIDE = "hydrogen_peroxide"
    GPX = "gpx"
    GSH = "gsh"
    GSSG = "gssg"
    WATER = "water"
    OXIDATIVE_STRESS = "oxidative_stress"


TEACHING_SOURCES = {
    "mccord_fridovich_1969": {
        "citation": (
            "McCord JM, Fridovich I. Superoxide dismutase. An enzymic function "
            "for erythrocuprein (hemocuprein). J Biol Chem. 1969;244(22):6049-55."
        ),
        "pmid": "5389100",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/5389100/",
        "supports": "SOD converts superoxide to hydrogen peroxide",
        "does_not_support": "a superoxide ledger derived from a meal fiber field",
        "verified": "2026-09-07",
    },
    "lubos_2011": {
        "citation": (
            "Lubos E, Loscalzo J, Handy DE. Glutathione peroxidase-1 in health and "
            "disease: from molecular mechanisms to therapeutic opportunities. "
            "Antioxid Redox Signal. 2011;15(7):1957-97."
        ),
        "pmid": "21087145",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/21087145/",
        "supports": "GPx reduces H2O2 with GSH",
        "does_not_support": "a pasted spillover ledger as a damage score",
        "verified": "2026-09-07",
        "note": "The pasted card used 21924744, which names an unrelated surgical paper.",
    },
}


@dataclass(frozen=True, slots=True)
class DefenseResult:
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


def defend(mito: MitoResult, *, gsh_declared: bool | None) -> DefenseResult:
    """Route superoxide if the mito walk HOLDS. GSH seat is fail-closed.

    * ``gsh_declared is None`` → UNEVALUABLE (host pool not on the packet)
    * ``gsh_declared is False`` → gate closed; H2O2 is not dropped
    * ``gsh_declared is True`` → path HOLDS; GSH/GSSG *amounts* stay OPEN
    """
    if mito.state != "HOLDS" or "superoxide" not in mito.sinks:
        return DefenseResult(
            state=mito.state if mito.state != "HOLDS" else "UNEVALUABLE",
            gate="unknown",
            sinks=(),
            stoichiometry={},
            amounts={},
            note="no defense walk without a named superoxide sink",
            provenance=(),
        )

    stoich = {
        "sod_o2_per_h2o2": SOD_O2_PER_H2O2,
        "gpx_gsh_per_h2o2": GPX_GSH_PER_H2O2,
    }
    provenance = (
        TEACHING_SOURCES["mccord_fridovich_1969"],
        TEACHING_SOURCES["lubos_2011"],
    )

    if gsh_declared is None:
        return DefenseResult(
            state="UNEVALUABLE",
            gate="unknown",
            sinks=(DefenseSink.SUPEROXIDE.value, DefenseSink.SOD.value, DefenseSink.HYDROGEN_PEROXIDE.value),
            stoichiometry=stoich,
            amounts={},
            note="GSH pool undeclared — not a zero pool and not full neutralization",
            provenance=provenance,
        )

    if gsh_declared is False:
        return DefenseResult(
            state="REFUTED",
            gate="closed",
            sinks=(
                DefenseSink.SUPEROXIDE.value,
                DefenseSink.SOD.value,
                DefenseSink.HYDROGEN_PEROXIDE.value,
                DefenseSink.OXIDATIVE_STRESS.value,
            ),
            stoichiometry=stoich,
            amounts={DefenseSink.HYDROGEN_PEROXIDE.value: None, DefenseSink.OXIDATIVE_STRESS.value: None},
            note="GSH seat closed; H2O2 is not silently dropped; magnitude stays OPEN",
            provenance=provenance,
        )

    sinks = tuple(s.value for s in DefenseSink if s is not DefenseSink.OXIDATIVE_STRESS)
    return DefenseResult(
        state="HOLDS",
        gate="open",
        sinks=sinks,
        stoichiometry=stoich,
        amounts={s: None for s in sinks},
        note="SOD/GPx path open; GSH:GSSG ratio is evidence, not this function",
        provenance=provenance,
    )
