"""
respiratory_quotient.py
=================================================================
Respiratory Quotient (RQ) model from Nutritional Biochemistry preface
=================================================================
"""

from dataclasses import dataclass


@dataclass
class RespiratoryQuotient:
    co2_produced_ml: float   # CO₂ volume produced
    o2_consumed_ml: float    # O₂ volume consumed
    rq: float = 0.0

    def calculate(self) -> float:
        self.rq = self.co2_produced_ml / self.o2_consumed_ml if self.o2_consumed_ml else 0.0
        return self.rq

    def interpretation(self) -> str:
        if self.rq > 1.0:
            return "carbohydrate oxidation + lipogenesis (excess calories)"
        elif self.rq == 1.0:
            return "pure carbohydrate oxidation"
        elif 0.85 < self.rq < 1.0:
            return "mixed diet (carbs + fat)"
        elif self.rq == 0.7:
            return "pure fat oxidation"
        else:
            return "protein or mixed with ketogenesis"

    def summary(self) -> dict:
        return {
            "rq": self.calculate(),
            "interpretation": self.interpretation()
        }


def get_rq_example() -> RespiratoryQuotient:
    # Typical mixed diet example
    return RespiratoryQuotient(co2_produced_ml=200, o2_consumed_ml=220)


if __name__ == "__main__":
    rq = get_rq_example()
    print(rq.summary())
