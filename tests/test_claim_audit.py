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
from biology_as_code.packets import FoodPacket, get_packet, iter_packets, validate_against
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


# A carotenoid source that declares the cargo but is silent on the fat vehicle.
# No packet in examples/foods/ is shaped like this — every filled fat-vehicle
# packet declares a lipid field, and stubs omit the cargo — so the L3 "silent
# gate" branch is only reachable from a hand-built packet. It is the exact case
# the auditor docstring calls load-bearing ("silent about dietary lipid is not a
# packet that declares zero"), so it gets a dedicated fixture.
SILENT_GATE_PACKET = FoodPacket.from_dict(
    {
        "id": "ex.synthetic.silent_gate",
        "identity": {"common_name": "carotenoid source, fat unstated"},
        "status": "filled",
        "cargo": [{"nutrient": "beta_carotene", "label_amount": "open"}],
        "partners": [],  # neither dietary_lipid_g nor lipid_phase_present declared
    }
)


def test_declared_cargo_but_silent_cofactor_is_unevaluable_at_the_gate():
    """Cargo present, fat vehicle unstated: the gate is UNKNOWN, not open or shut.

    This is a different code path from the stub case above. ``ex.banana`` never
    declares the cargo, so it fails closed at L2 (cargo absent); here the cargo is
    declared and the walk reaches L3, where silence about the required co-factor
    must yield UNEVALUABLE rather than a satisfied gate. Both are UNEVALUABLE, but
    conflating the two would let a regression in the L3 gate logic hide behind the
    L2 test.
    """
    result = audit_claim(SPINACH_CLAIM, SILENT_GATE_PACKET)

    assert result.verdict == "UNEVALUABLE"
    assert result.gate_check == "unevaluable"
    # Reached the gate (L3), not stopped at the cargo check (L2).
    assert result.l1_to_l5["L2"] == "beta_carotene present in matrix"
    assert result.l1_to_l5["closed_through"] == "L3"
    assert "gate state UNKNOWN" in result.l1_to_l5["L3"]
    assert any("declares none of" in reason for reason in result.unevaluable_because)
    # Gate state itself is unknown -> the constitution's UNEVALUABLE, not OPEN.
    assert result.constitution_state == "UNEVALUABLE"


def test_silent_gate_and_absent_cargo_are_distinct_unevaluable_paths():
    """Both fail closed, but through different ladder rungs — keep them separable."""
    silent_gate = audit_claim(SPINACH_CLAIM, SILENT_GATE_PACKET)
    absent_cargo = audit_claim(SPINACH_CLAIM, get_packet("ex.banana"))

    assert silent_gate.verdict == absent_cargo.verdict == "UNEVALUABLE"
    assert silent_gate.l1_to_l5["closed_through"] == "L3"
    assert absent_cargo.l1_to_l5["closed_through"] == "L2"


def test_silent_gate_audit_conforms_to_schema():
    """A verdict from the L3 gate branch still serialises to the audit schema."""
    payload = audit_claim(SPINACH_CLAIM, SILENT_GATE_PACKET).to_dict()
    assert validate_against(payload, claim_audit_schema()).valid


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


# --- Constitution vocabulary ---------------------------------------------------

CONSTITUTION_STATES = {"HOLDS", "UNEVALUABLE", "REFUSE", "OPEN", "REFUTED"}


def test_constitution_state_is_always_one_of_the_documented_values():
    for packet in iter_packets():
        for claim in (SPINACH_CLAIM, SOFT_IRON_CLAIM, IRON_BOUND_CLAIM, MATRIX_CLAIM):
            state = audit_claim(claim, packet).constitution_state
            assert state in CONSTITUTION_STATES, state


@pytest.mark.parametrize(
    ("claim", "packet_id", "verdict", "state"),
    [
        # Gate closed on a declared fact: determinate negative, not a missing field.
        (SPINACH_CLAIM, "ex.spinach_salad.zero_fat", "Busted", "REFUTED"),
        # Gate open, endpoint unreachable from one meal: magnitude/endpoint unlocked.
        (SPINACH_CLAIM, "ex.spinach_salad.with_oil", "UNEVALUABLE", "OPEN"),
        # Gate state unknown because the packet is silent.
        (SPINACH_CLAIM, "ex.banana", "UNEVALUABLE", "UNEVALUABLE"),
        # Soft verb: declined before reading the packet.
        (SOFT_IRON_CLAIM, "ex.lentils.with_ascorbate", "REFUSE", "REFUSE"),
        # Bound evaluable with declared fields.
        (IRON_BOUND_CLAIM, "ex.lentils.with_ascorbate", "Plausible", "HOLDS"),
    ],
)
def test_constitution_state_mapping(claim, packet_id, verdict, state):
    result = audit_claim(claim, get_packet(packet_id))
    assert result.verdict == verdict
    assert result.constitution_state == state


def test_open_and_unevaluable_are_distinguished_by_gate_resolution():
    """The constitution separates 'magnitude not locked' from 'field missing'."""
    gate_passed = audit_claim(SPINACH_CLAIM, get_packet("ex.spinach_salad.with_oil"))
    gate_unknown = audit_claim(SPINACH_CLAIM, get_packet("ex.banana"))

    assert gate_passed.verdict == gate_unknown.verdict == "UNEVALUABLE"
    assert gate_passed.constitution_state == "OPEN"
    assert gate_unknown.constitution_state == "UNEVALUABLE"


def test_refuted_is_not_collapsed_into_refuse():
    """'We evaluated and the answer is no' must not read as 'we declined'."""
    busted = audit_claim(SPINACH_CLAIM, get_packet("ex.spinach_salad.zero_fat"))
    refused = audit_claim(SOFT_IRON_CLAIM, get_packet("ex.banana"))
    assert busted.constitution_state != refused.constitution_state


def test_constitution_state_does_not_leak_into_the_schema_payload():
    """Schema conformance is unaffected: constitution_state is a view, not a field."""
    result = audit_claim(SPINACH_CLAIM, get_packet("ex.spinach_salad.zero_fat"))
    payload = result.to_dict()
    assert "constitution_state" not in payload
    assert validate_against(payload, claim_audit_schema()).valid
