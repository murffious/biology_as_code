"""
Energy: the scoring guard holds, and the corrected constants stay corrected.

The guard is the point of the module. Energy has no reference intake and cannot
have one, so a score may judge macronutrient *distribution* and substrate storage
cost but must never judge an absolute kilocalorie target. That rule is easy to
erode by accident, so it is pinned here.

The constants are pinned for a different reason: two of them are corrections to a
cited textbook, and a correction that nothing tests is a correction waiting to be
reverted by someone reading the printed page.
"""

from __future__ import annotations

import pytest

from biology_as_code.simulation.energy_accounting import (
    AMDR,
    ATP_PER_GLUCOSE_AS_PRINTED,
    ATP_PER_GLUCOSE_CORRECTED,
    GLUCOSE_KCAL_PER_MOL,
    GLUCOSE_KCAL_PER_MOL_AS_PRINTED,
    SCORING_GUARD,
    EnergyCascade,
    amdr_verdict,
    efficiency_de_novo_lipogenesis,
    efficiency_preformed_fat_storage,
    is_postabsorptive,
    storage_cost_asymmetry,
)
from biology_as_code.simulation.respiratory_quotient import (
    RespiratoryQuotient,
    substrate_mix_from_rq,
)


def test_energy_has_no_reference_intake_and_cannot():
    assert SCORING_GUARD["has_rda"] is False
    assert SCORING_GUARD["can_have_rda"] is False
    assert SCORING_GUARD["response_shape"] == "balance"
    assert SCORING_GUARD["monotonic_safe"] is False


def test_a_score_may_not_act_on_an_absolute_kcal_target():
    """The one rule this module exists to enforce."""
    assert "absolute_kcal_target" in SCORING_GUARD["do_not_act_on"]
    assert "absolute_kcal_target" not in SCORING_GUARD["act_on"]
    assert set(SCORING_GUARD["act_on"]) == {
        "macronutrient_distribution",
        "substrate_storage_cost",
    }


def test_amdr_judges_distribution_not_amount():
    """Two diets with wildly different energy get the same distribution verdict."""
    fractions = {"fat": 0.30, "carbohydrate": 0.50, "protein": 0.20}
    verdict = amdr_verdict("adult", fractions)
    assert verdict == {"fat": "within", "carbohydrate": "within", "protein": "within"}

    assert amdr_verdict("adult", {"fat": 0.45})["fat"] == "above"
    assert amdr_verdict("adult", {"carbohydrate": 0.20})["carbohydrate"] == "below"


def test_amdr_bands_differ_by_life_stage():
    """Toddlers need a higher fat floor; a single adult band would misjudge them."""
    assert AMDR["child_1_3"]["fat"] == (30, 40)
    assert AMDR["adult"]["fat"] == (20, 35)
    assert amdr_verdict("child_1_3", {"fat": 0.35})["fat"] == "within"
    assert amdr_verdict("adult", {"fat": 0.35})["fat"] == "within"
    assert amdr_verdict("child_1_3", {"fat": 0.22})["fat"] == "below"


def test_unknown_life_stage_raises_rather_than_defaulting_to_adult():
    with pytest.raises(ValueError):
        amdr_verdict("neonate", {"fat": 0.3})


def test_glucose_constant_is_the_corrected_one():
    """ERR-GLU-01. The printed 294.8 kcal/mol is low by a factor of 2.27."""
    assert GLUCOSE_KCAL_PER_MOL == 669.87
    assert GLUCOSE_KCAL_PER_MOL_AS_PRINTED == 294.8
    assert GLUCOSE_KCAL_PER_MOL / GLUCOSE_KCAL_PER_MOL_AS_PRINTED == pytest.approx(2.27, abs=0.01)


def test_berdanier_framing_goes_negative_with_the_correct_constant():
    """This is what exposed the error: her expression only works because it is wrong.

    Berdanier writes efficiency as (tripalmitin - glucose cost) / tripalmitin. With
    the correct heat of combustion the glucose cost exceeds the tripalmitin value
    outright, so the expression returns a negative "efficiency".
    """
    tripalmitin = 7597.0
    glucose_cost_correct = 12.5 * GLUCOSE_KCAL_PER_MOL
    glucose_cost_as_printed = 12.5 * GLUCOSE_KCAL_PER_MOL_AS_PRINTED

    assert (tripalmitin - glucose_cost_as_printed) / tripalmitin > 0
    assert (tripalmitin - glucose_cost_correct) / tripalmitin < 0


def test_de_novo_lipogenesis_agrees_with_the_cross_read():
    """~80.5%, against McGuire & Beerman's reported 20-25% cost (75-80% efficient).

    Just above their band rather than inside it, which is the honest result: the
    accounting here covers carbon and ATP and not the whole-body overhead.
    """
    efficiency = efficiency_de_novo_lipogenesis(ATP_PER_GLUCOSE_CORRECTED)
    assert efficiency == pytest.approx(0.805, abs=0.005)


def test_correcting_the_atp_yield_widens_the_asymmetry():
    """Fewer ATP per glucose makes de novo lipogenesis look worse, not better.

    So the qualitative conclusion survives the errata — which is why the storage
    asymmetry is safe to act on even though its inputs needed correcting.
    """
    printed = efficiency_de_novo_lipogenesis(ATP_PER_GLUCOSE_AS_PRINTED)
    corrected = efficiency_de_novo_lipogenesis(ATP_PER_GLUCOSE_CORRECTED)
    assert corrected < printed
    assert storage_cost_asymmetry()["ratio"] > 1.0


def test_preformed_fat_efficiency_is_the_narrow_biochemical_scope():
    """~99%, not McGuire's ~95%. Different scope, and the docstring must not blur it.

    The extraction this came from claimed the corrected model agreed with McGuire
    on both routes. It agrees on one.
    """
    efficiency = efficiency_preformed_fat_storage()
    assert efficiency == pytest.approx(0.990, abs=0.002)
    assert efficiency > 0.95, "the biochemical-only figure is above the whole-body one"
    assert "whole-body" in efficiency_preformed_fat_storage.__doc__


def test_energy_cascade_steps_down():
    cascade = EnergyCascade(gross_energy_kcal=2400)
    values = cascade.as_dict()
    assert values["GE"] > values["DE"] > values["NE"]
    assert values["DE"] == pytest.approx(2160.0)


def test_energy_balance_is_the_only_free_term():
    cascade = EnergyCascade(gross_energy_kcal=2400)
    stored = cascade.energy_balance_kcal(basal_kcal=1500, activity_kcal=200)
    withdrawn = cascade.energy_balance_kcal(basal_kcal=1500, activity_kcal=900)
    assert stored > 0
    assert withdrawn < 0


def test_postabsorptive_clock_is_species_specific():
    """A 12-hour fast is postabsorptive in a human and nowhere near it in a pig."""
    assert is_postabsorptive(14, "human") is True
    assert is_postabsorptive(14, "rat") is False
    assert is_postabsorptive(14, "pig") is False
    assert is_postabsorptive(13, "human") is None  # inside the transition window


def test_unknown_species_does_not_fall_back_to_human():
    assert is_postabsorptive(14, "axolotl") is None


# --- respiratory quotient -------------------------------------------------


def test_rq_interpretation_does_not_need_exact_float_equality():
    """0.70 and 1.00 are effectively unreachable by division; bands are required."""
    assert "fat" in RespiratoryQuotient(70.0, 100.0).interpretation()
    assert "carbohydrate" in RespiratoryQuotient(100.0, 100.0).interpretation()
    # 0.699..., not 0.70 exactly
    assert "fat" in RespiratoryQuotient(699.0, 1000.0).interpretation()


def test_fat_predominant_rq_is_not_reported_as_ketogenic():
    """0.75 is ordinary fat-predominant oxidation and must read that way."""
    reading = RespiratoryQuotient(75.0, 100.0).interpretation()
    assert "fat-predominant" in reading
    assert "ketogenesis" not in reading


def test_interpretation_without_calculate_does_not_read_the_zero_default():
    rq = RespiratoryQuotient(co2_produced_ml=85.0, o2_consumed_ml=100.0)
    assert rq.rq == 0.0  # not yet computed
    assert "no measurement" not in rq.interpretation()


def test_substrate_mix_interpolates_between_the_endpoints():
    assert substrate_mix_from_rq(0.70) == {"carbohydrate_fraction": 0.0, "fat_fraction": 1.0}
    assert substrate_mix_from_rq(1.00) == {"carbohydrate_fraction": 1.0, "fat_fraction": 0.0}
    assert substrate_mix_from_rq(0.85) == {"carbohydrate_fraction": 0.5, "fat_fraction": 0.5}


def test_substrate_mix_refuses_to_extrapolate():
    """Above 1.00 means lipogenesis, below 0.70 means something else entirely."""
    assert substrate_mix_from_rq(1.05) is None
    assert substrate_mix_from_rq(0.65) is None
