
"""
hormonal_energy.py
More complete hormonal / energy homeostasis module based on Chapter 7
(Advanced Nutrition and Human Metabolism) – fed, fasting, and exercise states.
"""

import math
from dataclasses import dataclass
from enum import Enum


class MetabolicPhase(Enum):
    FED = "fed"                 # 0–4 h after meal
    POSTABSORPTIVE = "postabsorptive"  # 4–16 h
    FASTING = "fasting"         # 16–48 h
    STARVATION = "starvation"   # >48 h
    EXERCISE = "exercise"
    RECOVERY = "recovery"

@dataclass
class HormonalProfile:
    """Circulating hormone levels (relative units 0–2, 1.0 = normal baseline)."""
    insulin: float = 1.0
    glucagon: float = 1.0
    cortisol: float = 1.0
    epinephrine: float = 1.0
    norepinephrine: float = 1.0
    growth_hormone: float = 1.0
    thyroid_t3: float = 1.0
    leptin: float = 1.0
    ghrelin: float = 1.0
    glp1: float = 0.0
    pyy: float = 0.0
    ampk_activity: float = 0.3      # 0–1
    mtor_activity: float = 0.7      # 0–1

@dataclass
class EnergySystems:
    """Relative contribution / capacity of energy systems."""
    phosphagen: float = 1.0     # ATP-PCr
    glycolytic: float = 1.0     # Anaerobic glycolysis
    oxidative: float = 1.0      # Aerobic (CHO + fat)
    fatty_acid_oxidation: float = 0.8
    gluconeogenesis: float = 0.2
    ketogenesis: float = 0.0

class HormonalEnergyController:
    """
    Manages transitions between metabolic phases and updates
    hormonal profile + energy system priorities.
    """

    def __init__(self):
        self.phase = MetabolicPhase.FED
        self.hormones = HormonalProfile()
        self.energy = EnergySystems()
        self.hours_since_meal: float = 0.0
        self.exercise_intensity: float = 0.0   # 0–1
        self.glycogen_liver: float = 1.0       # 0–1
        self.glycogen_muscle: float = 1.0      # 0–1
        self.adipose_lipolysis: float = 0.2

    def set_phase(self, phase: MetabolicPhase, intensity: float = 0.0):
        self.phase = phase
        self.exercise_intensity = intensity
        self._update_hormones()
        self._update_energy_systems()

    def advance_time(self, hours: float, fed: bool = False):
        """Advance simulation time and update phase if needed."""
        if fed:
            self.hours_since_meal = 0.0
            self.phase = MetabolicPhase.FED
            self.glycogen_liver = min(1.0, self.glycogen_liver + 0.3)
            self.glycogen_muscle = min(1.0, self.glycogen_muscle + 0.15)
        else:
            self.hours_since_meal += hours

            if self.hours_since_meal < 4:
                self.phase = MetabolicPhase.FED
            elif self.hours_since_meal < 16:
                self.phase = MetabolicPhase.POSTABSORPTIVE
            elif self.hours_since_meal < 48:
                self.phase = MetabolicPhase.FASTING
            else:
                self.phase = MetabolicPhase.STARVATION

        self._update_hormones()
        self._update_energy_systems()
        self._update_glycogen(hours)

    def start_exercise(self, intensity: float = 0.7, duration_min: float = 30):
        """Transition into exercise phase."""
        self.phase = MetabolicPhase.EXERCISE
        self.exercise_intensity = max(0.0, min(1.0, intensity))
        self._update_hormones()
        self._update_energy_systems()
        # Glycogen drain proportional to intensity and duration
        drain = intensity * (duration_min / 60) * 0.4
        self.glycogen_muscle = max(0.05, self.glycogen_muscle - drain)
        self.glycogen_liver = max(0.1, self.glycogen_liver - drain * 0.5)

    def end_exercise(self):
        self.phase = MetabolicPhase.RECOVERY
        self.exercise_intensity = 0.0
        self._update_hormones()
        self._update_energy_systems()

    def _update_hormones(self):
        h = self.hormones
        p = self.phase

        if p == MetabolicPhase.FED:
            h.insulin = 1.8
            h.glucagon = 0.6
            h.cortisol = 0.9
            h.epinephrine = 0.7
            h.growth_hormone = 0.8
            h.leptin = 1.2
            h.ghrelin = 0.4
            h.glp1 = 1.4
            h.pyy = 1.3
            h.ampk_activity = 0.25
            h.mtor_activity = 1.4

        elif p == MetabolicPhase.POSTABSORPTIVE:
            h.insulin = 1.0
            h.glucagon = 1.1
            h.cortisol = 1.0
            h.epinephrine = 0.9
            h.growth_hormone = 1.1
            h.leptin = 1.0
            h.ghrelin = 0.8
            h.glp1 = 0.6
            h.pyy = 0.5
            h.ampk_activity = 0.45
            h.mtor_activity = 0.9

        elif p == MetabolicPhase.FASTING:
            h.insulin = 0.5
            h.glucagon = 1.6
            h.cortisol = 1.3
            h.epinephrine = 1.2
            h.growth_hormone = 1.5
            h.leptin = 0.6
            h.ghrelin = 1.4
            h.glp1 = 0.3
            h.pyy = 0.3
            h.ampk_activity = 0.75
            h.mtor_activity = 0.4

        elif p == MetabolicPhase.STARVATION:
            h.insulin = 0.3
            h.glucagon = 1.8
            h.cortisol = 1.5
            h.epinephrine = 1.3
            h.growth_hormone = 1.7
            h.leptin = 0.3
            h.ghrelin = 1.6
            h.glp1 = 0.2
            h.pyy = 0.2
            h.ampk_activity = 0.9
            h.mtor_activity = 0.25

        elif p == MetabolicPhase.EXERCISE:
            intensity = self.exercise_intensity
            h.insulin = 0.6 - 0.3 * intensity
            h.glucagon = 1.2 + 0.6 * intensity
            h.cortisol = 1.1 + 0.5 * intensity
            h.epinephrine = 1.0 + 1.2 * intensity
            h.norepinephrine = 1.0 + 1.0 * intensity
            h.growth_hormone = 1.2 + 0.8 * intensity
            h.ampk_activity = 0.5 + 0.45 * intensity
            h.mtor_activity = 0.6 - 0.3 * intensity
            h.glp1 = 0.8
            h.pyy = 0.7

        elif p == MetabolicPhase.RECOVERY:
            h.insulin = 1.3
            h.glucagon = 0.9
            h.cortisol = 1.1
            h.epinephrine = 0.8
            h.growth_hormone = 1.4
            h.ampk_activity = 0.5
            h.mtor_activity = 1.1
            h.glp1 = 0.9
            h.pyy = 0.8

    def _update_energy_systems(self):
        e = self.energy
        p = self.phase
        intensity = self.exercise_intensity

        if p == MetabolicPhase.FED:
            e.phosphagen = 0.9
            e.glycolytic = 1.0
            e.oxidative = 1.1
            e.fatty_acid_oxidation = 0.5
            e.gluconeogenesis = 0.1
            e.ketogenesis = 0.0

        elif p in (MetabolicPhase.POSTABSORPTIVE, MetabolicPhase.FASTING):
            e.phosphagen = 0.9
            e.glycolytic = 0.7
            e.oxidative = 1.0
            e.fatty_acid_oxidation = 1.3 if p == MetabolicPhase.FASTING else 1.0
            e.gluconeogenesis = 0.8 if p == MetabolicPhase.FASTING else 0.4
            e.ketogenesis = 0.6 if p == MetabolicPhase.FASTING else 0.1

        elif p == MetabolicPhase.STARVATION:
            e.phosphagen = 0.8
            e.glycolytic = 0.4
            e.oxidative = 0.9
            e.fatty_acid_oxidation = 1.5
            e.gluconeogenesis = 1.2
            e.ketogenesis = 1.4

        elif p == MetabolicPhase.EXERCISE:
            # High intensity favors phosphagen + glycolytic
            e.phosphagen = 1.0 + 0.5 * intensity
            e.glycolytic = 0.8 + 0.9 * intensity
            e.oxidative = 1.0 - 0.3 * intensity   # drops at very high intensity
            e.fatty_acid_oxidation = 0.9 - 0.5 * intensity
            e.gluconeogenesis = 0.3
            e.ketogenesis = 0.1

        elif p == MetabolicPhase.RECOVERY:
            e.phosphagen = 1.1
            e.glycolytic = 0.9
            e.oxidative = 1.2
            e.fatty_acid_oxidation = 1.0
            e.gluconeogenesis = 0.3
            e.ketogenesis = 0.1

    def _update_glycogen(self, hours: float):
        if self.phase in (MetabolicPhase.FASTING, MetabolicPhase.STARVATION):
            self.glycogen_liver = max(0.05, self.glycogen_liver - 0.08 * hours)
            self.glycogen_muscle = max(0.1, self.glycogen_muscle - 0.03 * hours)
        elif self.phase == MetabolicPhase.POSTABSORPTIVE:
            self.glycogen_liver = max(0.2, self.glycogen_liver - 0.04 * hours)

    def get_insulin_glucagon_ratio(self) -> float:
        return self.hormones.insulin / max(0.1, self.hormones.glucagon)

    def get_anabolic_catabolic_balance(self) -> float:
        """Positive = anabolic, negative = catabolic."""
        anabolic = (self.hormones.insulin * 0.5 +
                    self.hormones.mtor_activity * 0.4 +
                    self.hormones.growth_hormone * 0.2)
        catabolic = (self.hormones.glucagon * 0.3 +
                     self.hormones.cortisol * 0.3 +
                     self.hormones.ampk_activity * 0.3 +
                     self.hormones.epinephrine * 0.2)
        return anabolic - catabolic

    def update_from_meal(
        self,
        carbs_g: float = 0.0,
        protein_g: float = 0.0,
        fat_g: float = 0.0,
        fiber_g: float = 0.0,
    ) -> dict:
        """
        Engine hook: apply a meal and return hormonal / energy report.
        """
        self.advance_time(0.0, fed=True)
        # Protein + carbs drive mTOR/insulin; fat slower
        load = carbs_g + protein_g * 0.6 + fat_g * 0.2
        self.hormones.insulin = min(2.2, 1.2 + load / 80.0)
        self.hormones.glucagon = max(0.4, 1.0 - carbs_g / 120.0)
        self.hormones.mtor_activity = min(1.6, 0.8 + protein_g / 50.0 + carbs_g / 200.0)
        self.hormones.ampk_activity = max(0.15, 0.4 - load / 200.0)
        # SCFA-linked satiety signals from fiber
        if fiber_g > 0:
            self.hormones.glp1 = min(1.8, 0.8 + fiber_g / 40.0)
            self.hormones.pyy = min(1.6, 0.7 + fiber_g / 45.0)
        self._update_energy_systems()
        report = self.summary()
        report["energy_multiplier"] = round(
            1.0 + 0.05 * (self.get_anabolic_catabolic_balance()), 3
        )
        report["meal_macros"] = {
            "carbs_g": carbs_g, "protein_g": protein_g, "fat_g": fat_g, "fiber_g": fiber_g
        }
        return report

    # ------------------------------------------------------------------
    # Quantitative ATP system time courses (Ch 7 style)
    # ------------------------------------------------------------------
    def energy_system_time_course(
        self,
        duration_sec: float = 120.0,
        intensity: float = 0.85,
        dt_sec: float = 1.0,
    ) -> dict:
        """
        Relative contribution of ATP-PCr, glycolytic, and oxidative systems
        over exercise time at a given intensity (0–1).

        Classic teaching curves:
          - Phosphagen dominant ~0–10 s
          - Glycolytic peaks ~10–60 s
          - Oxidative rises and dominates after ~90–120 s+
        """
        intensity = max(0.0, min(1.0, intensity))
        t = 0.0
        series = []
        # Simple reservoir model
        pcr = 1.0
        glycolytic_cap = 1.0
        while t <= duration_sec:
            # Phosphagen: exponential depletion, faster at high intensity
            pcr_contrib = pcr * math.exp(-t / (8.0 / max(intensity, 0.2)))
            # Glycolysis: rises then falls as acidosis / glycogen limit
            peak = 25.0 + 20.0 * (1.0 - intensity)  # peak later if easier
            glyc = math.exp(-((t - peak) ** 2) / (2 * (18 ** 2))) * intensity
            glyc *= glycolytic_cap
            # Oxidative: asymptotic rise (VO2 kinetics)
            tau = 25.0 + 15.0 * intensity  # slower at very high intensity (O2 deficit)
            ox = (1.0 - math.exp(-t / tau)) * (0.55 + 0.35 * (1.0 - intensity * 0.5))
            # Fat oxidation suppressed at high intensity
            fat_ox = ox * max(0.1, 0.8 - 0.7 * intensity) * (1.0 if t > 60 else t / 60.0)

            total = pcr_contrib + glyc + ox + 1e-6
            series.append({
                "t_sec": round(t, 1),
                "phosphagen": round(pcr_contrib / total, 3),
                "glycolytic": round(glyc / total, 3),
                "oxidative": round(ox / total, 3),
                "fat_oxidation_share": round(fat_ox / total, 3),
                "absolute": {
                    "pcr": round(pcr_contrib, 3),
                    "glyc": round(glyc, 3),
                    "ox": round(ox, 3),
                },
            })
            # deplete reservoirs
            pcr = max(0.05, pcr - 0.04 * intensity * dt_sec / 5.0)
            if t > 45:
                glycolytic_cap = max(0.4, glycolytic_cap - 0.002 * intensity * dt_sec)
            t += dt_sec

        # AMPK / mTOR / PGC-1α signaling sketch after bout
        ampk = min(1.0, 0.35 + intensity * 0.55 + min(duration_sec, 180) / 400.0)
        mtor = max(0.2, 0.7 - intensity * 0.35)  # suppressed during hard work
        # PGC-1α induction scales with AMPK + duration (mitochondrial biogenesis drive)
        pgc1a = min(1.0, ampk * 0.6 + min(duration_sec, 3600) / 3600.0 * 0.5)

        return {
            "duration_sec": duration_sec,
            "intensity": intensity,
            "time_course": series[:: max(1, int(5 / dt_sec))],  # thin for readability
            "signaling": {
                "ampk": round(ampk, 3),
                "mtor": round(mtor, 3),
                "pgc1a_induction": round(pgc1a, 3),
                "note": "PGC-1α rises with AMPK + endurance volume; mTOR recovers post-exercise with feeding",
            },
            "crossover_notes": {
                "phosphagen_dominant_sec": "~0–10 s",
                "glycolytic_peak_sec": "~15–60 s",
                "oxidative_dominant_after_sec": "~90–120 s+",
            },
        }

    def apply_exercise_signaling(self, intensity: float, duration_min: float) -> dict:
        """Update hormone profile after exercise using AMPK–mTOR–PGC-1α axis."""
        self.start_exercise(intensity, duration_min)
        course = self.energy_system_time_course(duration_min * 60.0, intensity)
        sig = course["signaling"]
        self.hormones.ampk_activity = sig["ampk"]
        self.hormones.mtor_activity = sig["mtor"]
        self.end_exercise()
        # Recovery: mTOR rebounds if not still AMPK-dominant
        self.hormones.mtor_activity = min(1.4, sig["mtor"] + 0.35)
        out = self.summary()
        out["exercise_time_course_meta"] = course["crossover_notes"]
        out["pgc1a_induction"] = sig["pgc1a_induction"]
        return out

    def summary(self) -> dict:
        return {
            "phase": self.phase.value,
            "hours_since_meal": round(self.hours_since_meal, 1),
            "insulin_glucagon_ratio": round(self.get_insulin_glucagon_ratio(), 2),
            "anabolic_catabolic": round(self.get_anabolic_catabolic_balance(), 2),
            "ampk": round(self.hormones.ampk_activity, 2),
            "mtor": round(self.hormones.mtor_activity, 2),
            "epinephrine": round(self.hormones.epinephrine, 2),
            "norepinephrine": round(self.hormones.norepinephrine, 2),
            "thyroid_t3": round(self.hormones.thyroid_t3, 2),
            "liver_glycogen": round(self.glycogen_liver, 2),
            "muscle_glycogen": round(self.glycogen_muscle, 2),
            "fatty_acid_ox": round(self.energy.fatty_acid_oxidation, 2),
            "gluconeogenesis": round(self.energy.gluconeogenesis, 2),
            "ketogenesis": round(self.energy.ketogenesis, 2),
            "energy_systems": {
                "phosphagen": round(self.energy.phosphagen, 2),
                "glycolytic": round(self.energy.glycolytic, 2),
                "oxidative": round(self.energy.oxidative, 2),
            },
        }

