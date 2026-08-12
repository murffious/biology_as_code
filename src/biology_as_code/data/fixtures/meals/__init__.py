"""Open meal fixtures for dig sim — no product meal score / flow_score fields."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

log = logging.getLogger(__name__)

MEALS_DIR = Path(__file__).resolve().parent


def list_meal_files() -> list[Path]:
    return sorted(p for p in MEALS_DIR.glob("*.json") if p.name not in ("index.json",))


def list_meal_ids() -> list[str]:
    ids: list[str] = []
    for p in list_meal_files():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            ids.append(str(data.get("id") or p.stem))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            ids.append(p.stem)
    return ids


def load_meal(meal_id: str) -> dict[str, Any] | None:
    """Load one meal by id or filename stem (no score fields in public fixtures)."""
    key = meal_id.strip().lower()
    for p in list_meal_files():
        if p.stem.lower() == key or p.name.lower() == key:
            return json.loads(p.read_text(encoding="utf-8"))
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            log.debug("skip unreadable meal fixture %s", p.name)
            continue
        if str(data.get("id", "")).lower() == key:
            return data
    return None


def meal_to_food_payload_dict(meal: dict[str, Any]) -> dict[str, Any]:
    """
    Map fixture meal → fields useful for FoodPayload / dig (open path).

    Does **not** compute product meal score or vendor-variable score.
    """
    n = meal.get("nutrition_per_serving") or meal.get("nutrition") or {}
    derived = meal.get("derived") or {}
    return {
        "name": meal.get("name") or meal.get("id"),
        "macros_g": {
            "carbs": float(n.get("carbs_g") or n.get("carbs") or 0),
            "protein": float(n.get("protein_g") or n.get("protein") or 0),
            "fats": float(n.get("fat_g") or n.get("fats") or n.get("fat") or 0),
        },
        "fiber_g": float(n.get("fiber_g") or n.get("fiber") or 0),
        "quality_score": float(
            derived.get("food_quality") or meal.get("quality_score") or 0.7
        ),
        "nutrient_density_score": float(
            derived.get("nutrient_density") or meal.get("nutrient_density_score") or 0.7
        ),
        "vitamins_mg": {
            k.replace("_mg", "").replace("vitamin_", ""): float(v)
            for k, v in n.items()
            if ("vitamin" in k or k in ("folate_mcg", "iron_mg", "zinc_mg"))
            and isinstance(v, (int, float))
        },
        "meal_id": meal.get("id"),
    }


__all__ = [
    "MEALS_DIR",
    "list_meal_files",
    "list_meal_ids",
    "load_meal",
    "meal_to_food_payload_dict",
]
