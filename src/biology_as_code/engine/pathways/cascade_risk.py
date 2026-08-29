"""
Soft system-cascade risk priors (screenshot C-7 idea, our 7 systems).

Does not diagnose disease. Does not use C-5/C-7 numbering.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from biology_as_code.engine.paths import data_file

_JSON = data_file("system_cascade_risk.json")

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


def load_cascades(path: Path | str | None = None) -> dict[str, Any]:
    p = Path(path) if path else _JSON
    return json.loads(p.read_text(encoding="utf-8"))


def _trigger_hits(trigger: dict[str, Any], nutrient_flags: dict[str, str]) -> bool:
    """nutrient_flags values: 'low' | 'ok' | 'high' etc."""
    refs = [trigger.get("nutrient_ref")] + list(trigger.get("also_accept") or [])
    for ref in refs:
        if not ref:
            continue
        if nutrient_flags.get(ref) == "low":
            return True
    return False


def propagate_cascades(
    nutrient_flags: dict[str, str],
    *,
    doc: dict[str, Any] | None = None,
    amplification: float = 1.0,
) -> dict[str, Any]:
    """
    Given nutrient status flags, walk matching cascades and sum soft risk deltas.

    amplification < 1 models 'variety over restriction' dampening.
    """
    doc = doc or load_cascades()
    amp = max(0.0, min(1.0, float(amplification)))
    risk_priors: dict[str, float] = {}
    fired: list[dict[str, Any]] = []
    systems_touched: set[str] = set()

    for cascade in doc.get("cascades") or []:
        if not _trigger_hits(cascade["trigger"], nutrient_flags):
            continue
        hop_log = []
        for hop in cascade.get("hops") or []:
            sys = hop["system"]
            if sys not in SEVEN:
                raise ValueError(f"bad system {sys} in {cascade['id']}")
            systems_touched.add(sys)
            key = hop["risk_key"]
            delta = float(hop["delta"]) * amp
            risk_priors[key] = risk_priors.get(key, 0.0) + delta
            hop_log.append(
                {
                    "order": hop["order"],
                    "system": sys,
                    "risk_key": key,
                    "delta": delta,
                    "node": hop["node"],
                }
            )
        fired.append(
            {
                "cascade_id": cascade["id"],
                "label": cascade["label"],
                "hops": hop_log,
                "narrative": cascade.get("narrative_template"),
                "claim_tier": doc.get("claim_tier_default", "open"),
                "ssi": cascade.get("ssi"),
            }
        )

    return {
        "nutrient_flags": nutrient_flags,
        "amplification": amp,
        "risk_priors": risk_priors,
        "cascades_fired": fired,
        "systems_touched": sorted(systems_touched),
        "refuse": doc.get("refuse"),
        "diagnosis": False,
        "message": (
            "Soft multi-system risk priors only — not a clinical diagnosis."
            if fired
            else "No cascade triggers matched."
        ),
    }


def variety_amplification(distinct_nutrient_ok_count: int, *, full_panel: int = 12) -> float:
    """
    Higher dietary variety (more nutrients not flagged low) → lower cascade amp.
    full_panel is a teaching constant, not an RDA.
    """
    if full_panel <= 0:
        return 1.0
    covered = max(0, min(full_panel, distinct_nutrient_ok_count))
    # 0 ok → amp 1.0; full panel ok → amp 0.4
    return round(1.0 - 0.6 * (covered / full_panel), 3)
