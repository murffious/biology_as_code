"""Digestive path geography (K1–K7) — where; systems are what job."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Kingdom:
    id: str
    name: str
    primary_system: str
    organ_seat: str
    sim_phase: str | None = None


KINGDOMS: tuple[Kingdom, ...] = (
    Kingdom("K1", "Ingestion", "Assimilation", "Mouth, teeth", "mouth"),
    Kingdom("K2", "Acid reactor", "Assimilation", "Stomach", "stomach"),
    Kingdom(
        "K3",
        "Emulsification",
        "Assimilation",
        "Liver, gallbladder, pancreas",
        "small_intestine",
    ),
    Kingdom("K4", "Assimilation (SI)", "Assimilation", "Small intestine", "small_intestine"),
    Kingdom("K5", "Fermentation", "Energy", "Colon", "large_intestine"),
    Kingdom("K6", "Transport highways", "Transport", "Blood, lymph", None),
    Kingdom("K7", "Energy & structure", "Energy", "Cell, mitochondrion, tissues", "liver"),
)


def kingdom_for_phase(phase_name: str) -> Kingdom | None:
    for k in KINGDOMS:
        if k.sim_phase == phase_name:
            return k
    return None
