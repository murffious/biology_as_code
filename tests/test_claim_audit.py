"""
Claim auditor: golden reproduction, the Gate ≠ Bound distinction, fail-closed
behaviour, and a structural invariant that keeps the rule table honest.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from biology_as_code import Claim, audit_claim, law_card, list_laws
from biology_as_code.audit import (
    BOUND_RULES,
    GATE_RULES,
    all_law_refs,
    audit_packet_coverage,
    known_nutrients,
)
from biology_as_code.packets import get_packet, iter_packets, validate_against
from biology_as_code.packets.loader import schemas_dir


def claim_audit_schema() -> dict:
    return json.loads(
        (schemas_dir() / "claim_audit.schema.json").read_text(encoding="utf-8")
    )


# --- The rule table must not drift from the LAW-SPEC register -----------------


def test_every_cited_law_exists():
    """No fabricated law references. 'Empty beats fake' applies to citations too."""
    known = set(list_laws())
    unknown = [ref for ref in all_law_refs() if ref not in known]
    assert unknown == [], f"rule table cites nonexistent laws: {unknown}"


def test_gate_rules_only_cite_laws_that_declare_a_gate():
    """A categorical rule may only rest on a law whose card has gate.present."""
    offenders = []
    for rule in GATE_RULES:
        for ref in rule.law_refs:
            if not law_card(ref)["gate"]["present"]:
                offenders.append((rule.nutrient, ref))
    assert offenders == [], f"GateRule cites a non-gate law: {offenders}"


def test_bound_rules_only_cite_laws_that_declare_no_gate():
    """A magnitude rule may not borrow authority from a categorical law."""
    offenders = []
    for rule in BOUND_RULES:
        for ref in rule.law_refs:
            if law_card(ref)["gate"]["present"]:
                offenders.append((rule.nutrient, ref))
    assert offenders == [], f"BoundRule cites a gate law: {offenders}"


def test_every_rule_carries_provenance():
    for rule in (*GATE_RULES, *BOUND_RULES):
        assert rule.law_refs, f"rule without law_refs: {rule}"


def test_known_nutrients_is_non_empty():
    assert "nonhaem_iron" in known_nutrients()
    assert "beta_carotene" in known_nutrients()


# --- Golden fixture reproduction ----------------------------------------------

SPINACH_CLAIM = Claim(
    id="claim.spinach_vitA_no_fat",
    surface_claim=(
        "Eat fat-free spinach salad for vitamin A / carotenoids to prevent deficiency disease"
    ),
    verb_class="disease_claim",
    nutrient="beta_carotene",
    surface_verb="prevents",
    atomized=(
        "spinach delivers carotenoids without fat",
        "panel vitamin A implies absorption",
        "absorption implies disease prevention",
    ),
)

SOFT_IRON_CLAIM = Claim(
    id="claim.iron_supports_energy",
    surface_claim="Iron supports energy and boosts vitality",
    verb_class="soft",
    nutrient="nonhaem_iron",
    surface_verb="supports / boosts",
    atomized=("supports energy", "boosts vitality"),
)


def _golden(name: str) -> dict:
    path = Path(schemas_dir()).parent / "examples" / "claims" / name
    return json.loads(path.read_text(encoding="utf-8"))


def test_reproduces_hand_written_spinach_audit():
    """The auditor derives what was previously hand-written by a human."""
    expected = _golden("claim_spinach_prevents_disease_no_fat.json")
    result = audit_claim(SPINACH_CLAIM, get_packet("ex.spinach_salad.zero_fat")).to_dict()

    assert result["verdict"] == expected["verdict"] == "Busted"
    assert result["gate_check"] == expected["gate_check"] == "fail"
    assert result["kingdom"] == expected["kingdom"] == "lumen"
    assert result["gate_note"] == expected["gate_note"]
    assert result["l1_to_l5"]["closed_through"] == expected["l1_to_l5"]["closed_through"] == "L3"
    assert result["rosetta"]["relation_enum"] == expected["rosetta"]["relation_enum"]
    assert result["atomized"] == expected["atomized"]


def test_reproduces_hand_written_soft_claim_refusal():
    """Soft verbs are refused before any packet is read."""
    expected = _golden("claim_iron_supports_energy_soft.json")
    result = audit_claim(SOFT_IRON_CLAIM, get_packet("ex.lentils.with_ascorbate")).to_dict()

    assert result["verdict"] == expected["verdict"] == "REFUSE"
    assert result["gate_check"] == expected["gate_check"] == "unevaluable"
    assert result["kingdom"] == expected["kingdom"] == "mixed"
    assert result["rosetta"]["relation_enum"] == expected["rosetta"]["relation_enum"]
    # Divergence on purpose: the hand-written fixture recorded the descriptive
    # string "soft / marketing"; verb_class is a single enum value from
    # relation_enums.subset.json, so the derived audit records "soft".
    assert result["rosetta"]["class"] == "soft"
    assert "l1_to_l5" not in result, "a refused claim never walks the ladder"


def test_audits_conform_to_claim_audit_schema():
    for claim, packet_id in (
        (SPINACH_CLAIM, "ex.spinach_salad.zero_fat"),
        (SPINACH_CLAIM, "ex.spinach_salad.with_oil"),
        (SOFT_IRON_CLAIM, "ex.lentils.with_ascorbate"),
    ):
        result = audit_claim(claim, get_packet(packet_id)).to_dict()
        outcome = validate_against(result, claim_audit_schema())
        assert outcome.valid, (packet_id, outcome.errors)


# --- Gate ≠ Bound -------------------------------------------------------------


def test_fat_vehicle_is_a_gate_that_closes():
    zero = audit_claim(SPINACH_CLAIM, get_packet("ex.spinach_salad.zero_fat"))
    assert zero.gate_check == "fail"
    assert zero.verdict == "Busted"


def test_adding_the_lipid_phase_opens_the_gate_but_not_the_disease_claim():
    """Fixing the mechanism does not license the endpoint."""
    with_oil = audit_claim(SPINACH_CLAIM, get_packet("ex.spinach_salad.with_oil"))
    assert with_oil.gate_check == "pass"
    assert with_oil.verdict == "UNEVALUABLE"
    assert with_oil.l1_to_l5["closed_through"] == "L5"


IRON_BOUND_CLAIM = Claim(
    id="claim.iron_bound",
    surface_claim="This meal changes absorbable non-haem iron",
    verb_class="bound_increase",
    nutrient="nonhaem_iron",
)


@pytest.mark.parametrize(
    ("packet_id", "direction", "law"),
    [
        ("ex.lentils.with_ascorbate", "EXPANDS_BOUND", "LAW-004"),
        ("ex.lentils.with_tea", "NARROWS_BOUND", "LAW-006"),
    ],
)
def test_iron_is_a_bound_story_with_the_gate_left_open(packet_id, direction, law):
    """Same label milligrams, opposite bound, gate never closes."""
    result = audit_claim(IRON_BOUND_CLAIM, get_packet(packet_id))
    assert result.gate_check == "pass"
    assert result.verdict == "Plausible"
    assert [f.direction for f in result.bound_findings] == [direction]
    assert law in result.law_refs


MATRIX_CLAIM = Claim(
    id="claim.matrix",
    surface_claim="Food form changes lipid accessibility",
    verb_class="bound_increase",
    nutrient="lipid",
)


@pytest.mark.parametrize(
    ("packet_id", "direction"),
    [("ex.almond.whole", "NARROWS_BOUND"), ("ex.almond.flour", "EXPANDS_BOUND")],
)
def test_matrix_integrity_flips_the_bound_direction(packet_id, direction):
    result = audit_claim(MATRIX_CLAIM, get_packet(packet_id))
    assert [f.direction for f in result.bound_findings] == [direction]
    assert "LAW-024" in result.law_refs


# --- Fail-closed --------------------------------------------------------------


def test_stub_packets_are_unevaluable_not_passing():
    """Silence about a co-factor must never read as a satisfied gate."""
    result = audit_claim(SPINACH_CLAIM, get_packet("ex.banana"))
    assert result.verdict == "UNEVALUABLE"
    assert result.unevaluable_because


def test_unknown_nutrient_is_unevaluable():
    claim = Claim(
        id="claim.unknown",
        surface_claim="Mystery nutrient does something",
        verb_class="bound_increase",
        nutrient="unobtainium",
    )
    assert audit_claim(claim, get_packet("ex.banana")).verdict == "UNEVALUABLE"


def test_missing_packet_is_unevaluable_not_an_exception():
    assert audit_claim(IRON_BOUND_CLAIM, None).verdict == "UNEVALUABLE"


def test_claim_without_nutrient_is_refused():
    claim = Claim(id="claim.none", surface_claim="Food is healthy", verb_class="gate")
    assert audit_claim(claim, get_packet("ex.banana")).verdict == "REFUSE"


def test_confirmed_is_never_emitted_by_a_mechanism_walk():
    """Confirmation is an evidence judgement, not a mechanism result."""
    verdicts = set()
    for packet in iter_packets():
        for claim in (SPINACH_CLAIM, SOFT_IRON_CLAIM, IRON_BOUND_CLAIM, MATRIX_CLAIM):
            verdicts.add(audit_claim(claim, packet).verdict)
    assert "Confirmed" not in verdicts
    assert verdicts <= {"Busted", "Plausible", "UNEVALUABLE", "REFUSE"}


def test_coverage_is_honestly_mostly_unevaluable():
    """40 of 46 packets are stubs; the auditor must say so rather than guess."""
    packets = list(iter_packets())
    coverage = audit_packet_coverage(packets, "beta_carotene")
    assert coverage["UNEVALUABLE"] > coverage.get("Plausible", 0)
    assert sum(coverage.values()) == len(packets)


def test_audit_never_raises_on_any_packet():
    for packet in iter_packets():
        audit_claim(SPINACH_CLAIM, packet)
        audit_claim(IRON_BOUND_CLAIM, packet)
