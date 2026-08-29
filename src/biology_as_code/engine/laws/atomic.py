"""Load atomic pathway JSON — nutrient-bound stages walking down the system."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from biology_as_code.engine.paths import data_file

_DATA = data_file("path_nonhaem_iron.atomic.json")


def load_atomic_pathway(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else _DATA
    return json.loads(p.read_text(encoding="utf-8"))


def stages_in_order(doc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    d = doc or load_atomic_pathway()
    return sorted(d["stages"], key=lambda s: s["order"])


def iter_down_system(doc: dict[str, Any] | None = None) -> Iterator[dict[str, Any]]:
    """Yield stages from payload → terminus (spine order)."""
    yield from stages_in_order(doc)


def nutrient_bindings_at(stage: dict[str, Any]) -> dict[str, Any]:
    """All nutrient refs touched at this atomic unit."""
    cargo = stage.get("cargo") or {}
    primary = cargo.get("primary") or {}
    refs = []
    if primary.get("nutrient_ref"):
        refs.append(
            {
                "ref": primary["nutrient_ref"],
                "role": "primary_cargo",
                "form": primary.get("form"),
                "state": primary.get("state"),
                "ontology": primary.get("ontology"),
            }
        )
    for co in cargo.get("co_nutrients") or []:
        refs.append(
            {
                "ref": co.get("nutrient_ref"),
                "role": co.get("role"),
                "required_context": co.get("required_context"),
            }
        )
    for mod in (*(stage.get("enhancers") or []), *(stage.get("inhibitors") or [])):
        refs.append(
            {
                "ref": mod.get("nutrient_ref"),
                "role": f"modifier:{mod.get('relation')}",
                "law_id": mod.get("law_id"),
                "magnitude": mod.get("magnitude"),
            }
        )
    return {
        "stage_id": stage["id"],
        "system": stage["system"],
        "order": stage["order"],
        "bindings": refs,
    }


def walk_bindings(doc: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    """Full stack: nutrient science bindings moving down the system."""
    d = doc or load_atomic_pathway()
    catalog = d.get("nutrient_catalog") or {}
    out = []
    for stage in stages_in_order(d):
        unit = nutrient_bindings_at(stage)
        # enrich with catalog science
        for b in unit["bindings"]:
            ref = b.get("ref")
            if ref and ref in catalog:
                b["catalog"] = {
                    "label": catalog[ref].get("label"),
                    "ontology": catalog[ref].get("ontology"),
                    "laws": catalog[ref].get("laws"),
                    "roles_on_this_pathway": catalog[ref].get("roles_on_this_pathway"),
                }
        unit["science"] = stage.get("science")
        unit["mechanisms"] = stage.get("mechanisms")
        unit["transporters"] = stage.get("transporters")
        unit["laws"] = stage.get("laws")
        unit["next_pathways"] = stage.get("next_pathways")
        unit["priors"] = stage.get("priors")
        out.append(unit)
    return out


def binding_qa(doc: dict[str, Any] | None = None) -> dict[str, Any]:
    d = doc or load_atomic_pathway()
    catalog = d.get("nutrient_catalog") or {}
    errors: list[str] = []
    warns: list[str] = []
    stages = stages_in_order(d)
    # spine continuity
    for i, s in enumerate(stages[:-1]):
        nxt = s.get("next_pathways") or []
        if not nxt:
            errors.append(f"{s['id']} non-terminus missing next_pathways")
        elif nxt[0] != stages[i + 1]["id"]:
            errors.append(f"{s['id']} next {nxt[0]} != spine {stages[i+1]['id']}")
    # every nutrient_ref in catalog
    for s in stages:
        for b in nutrient_bindings_at(s)["bindings"]:
            ref = b.get("ref")
            if not ref:
                errors.append(f"{s['id']} empty nutrient_ref")
            elif ref not in catalog:
                errors.append(f"{s['id']} unbound nutrient_ref {ref}")
        if not s.get("cargo", {}).get("primary", {}).get("nutrient_ref"):
            errors.append(f"{s['id']} missing primary nutrient_ref")
        if not s.get("priors"):
            errors.append(f"{s['id']} missing priors")
        if not s.get("science", {}).get("summary") and not s.get("science", {}).get("gap"):
            warns.append(f"{s['id']} thin science block")
        if not s.get("laws"):
            warns.append(f"{s['id']} no laws attached (growth point)")
    return {
        "ok": len(errors) == 0,
        "errors": errors,
        "warns": warns,
        "n_stages": len(stages),
        "n_catalog": len(catalog),
    }
