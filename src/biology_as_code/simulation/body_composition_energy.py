"""
body_composition_energy.py
Chapter 8 – Body Composition & Energy Expenditure module.

Implements classic BMR equations, activity factors (PAL), NEAT,
body-composition estimates, and multi-component adaptive thermogenesis.
Based on Advanced Nutrition and Human Metabolism (Chapter 8)
and standard clinical equations.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum
from typing import Any


class Sex(Enum):
    MALE = "male"
    FEMALE = "female"


class ActivityLevel(Enum):
    SEDENTARY = "sedentary"
    LIGHTLY_ACTIVE = "lightly_active"
    MODERATELY_ACTIVE = "moderately_active"
    VERY_ACTIVE = "very_active"
    EXTRA_ACTIVE = "extra_active"


class OccupationActivity(Enum):
    DESK = "desk"                 # seated most of day
    STANDING = "standing"         # retail, teaching
    WALKING = "walking"           # delivery, nursing
    MANUAL = "manual"             # construction, farming


PAL_FACTORS = {
    ActivityLevel.SEDENTARY: 1.2,
    ActivityLevel.LIGHTLY_ACTIVE: 1.375,
    ActivityLevel.MODERATELY_ACTIVE: 1.55,
    ActivityLevel.VERY_ACTIVE: 1.725,
    ActivityLevel.EXTRA_ACTIVE: 1.9,
}

# Occupation baseline NEAT kcal/day for ~70–80 kg adult (order-of-magnitude)
OCCUPATION_NEAT_KCAL = {
    OccupationActivity.DESK: 250,
    OccupationActivity.STANDING: 450,
    OccupationActivity.WALKING: 700,
    OccupationActivity.MANUAL: 1100,
}


@dataclass
class Anthropometrics:
    sex: Sex
    age_years: float
    weight_kg: float
    height_cm: float
    body_fat_percent: float | None = None
    lean_mass_kg: float | None = None


@dataclass
class EnergyExpenditureResult:
    bmr_mifflin: float
    bmr_harris_benedict: float
    bmr_cunningham: float | None
    bmr_katch_mcardle: float | None
    chosen_bmr: float
    pal: float
    tdee: float
    neat_kcal: float
    eat_kcal: float
    tef_kcal: float
    adaptive_thermogenesis_factor: float
    adjusted_tdee: float
    method_notes: str


# ==============================================================================
# NEAT – Non-Exercise Activity Thermogenesis
# ==============================================================================

@dataclass
class NEATProfile:
    """
    Explicit NEAT model.

    NEAT = energy for all activity that is not sleeping, eating, or formal exercise.
    Most variable TDEE component (often 150–2000+ kcal/day).
    """
    occupation: OccupationActivity = OccupationActivity.DESK
    fidgeting_score: float = 0.5          # 0–1 spontaneous movement
    steps_per_day: int = 6000
    standing_hours: float = 2.0
    ambient_cold_exposure: float = 0.0    # 0–1 mild cold
    environment_walkability: float = 0.5  # 0–1
    screen_hours: float = 6.0

    def baseline_kcal(self, weight_kg: float = 75.0) -> float:
        """Estimate daily NEAT kcal before adaptive suppression."""
        occ = OCCUPATION_NEAT_KCAL[self.occupation]
        # Scale lightly with body size
        size = weight_kg / 75.0
        fidget = 80 + 220 * self.fidgeting_score
        # ~0.04–0.05 kcal/step rough ambulatory cost scaled by weight
        step_kcal = self.steps_per_day * 0.045 * size
        stand_kcal = self.standing_hours * 20 * size
        cold = 50 * self.ambient_cold_exposure
        walk_env = 80 * self.environment_walkability
        screen_penalty = min(200, self.screen_hours * 15)

        total = (occ * 0.5 + fidget + step_kcal + stand_kcal + cold + walk_env - screen_penalty) * size
        # Avoid double-counting occupation vs steps heavily
        return max(100.0, total)

    def summary(self, weight_kg: float = 75.0) -> dict[str, Any]:
        return {
            "occupation": self.occupation.value,
            "fidgeting_score": self.fidgeting_score,
            "steps_per_day": self.steps_per_day,
            "standing_hours": self.standing_hours,
            "baseline_neat_kcal": round(self.baseline_kcal(weight_kg), 1),
            "environment_walkability": self.environment_walkability,
            "screen_hours": self.screen_hours,
        }


class NEATModel:
    """
    NEAT response to underfeeding / overfeeding + linkage to leptin/SNS.
    """

    def __init__(self, profile: NEATProfile | None = None):
        self.profile = profile or NEATProfile()
        self.adaptation_factor: float = 1.0  # multiplies baseline NEAT

    def apply_restriction(
        self,
        percent_weight_loss: float,
        weeks: float,
        leptin_factor: float = 1.0,
        sns_factor: float = 1.0,
    ) -> float:
        """
        NEAT typically falls more than BMR during deficit.
        Returns adaptation factor (often 0.70–0.95).
        """
        severity = min(1.0, percent_weight_loss / 15.0)
        time_factor = min(1.0, weeks / 8.0)
        # Large behavioral + biological drop
        drop = 0.35 * severity * time_factor
        # Leptin/SNS couple: low leptin → lower drive to move
        hormone_drag = 0.5 * (1.0 - leptin_factor) + 0.5 * (1.0 - sns_factor)
        self.adaptation_factor = max(0.55, 1.0 - drop - 0.25 * hormone_drag)
        return self.adaptation_factor

    def apply_overfeeding(
        self,
        percent_weight_gain: float,
        weeks: float,
        spontaneous_responder: bool = True,
    ) -> float:
        """Some people spontaneously raise NEAT when overfed (obesity resistance)."""
        severity = min(1.0, percent_weight_gain / 12.0)
        time_factor = min(1.0, weeks / 6.0)
        if spontaneous_responder:
            self.adaptation_factor = min(1.35, 1.0 + 0.25 * severity * time_factor)
        else:
            self.adaptation_factor = min(1.08, 1.0 + 0.05 * severity * time_factor)
        return self.adaptation_factor

    def daily_kcal(self, weight_kg: float = 75.0) -> float:
        return self.profile.baseline_kcal(weight_kg) * self.adaptation_factor

    def reset(self):
        self.adaptation_factor = 1.0


# ==============================================================================
# Adaptive Thermogenesis
# ==============================================================================

@dataclass
class AdaptiveThermogenesisState:
    """
    Multi-component metabolic adaptation beyond mass change alone.

    Mechanisms:
      1. Leptin decline → lower EE drive + NEAT
      2. Thyroid T3 downregulation → lower BMR
      3. SNS / catecholamine withdrawal
      4. Increased mitochondrial efficiency (less proton leak)
      5. Improved muscle contractile efficiency
      6. NEAT behavioral drop
    """
    leptin_factor: float = 1.0
    thyroid_t3_factor: float = 1.0
    sns_factor: float = 1.0
    mitochondrial_efficiency: float = 1.0  # >1 less heat per ATP
    muscle_efficiency: float = 1.0
    neat_factor: float = 1.0
    overall_factor: float = 1.0
    weeks_in_deficit: float = 0.0
    percent_weight_lost: float = 0.0

    # aliases used by older call sites
    @property
    def thyroid_factor(self) -> float:
        return self.thyroid_t3_factor

    @thyroid_factor.setter
    def thyroid_factor(self, v: float):
        self.thyroid_t3_factor = v

    @property
    def total_adaptation_multiplier(self) -> float:
        return self.overall_factor

    def recompute_overall(self):
        self.overall_factor = (
            0.30 * self.leptin_factor
            + 0.20 * self.thyroid_t3_factor
            + 0.15 * self.sns_factor
            + 0.10 * (2.0 - self.mitochondrial_efficiency)
            + 0.05 * (2.0 - self.muscle_efficiency)
            + 0.20 * self.neat_factor
        )
        self.overall_factor = max(0.75, min(1.20, self.overall_factor))

    def update_from_deficit(self, weeks: float, percent_lost: float, severity: float = 0.25):
        """Progressive weekly adaptation (used by demos)."""
        self.weeks_in_deficit = weeks
        self.percent_weight_lost = percent_lost
        self.leptin_factor = max(0.70, 1.0 - (percent_lost * 0.025) - (weeks * 0.008))
        self.thyroid_t3_factor = max(0.85, 1.0 - (weeks * 0.012) * (severity / 0.25))
        self.sns_factor = max(0.75, 1.0 - (weeks * 0.015) * (severity / 0.25))
        self.mitochondrial_efficiency = min(1.25, 1.0 + (weeks * 0.01))
        self.muscle_efficiency = min(1.15, 1.0 + (weeks * 0.008))
        self.neat_factor = max(0.65, 1.0 - (weeks * 0.018) * (severity / 0.25))
        self.recompute_overall()

    def summary(self) -> dict:
        return {
            "leptin_factor": round(self.leptin_factor, 3),
            "thyroid_t3_factor": round(self.thyroid_t3_factor, 3),
            "sns_factor": round(self.sns_factor, 3),
            "mitochondrial_efficiency": round(self.mitochondrial_efficiency, 3),
            "muscle_efficiency": round(self.muscle_efficiency, 3),
            "neat_factor": round(self.neat_factor, 3),
            "overall_adaptive_factor": round(self.overall_factor, 3),
            "weeks_in_deficit": self.weeks_in_deficit,
            "percent_weight_lost": self.percent_weight_lost,
        }


class AdaptiveThermogenesisModel:
    """Caloric restriction / overfeeding adaptation driver."""

    def __init__(self, neat_model: NEATModel | None = None):
        self.state = AdaptiveThermogenesisState()
        self.neat = neat_model or NEATModel()

    def apply_caloric_restriction(self, percent_weight_loss: float, weeks: float = 4.0):
        severity = min(1.0, percent_weight_loss / 15.0)
        time_factor = min(1.0, weeks / 8.0)

        self.state.percent_weight_lost = percent_weight_loss
        self.state.weeks_in_deficit = weeks
        self.state.leptin_factor = 1.0 - 0.25 * severity * time_factor
        self.state.thyroid_t3_factor = 1.0 - 0.12 * severity * time_factor
        self.state.sns_factor = 1.0 - 0.18 * severity * time_factor
        self.state.mitochondrial_efficiency = 1.0 + 0.08 * severity * time_factor
        self.state.muscle_efficiency = 1.0 + 0.06 * severity * time_factor

        neat_f = self.neat.apply_restriction(
            percent_weight_loss, weeks,
            leptin_factor=self.state.leptin_factor,
            sns_factor=self.state.sns_factor,
        )
        self.state.neat_factor = neat_f
        self.state.recompute_overall()
        return self.state

    def apply_overfeeding(self, percent_weight_gain: float, weeks: float = 4.0,
                          spontaneous_neat: bool = True):
        severity = min(1.0, percent_weight_gain / 12.0)
        time_factor = min(1.0, weeks / 6.0)

        self.state.leptin_factor = 1.0 + 0.10 * severity * time_factor
        self.state.thyroid_t3_factor = 1.0 + 0.06 * severity * time_factor
        self.state.sns_factor = 1.0 + 0.08 * severity * time_factor
        self.state.mitochondrial_efficiency = 1.0 - 0.04 * severity * time_factor
        self.state.muscle_efficiency = 1.0 - 0.03 * severity * time_factor
        neat_f = self.neat.apply_overfeeding(percent_weight_gain, weeks, spontaneous_neat)
        self.state.neat_factor = neat_f
        self.state.recompute_overall()
        return self.state

    def reset(self):
        self.state = AdaptiveThermogenesisState()
        self.neat.reset()


# ==============================================================================
# Body composition + BMR / TDEE
# ==============================================================================

class BodyCompositionEnergy:
    """Calculates BMR, TDEE, NEAT, and applies adaptive thermogenesis."""

    def __init__(self):
        self.adaptive_factor = 1.0
        self.neat_model = NEATModel()
        self.adaptive_model = AdaptiveThermogenesisModel(self.neat_model)

    # ------------------------------------------------------------------
    # BMR equations
    # ------------------------------------------------------------------
    @staticmethod
    def mifflin_st_jeor(sex: Sex, weight_kg: float, height_cm: float, age: float) -> float:
        base = 10 * weight_kg + 6.25 * height_cm - 5 * age
        return base + 5 if sex == Sex.MALE else base - 161

    @staticmethod
    def harris_benedict_revised(sex: Sex, weight_kg: float, height_cm: float, age: float) -> float:
        if sex == Sex.MALE:
            return 88.362 + (13.397 * weight_kg) + (4.799 * height_cm) - (5.677 * age)
        return 447.593 + (9.247 * weight_kg) + (3.098 * height_cm) - (4.330 * age)

    @staticmethod
    def cunningham(lean_mass_kg: float) -> float:
        return 500 + 22 * lean_mass_kg

    @staticmethod
    def katch_mcardle(lean_mass_kg: float) -> float:
        return 370 + 21.6 * lean_mass_kg

    @staticmethod
    def estimate_lean_mass(weight_kg: float, body_fat_percent: float) -> float:
        return weight_kg * (1 - body_fat_percent / 100.0)

    @staticmethod
    def bmi(weight_kg: float, height_cm: float) -> float:
        return weight_kg / ((height_cm / 100.0) ** 2)

    @staticmethod
    def bmi_category(bmi_value: float) -> str:
        if bmi_value < 18.5:
            return "Underweight"
        if bmi_value < 25:
            return "Normal weight"
        if bmi_value < 30:
            return "Overweight"
        return "Obese"

    @staticmethod
    def navy_body_fat(
        sex: Sex,
        height_cm: float,
        waist_cm: float,
        neck_cm: float,
        hip_cm: float | None = None,
    ) -> float:
        if sex == Sex.MALE:
            return 86.010 * math.log10(waist_cm - neck_cm) - 70.041 * math.log10(height_cm) + 36.76
        if hip_cm is None:
            raise ValueError("hip_cm required for female Navy formula")
        return (
            163.205 * math.log10(waist_cm + hip_cm - neck_cm)
            - 97.684 * math.log10(height_cm)
            - 78.387
        )

    @staticmethod
    def tef_kcal(calories_intake: float, meal_composition: dict[str, float] | None = None) -> float:
        """
        Thermic effect of food ~8–10% mixed diet.
        Protein ~20–30%, carb ~5–10%, fat ~0–3%.
        """
        if not meal_composition:
            return calories_intake * 0.10
        p = meal_composition.get("protein_g", 0) * 4
        c = meal_composition.get("carbs_g", 0) * 4
        f = meal_composition.get("fat_g", 0) * 9
        total = p + c + f
        if total <= 0:
            return calories_intake * 0.10
        return p * 0.25 + c * 0.08 + f * 0.02

    def calculate(
        self,
        anthro: Anthropometrics,
        activity: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE,
        prefer_cunningham: bool = True,
        exercise_kcal: float = 0.0,
        calories_intake: float = 0.0,
    ) -> EnergyExpenditureResult:
        bmr_mifflin = self.mifflin_st_jeor(anthro.sex, anthro.weight_kg, anthro.height_cm, anthro.age_years)
        bmr_hb = self.harris_benedict_revised(anthro.sex, anthro.weight_kg, anthro.height_cm, anthro.age_years)

        bmr_cunningham = None
        bmr_km = None
        chosen_bmr = bmr_mifflin
        notes = "Mifflin-St Jeor selected (default)"

        lbm = anthro.lean_mass_kg
        if lbm is None and anthro.body_fat_percent is not None:
            lbm = self.estimate_lean_mass(anthro.weight_kg, anthro.body_fat_percent)

        if lbm is not None:
            bmr_cunningham = self.cunningham(lbm)
            bmr_km = self.katch_mcardle(lbm)
            if prefer_cunningham:
                chosen_bmr = bmr_cunningham
                notes = "Cunningham selected (lean mass known/estimated)"

        pal = PAL_FACTORS[activity]
        neat = self.neat_model.daily_kcal(anthro.weight_kg)
        # Classic PAL TDEE for comparison; also component breakdown
        tdee_pal = chosen_bmr * pal
        tef = self.tef_kcal(calories_intake) if calories_intake > 0 else chosen_bmr * 0.10
        # Component TDEE ≈ BMR + TEF + NEAT + EAT
        tdee_components = chosen_bmr + tef + neat + exercise_kcal
        # Blend: prefer PAL when no detailed NEAT profile customization
        tdee = 0.6 * tdee_pal + 0.4 * tdee_components

        adaptive = self.adaptive_factor
        if self.adaptive_model.state.overall_factor != 1.0:
            adaptive = self.adaptive_model.state.overall_factor
        adjusted = tdee * adaptive

        return EnergyExpenditureResult(
            bmr_mifflin=round(bmr_mifflin, 1),
            bmr_harris_benedict=round(bmr_hb, 1),
            bmr_cunningham=round(bmr_cunningham, 1) if bmr_cunningham else None,
            bmr_katch_mcardle=round(bmr_km, 1) if bmr_km else None,
            chosen_bmr=round(chosen_bmr, 1),
            pal=pal,
            tdee=round(tdee, 1),
            neat_kcal=round(neat, 1),
            eat_kcal=round(exercise_kcal, 1),
            tef_kcal=round(tef, 1),
            adaptive_thermogenesis_factor=round(adaptive, 3),
            adjusted_tdee=round(adjusted, 1),
            method_notes=notes,
        )

    def set_adaptive_thermogenesis(self, factor: float):
        self.adaptive_factor = max(0.7, min(1.3, factor))

    def set_neat_profile(self, profile: NEATProfile):
        self.neat_model.profile = profile
        self.adaptive_model.neat = self.neat_model

    def summary(self, anthro: Anthropometrics, activity: ActivityLevel) -> dict:
        result = self.calculate(anthro, activity)
        bmi_val = self.bmi(anthro.weight_kg, anthro.height_cm)
        return {
            "sex": anthro.sex.value,
            "age": anthro.age_years,
            "weight_kg": anthro.weight_kg,
            "height_cm": anthro.height_cm,
            "bmi": round(bmi_val, 1),
            "bmi_category": self.bmi_category(bmi_val),
            "bmr_mifflin": result.bmr_mifflin,
            "bmr_harris_benedict": result.bmr_harris_benedict,
            "bmr_cunningham": result.bmr_cunningham,
            "bmr_katch_mcardle": result.bmr_katch_mcardle,
            "chosen_bmr": result.chosen_bmr,
            "activity": activity.value,
            "pal": result.pal,
            "neat_kcal": result.neat_kcal,
            "eat_kcal": result.eat_kcal,
            "tef_kcal": result.tef_kcal,
            "tdee": result.tdee,
            "adaptive_factor": result.adaptive_thermogenesis_factor,
            "adjusted_tdee": result.adjusted_tdee,
            "neat_profile": self.neat_model.profile.summary(anthro.weight_kg),
            "notes": result.method_notes,
        }

    def full_report(
        self,
        anthro: Anthropometrics,
        activity: ActivityLevel = ActivityLevel.MODERATELY_ACTIVE,
        known_ffm_kg: float | None = None,
        exercise_kcal: float = 0.0,
    ) -> dict:
        """Rich report used by demos / engine."""
        if known_ffm_kg is not None:
            anthro.lean_mass_kg = known_ffm_kg
            if anthro.body_fat_percent is None and anthro.weight_kg > 0:
                anthro.body_fat_percent = 100.0 * (1 - known_ffm_kg / anthro.weight_kg)
        base = self.summary(anthro, activity)
        # component energy identity
        base["energy_partition"] = {
            "bmr": base["chosen_bmr"],
            "tef": base["tef_kcal"],
            "neat": base["neat_kcal"],
            "eat": exercise_kcal or base["eat_kcal"],
            "adaptive_multiplier": base["adaptive_factor"],
        }
        base["adaptive_components"] = self.adaptive_model.state.summary()
        base["methods"] = {
            "body_composition": ["BMI", "Navy circumference", "known FFM / DEXA input"],
            "bmr": ["Mifflin-St Jeor", "Harris-Benedict revised", "Cunningham", "Katch-McArdle"],
            "notes": "DEXA/BIA/skinfold are measurement methods; pass lean_mass_kg or body_fat_percent when known",
        }
        return base


def demonstrate_adaptive_thermogenesis():
    state = AdaptiveThermogenesisState()
    print("=== Adaptive Thermogenesis Progression (25% deficit) ===")
    print(f"{'Week':<6} {'%Lost':<8} {'Leptin':<8} {'Thyroid':<8} {'SNS':<8} {'NEAT':<8} {'Total':<10}")
    for week in [0, 2, 4, 8, 12, 16]:
        pct_lost = week * 0.6
        state.update_from_deficit(week, pct_lost, severity=0.25)
        print(
            f"{week:<6} {pct_lost:<8.1f} {state.leptin_factor:<8.3f} "
            f"{state.thyroid_t3_factor:<8.3f} {state.sns_factor:<8.3f} "
            f"{state.neat_factor:<8.3f} {state.overall_factor:<10.3f}"
        )


if __name__ == "__main__":
    import json

    demonstrate_adaptive_thermogenesis()
    print()
    engine = BodyCompositionEnergy()
    engine.set_neat_profile(NEATProfile(
        occupation=OccupationActivity.DESK,
        fidgeting_score=0.3,
        steps_per_day=4500,
        screen_hours=8,
    ))
    athlete = Anthropometrics(
        age_years=28, sex=Sex.MALE, weight_kg=82, height_cm=180, body_fat_percent=12
    )
    report = engine.full_report(athlete, activity=ActivityLevel.VERY_ACTIVE, known_ffm_kg=73)
    print(json.dumps(report, indent=2))

    print("\n=== Restriction 10% BW / 8 weeks ===")
    engine.adaptive_model.apply_caloric_restriction(10, 8)
    engine.adaptive_factor = engine.adaptive_model.state.overall_factor
    print(json.dumps(engine.full_report(athlete, ActivityLevel.VERY_ACTIVE, known_ffm_kg=73), indent=2))
