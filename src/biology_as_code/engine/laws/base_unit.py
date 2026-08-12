"""
Base unit = one AtomicPathwayStage fully filled.

Inspired by GROK_laws.md law object (id, systems, organs, bounds, pathwayDetails,
appApplications, sources) but seated on OUR stack:
  7 systems · cargo nutrient_ref · digestive FKs · laws · next_pathways · priors

A pathway is an ordered list of base units.
A WalkPacket carries meal/host context across units.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SEVEN = frozenset(
    {
        "Assimilation",
        "Transport",
        "Communication",
        "Defense",
        "Biotransformation",
        "Energy",
        "Structure",
    }
)

# Required top-level keys for a "fully filled" base unit
REQUIRED_KEYS = frozenset(
    {
        "id",
        "order",
        "label",
        "system",
        "organ",
        "subsystem",
        "depth",
        "science",
        "cargo",
        "mechanisms",
        "transporters",
        "compartments",
        "laws",
        "enhancers",
        "inhibitors",
        "gates",
        "priors",
        "next_pathways",
        "bounds_and_conditions",  # GROK-shaped, explicit
        "sources",
        "app_applications",
        "ontology_layer_span",
    }
)

from biology_as_code.engine.paths import DATA as _DATA

_GOLDEN = _DATA / "base_unit_lumen_iron.filled.json"


@dataclass
class BoundsAndConditions:
    """GROK-inspired bounds block — magnitudes + modifiers, not a gate dump."""

    lower_bound: float | str | None = None
    upper_bound: float | str | None = None
    units: str = ""
    modifying_factors: list[str] = field(default_factory=list)
    risks_of_deviation: str = ""
    gate_text: str = "none"
    conditions_text: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def validate_base_unit(unit: dict[str, Any], *, strict_full: bool = True) -> dict[str, Any]:
    """
    Validate a base-unit dict.

    strict_full=True requires all REQUIRED_KEYS and non-empty science/cargo/priors.
    """
    errors: list[str] = []
    warns: list[str] = []

    if strict_full:
        missing = REQUIRED_KEYS - set(unit.keys())
        if missing:
            errors.append(f"missing keys: {sorted(missing)}")

    uid = unit.get("id", "?")
    system = unit.get("system")
    if system not in SEVEN:
        errors.append(f"{uid}: system must be one of 7, got {system!r}")

    cargo = unit.get("cargo") or {}
    primary = cargo.get("primary") or {}
    if not primary.get("nutrient_ref"):
        errors.append(f"{uid}: cargo.primary.nutrient_ref required")
    if not primary.get("form"):
        errors.append(f"{uid}: cargo.primary.form required")
    if not primary.get("state"):
        errors.append(f"{uid}: cargo.primary.state required")

    priors = unit.get("priors") or {}
    for k, v in priors.items():
        try:
            fv = float(v)
        except (TypeError, ValueError):
            errors.append(f"{uid}: prior {k} not numeric")
            continue
        if not 0.0 <= fv <= 1.0:
            errors.append(f"{uid}: prior {k}={fv} out of [0,1]")

    for key in ("human_evidence", "magnitude_locked", "ontology_bound"):
        if key not in priors and strict_full:
            warns.append(f"{uid}: recommended prior missing: {key}")

    if "next_pathways" not in unit:
        errors.append(f"{uid}: next_pathways required (use [] at terminus)")
    elif not isinstance(unit["next_pathways"], list):
        errors.append(f"{uid}: next_pathways must be list")

    science = unit.get("science") or {}
    if strict_full and not science.get("summary"):
        errors.append(f"{uid}: science.summary required when fully filled")

    bac = unit.get("bounds_and_conditions") or {}
    if strict_full:
        if "modifying_factors" not in bac:
            errors.append(f"{uid}: bounds_and_conditions.modifying_factors required")
        if not bac.get("conditions_text") and not bac.get("gate_text"):
            warns.append(f"{uid}: bounds_and_conditions thin")

    # Modifier shapes
    for bucket in ("enhancers", "inhibitors"):
        for mod in unit.get(bucket) or []:
            if not mod.get("law_id", "").startswith("LAW-") and not mod.get("law_id", "").startswith("L-"):
                warns.append(f"{uid}: {bucket} {mod.get('id')} law_id unusual: {mod.get('law_id')}")
            if mod.get("requires_context") is None and bucket in ("enhancers", "inhibitors"):
                if mod.get("relation") not in (None, "IDENTITY"):
                    errors.append(f"{uid}: {mod.get('id')} needs requires_context")
            mag = mod.get("magnitude")
            if mag is not None and float(mag) <= 0:
                errors.append(f"{uid}: {mod.get('id')} magnitude must be > 0")

    # Ontology layer span 1-5
    span = unit.get("ontology_layer_span") or []
    if strict_full:
        if not span:
            errors.append(f"{uid}: ontology_layer_span required e.g. [2,3,4]")
        for n in span:
            if n not in (1, 2, 3, 4, 5):
                errors.append(f"{uid}: bad layer {n}")

    return {"ok": len(errors) == 0, "errors": errors, "warns": warns, "id": uid}


def load_golden_base_unit(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else _GOLDEN
    return json.loads(p.read_text(encoding="utf-8"))


def base_unit_to_pathway_node_fields(unit: dict[str, Any]) -> dict[str, Any]:
    """Project a filled base unit onto PathwayNode-relevant fields for walk engine."""
    return {
        "id": unit["id"],
        "label": unit.get("label", unit["id"]),
        "system": unit["system"],
        "organ": unit.get("organ", ""),
        "subsystem": unit.get("subsystem", ""),
        "next_pathways": tuple(unit.get("next_pathways") or ()),
        "law_ids": tuple(
            (x.get("id") if isinstance(x, dict) else x) for x in (unit.get("laws") or [])
        ),
        "priors": dict(unit.get("priors") or {}),
        "enhancers": unit.get("enhancers") or [],
        "inhibitors": unit.get("inhibitors") or [],
    }
