"""Whole vs skim milk: same vitamin_d cargo, lipid phase flips the LAW-020 gate."""

from __future__ import annotations

from biology_as_code import Claim, audit_claim
from biology_as_code.packets import get_packet

DISEASE = Claim(
    id="claim.milk_vitd_prevents_rickets",
    surface_claim="Drink this milk to prevent rickets",
    verb_class="disease_claim",
    nutrient="vitamin_d",
    surface_verb="prevents",
)

MECHANISM = Claim(
    id="claim.milk_vitd_micelle",
    surface_claim="Whole-milk fat makes vitamin D absorbable via micelles",
    verb_class="bound_increase",
    nutrient="vitamin_d",
)


def test_packets_are_filled_and_named():
    whole = get_packet("ex.milk.cow")
    skim = get_packet("ex.milk.cow.skim")
    multi = get_packet("ex.multivitamin.tablet")
    assert whole.status == "filled"
    assert skim.status == "filled"
    assert multi.status == "filled"
    assert "vitamin_d" in whole.cargo_nutrients()
    assert "vitamin_d" in skim.cargo_nutrients()


def test_skim_closes_the_fat_vehicle_gate():
    result = audit_claim(DISEASE, get_packet("ex.milk.cow.skim"))
    assert result.gate_check == "fail"
    assert result.verdict == "Busted"
    assert result.l1_to_l5["closed_through"] == "L3"


def test_whole_opens_the_gate_but_not_rickets():
    result = audit_claim(DISEASE, get_packet("ex.milk.cow"))
    assert result.gate_check == "pass"
    assert result.verdict == "UNEVALUABLE"
    assert result.l1_to_l5["closed_through"] == "L5"


def test_whole_mechanism_claim_holds():
    result = audit_claim(MECHANISM, get_packet("ex.milk.cow"))
    assert result.gate_check == "pass"
    assert result.verdict == "Plausible"


def test_dry_multivitamin_closes_fat_soluble_not_ascorbate_story():
    vitd = Claim(
        id="claim.multi_d",
        surface_claim="This tablet prevents rickets",
        verb_class="disease_claim",
        nutrient="vitamin_d",
        surface_verb="prevents",
    )
    result = audit_claim(vitd, get_packet("ex.multivitamin.tablet"))
    assert result.gate_check == "fail"
    assert result.verdict == "Busted"
