"""
energy_intake_need.py
=================================================================
Energy Intake & Energy Need model from Nutritional Biochemistry
(Table 1.2 + preface text)
=================================================================
"""

from dataclasses import dataclass


@dataclass
class EnergyBalance:
    intake_kcal: float
    expenditure_kcal: float
    balance_kcal: float = 0.0

    def calculate(self) -> str:
        self.balance_kcal = self.intake_kcal - self.expenditure_kcal
        if self.balance_kcal > 100:
            return "positive (weight gain likely)"
        elif self.balance_kcal < -100:
            return "negative (weight loss likely)"
        else:
            return "equilibrium (maintenance)"

    def summary(self) -> dict:
        return {
            "intake_kcal": self.intake_kcal,
            "expenditure_kcal": self.expenditure_kcal,
            "balance_kcal": self.balance_kcal,
            "status": self.calculate()
        }


def get_energy_example() -> EnergyBalance:
    # Typical maintenance example
    return EnergyBalance(intake_kcal=2500, expenditure_kcal=2500)


if __name__ == "__main__":
    eb = get_energy_example()
    print(eb.summary())

    # Weight loss example
    eb2 = EnergyBalance(intake_kcal=2200, expenditure_kcal=2500)
    print(eb2.summary())
