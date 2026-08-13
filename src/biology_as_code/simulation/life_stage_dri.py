"""
life_stage_dri.py
Life-stage specific dietary reference intakes and demand multipliers.

Covers infancy, childhood, adolescence, adulthood, pregnancy, lactation,
and older adults — vitamins + minerals used by the engine.
Values are simplified textbook/DRI-style references for modeling (not medical advice).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class LifeStage(Enum):
    INFANT_0_6MO = "infant_0_6mo"
    INFANT_7_12MO = "infant_7_12mo"
    CHILD_1_3 = "child_1_3"
    CHILD_4_8 = "child_4_8"
    MALE_9_13 = "male_9_13"
    FEMALE_9_13 = "female_9_13"
    MALE_14_18 = "male_14_18"
    FEMALE_14_18 = "female_14_18"
    MALE_19_50 = "male_19_50"
    FEMALE_19_50 = "female_19_50"
    MALE_51_70 = "male_51_70"
    FEMALE_51_70 = "female_51_70"
    MALE_70PLUS = "male_70plus"
    FEMALE_70PLUS = "female_70plus"
    PREGNANT_19_50 = "pregnant_19_50"
    LACTATING_19_50 = "lactating_19_50"
    ATHLETE_ADULT = "athlete_adult"


@dataclass
class NutrientDRI:
    """Reference intake for one nutrient at one life stage."""
    nutrient_id: str
    amount: float
    unit: str = "mg"
    kind: str = "RDA"  # RDA | AI | UL note
    notes: str = ""


@dataclass
class LifeStageProfile:
    stage: LifeStage
    label: str
    energy_multiplier: float = 1.0       # vs young adult sedentary baseline
    protein_g_per_kg: float = 0.8
    iron_demand_multiplier: float = 1.0
    calcium_demand_multiplier: float = 1.0
    absorption_modifiers: dict[str, float] = field(default_factory=dict)
    special_notes: list[str] = field(default_factory=list)
    dri: dict[str, NutrientDRI] = field(default_factory=dict)


def _d(nid: str, amount: float, unit: str = "mg", kind: str = "RDA", notes: str = "") -> NutrientDRI:
    return NutrientDRI(nid, amount, unit, kind, notes)


def _build_adult_male() -> dict[str, NutrientDRI]:
    return {
        "c": _d("c", 90),
        "b1": _d("b1", 1.2),
        "b2": _d("b2", 1.3),
        "b3": _d("b3", 16),
        "b6": _d("b6", 1.3),
        "b9": _d("b9", 0.4, notes="folate DFE mg"),
        "folate": _d("folate", 0.4),
        "b12": _d("b12", 0.0024),
        "a": _d("a", 0.9, notes="RAE mg-eq"),
        "d": _d("d", 0.015),
        "e": _d("e", 15),
        "k": _d("k", 0.120, kind="AI"),
        "ca": _d("ca", 1000),
        "mg": _d("mg", 400),
        "p": _d("p", 700),
        "fe": _d("fe", 8),
        "zn": _d("zn", 11),
        "cu": _d("cu", 0.9),
        "se": _d("se", 0.055),
        "i": _d("i", 0.150),
        "k_mineral": _d("k_mineral", 3400, kind="AI"),
        "na": _d("na", 1500, kind="AI/CDRR"),
    }


def _scale(base: dict[str, NutrientDRI], factors: dict[str, float]) -> dict[str, NutrientDRI]:
    out = {}
    for k, v in base.items():
        f = factors.get(k, factors.get("*", 1.0))
        out[k] = NutrientDRI(v.nutrient_id, round(v.amount * f, 4), v.unit, v.kind, v.notes)
    return out


def _build_registry() -> dict[LifeStage, LifeStageProfile]:
    adult_m = _build_adult_male()
    adult_f = _scale(adult_m, {"fe": 2.25, "c": 0.83, "b1": 0.92, "b2": 0.85, "b3": 0.875,
                               "zn": 0.73, "mg": 0.78, "a": 0.78, "k": 0.75})
    # female iron 18 mg vs male 8 ≈ 2.25

    reg: dict[LifeStage, LifeStageProfile] = {}

    reg[LifeStage.MALE_19_50] = LifeStageProfile(
        LifeStage.MALE_19_50, "Adult male 19–50",
        energy_multiplier=1.0, protein_g_per_kg=0.8, dri=adult_m,
    )
    reg[LifeStage.FEMALE_19_50] = LifeStageProfile(
        LifeStage.FEMALE_19_50, "Adult female 19–50",
        energy_multiplier=0.85, protein_g_per_kg=0.8,
        iron_demand_multiplier=2.25, dri=adult_f,
        special_notes=["Menstrual iron losses elevate Fe RDA to ~18 mg"],
    )

    # Pregnancy – elevated folate, iron, energy, protein
    preg = _scale(adult_f, {
        "b9": 1.5, "folate": 1.5, "fe": 1.5, "zn": 1.375, "c": 1.13,
        "b6": 1.46, "b12": 1.08, "a": 1.1, "d": 1.0, "ca": 1.0,
        "i": 1.47, "mg": 1.12, "*": 1.05,
    })
    # absolute overrides matching common DRI teaching values
    preg["b9"] = _d("b9", 0.6, notes="600 µg DFE")
    preg["folate"] = _d("folate", 0.6)
    preg["fe"] = _d("fe", 27)
    preg["i"] = _d("i", 0.220)
    preg["zn"] = _d("zn", 11)
    reg[LifeStage.PREGNANT_19_50] = LifeStageProfile(
        LifeStage.PREGNANT_19_50, "Pregnancy 19–50",
        energy_multiplier=1.15, protein_g_per_kg=1.1,
        iron_demand_multiplier=3.4, calcium_demand_multiplier=1.0,
        absorption_modifiers={"fe": 1.5, "ca": 1.3},  # adaptive ↑ absorption
        special_notes=[
            "2nd/3rd trimester energy +340–450 kcal/day typical",
            "Folate critical preconception + neural tube",
            "Iron absorption upregulates but demand still high",
        ],
        dri=preg,
    )

    lact = _scale(adult_f, {
        "c": 1.4, "b1": 1.3, "b2": 1.4, "b3": 1.2, "b6": 1.5,
        "b9": 1.25, "folate": 1.25, "b12": 1.17, "a": 1.7,
        "zn": 1.5, "i": 1.93, "fe": 0.5,  # postpartum amenorrhea lowers Fe need
        "*": 1.1,
    })
    lact["fe"] = _d("fe", 9)
    lact["i"] = _d("i", 0.290)
    lact["a"] = _d("a", 1.3)
    lact["c"] = _d("c", 120)
    reg[LifeStage.LACTATING_19_50] = LifeStageProfile(
        LifeStage.LACTATING_19_50, "Lactation 19–50",
        energy_multiplier=1.25, protein_g_per_kg=1.3,
        iron_demand_multiplier=1.1,
        special_notes=["Milk secretion raises many micronutrient RDAs", "Energy +330–400+ kcal"],
        dri=lact,
    )

    # Infants
    inf06 = {
        "c": _d("c", 40, kind="AI"), "b1": _d("b1", 0.2, kind="AI"),
        "b9": _d("b9", 0.065, kind="AI"), "b12": _d("b12", 0.0004, kind="AI"),
        "d": _d("d", 0.010), "a": _d("a", 0.4, kind="AI"),
        "ca": _d("ca", 200, kind="AI"), "fe": _d("fe", 0.27, kind="AI"),
        "zn": _d("zn", 2, kind="AI"), "i": _d("i", 0.110, kind="AI"),
    }
    reg[LifeStage.INFANT_0_6MO] = LifeStageProfile(
        LifeStage.INFANT_0_6MO, "Infant 0–6 months",
        energy_multiplier=0.45, protein_g_per_kg=1.52,
        dri=inf06,
        special_notes=["Human milk / formula primary; vit D often supplemented"],
    )
    inf712 = dict(inf06)
    inf712.update({
        "c": _d("c", 50, kind="AI"), "fe": _d("fe", 11), "zn": _d("zn", 3),
        "ca": _d("ca", 260, kind="AI"), "b9": _d("b9", 0.080, kind="AI"),
    })
    reg[LifeStage.INFANT_7_12MO] = LifeStageProfile(
        LifeStage.INFANT_7_12MO, "Infant 7–12 months",
        energy_multiplier=0.55, protein_g_per_kg=1.2,
        iron_demand_multiplier=1.4, dri=inf712,
        special_notes=["Complementary foods; iron-rich foods critical after ~6 mo"],
    )

    # Children
    reg[LifeStage.CHILD_1_3] = LifeStageProfile(
        LifeStage.CHILD_1_3, "Child 1–3 years",
        energy_multiplier=0.60, protein_g_per_kg=1.05,
        dri=_scale(adult_m, {"*": 0.4, "fe": 0.875, "ca": 0.7, "d": 1.0, "zn": 0.27}),
    )
    reg[LifeStage.CHILD_4_8] = LifeStageProfile(
        LifeStage.CHILD_4_8, "Child 4–8 years",
        energy_multiplier=0.75, protein_g_per_kg=0.95,
        dri=_scale(adult_m, {"*": 0.55, "fe": 1.25, "ca": 1.0, "zn": 0.45}),
    )

    # Adolescents – peak bone mass window
    reg[LifeStage.MALE_9_13] = LifeStageProfile(
        LifeStage.MALE_9_13, "Male 9–13",
        energy_multiplier=0.95, protein_g_per_kg=0.95,
        calcium_demand_multiplier=1.3,
        dri=_scale(adult_m, {"*": 0.7, "ca": 1.3, "fe": 1.0, "zn": 0.73}),
        special_notes=["Peak bone mineral accretion → Ca 1300 mg"],
    )
    reg[LifeStage.FEMALE_9_13] = LifeStageProfile(
        LifeStage.FEMALE_9_13, "Female 9–13",
        energy_multiplier=0.90, protein_g_per_kg=0.95,
        calcium_demand_multiplier=1.3, iron_demand_multiplier=1.0,
        dri=_scale(adult_f, {"*": 0.75, "ca": 1.3, "fe": 0.44}),
    )
    reg[LifeStage.MALE_14_18] = LifeStageProfile(
        LifeStage.MALE_14_18, "Male 14–18",
        energy_multiplier=1.15, protein_g_per_kg=0.85,
        calcium_demand_multiplier=1.3,
        dri=_scale(adult_m, {"ca": 1.3, "fe": 1.375, "zn": 1.0, "*": 1.0}),
    )
    reg[LifeStage.FEMALE_14_18] = LifeStageProfile(
        LifeStage.FEMALE_14_18, "Female 14–18",
        energy_multiplier=1.0, protein_g_per_kg=0.85,
        calcium_demand_multiplier=1.3, iron_demand_multiplier=1.9,
        dri=_scale(adult_f, {"ca": 1.3, "fe": 0.83, "zn": 1.125, "*": 1.0}),
        special_notes=["Menarche elevates iron needs"],
    )

    # Older adults
    older_m = _scale(adult_m, {"b6": 1.3, "d": 1.33, "ca": 1.0, "b12": 1.0, "*": 1.0})
    older_m["d"] = _d("d", 0.020)
    older_m["ca"] = _d("ca", 1000)
    reg[LifeStage.MALE_51_70] = LifeStageProfile(
        LifeStage.MALE_51_70, "Male 51–70",
        energy_multiplier=0.92, protein_g_per_kg=0.8,
        absorption_modifiers={"b12": 0.75, "ca": 0.90, "d": 0.85},
        special_notes=["B12 absorption may fall with atrophic gastritis / PPI use"],
        dri=older_m,
    )
    older_f = _scale(adult_f, {"fe": 0.44, "b6": 1.3, "d": 1.33, "ca": 1.2})
    older_f["fe"] = _d("fe", 8)  # post-menopause
    older_f["ca"] = _d("ca", 1200)
    older_f["d"] = _d("d", 0.020)
    reg[LifeStage.FEMALE_51_70] = LifeStageProfile(
        LifeStage.FEMALE_51_70, "Female 51–70",
        energy_multiplier=0.85, protein_g_per_kg=0.8,
        iron_demand_multiplier=1.0, calcium_demand_multiplier=1.2,
        absorption_modifiers={"b12": 0.75, "ca": 0.90, "d": 0.85},
        special_notes=["Post-menopause: Fe RDA drops; Ca rises to 1200 mg"],
        dri=older_f,
    )

    elderly_m = dict(older_m)
    elderly_m["ca"] = _d("ca", 1200)
    elderly_m["d"] = _d("d", 0.020)
    elderly_m["b6"] = _d("b6", 1.7)
    reg[LifeStage.MALE_70PLUS] = LifeStageProfile(
        LifeStage.MALE_70PLUS, "Male >70",
        energy_multiplier=0.85, protein_g_per_kg=1.0,
        calcium_demand_multiplier=1.2,
        absorption_modifiers={"b12": 0.65, "ca": 0.85, "d": 0.80, "protein": 0.95},
        special_notes=["Higher protein often recommended to limit sarcopenia", "Ca 1200 mg"],
        dri=elderly_m,
    )
    elderly_f = dict(older_f)
    elderly_f["b6"] = _d("b6", 1.5)
    reg[LifeStage.FEMALE_70PLUS] = LifeStageProfile(
        LifeStage.FEMALE_70PLUS, "Female >70",
        energy_multiplier=0.80, protein_g_per_kg=1.0,
        calcium_demand_multiplier=1.2,
        absorption_modifiers={"b12": 0.65, "ca": 0.85, "d": 0.80},
        dri=elderly_f,
    )

    # Athlete – not DRI official, but useful engine profile
    ath = _scale(adult_m, {"c": 1.2, "b1": 1.3, "b2": 1.3, "fe": 1.2, "zn": 1.1, "mg": 1.15, "*": 1.1})
    reg[LifeStage.ATHLETE_ADULT] = LifeStageProfile(
        LifeStage.ATHLETE_ADULT, "Adult athlete (model)",
        energy_multiplier=1.4, protein_g_per_kg=1.6,
        iron_demand_multiplier=1.2,
        special_notes=["Elevated energy + sweat mineral losses; not formal DRI category"],
        dri=ath,
    )

    return reg


LIFE_STAGE_REGISTRY = _build_registry()


class LifeStageDRISystem:
    """Lookup DRIs and demand multipliers by life stage."""

    def __init__(self):
        self.registry = LIFE_STAGE_REGISTRY

    def get(self, stage: LifeStage) -> LifeStageProfile:
        return self.registry[stage]

    def resolve_stage(
        self,
        age_years: float,
        sex: str = "male",
        pregnant: bool = False,
        lactating: bool = False,
        athlete: bool = False,
    ) -> LifeStage:
        sex = sex.lower()
        if pregnant:
            return LifeStage.PREGNANT_19_50
        if lactating:
            return LifeStage.LACTATING_19_50
        if athlete and 18 <= age_years <= 50:
            return LifeStage.ATHLETE_ADULT
        if age_years < 0.5:
            return LifeStage.INFANT_0_6MO
        if age_years < 1:
            return LifeStage.INFANT_7_12MO
        if age_years < 4:
            return LifeStage.CHILD_1_3
        if age_years < 9:
            return LifeStage.CHILD_4_8
        if age_years < 14:
            return LifeStage.MALE_9_13 if sex.startswith("m") else LifeStage.FEMALE_9_13
        if age_years < 19:
            return LifeStage.MALE_14_18 if sex.startswith("m") else LifeStage.FEMALE_14_18
        if age_years < 51:
            return LifeStage.MALE_19_50 if sex.startswith("m") else LifeStage.FEMALE_19_50
        if age_years < 71:
            return LifeStage.MALE_51_70 if sex.startswith("m") else LifeStage.FEMALE_51_70
        return LifeStage.MALE_70PLUS if sex.startswith("m") else LifeStage.FEMALE_70PLUS

    def adequacy(
        self,
        stage: LifeStage,
        intakes: dict[str, float],
    ) -> dict[str, Any]:
        """Compare intakes to DRI; return fraction of RDA and flags."""
        profile = self.get(stage)
        report = {"stage": stage.value, "label": profile.label, "nutrients": {}}
        for nid, amount in intakes.items():
            key = "b9" if nid == "folate" else nid
            dri = profile.dri.get(key) or profile.dri.get(nid)
            if not dri:
                report["nutrients"][nid] = {"intake": amount, "status": "no_dri"}
                continue
            frac = amount / dri.amount if dri.amount > 0 else 0
            status = "adequate" if frac >= 1.0 else ("marginal" if frac >= 0.7 else "low")
            report["nutrients"][nid] = {
                "intake": amount,
                "dri": dri.amount,
                "unit": dri.unit,
                "fraction_of_dri": round(frac, 2),
                "status": status,
            }
        return report

    def protein_target_g(self, stage: LifeStage, weight_kg: float) -> float:
        return round(self.get(stage).protein_g_per_kg * weight_kg, 1)

    def summary(self, stage: LifeStage) -> dict[str, Any]:
        p = self.get(stage)
        return {
            "stage": stage.value,
            "label": p.label,
            "energy_multiplier": p.energy_multiplier,
            "protein_g_per_kg": p.protein_g_per_kg,
            "iron_demand_multiplier": p.iron_demand_multiplier,
            "calcium_demand_multiplier": p.calcium_demand_multiplier,
            "absorption_modifiers": p.absorption_modifiers,
            "notes": p.special_notes,
            "key_dris": {k: {"amount": v.amount, "unit": v.unit} for k, v in list(p.dri.items())[:12]},
        }


if __name__ == "__main__":
    sys = LifeStageDRISystem()
    for stage in [LifeStage.PREGNANT_19_50, LifeStage.FEMALE_70PLUS, LifeStage.INFANT_7_12MO]:
        print(sys.summary(stage))
        print()
    print("Adequacy example (pregnancy):")
    print(sys.adequacy(LifeStage.PREGNANT_19_50, {"fe": 18, "b9": 0.4, "ca": 1000, "c": 85}))
