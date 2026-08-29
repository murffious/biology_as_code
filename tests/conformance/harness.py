"""
Shared harness for the ward-conformance suite.

Two jobs. First, drive the real engine wherever the real engine can be driven,
so a conformance test fails on its assertion rather than on an import. Second,
raise :class:`MechanismMissing` with a precise statement of the gap wherever it
cannot, so an ``xfail`` reason reads as a specification requirement instead of
an accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from biology_as_code.packets import FoodPacket, get_packet

#: Atwater general factors, kcal per gram.
#:
#: Specified here for legacy compatibility only. They are the thing tests 2 and
#: 5 exist to show the limits of: they price a gram of a food's analyte panel
#: without asking whether the gram is reachable. Annex-B status — see
#: docs/notational-conventions.md. Not for new work.
ATWATER_GENERAL = {"carbs": 4.0, "protein": 4.0, "fats": 9.0, "fiber": 2.0}


class MechanismMissing(NotImplementedError):
    """
    The engine has no mechanism for what a conformance test needs.

    Carries the requirement, not just a failure: ``needs`` names what has to
    exist, so the xfail reason states a specification gap.
    """

    def __init__(self, what: str, needs: str):
        self.what = what
        self.needs = needs
        super().__init__(f"{what} — needs: {needs}")


@dataclass(frozen=True)
class EnergyPrediction:
    """What the engine thinks a food delivers, versus what its panel claims."""

    label_kcal: float
    """Metabolizable energy the engine predicts, including colonic salvage."""
    predicted_me_kcal: float

    @property
    def overestimate_percent(self) -> float:
        """
        How much the label overstates delivered energy, as a percentage.

        Positive means the panel promises more than the engine delivers.
        """
        if self.predicted_me_kcal <= 0:
            raise ValueError("predicted metabolizable energy must be positive")
        return 100.0 * (self.label_kcal - self.predicted_me_kcal) / self.label_kcal


def atwater_kcal(*, carbs_g: float, protein_g: float, fats_g: float, fiber_g: float = 0.0) -> float:
    """Gross energy by Atwater general factors. Annex-B; not for new work."""
    return (
        carbs_g * ATWATER_GENERAL["carbs"]
        + protein_g * ATWATER_GENERAL["protein"]
        + fats_g * ATWATER_GENERAL["fats"]
        + fiber_g * ATWATER_GENERAL["fiber"]
    )


def predict_energy(
    packet: FoodPacket,
    *,
    carbs_g: float,
    protein_g: float,
    fats_g: float,
    fiber_g: float = 0.0,
) -> EnergyPrediction:
    """
    Run the real engine on a packet's macros and report label vs delivered.

    The packet is passed in as well as the macros because the *point* of tests
    2 and 5 is that the macros alone are not enough. Today the engine ignores
    the packet — it takes grams — which is exactly why those tests fail. When
    the bioaccessibility gate lands, this call will start returning different
    answers for two packets with identical macros, and the tests flip.
    """
    from biology_as_code import simulate_meal

    result = simulate_meal(
        name=packet.id,
        carbs_g=carbs_g,
        protein_g=protein_g,
        fats_g=fats_g,
        fiber_g=fiber_g,
    )
    absorbed = result.absorbed_macros_g
    delivered = atwater_kcal(
        carbs_g=float(absorbed.get("carbs", 0.0)),
        protein_g=float(absorbed.get("protein", 0.0)),
        fats_g=float(absorbed.get("fats", 0.0)),
    )
    # Colonic salvage counts toward metabolizable energy: what the microbiota
    # ferment and the host takes up is delivered, just not by the small
    # intestine. Leaving it out would overstate the shortfall.
    salvage = float((result.report.get("scfa") or {}).get("total_scfa_kcal", 0.0))

    return EnergyPrediction(
        label_kcal=atwater_kcal(
            carbs_g=carbs_g, protein_g=protein_g, fats_g=fats_g, fiber_g=fiber_g
        ),
        predicted_me_kcal=delivered + salvage,
    )


def predicted_glycemic_iauc(
    packet: FoodPacket, *, carbs_g: float, fiber_g: float = 0.0
) -> float:
    """
    A GlycemicResponse/1.0 iAUC for a packet.

    The engine produces no timed glucose series, so there is nothing to
    integrate. It does produce a small-intestinal carbohydrate absorption
    total, which is the closest available proxy and is what this returns — a
    packet-blind number, which is the finding test 5 records.
    """
    from biology_as_code import simulate_meal

    result = simulate_meal(name=packet.id, carbs_g=carbs_g, fiber_g=fiber_g)
    return float(result.absorbed_macros_g.get("carbs", 0.0))


def predict_ad_libitum_intake_kcal(
    packets: list[str], *, days: int, host: dict[str, Any] | None = None
) -> float:
    """
    Spontaneous energy intake over an exposure period.

    Not implemented, and not implementable from what exists. Predicting what
    someone eats when free-feeding requires the eating occasion to be an
    outcome of the model rather than an input to it: an oral process on the
    bite clock, gastric filling and emptying, and a controller that closes the
    loop from satiation signals back to how much is consumed. The engine takes
    grams as an input and has no such loop.
    """
    raise MechanismMissing(
        f"spontaneous intake over {days} days for {len(packets)} packet(s)",
        "an oral (bite-clock) process, a gastric filling/emptying compartment, "
        "and an intake controller closing the loop from satiation signals back "
        "to consumed grams. simulate_meal takes grams as input, so intake "
        "cannot currently be an output.",
    )


def predict_ldl_response(packet_id: str, *, fat_g: float) -> float:
    """
    LDL-cholesterol response to a fat-matched packet.

    Not implemented. LDL response is a multi-week outcome on the adaptation
    clock, downstream of lipoprotein handling the engine does not model — the
    lipoprotein_transport pack describes the biology but exposes no state the
    simulation carries forward between meals.
    """
    raise MechanismMissing(
        f"LDL response to {packet_id} at {fat_g} g fat",
        "a lipoprotein compartment with adaptation-clock state carried between "
        "meals. The engine's horizon is a single eating occasion.",
    )


def packet_pair(a: str, b: str) -> tuple[FoodPacket, FoodPacket]:
    """Load two packets, failing loudly if either is missing."""
    return get_packet(a), get_packet(b)


def within_relative_tolerance(observed: float, target: float, tolerance_fraction: float) -> bool:
    """|observed - target| <= |target| * tolerance_fraction."""
    return abs(observed - target) <= abs(target) * tolerance_fraction


def within_percentage_points(observed_pct: float, target_pct: float, points: float) -> bool:
    """Agreement in percentage *points*, not relative percent."""
    return abs(observed_pct - target_pct) <= points
