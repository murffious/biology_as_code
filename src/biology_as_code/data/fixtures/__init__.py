"""Package fixtures — open teaching data (not product meal score IP)."""

from pathlib import Path

from .meals import (
    MEALS_DIR,
    list_meal_files,
    list_meal_ids,
    load_meal,
    meal_to_food_payload_dict,
)
from .user_personas import (
    apply_persona_to_physiological_state,
    get_persona,
    list_personas,
    list_slugs,
    load_seed,
    persona_engine_profile,
    persona_to_clinical_context,
    persona_to_host_state,
    summarize_personas,
)

FIXTURES_DIR = Path(__file__).resolve().parent
VITAMINS_JSON = FIXTURES_DIR / "vitamins.json"


def vitamins_path() -> Path:
    """Path to teaching vitamins.json registry."""
    return VITAMINS_JSON


__all__ = [
    "FIXTURES_DIR",
    "MEALS_DIR",
    "VITAMINS_JSON",
    "apply_persona_to_physiological_state",
    "get_persona",
    "list_meal_files",
    "list_meal_ids",
    "list_personas",
    "list_slugs",
    "load_meal",
    "load_seed",
    "meal_to_food_payload_dict",
    "persona_engine_profile",
    "persona_to_clinical_context",
    "persona_to_host_state",
    "summarize_personas",
    "vitamins_path",
]
