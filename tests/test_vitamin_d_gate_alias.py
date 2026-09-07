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


def _packet(lipid_g: int, nutrient: str = "cholecalciferol") -> FoodPacket:
    return FoodPacket.from_dict(
        {
            "id": f"ex.synthetic.vitd.{nutrient}.lipid_{lipid_g}",
            "identity": {"common_name": f"vitamin D teaching packet lipid={lipid_g}"},
            "status": "filled",
            "cargo": [{"nutrient": nutrient, "label_amount": "open"}],
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
    """An open vehicle gate is a gate, not a verdict.

    Declaring lipid lets the micelle path open; it closes no evidence chain, so
    the disease claim stays OPEN/UNEVALUABLE rather than earning a level.
    """
    result = audit_claim(RICKETS, _packet(1))
    assert result.gate_check == "pass"
    assert result.verdict == "UNEVALUABLE"
    assert result.l1_to_l5["closed_through"] == "none"
    assert result.constitution_state == "OPEN"


def test_alias_audits_identically_to_vitamin_d():
    """Parity is the real contract: an alias is the same LAW-020 cargo.

    Whatever the auditor decides for ``vitamin_d`` it must decide for the
    chemical names — same gate, same verdict, same constitution state. Pinning
    parity (rather than a hardcoded verdict) keeps this test honest if the
    auditor's own verdict vocabulary later changes.
    """
    for verb_class, extra in (
        ("disease_claim", {"surface_verb": "prevents"}),
        ("bound_increase", {}),
    ):
        canonical = Claim(
            id=f"claim.canonical.{verb_class}",
            surface_claim="vitamin D claim under test",
            verb_class=verb_class,
            nutrient="vitamin_d",
            **extra,
        )
        for alias in VITD_ALIASES:
            aliased = Claim(
                id=f"claim.{alias}.{verb_class}",
                surface_claim="vitamin D claim under test",
                verb_class=verb_class,
                nutrient=alias,
                **extra,
            )
            for lipid_g in (0, 1):
                base = audit_claim(canonical, _packet(lipid_g, "vitamin_d"))
                aliased_result = audit_claim(aliased, _packet(lipid_g, alias))
                assert aliased_result.gate_check == base.gate_check, alias
                assert aliased_result.verdict == base.verdict, alias
                assert aliased_result.constitution_state == base.constitution_state, alias
                assert (
                    aliased_result.l1_to_l5["closed_through"]
                    == base.l1_to_l5["closed_through"]
                ), alias


def test_still_no_percent_absorbed():
    """Alias work must not grow a magnitude table."""
    result = audit_claim(MECHANISM, _packet(1))
    payload = result.to_dict()
    blob = str(payload).lower()
    assert "%" not in blob
    assert "nmol" not in blob
