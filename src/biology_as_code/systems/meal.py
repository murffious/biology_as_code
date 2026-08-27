"""Meal observation object.

Only *declared* fields may close a gate. Missing ≠ 0.
A plain dict is accepted; this wrapper records which keys were actually present.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

# Keys adapters are allowed to read. Anything else is ignored, not invented.
KNOWN_FIELDS: frozenset[str] = frozenset(
    {
        "meal_id",
        "label",
        "nova_group",
        "matrix",  # intact | disrupted | unknown
        "eating_rate_kcal_min",
        "eating_rate_g_min",
        "energy_density_kcal_g",
        "energy_kcal",
        "available_carb_g",
        "protein_g",
        "fat_g",
        "fiber_g",
        "sodium_mg",
        "added_sugar_g",
        "gi",
        "gl",
        "hpf_fat_sodium",
        "hpf_fat_sugar",
        "hpf_carb_sodium",
        "emulsifiers_declared",
        "cosmetic_additives_declared",
        "lipid_vehicle_g",
        "fat_soluble_cargo",
        "nonhaem_iron_mg",
        "ascorbate_mg",
        "tea_polyphenols",
        "incretin_measured",
        "glp1_iAUC",
        "weight_change_kg",
        "notes",
    }
)


@dataclass(frozen=True)
class MealObservation:
    raw: Mapping[str, Any]
    declared: frozenset[str]

    @classmethod
    def from_mapping(cls, data: Mapping[str, Any] | None) -> "MealObservation":
        raw = dict(data or {})
        declared = frozenset(k for k in raw if k in KNOWN_FIELDS and raw[k] is not None)
        return cls(raw=raw, declared=declared)

    def declares(self, key: str) -> bool:
        return key in self.declared

    def get(self, key: str, default: Any = None) -> Any:
        if key not in self.declared:
            return default
        return self.raw[key]

    @property
    def meal_id(self) -> str:
        return str(self.raw.get("meal_id") or self.raw.get("label") or "unnamed")
