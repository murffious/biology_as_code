"""The 7 functional systems — single source for the package."""

from __future__ import annotations

from typing import Literal

SevenSystem = Literal[
    "Assimilation",
    "Transport",
    "Communication",
    "Defense",
    "Biotransformation",
    "Energy",
    "Structure",
]

SEVEN_SYSTEMS: tuple[SevenSystem, ...] = (
    "Assimilation",
    "Transport",
    "Communication",
    "Defense",
    "Biotransformation",
    "Energy",
    "Structure",
)

SEVEN = frozenset(SEVEN_SYSTEMS)

# Short role cards (book Part 1)
SYSTEM_ROLES: dict[str, str] = {
    "Assimilation": "Break down food and absorb nutrients (lumen → enterocyte)",
    "Transport": "Move cargo in blood/lymph (lipoproteins, carriers)",
    "Communication": "Hormones, appetite, neural signals",
    "Defense": "Immune, barrier, antioxidant / iron-risk framing",
    "Biotransformation": "Hepatic pools, bile, redox, detox-style chemistry",
    "Energy": "ATP, fuel choice, SCFA recovery, storage/mobilization",
    "Structure": "Protein turnover, body composition, life-stage requirements",
}
