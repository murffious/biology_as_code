"""
Organ → body system map for multi-organ claim charts.

Pinterest/TikTok "heal your organs" cards name organs; evaluation should
also surface the *system* so claims can be catalogued under cardiovascular,
hepatic, renal, etc. — not only a laundry list of organs.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrganSystem:
    organ: str
    organ_key: str
    system_id: str
    system_label: str
    """UBERON-ish site label for AtomicClaim.site"""
    site: str
    """Honest functional capacity language (not disease cure)"""
    capacity_frame: str


# Canonical organ rows for the viral "ORGAN HEALING DRINKS" family of cards.
ORGAN_SYSTEMS: dict[str, OrganSystem] = {
    "eyes": OrganSystem(
        organ="eyes",
        organ_key="eyes",
        system_id="sensory-visual",
        system_label="Sensory / visual system",
        site="eye / retina",
        capacity_frame="visual function / macular nutrition research",
    ),
    "eye": OrganSystem(
        organ="eyes",
        organ_key="eyes",
        system_id="sensory-visual",
        system_label="Sensory / visual system",
        site="eye / retina",
        capacity_frame="visual function / macular nutrition research",
    ),
    "brain": OrganSystem(
        organ="brain",
        organ_key="brain",
        system_id="nervous",
        system_label="Nervous system / cerebral perfusion",
        site="brain / cerebral vasculature",
        capacity_frame="cerebral blood flow / cognitive nutrition literature",
    ),
    "lungs": OrganSystem(
        organ="lungs",
        organ_key="lungs",
        system_id="respiratory",
        system_label="Respiratory system",
        site="lungs / airways",
        capacity_frame="airway comfort / respiratory symptom literature",
    ),
    "lung": OrganSystem(
        organ="lungs",
        organ_key="lungs",
        system_id="respiratory",
        system_label="Respiratory system",
        site="lungs / airways",
        capacity_frame="airway comfort / respiratory symptom literature",
    ),
    "liver": OrganSystem(
        organ="liver",
        organ_key="liver",
        system_id="hepatic-metabolic",
        system_label="Hepatic / metabolic system",
        site="liver",
        capacity_frame="hepatic enzyme / metabolic literature (not 'detox' slogans)",
    ),
    "kidneys": OrganSystem(
        organ="kidneys",
        organ_key="kidneys",
        system_id="renal",
        system_label="Renal / fluid-electrolyte system",
        site="kidneys",
        capacity_frame="hydration / electrolyte balance (not kidney 'cleanse')",
    ),
    "kidney": OrganSystem(
        organ="kidneys",
        organ_key="kidneys",
        system_id="renal",
        system_label="Renal / fluid-electrolyte system",
        site="kidneys",
        capacity_frame="hydration / electrolyte balance (not kidney 'cleanse')",
    ),
    "heart": OrganSystem(
        organ="heart",
        organ_key="heart",
        system_id="cardiovascular",
        system_label="Cardiovascular system",
        site="heart / vessels",
        capacity_frame="vascular function / cardiometabolic diet literature",
    ),
}


def resolve_organ(token: str) -> OrganSystem | None:
    t = token.strip().lower()
    return ORGAN_SYSTEMS.get(t)


def systems_index() -> list[dict[str, str]]:
    """Unique systems for UI grouping."""
    seen: dict[str, dict[str, str]] = {}
    for o in ORGAN_SYSTEMS.values():
        if o.system_id not in seen:
            seen[o.system_id] = {
                "system_id": o.system_id,
                "system_label": o.system_label,
                "example_organ": o.organ,
            }
    return list(seen.values())
