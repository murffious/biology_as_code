"""
bridge_engine.py
================
Product-facing simulator **bridged to engine**.

- FoodPayload / lifecycle / lifestyle (product API)
- Digestive narrative segments (mouth→rectum) with **LAW-###** ids
- **L-FAT-1** micelle gate (no fat → no ADEK bump)
- engine.sim compartmental FLOW (open tier)
- Iron walk (LAW-004 family) when C / tannin / phytate context present
- vitamins.json load + topics registry
- Cascades soft priors (not diagnoses)

Honesty: claim_tier open unless engine marks otherwise. Not clinical advice.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from biology_as_code.engine import (
    KINGDOMS,
    NONHAEM_IRON_PATHWAY,
    SEVEN_SYSTEMS,
    MetabolicSimulator,
    load_system_bound_registry,
    load_topics,
    walk_pathway,
)
from biology_as_code.engine import (
    MetabolicState as CoreState,
)
from biology_as_code.engine.pathways import propagate_cascades
from biology_as_code.engine.topics import build_sim_context_template

PKG = Path(__file__).resolve().parent
# Teaching vitamin registry (fixture data — not product score IP)
VITAMINS_JSON = PKG.parent / "data" / "fixtures" / "vitamins.json"

# Map GI narrative segments → kingdoms + primary systems + law ids
SEGMENT_MAP: list[dict[str, Any]] = [
    {
        "id": "mouth",
        "label": "Mouth",
        "kingdom": "K1",
        "systems": ["Assimilation"],
        "laws": [],
        "terms": ["mastication", "salivary amylase", "lingual lipase"],
    },
    {
        "id": "esophagus",
        "label": "Esophagus",
        "kingdom": "K1",
        "systems": ["Assimilation"],
        "laws": [],
        "terms": ["peristalsis", "LES"],
    },
    {
        "id": "stomach",
        "label": "Stomach",
        "kingdom": "K2",
        "systems": ["Assimilation"],
        "laws": ["STUB-A-03"],  # pepsin pH still open
        "terms": ["gastric acid", "pepsin", "gastrin", "intrinsic factor"],
    },
    {
        "id": "duodenum",
        "label": "Duodenum",
        "kingdom": "K3",
        "systems": ["Assimilation", "Biotransformation"],
        "laws": ["L-FAT-1", "LAW-016", "LAW-020", "LAW-045"],
        "terms": ["CCK", "bile salts", "micelle", "pancreatic lipase", "colipase"],
    },
    {
        "id": "jejunum",
        "label": "Jejunum",
        "kingdom": "K4",
        "systems": ["Assimilation"],
        "laws": ["LAW-004", "LAW-041", "LAW-042", "LAW-044", "LAW-047"],
        "terms": ["brush border", "SGLT1", "GLUT5", "amino acid transporters"],
    },
    {
        "id": "ileum",
        "label": "Ileum",
        "kingdom": "K4",
        "systems": ["Assimilation", "Biotransformation", "Transport"],
        "laws": ["LAW-043", "LAW-039", "LAW-046"],
        "terms": ["B12-IF complex", "bile reabsorption", "enterohepatic", "portal vs lymph"],
    },
    {
        "id": "colon",
        "label": "Colon",
        "kingdom": "K5",
        "systems": ["Energy", "Communication"],
        "laws": ["LAW-025", "LAW-026"],
        "terms": ["fermentation", "SCFA", "butyrate", "GLP-1", "PYY"],
    },
    {
        "id": "rectum",
        "label": "Rectum",
        "kingdom": "K_end",
        "systems": ["Assimilation"],
        "laws": [],
        "terms": ["fecal bulk"],
    },
]


class LifecycleStage(StrEnum):
    INFANT = "infant"
    ADOLESCENT = "adolescent"
    ADULT = "adult"
    PREGNANT = "pregnant"
    LACTATING = "lactating"
    ELDERLY = "elderly"
    ATHLETE = "athlete"


@dataclass
class LifestyleFactors:
    activity_level: float = 1.0
    stress_level: float = 0.3
    smoking: bool = False
    alcohol_units_per_day: float = 0.0
    sleep_hours: float = 7.5
    diet_pattern: str = "standard"


@dataclass
class FoodPayload:
    name: str
    nutrient_density_score: float = 0.7
    quality_score: float = 0.7
    macros_g: dict[str, float] = field(default_factory=dict)
    vitamins_mg: dict[str, float] = field(default_factory=dict)
    fiber_g: float = 0.0
    anti_nutrients: float = 0.0  # 0–1 phytate/tannin intensity proxy
    rs_breakdown: dict[str, float] = field(
        default_factory=lambda: {"rs2": 0.3, "rs3": 0.2}
    )
    # explicit same-meal flags (override heuristics)
    ascorbate_same_meal: bool | None = None
    tannin_same_meal: bool = False


@dataclass
class VitaminStatus:
    id: str
    name: str
    adequacy: float = 1.0
    solubility: str = "water"
    deficiency_disease: str = ""
    deficiency_symptoms: list[str] = field(default_factory=list)
    affected_systems: list[str] = field(default_factory=list)
    law_links: list[str] = field(default_factory=list)
    dri_rda: float | None = None
    claim_tier: str = "open"


@dataclass
class MicrobiomeProfile:
    diversity_score: float = 0.8
    scfa_production_factor: float = 1.0
    resistant_fraction: float = 0.05


# Vitamin id → law / stub links
VIT_LAW_LINKS: dict[str, list[str]] = {
    "c": ["LAW-004", "STUB-S-01"],
    "b1": ["LAW-036"],
    "b9": ["STUB-B-02"],
    "folate": ["STUB-B-02"],
    "b12": ["LAW-043"],
    "a": ["LAW-020", "L-FAT-1"],
    "d": ["L-FAT-1", "STUB-S-02"],
    "e": ["LAW-035", "L-FAT-1"],
    "k": ["L-FAT-1"],
    "iron": ["LAW-004", "LAW-041", "LAW-042"],
    "zinc": ["LAW-003", "LAW-042"],
    "calcium": ["LAW-042", "LAW-047"],
}

FAT_SOLUBLE = frozenset({"a", "d", "e", "k"})


def load_vitamins_json(path: Path | None = None) -> dict[str, VitaminStatus]:
    p = path or VITAMINS_JSON
    pool: dict[str, VitaminStatus] = {}
    if p.is_file():
        data = json.loads(p.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("vitamins") or []
        for raw in items:
            vid = str(raw.get("id") or "").lower()
            defic = raw.get("deficiency") or {}
            dri = raw.get("DRI") or {}
            pool[vid] = VitaminStatus(
                id=vid,
                name=str(raw.get("name") or vid),
                solubility=str(raw.get("solubility") or "water"),
                deficiency_disease=str(defic.get("disease") or ""),
                deficiency_symptoms=list(defic.get("symptoms") or []),
                affected_systems=list(defic.get("affected_systems") or []),
                law_links=list(VIT_LAW_LINKS.get(vid, [])),
                dri_rda=dri.get("rda"),
            )
    # ensure core minerals/vitamins exist even if JSON is partial
    for vid, name in [
        ("iron", "Iron"),
        ("zinc", "Zinc"),
        ("calcium", "Calcium"),
        ("folate", "Folate"),
        ("b12", "Vitamin B12"),
    ]:
        if vid not in pool:
            pool[vid] = VitaminStatus(
                id=vid,
                name=name,
                law_links=list(VIT_LAW_LINKS.get(vid, [])),
            )
    return pool


def _map_systems_from_affected(names: list[str]) -> list[str]:
    """Map vitamin JSON organ language → 7 systems (soft)."""
    out: list[str] = []
    blob = " ".join(names).lower()
    if any(x in blob for x in ("immune", "blood vessel", "infection")):
        out.append("Defense")
    if any(x in blob for x in ("connective", "bone", "muscle", "nervous")):
        out.append("Structure")
    if any(x in blob for x in ("heart", "cardio")):
        out.append("Transport")
    if any(x in blob for x in ("metabol", "energy")):
        out.append("Energy")
    return out or ["Assimilation"]


class BridgedMealEngine:
    """
    Product API over engine.

    Uses:
      - engine.sim for compartmental FLOW
      - iron pathway walk when micronutrient context present
      - law registry + topics for vocabulary
      - vitamins.json for deficiency reporting
    """

    def __init__(self) -> None:
        self.law_registry = load_system_bound_registry()
        self.topics = load_topics()
        self.vitamin_pool = load_vitamins_json()
        self.core_sim = MetabolicSimulator()
        self.lifecycle = LifecycleStage.ADULT
        self.lifestyle = LifestyleFactors()
        self.microbiome = MicrobiomeProfile()
        self.energy_charge = 0.85
        self.inflammation_score = 0.2
        self.last_core_state: CoreState | None = None
        self.last_report: dict[str, Any] = {}
        self.claim_tier = "open"
        self.refuse = [
            "clinical_diagnosis",
            "locked_scfa_kcal_as_law",
            "adek_without_fat_vehicle",
        ]

    def apply_profile(
        self, lifecycle: LifecycleStage, lifestyle: LifestyleFactors
    ) -> None:
        self.lifecycle = lifecycle
        self.lifestyle = lifestyle
        e = self.energy_charge
        if lifecycle == LifecycleStage.PREGNANT:
            e = min(1.0, e + 0.05)
            for vid in ("folate", "iron", "c", "d", "b9"):
                if vid in self.vitamin_pool:
                    self.vitamin_pool[vid].adequacy = min(
                        1.0, self.vitamin_pool[vid].adequacy + 0.15
                    )
        elif lifecycle == LifecycleStage.ATHLETE:
            e = min(1.0, e + 0.10)
        elif lifecycle == LifecycleStage.ELDERLY:
            e *= 0.92
            for st in self.vitamin_pool.values():
                st.adequacy *= 0.95
        if lifestyle.smoking and "c" in self.vitamin_pool:
            self.vitamin_pool["c"].adequacy *= 0.8
        if lifestyle.activity_level > 1.4:
            e = min(1.0, e + 0.05 * (lifestyle.activity_level - 1.0))
        if lifestyle.stress_level > 0.6:
            e *= 1.0 - 0.04 * lifestyle.stress_level
            self.inflammation_score = min(1.0, self.inflammation_score + 0.1)
        self.energy_charge = max(0.0, min(1.0, e))

    def _payload_to_core(self, payload: FoodPayload) -> CoreState:
        fats = float(payload.macros_g.get("fats") or payload.macros_g.get("fat") or 0)
        carbs = float(payload.macros_g.get("carbs") or payload.macros_g.get("carb") or 0)
        protein = float(payload.macros_g.get("protein") or 0)
        # ascorbate heuristic: vitamin c mg or explicit flag
        c_mg = float(payload.vitamins_mg.get("c") or 0)
        ascorbate = (
            payload.ascorbate_same_meal
            if payload.ascorbate_same_meal is not None
            else c_mg >= 30
        )
        phytate = payload.anti_nutrients >= 0.25
        tannin = payload.tannin_same_meal or payload.anti_nutrients >= 0.5
        return CoreState(
            fat_g=fats,
            carb_g=carbs,
            protein_g=protein,
            fiber_g=payload.fiber_g,
            iron_rel=float(payload.vitamins_mg.get("iron") or 1.0),
            zinc_rel=float(payload.vitamins_mg.get("zinc") or 1.0),
            calcium_rel=float(payload.vitamins_mg.get("calcium") or 1.0),
            ascorbate_same_meal=ascorbate,
            tannin_same_meal=tannin,
            phytate_matrix=phytate,
            fed=True,
            hours_since_meal=0.0,
        )

    def _narrative_events(
        self, payload: FoodPayload, core: CoreState
    ) -> list[dict[str, Any]]:
        """Mouth→rectum log with LAW ids (not freestyle law names)."""
        events = []
        fat = core.fat_g
        for seg in SEGMENT_MAP:
            laws = list(seg["laws"])
            note = ""
            absorbed: dict[str, float] = {}
            if seg["id"] == "duodenum":
                if core.micelle_gate_open or fat > 0:
                    note = "Micelle gate OPEN (L-FAT-1) — fat-soluble path allowed"
                    absorbed["fat_fraction_flow"] = 0.35
                else:
                    note = "Micelle gate CLOSED (L-FAT-1) — ADEK absorption absent"
                    laws = ["L-FAT-1"]
            elif seg["id"] == "jejunum":
                note = "Primary CHO/protein absorption + mineral competition (LAW-042 family)"
            elif seg["id"] == "ileum":
                note = "B12-IF gate (LAW-043) + bile recycle (LAW-039) + portal/lymph partition (LAW-046)"
            elif seg["id"] == "colon":
                note = (
                    f"SCFA FLOW from fiber={payload.fiber_g}g "
                    f"(LAW-025/026 magnitudes open — not locked kcal law)"
                )
            events.append(
                {
                    "segment": seg["label"],
                    "kingdom": seg["kingdom"],
                    "systems": seg["systems"],
                    "laws_fired": laws,
                    "terminology": seg["terms"],
                    "absorbed_flow": absorbed,
                    "note": note,
                }
            )
        return events

    def _apply_vitamin_absorption(
        self, payload: FoodPayload, core: CoreState
    ) -> list[str]:
        """Update vitamin adequacy with L-FAT-1 honesty for fat-solubles."""
        notes: list[str] = []
        fat_open = core.micelle_gate_open
        quality = max(0.0, min(1.0, payload.quality_score * payload.nutrient_density_score))
        anti = max(0.0, min(1.0, payload.anti_nutrients))

        for vid, status in self.vitamin_pool.items():
            intake = float(payload.vitamins_mg.get(vid) or 0.0)
            if vid in FAT_SOLUBLE:
                if not fat_open:
                    notes.append(
                        f"{vid}: ADEK blocked — no co-present fat (L-FAT-1 gate closed)"
                    )
                    # no adequacy bump
                    continue
                bump = 0.12 * quality + min(0.2, intake / 50.0)
                status.adequacy = min(1.0, status.adequacy + bump)
                notes.append(f"{vid}: fat-soluble path open (L-FAT-1); +{bump:.2f}")
            elif vid == "c" or vid == "iron":
                # water soluble / mineral — LAW-004 expand if C present
                bump = 0.08 * quality + min(0.15, intake / 100.0)
                if vid == "iron" and core.ascorbate_same_meal:
                    # LAW-004: ascorbate expands non-haem iron bound (factor >= 1)
                    bump *= max(1.0, min(2.0, core.iron_bioavailability_factor))
                    notes.append(
                        f"iron: LAW-004 ascorbate factor={core.iron_bioavailability_factor}"
                    )
                if anti > 0.2 and vid in ("iron", "zinc", "calcium"):
                    bump *= 1.0 - 0.3 * anti
                    notes.append(f"{vid}: anti-nutrient proxy narrowed absorption")
                status.adequacy = min(1.0, status.adequacy + bump)
            else:
                bump = 0.06 * quality + min(0.1, intake / 20.0 if intake else 0)
                status.adequacy = min(1.0, max(0.0, status.adequacy * (1 - 0.05 * anti) + bump))

        return notes

    def simulate_payload(
        self, payload: FoodPayload, verbose: bool = True
    ) -> dict[str, Any]:
        if verbose:
            print(f"\n=== Bridged run: {payload.name} ===")
            print(
                f"  density={payload.nutrient_density_score:.2f} "
                f"quality={payload.quality_score:.2f} fiber={payload.fiber_g}g"
            )

        core_in = self._payload_to_core(payload)
        # run engine compartmental sim
        core_out = self.core_sim.run(core_in)
        self.last_core_state = core_out

        # iron pathway walk (UNITS layer)
        iron_ctx = {
            "ascorbate_same_meal": core_out.ascorbate_same_meal,
            "tannin": core_out.tannin_same_meal,
            "phytate": core_out.phytate_matrix,
        }
        iron_walk = walk_pathway(
            NONHAEM_IRON_PATHWAY, "fe.meal_payload", context=iron_ctx
        )

        vit_notes = self._apply_vitamin_absorption(payload, core_out)
        events = self._narrative_events(payload, core_out)

        # soft cascade if micronutrient flags low
        flags = {}
        if self.vitamin_pool.get("a") and self.vitamin_pool["a"].adequacy < 0.5:
            flags["nut.retinol"] = "low"
        cascade = (
            propagate_cascades(flags) if flags else {"cascades_fired": [], "diagnosis": False}
        )

        # energy charge from core (soft)
        self.energy_charge = min(
            1.0, 0.5 + core_out.flow_score / 200.0 + self.microbiome.diversity_score * 0.1
        )

        # topic context template (available for extension)
        topic_ctx = build_sim_context_template()
        topic_ctx["ascorbate_same_meal"] = core_out.ascorbate_same_meal

        laws_cited = sorted(set(core_out.laws_cited + iron_walk.modifiers_fired))
        # add segment laws
        for ev in events:
            for lid in ev["laws_fired"]:
                if lid not in laws_cited:
                    laws_cited.append(lid)

        report: dict[str, Any] = {
            "payload_name": payload.name,
            "claim_tier": "open",
            "seven_systems": list(SEVEN_SYSTEMS),
            "micelle_gate_open": core_out.micelle_gate_open,
            "core_sim": self.core_sim.summary(core_out),
            "iron_walk_yield": round(iron_walk.yield_factor, 4),
            "iron_walk_path": iron_walk.path,
            "iron_modifiers_fired": iron_walk.modifiers_fired,
            "narrative_events": events,
            "vitamin_status": {
                k: {
                    "adequacy": round(v.adequacy, 3),
                    "name": v.name,
                    "law_links": v.law_links,
                    "deficiency_if_low": v.deficiency_disease,
                }
                for k, v in self.vitamin_pool.items()
            },
            "vitamin_notes": vit_notes,
            "deficiency_symptoms": {
                k: v.deficiency_symptoms
                for k, v in self.vitamin_pool.items()
                if v.adequacy < 0.55
            },
            "laws_cited": laws_cited,
            "law_count_registry": len(self.law_registry),
            "topics_loaded": len(self.topics),
            "cascade": {
                "fired": len(cascade.get("cascades_fired") or []),
                "diagnosis": cascade.get("diagnosis", False),
                "systems": cascade.get("systems_touched") or [],
            },
            "lifecycle": self.lifecycle.value,
            "lifestyle": {
                "activity": self.lifestyle.activity_level,
                "stress": self.lifestyle.stress_level,
            },
            "microbiome_diversity": self.microbiome.diversity_score,
            "energy_charge": round(self.energy_charge, 3),
            "refuse": list(set(self.refuse + list(core_out.refuse))),
            "kingdoms": [k.id for k in KINGDOMS],
        }
        self.last_report = report

        if verbose:
            print(f"  micelle_gate_open={core_out.micelle_gate_open}")
            print(f"  iron_walk_yield={report['iron_walk_yield']}")
            print(f"  laws_cited ({len(laws_cited)}): {laws_cited[:12]}...")
            print(f"  energy_charge={report['energy_charge']}")
            print("  --- GI narrative (LAW-linked) ---")
            for ev in events:
                print(
                    f"  [{ev['segment']}] {ev['kingdom']} laws={ev['laws_fired'] or '—'}"
                )
                if ev["note"]:
                    print(f"    {ev['note']}")
            if vit_notes:
                print("  --- vitamin absorption notes ---")
                for n in vit_notes[:8]:
                    print(f"    • {n}")
            print("  refuse:", report["refuse"][:5], "...")

        return report

    def simulate_antibiotic_dysbiosis(
        self, days: int = 7, verbose: bool = True
    ) -> MicrobiomeProfile:
        if verbose:
            print(f"\n=== Antibiotic dysbiosis ({days}d) — open-tier scenario ===")
        self.microbiome.diversity_score = 0.15
        self.microbiome.resistant_fraction = 0.55
        self.energy_charge *= 0.75
        for day in range(1, days + 1):
            if day <= 3:
                self.microbiome.diversity_score = max(
                    0.1, self.microbiome.diversity_score - 0.02
                )
            else:
                self.microbiome.diversity_score = min(
                    0.95, self.microbiome.diversity_score + 0.12
                )
                self.microbiome.resistant_fraction = max(
                    0.05, self.microbiome.resistant_fraction - 0.08
                )
                self.energy_charge = min(1.0, self.energy_charge + 0.04)
            if verbose:
                print(
                    f"  Day {day}: diversity={self.microbiome.diversity_score:.2f} "
                    f"energy={self.energy_charge:.2f}"
                )
        return self.microbiome

    def lookup_topic(self, name: str) -> dict[str, Any] | None:
        t = self.topics.find(name)
        if not t:
            return None
        return {
            "id": t.id,
            "label": t.label,
            "sim_role": t.sim_role,
            "systems": list(t.systems),
            "law_links": list(t.law_links),
            "field": t.field_hint,
            "status": t.status,
        }

    def get_law(self, law_id: str) -> dict[str, Any] | None:
        if law_id not in self.law_registry:
            return None
        L = self.law_registry.get(law_id)
        return {
            "id": L.id,
            "functional_system": L.functional_system,
            "organ": L.organ,
            "statement": L.law_statement,
            "gate": L.gate_text,
            "bound": L.bound_text,
            "relation": L.relation_type,
        }


# Back-compat alias
MealEngine = BridgedMealEngine


def demo() -> None:
    engine = BridgedMealEngine()
    engine.apply_profile(
        LifecycleStage.ATHLETE,
        LifestyleFactors(activity_level=1.7, stress_level=0.4),
    )

    good = FoodPayload(
        name="High-RS whole-food meal + fat + C",
        nutrient_density_score=0.92,
        quality_score=0.95,
        macros_g={"carbs": 55, "protein": 35, "fats": 18},
        vitamins_mg={"c": 120, "b1": 1.8, "folate": 0.4, "a": 0.5},
        fiber_g=32,
        anti_nutrients=0.08,
    )
    engine.simulate_payload(good, verbose=True)

    print("\n=== Control: fat-free salad (L-FAT-1 gate test) ===")
    no_fat = FoodPayload(
        name="Fat-free carotenoid salad",
        quality_score=0.9,
        nutrient_density_score=0.9,
        macros_g={"carbs": 20, "protein": 5, "fats": 0},
        vitamins_mg={"a": 1.0, "c": 40, "k": 0.1},
        fiber_g=8,
    )
    r = engine.simulate_payload(no_fat, verbose=True)
    assert r["micelle_gate_open"] is False

    engine.simulate_antibiotic_dysbiosis(days=5, verbose=True)
    print("\nlookup Iron:", engine.lookup_topic("Iron"))
    print("LAW-004:", engine.get_law("LAW-004"))
    print("\n✅ Bridge demo complete")


if __name__ == "__main__":
    demo()
