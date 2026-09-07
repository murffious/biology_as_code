"""Cholecalciferol is vitamin D cargo under LAW-020, not a new mechanism."""

from __future__ import annotations

from biology_as_code import Claim, audit_claim
from biology_as_code.audit import gates_for, known_nutrients
from biology_as_code.packets import FoodPacket

VITD_ALIASES = ("vitamin_d", "cholecalciferol", "ergocalciferol", "calciferol")

RICKETS = Claim(
    id="claim.vitd_prevents_rickets",
    surface_claim="Take this vitamin D to prevent rickets",
    verb_class="disease_claim",
    nutrient="cholecalciferol",
    surface_verb="prevents",
)

MECHANISM = Claim(
    id="claim.vitd_needs_lipid",
    surface_claim="An oil vehicle makes this vitamin D absorbable via micelles",
    verb_class="bound_increase",
    nutrient="cholecalciferol",
)


def _packet(lipid_g: int) -> FoodPacket:
    return FoodPacket.from_dict(
        {
            "id": f"ex.synthetic.vitd.lipid_{lipid_g}",
            "identity": {"common_name": f"vitamin D teaching packet lipid={lipid_g}"},
            "status": "filled",
            "cargo": [{"nutrient": "cholecalciferol", "label_amount": "open"}],
            "partners": [
                {"field": "dietary_lipid_g", "value": lipid_g, "concurrency": "same_meal"}
            ],
        }
    )


def test_aliases_share_the_fat_vehicle_gate():
    vitamin_d = gates_for("vitamin_d")
    assert vitamin_d, "vitamin_d must stay on the fat-vehicle register"
    for alias in VITD_ALIASES:
        rules = gates_for(alias)
        assert rules, alias
        assert rules[0].requires == vitamin_d[0].requires
        assert rules[0].law_refs == ("LAW-020", "LAW-045")
        assert alias in known_nutrients()


def test_zero_lipid_closes_the_gate_for_cholecalciferol():
    result = audit_claim(RICKETS, _packet(0))
    assert result.gate_check == "fail"
    assert result.verdict == "Busted"
    assert result.l1_to_l5["closed_through"] == "L3"
    assert result.constitution_state == "REFUTED"


def test_oil_opens_the_gate_but_not_a_rickets_claim():
    result = audit_claim(RICKETS, _packet(1))
    assert result.gate_check == "pass"
    assert result.verdict == "UNEVALUABLE"
    assert result.l1_to_l5["closed_through"] == "L5"
    assert result.constitution_state == "OPEN"


def test_mechanism_claim_is_plausible_when_vehicle_declared():
    result = audit_claim(MECHANISM, _packet(1))
    assert result.gate_check == "pass"
    assert result.verdict == "Plausible"
    assert result.constitution_state == "HOLDS"


def test_still_no_percent_absorbed():
    """Alias work must not grow a magnitude table."""
    result = audit_claim(MECHANISM, _packet(1))
    payload = result.to_dict()
    blob = str(payload).lower()
    assert "%" not in blob
    assert "nmol" not in blob
