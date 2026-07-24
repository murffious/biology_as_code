"""
Teaching organ bounds (Gropper-style crib — open tier).

Values are textbook ranges for FLOW metadata, not locked LAW-SPEC gates.
Source reference: biology_as_code_nutrition_intelligence-main (frozen).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrganBounds:
    name: str
    pH_range: tuple[float, float]
    transit_hours: tuple[float, float] | None
    daily_secretion_L: float | None
    notes: str = ""
    claim_tier: str = "open"


ORGAN_BOUNDS: dict[str, OrganBounds] = {
    "oral": OrganBounds(
        "Oral cavity",
        (6.5, 7.5),
        None,
        1.5,
        "Saliva ~1–2 L/day; α-amylase, lingual lipase",
    ),
    "stomach": OrganBounds(
        "Stomach",
        (1.5, 3.5),
        (1.0, 4.0),
        2.0,
        "Pepsin optimal ~3.5; high-fat emptying up to ~6 h",
    ),
    "small_intestine": OrganBounds(
        "Small intestine",
        (6.0, 7.5),
        (3.0, 5.0),
        None,
        "Primary absorption; duodenum neutralized by bicarbonate",
    ),
    "pancreas": OrganBounds(
        "Pancreas",
        (7.5, 8.5),
        None,
        2.0,
        "Zymogens + lipase/colipase; accessory",
    ),
    "liver_gallbladder": OrganBounds(
        "Liver + gallbladder",
        (7.0, 8.0),
        None,
        None,
        "Bile pool ~2.5–5 g; >90% enterohepatic reuptake (LAW-039 family)",
    ),
    "large_intestine": OrganBounds(
        "Large intestine",
        (5.5, 7.0),
        (12.0, 72.0),
        None,
        "SCFA from fermentation; LAW-025/026 open magnitudes",
    ),
}
