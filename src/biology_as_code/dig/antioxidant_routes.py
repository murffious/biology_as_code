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

ConstitutionState = Literal["HOLDS", "UNEVALUABLE", "REFUTED", "OPEN", "REFUSE"]

# Identity only — never multiplied by a meal mass.
SOD_O2_PER_H2O2 = 2
GPX_GSH_PER_H2O2 = 2


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
            "for erythrocuprein (hemocuprein)."
        ),
        "pmid": "5389100",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/5389100/",
        "supports": "SOD converts superoxide to hydrogen peroxide",
        "does_not_support": "mmol superoxide from a meal fiber field",
    },
    "lubos_2011": {
        "citation": "Lubos E, Loscalzo J, Handy DE. Glutathione peroxidase-1 in health and disease.",
        "pmid": "21924744",
        "pubmed_url": "https://pubmed.ncbi.nlm.nih.gov/21924744/",
        "supports": "GPx reduces H2O2 with GSH",
        "does_not_support": "LAW-082 spillover mmol as a damage score",
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
