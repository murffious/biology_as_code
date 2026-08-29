"""BodySystem protocol — biology-as-code side of the nutrition ontology.

Need and System Load Index are functions over implementers.
Missing systems lower confidence; they do not raise exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Literal, Protocol


SystemKind = Literal["gi", "renal", "endocrine"]
NutrientId = str


@dataclass(frozen=True)
class Measurement:
    nutrient_id: NutrientId
    amount: float
    unit: str
    confidence: float = 1.0


NutrientVector = tuple[Measurement, ...]


@dataclass
class MealContext:
    processing_level: str | None = None
    phytochemical_load: float | None = None
    transit_time_h: float | None = None
    portion: float = 1.0


@dataclass
class SystemLoad:
    system_kind: SystemKind
    score: float  # 0–100
    drivers: tuple[str, ...] = ()
    confidence: float = 1.0


class BodySystem(Protocol):
    system_id: str
    human_id: str
    system_kind: SystemKind
    as_of: datetime
    source: str
    confidence: float

    def absorb(self, incoming: NutrientVector, ctx: MealContext) -> NutrientVector:
        """Transform the incoming vector. Default implementers may return incoming."""

    def target_adjust(self, base_target: NutrientVector, activity_level: str) -> NutrientVector:
        """Shift DRI-like targets for this human."""

    def load(self, incoming: NutrientVector, ctx: MealContext) -> SystemLoad:
        """Work this meal imposed on the system."""


def scale(vec: NutrientVector, factor: float, conf: float) -> NutrientVector:
    return tuple(
        Measurement(m.nutrient_id, m.amount * factor, m.unit, min(m.confidence, conf))
        for m in vec
    )


def by_id(vec: NutrientVector, nutrient_id: NutrientId) -> Measurement | None:
    for m in vec:
        if m.nutrient_id == nutrient_id:
            return m
    return None


@dataclass
class DigestiveAssimilation:
    system_id: str
    human_id: str
    as_of: datetime
    source: str = "inferred"
    confidence: float = 0.4
    enzyme_output: float = 1.0          # 1.0 = textbook baseline
    microbiome_diversity: float = 1.0
    villus_integrity: float = 1.0
    transit_baseline_h: float = 24.0
    system_kind: SystemKind = "gi"

    def absorb(self, incoming: NutrientVector, ctx: MealContext) -> NutrientVector:
        matrix = 0.7 if ctx.processing_level == "ultra" else 1.0
        hydro = max(0.2, min(1.0, self.enzyme_output))
        uptake = max(0.2, min(1.0, self.villus_integrity))
        factor = matrix * hydro * uptake
        return scale(incoming, factor, self.confidence)

    def target_adjust(self, base_target: NutrientVector, activity_level: str) -> NutrientVector:
        if self.villus_integrity >= 0.8:
            return base_target
        # malabsorption raises need rather than pretending food was absorbed
        return scale(base_target, 1.0 + (1.0 - self.villus_integrity) * 0.25, self.confidence)

    def load(self, incoming: NutrientVector, ctx: MealContext) -> SystemLoad:
        processing_penalty = 25.0 if ctx.processing_level == "ultra" else 0.0
        enzyme_strain = max(0.0, (1.0 - self.enzyme_output) * 40.0)
        score = min(100.0, 20.0 + processing_penalty + enzyme_strain)
        drivers = []
        if processing_penalty:
            drivers.append("collapsed_matrix")
        if enzyme_strain:
            drivers.append("enzyme_demand")
        return SystemLoad("gi", score, tuple(drivers), self.confidence)


@dataclass
class EndocrineSetpoint:
    system_id: str
    human_id: str
    as_of: datetime
    source: str = "inferred"
    confidence: float = 0.4
    insulin_sensitivity: float = 1.0
    inferred_metabolic_rate: float = 1.0
    vit_d_status: float = 1.0
    system_kind: SystemKind = "endocrine"

    def absorb(self, incoming: NutrientVector, ctx: MealContext) -> NutrientVector:
        # Disposal, not a second gut. Scale glucose-like nutrients only.
        out = []
        for m in incoming:
            if m.nutrient_id in {"glucose", "available_carb"}:
                out.append(
                    Measurement(
                        m.nutrient_id,
                        m.amount * self.insulin_sensitivity,
                        m.unit,
                        min(m.confidence, self.confidence),
                    )
                )
            else:
                out.append(m)
        return tuple(out)

    def target_adjust(self, base_target: NutrientVector, activity_level: str) -> NutrientVector:
        out = []
        for m in base_target:
            amt = m.amount
            if m.nutrient_id in {"energy_kcal", "energy"}:
                amt *= self.inferred_metabolic_rate
            if m.nutrient_id in {"vitamin_d", "vit_d"}:
                amt *= 1.0 + max(0.0, 1.0 - self.vit_d_status) * 0.5
            out.append(Measurement(m.nutrient_id, amt, m.unit, min(m.confidence, self.confidence)))
        return tuple(out)

    def load(self, incoming: NutrientVector, ctx: MealContext) -> SystemLoad:
        carb = by_id(incoming, "available_carb") or by_id(incoming, "glucose")
        carb_amt = carb.amount if carb else 0.0
        glycemic_strain = (carb_amt / 50.0) * (2.0 - self.insulin_sensitivity) * 20.0
        score = min(100.0, 15.0 + max(0.0, glycemic_strain))
        drivers = ("glycemic_demand",) if glycemic_strain > 10 else ()
        return SystemLoad("endocrine", score, drivers, self.confidence)


@dataclass
class RenalHandling:
    system_id: str
    human_id: str
    as_of: datetime
    source: str = "inferred"
    confidence: float = 0.3
    egfr: float | None = None
    protein_load_tolerance: float = 1.0
    system_kind: SystemKind = "renal"

    def absorb(self, incoming: NutrientVector, ctx: MealContext) -> NutrientVector:
        if self.egfr is None or self.egfr >= 60:
            return incoming
        # reduced retention of water-solubles when wasting is documented
        factor = max(0.5, self.egfr / 90.0)
        water_soluble = {"vitamin_c", "b6", "b12", "folate", "potassium", "magnesium"}
        out = []
        for m in incoming:
            if m.nutrient_id in water_soluble:
                out.append(Measurement(m.nutrient_id, m.amount * factor, m.unit, min(m.confidence, self.confidence)))
            else:
                out.append(m)
        return tuple(out)

    def target_adjust(self, base_target: NutrientVector, activity_level: str) -> NutrientVector:
        if self.egfr is None or self.egfr >= 60:
            return base_target
        out = []
        for m in base_target:
            amt = m.amount
            if m.nutrient_id in {"protein", "potassium", "phosphorus"}:
                amt *= 0.8  # cap, not raise
            out.append(Measurement(m.nutrient_id, amt, m.unit, min(m.confidence, self.confidence)))
        return tuple(out)

    def load(self, incoming: NutrientVector, ctx: MealContext) -> SystemLoad:
        protein = by_id(incoming, "protein")
        p = protein.amount if protein else 0.0
        score = min(100.0, 10.0 + p * 0.6 / max(self.protein_load_tolerance, 0.2))
        return SystemLoad("renal", score, ("nitrogen_load",) if p else (), self.confidence)


WEIGHTS = {"gi": 0.45, "endocrine": 0.30, "renal": 0.25}


def predict_absorption(
    incoming: NutrientVector,
    ctx: MealContext,
    systems: Iterable[BodySystem],
) -> NutrientVector:
    vec = incoming
    order = {"gi": 0, "endocrine": 1, "renal": 2}
    for sys in sorted(systems, key=lambda s: order.get(s.system_kind, 9)):
        vec = sys.absorb(vec, ctx)
    return vec


def nutrient_gap(
    base_target: NutrientVector,
    absorbed: NutrientVector,
    systems: Iterable[BodySystem],
    activity_level: str = "moderate",
) -> NutrientVector:
    target = base_target
    for sys in systems:
        target = sys.target_adjust(target, activity_level)
    absorbed_map = {m.nutrient_id: m for m in absorbed}
    gaps = []
    for t in target:
        got = absorbed_map.get(t.nutrient_id)
        got_amt = got.amount if got else 0.0
        conf = min(t.confidence, got.confidence if got else 0.3)
        gaps.append(Measurement(t.nutrient_id, t.amount - got_amt, t.unit, conf))
    return tuple(gaps)


def system_load_index(
    incoming: NutrientVector,
    ctx: MealContext,
    systems: Iterable[BodySystem],
) -> tuple[float, tuple[SystemLoad, ...]]:
    loads = tuple(sys.load(incoming, ctx) for sys in systems)
    if not loads:
        return 0.0, ()
    wsum = sum(WEIGHTS.get(ld.system_kind, 0.0) * ld.score * ld.confidence for ld in loads)
    w = sum(WEIGHTS.get(ld.system_kind, 0.0) * ld.confidence for ld in loads)
    return (wsum / w if w else 0.0), loads
