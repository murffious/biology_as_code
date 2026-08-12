"""
User persona seed loader (public package fixtures).

SSOT: biology_as_code/data/fixtures/user-personas.json
Any external-scorer telemetry is stripped from public fixtures.

Not real PHI. Not clinical decision support. Carries no scoring IP.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

_HERE = Path(__file__).resolve().parent
_LOCAL_SEED = _HERE / "user-personas.json"
_LOCAL_INVENTORY = _HERE / "user-persona-data-inventory.json"

# Keys never exposed on public load. The committed seed carries none of them;
# the filter is a standing guard so an upstream re-export cannot leak scorer
# telemetry into the open fixtures without the test suite noticing.
_SCRUB_KEYS = frozenset(
    {
        "flow_score",
        "app_vendor_score",
        "vendor_score_hint",
        "vendor_score_trend",
        "product_score",
        "external_score_analysis",
        "vendor_vars",
        "vendor_scores",
        "score_axes",
        "meal_score",
    }
)


def _scrub(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _scrub(v) for k, v in obj.items() if k not in _SCRUB_KEYS}
    if isinstance(obj, list):
        return [_scrub(x) for x in obj]
    return obj


def seed_path() -> Path:
    if _LOCAL_SEED.is_file():
        return _LOCAL_SEED
    raise FileNotFoundError(f"user-personas.json not found at {_LOCAL_SEED}")


def inventory_path() -> Path | None:
    return _LOCAL_INVENTORY if _LOCAL_INVENTORY.is_file() else None


def load_seed(path: Path | None = None) -> dict[str, Any]:
    p = path or seed_path()
    with open(p, encoding="utf-8") as f:
        return _scrub(json.load(f))


def load_inventory(path: Path | None = None) -> dict[str, Any]:
    p = path or inventory_path()
    if p is None:
        return {"by_slug": {}}
    # Scrub here too: inventory blocks are merged into public personas by
    # list_personas(), so any proprietary keys must be stripped on this path.
    with open(p, encoding="utf-8") as f:
        return _scrub(json.load(f))


def list_personas(path: Path | None = None) -> list[dict[str, Any]]:
    """Personas with data_inventory + microbiome merged when inventory file present."""
    inv = load_inventory().get("by_slug") or {}
    out: list[dict[str, Any]] = []
    for p in list(load_seed(path).get("personas") or []):
        slug = p.get("slug")
        row = dict(p)
        if slug and slug in inv:
            block = inv[slug]
            row["data_inventory"] = {
                "readiness": block.get("readiness"),
                "lifestyle_loads": block.get("lifestyle_loads"),
                "sources": block.get("sources"),
            }
            if block.get("microbiome"):
                clinical = dict(row.get("clinical") or {})
                clinical["microbiome"] = block["microbiome"]
                row["clinical"] = clinical
            ready_flag = (block.get("readiness") or {}).get("host_ready_flag")
            if ready_flag is not None:
                host = dict(row.get("host") or {})
                host["ready"] = ready_flag
                row["host"] = host
        out.append(row)
    return out


def list_slugs(path: Path | None = None) -> list[str]:
    return [p.get("slug", "") for p in list_personas(path) if p.get("slug")]


def get_persona(key: str, path: Path | None = None) -> dict[str, Any] | None:
    if not key:
        return None
    k = key.strip().lower()
    for p in list_personas(path):
        slug = str(p.get("slug", "")).lower()
        pid = str(p.get("id", ""))
        if slug == k or pid.lower() == k or pid.lower() == f"persona.{k}":
            return p
        if k.startswith("persona.") and pid.lower() == k:
            return p
    return None


def persona_to_host_state(persona: dict[str, Any]):
    """Build physiological_state.HostState from persona['host'] (+ body fat/muscle)."""
    from biology_as_code.simulation.physiological_state import HostState  # local package import

    h = persona.get("host") or {}
    return HostState(
        sleep_hours_last_night=float(h.get("sleep_hours_last_night", 7.5)),
        sleep_quality=float(h.get("sleep_quality", 0.8)),
        hrv_rmssd=h.get("hrv_rmssd"),
        resting_hr=h.get("resting_hr"),
        stress_level=float(h.get("stress_level", 0.3)),
        perceived_stress=float(h.get("perceived_stress", 0.3)),
        steps_today=int(h.get("steps_today", 0) or 0),
        active_minutes_today=int(h.get("active_minutes_today", 0) or 0),
        recent_exercise_intensity=float(h.get("recent_exercise_intensity", 0.0)),
        hydration_status=float(h.get("hydration_status", 0.8)),
        body_fat_percent=h.get("body_fat_percent"),
        muscle_mass_kg=h.get("muscle_mass_kg"),
    )


def persona_to_clinical_context(persona: dict[str, Any]):
    """Python ClinicalContext from medications/supplements (+ alcohol flag)."""
    from biology_as_code.simulation.physiological_state import ClinicalContext

    meds = list(persona.get("medications") or [])
    supps = list(persona.get("supplements") or [])
    host = persona.get("host") or {}
    alcohol = float(host.get("alcohol_with_meal") or 0)
    return ClinicalContext(
        medications=meds,
        supplements=supps,
        alcohol_recent=alcohol,
        tobacco_recent=0.0,
        statin_onboard=any("statin" in m.lower() or m.lower() == "atorvastatin" for m in meds),
        metformin_onboard=any("metformin" in m.lower() for m in meds),
    )


def persona_engine_profile(persona: dict[str, Any]) -> dict[str, Any]:
    """
    Flat profile dict for meal_engine / bridge adapters.
    Mirrors TS host + a few clinical/goal flags.
    """
    h = persona.get("host") or {}
    goals = persona.get("goals") or {}
    body = goals.get("body") or {}
    clinical = persona.get("clinical") or {}
    hormonal = clinical.get("hormonal_profile") or {}
    dynamic = clinical.get("dynamic_state") or {}
    app = persona.get("app") or {}
    prefs = persona.get("preferences") or {}

    return {
        "slug": persona.get("slug"),
        "id": persona.get("id"),
        "display_name": persona.get("display_name"),
        "ready": h.get("ready", 1),
        "lifecycle": h.get("lifecycle"),
        "sex": h.get("sex"),
        "age_years": h.get("age_years"),
        "acid_capacity": h.get("acid_capacity"),
        "bile_capacity": h.get("bile_capacity"),
        "insulin_resistance": h.get("insulin_resistance"),
        "post_surgical": h.get("post_surgical", False),
        "alcohol_with_meal": h.get("alcohol_with_meal", 0),
        "leucine_adequacy": h.get("leucine_adequacy"),
        "sleep_quality": h.get("sleep_quality"),
        "stress_level": h.get("stress_level"),
        "hydration_status": h.get("hydration_status"),
        "goal_primary": goals.get("primary"),
        "energy_bias": goals.get("energy_bias"),
        "height_cm": body.get("height_cm"),
        "weight_kg": body.get("weight_kg"),
        "target_weight_kg": body.get("target_weight_kg"),
        "bmi": body.get("bmi"),
        "bmi_band": body.get("bmi_band"),
        "hormonal_insulin_resistance": hormonal.get("insulin_resistance"),
        "inflammation_status": dynamic.get("inflammation_status"),
        "medications": list(persona.get("medications") or []),
        "supplements": list(persona.get("supplements") or []),
        "diet_style": prefs.get("diet_style"),
        "activity_level": prefs.get("activity_level"),
        "lifestyle_tags": list(prefs.get("lifestyle_tags") or []),
        "app_state": app.get("state"),
        # no flow_score / product meal score in public package
        "adherence_last_7d": app.get("adherence_last_7d"),
        "honesty": persona.get("honesty", "OPEN"),
    }


def apply_persona_to_physiological_state(persona: dict[str, Any], state=None):
    """
    Mutate/create PhysiologicalState with persona host + clinical layers.
    Leaves phase/hormones as-is unless state is new (defaults).
    """
    from biology_as_code.simulation.physiological_state import PhysiologicalState

    if state is None:
        state = PhysiologicalState()
    state.host = persona_to_host_state(persona)
    state.clinical = persona_to_clinical_context(persona)

    # Soft inflammation / IR teaching from clinical bands
    clinical = persona.get("clinical") or {}
    ir = (clinical.get("hormonal_profile") or {}).get("insulin_resistance")
    inflam = (clinical.get("dynamic_state") or {}).get("inflammation_status")
    band_map = {"LOW": 0.2, "NORMAL": 0.4, "HIGH": 0.85, "CRITICAL": 1.0}
    if ir in band_map:
        state.insulin_sensitivity = max(0.05, 1.0 - band_map[ir])
    if inflam in band_map:
        state.inflammation = band_map[inflam]
    # host.insulin_resistance 0–1 also available on engine profile
    return state


def summarize_personas(path: Path | None = None) -> list[dict[str, Any]]:
    out = []
    for p in list_personas(path):
        goals = p.get("goals") or {}
        app = p.get("app") or {}
        out.append(
            {
                "slug": p.get("slug"),
                "name": p.get("display_name"),
                "primary": goals.get("primary"),
                "app_state": app.get("state"),
                "why": p.get("why_useful"),
            }
        )
    return out


if __name__ == "__main__":
    print(f"seed: {seed_path()}")
    print(f"inventory: {inventory_path()}")
    for row in summarize_personas():
        print(
            f"  {row['slug']:8}  "
            f"{row['app_state']!s:12}  {row['primary']!s:18}  {row['name']}"
        )
    alex = get_persona("alex")
    assert alex is not None
    prof = persona_engine_profile(alex)
    print("alex profile keys:", sorted(prof.keys())[:12], "...")
    host = persona_to_host_state(alex)
    print("alex host:", asdict(host))
    inv = (alex.get("data_inventory") or {}).get("readiness") or {}
    print("alex readiness:", inv)
    sam = get_persona("sam")
    assert sam is not None
    print("sam microbiome:", (sam.get("clinical") or {}).get("microbiome", {}).get("provider_example"))
