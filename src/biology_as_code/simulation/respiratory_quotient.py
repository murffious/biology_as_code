"""
respiratory_quotient.py
=================================================================
Respiratory Quotient (RQ) — CO2 produced over O2 consumed, and what it says
about which substrate is being burned.

RQ is 1.00 for carbohydrate and about 0.70 for fat, because oxidising a molecule
that already carries oxygen needs less inhaled O2 per CO2 released. Between those
two lies a mixture, which is the useful signal: RQ reports what the body is
*actually* oxidising right now, not what was eaten.

Berdanier gives 0.87 as a typical daily mixed-diet average and 0.85 for the
postabsorptive state, with palmitate at 16/23 = 0.696.
=================================================================
"""

from __future__ import annotations

from dataclasses import dataclass

#: Pure-substrate endpoints. Fat is a range across fatty acids, not a constant;
#: 0.70 is the conventional value and palmitate is 0.696.
RQ_FAT = 0.70
RQ_CARBOHYDRATE = 1.00

#: Reference RQs (Berdanier pp. 6, 9-10). ``tripalmitin`` is the corrected value:
#: the printed combustion equation gives 55/76.5 = 0.719 but does not balance, and
#: tripalmitin is C51H98O6 — see ERR-TRIP-01 in docs/VALIDATION_LEDGER.md.
RQ_REFERENCE = {
    "carbohydrate_only": 1.00,
    "postabsorptive_mixed": 0.85,
    "fat_only": 0.70,
    "typical_mixed_diet_daily_average": 0.87,
    "palmitate": 16 / 23,
    "tripalmitin": 51 / 72.5,
    "tripalmitin_as_printed": 55 / 76.5,
}

#: Tolerance for calling a measured RQ "pure" carbohydrate or fat. Measured RQs
#: essentially never land on 1.00 or 0.70 exactly, so comparing with ``==`` makes
#: those branches unreachable and pushes ordinary fat-oxidising values (0.75) into
#: whatever the fallback happens to be.
RQ_TOLERANCE = 0.02


@dataclass
class RespiratoryQuotient:
    co2_produced_ml: float   # CO₂ volume produced
    o2_consumed_ml: float    # O₂ volume consumed
    rq: float = 0.0

    def calculate(self) -> float:
        self.rq = self.co2_produced_ml / self.o2_consumed_ml if self.o2_consumed_ml else 0.0
        return self.rq

    def interpretation(self) -> str:
        """Plain reading of the current RQ.

        Calls :meth:`calculate` first: reading ``self.rq`` before it is computed
        would silently interpret the 0.0 default as a real measurement.
        """
        rq = self.calculate()
        if rq <= 0:
            return "no measurement (O2 consumption is zero)"
        if rq > RQ_CARBOHYDRATE + RQ_TOLERANCE:
            return "carbohydrate oxidation + lipogenesis (excess calories)"
        if abs(rq - RQ_CARBOHYDRATE) <= RQ_TOLERANCE:
            return "pure carbohydrate oxidation"
        if abs(rq - RQ_FAT) <= RQ_TOLERANCE:
            return "pure fat oxidation"
        if rq < RQ_FAT:
            return "below fat-only; suggests ketogenesis, gluconeogenesis or hypoventilation"
        if rq > 0.85:
            return "mixed diet, carbohydrate-predominant"
        return "mixed diet, fat-predominant"

    def substrate_mix(self) -> dict[str, float] | None:
        """Fraction of oxidation from carbohydrate vs fat, or None if out of range.

        Linear interpolation between the fat and carbohydrate endpoints. This is
        the *non-protein* RQ convention: protein oxidation is ignored, which is
        standard and is also why the answer is an approximation.

        Returns None outside 0.70-1.00 rather than extrapolating. An RQ above 1.00
        means net lipogenesis and an RQ below 0.70 means something other than
        simple substrate mixing; interpolating either would produce a fraction
        outside 0-1 and report it as though it were a measurement.
        """
        rq = self.calculate()
        if not RQ_FAT <= rq <= RQ_CARBOHYDRATE:
            return None
        carbohydrate = (rq - RQ_FAT) / (RQ_CARBOHYDRATE - RQ_FAT)
        return {
            "carbohydrate_fraction": round(carbohydrate, 3),
            "fat_fraction": round(1 - carbohydrate, 3),
        }

    def summary(self) -> dict:
        return {
            "rq": self.calculate(),
            "interpretation": self.interpretation(),
            "substrate_mix": self.substrate_mix(),
        }


def substrate_mix_from_rq(rq: float) -> dict[str, float] | None:
    """Substrate mix straight from an RQ value. See :meth:`RespiratoryQuotient.substrate_mix`."""
    return RespiratoryQuotient(co2_produced_ml=rq, o2_consumed_ml=1.0).substrate_mix()


def get_rq_example() -> RespiratoryQuotient:
    # Typical mixed diet example
    return RespiratoryQuotient(co2_produced_ml=200, o2_consumed_ml=220)


if __name__ == "__main__":
    rq = get_rq_example()
    print(rq.summary())
    for label, value in [("fasted", 0.75), ("mixed", 0.85), ("post-meal", 0.95)]:
        print(f"  RQ {value} ({label:9}) -> {substrate_mix_from_rq(value)}")
