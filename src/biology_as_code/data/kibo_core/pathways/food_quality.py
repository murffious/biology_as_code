"""
Food quality claims as L2 substrate modifiers + Defense soft priors.

Does NOT use C-5 / C-7 numbering. Magnitudes are prototype priors from
food_quality_claims.json — replace with measured FA/residue panels when present.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from biology_as_code.data.kibo_core.paths import data_file

_CLAIMS_JSON = data_file("food_quality_claims.json")


def load_quality_claims(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else _CLAIMS_JSON
    return json.loads(p.read_text(encoding="utf-8"))


def apply_substrate_folds(
    nutrient_amounts: dict[str, float],
    claim_id: str,
    *,
    doc: dict[str, Any] | None = None,
) -> dict[str, float]:
    """
    Multiply nutrient amounts by claim substrate folds.

    nutrient_amounts keys should match nutrient_ref where possible
    (e.g. nut.omega3, nut.alpha_tocopherol). Unknown keys pass through.
    """
    doc = doc or load_quality_claims()
    claim = next((c for c in doc["claims"] if c["id"] == claim_id), None)
    if claim is None:
        raise KeyError(f"unknown claim_id {claim_id}")

    out = dict(nutrient_amounts)
    for mod in claim.get("substrate_modifiers") or []:
        rel = mod.get("relation")
        fold = float(mod.get("fold", 1.0))
        if rel == "IDENTITY":
            continue
        target = mod.get("nutrient_ref") or mod.get("target")
        if not target or target == "substrate.nutrient_vector":
            # whole-vector identity already handled
            if target == "substrate.nutrient_vector" and fold != 1.0:
                out = {k: v * fold for k, v in out.items()}
            continue
        if target in out:
            out[target] = out[target] * fold
        # if nutrient not in vector, optionally seed 0 — skip (no invent)
    return out


def defense_prior_deltas(
    claim_id: str,
    *,
    doc: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Soft Defense-channel deltas (not disease verdicts)."""
    doc = doc or load_quality_claims()
    claim = next((c for c in doc["claims"] if c["id"] == claim_id), None)
    if claim is None:
        raise KeyError(f"unknown claim_id {claim_id}")
    return list(claim.get("defense_modifiers") or [])


def apply_claim_pipeline(
    nutrient_amounts: dict[str, float],
    claim_id: str,
) -> dict[str, Any]:
    """Full small pipeline step: substrate folds + defense prior list."""
    folded = apply_substrate_folds(nutrient_amounts, claim_id)
    return {
        "claim_id": claim_id,
        "substrate_after": folded,
        "defense_modifiers": defense_prior_deltas(claim_id),
        "layer": "L2_substrate",
        "systems": ["Assimilation", "Defense"],
    }
