"""
nitrogen_balance.py
=================================================================
Nitrogen balance model from Nutritional Biochemistry preface
=================================================================
"""

from dataclasses import dataclass


@dataclass
class NitrogenBalance:
    intake_g: float          # dietary nitrogen intake (g/day)
    excretion_g: float       # urinary + fecal + miscellaneous N loss (g/day)
    balance_g: float = 0.0

    def calculate(self) -> str:
        self.balance_g = self.intake_g - self.excretion_g
        if self.balance_g > 0:
            return "positive (anabolic / growth)"
        elif self.balance_g < 0:
            return "negative (catabolic / deficiency)"
        else:
            return "equilibrium (maintenance)"

    def summary(self) -> dict:
        return {
            "intake_g": self.intake_g,
            "excretion_g": self.excretion_g,
            "balance_g": self.balance_g,
            "status": self.calculate()
        }


def get_nitrogen_balance_example() -> NitrogenBalance:
    # Example from typical adult maintenance
    return NitrogenBalance(intake_g=12.0, excretion_g=12.0)


if __name__ == "__main__":
    nb = get_nitrogen_balance_example()
    print(nb.summary())
    # Test a deficiency
    nb2 = NitrogenBalance(intake_g=8.0, excretion_g=12.0)
    print(nb2.summary())
