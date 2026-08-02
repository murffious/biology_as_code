"""
Nutrient nodes: the shipped instances validate, and the provenance vocabulary is
actually closed.

Before this, ``zinc.node.yaml`` and ``glucose.node.yaml`` both declared
``schema_version: nutrient-node/v1`` against a schema that did not exist, and
nothing in the package read them. Two carefully-built instances of an unwritten
contract cannot drift *detectably*, which is the worst of both worlds: they look
authoritative and nothing checks them.

The negative tests matter more than the positive ones here. A validator that only
ever sees valid input is indistinguishable from a validator that returns True.
"""

from __future__ import annotations

import copy

import pytest

from biology_as_code.nodes import (
    CERTIFICATION_ORDER,
    NutrientNode,
    claim_provenance_schema,
    list_nodes,
    load_node,
    node_schema,
    validate_node,
)
from biology_as_code.packets.validate import unsupported_keywords

pytest.importorskip("yaml", reason="nutrient nodes are YAML; PyYAML is in the dev extra")


def test_both_reference_nodes_ship():
    assert set(list_nodes()) >= {"zinc", "glucose"}


@pytest.mark.parametrize("nutrient_id", ["zinc", "glucose"])
def test_shipped_node_validates(nutrient_id):
    result = validate_node(load_node(nutrient_id))
    assert result.valid, "\n".join(result.errors)


def test_schema_stays_inside_the_validator_subset():
    """The repo's validator ignores keywords it does not implement.

    A schema that leans on an unimplemented keyword passes vacuously, so the
    schema must stay inside the subset entirely. Notably it uses no ``$ref``:
    ``validate_node`` lifts the claim subschema out of ``$defs`` and applies it
    by hand, which is why the vocabulary can live in one place without needing a
    reference resolver.
    """
    assert unsupported_keywords(node_schema()) == []


@pytest.mark.parametrize("nutrient_id", ["zinc", "glucose"])
def test_claim_vocabulary_is_closed(nutrient_id):
    node = load_node(nutrient_id)
    assert node.claims(), f"{nutrient_id}: expected provenance-bearing claims"
    for claim in node.claims():
        assert claim.certification in CERTIFICATION_ORDER, (
            f"{claim.path}: {claim.certification!r} is outside the gate lattice"
        )
        assert claim.tier >= 0


@pytest.mark.parametrize("nutrient_id", ["zinc", "glucose"])
def test_no_claim_is_bound_yet(nutrient_id):
    """Both nodes are built from textbooks, so nothing may claim Bound.

    This is the test that would fail if someone promoted a figure without reading
    the primary. It is expected to start passing for individual claims one day —
    when it does, the promotion should be a deliberate diff, not a silent one.
    """
    node = load_node(nutrient_id)
    assert node.at_least("bound") == ()
    assert node.at_least("candidate"), "every claim should sit somewhere on the lattice"


def test_zinc_records_its_unresolved_parents():
    """Kohlmeier names parents the extraction could not chase down.

    Fourteen of them. The node is only honest if that count survives in the
    document rather than being quietly dropped, because each one is a claim whose
    citation chain stops at a secondary source.
    """
    node = load_node("zinc")
    assert len(node.unresolved_parents) == 14
    assert node.promotion_blockers


def test_unresolved_parent_must_admit_it():
    """A parent_ref pointing nowhere is legal only alongside NOT_FOUND."""
    raw = copy.deepcopy(load_node("zinc").raw)
    prov = raw["stages"]["absorption"]["transporters"][0]["provenance"]
    assert prov["parent_ref"] == "wang2002"
    assert prov["existence_verdict"] == "NOT_FOUND"

    prov["existence_verdict"] = "REAL"
    result = validate_node(NutrientNode.from_dict(raw))
    assert not result.valid
    assert any("wang2002" in e for e in result.errors)


def test_source_ref_must_always_resolve():
    """Unlike parent_ref, the document actually read has no excuse for missing."""
    raw = copy.deepcopy(load_node("glucose").raw)
    raw["stages"]["absorption"]["fraction"]["provenance"]["source_ref"] = "nosuchbook1999"
    result = validate_node(NutrientNode.from_dict(raw))
    assert not result.valid
    assert any("nosuchbook1999" in e for e in result.errors)


def test_duplicate_claim_ids_are_rejected():
    """Two claims sharing an id silently collapse into one when indexed."""
    raw = copy.deepcopy(load_node("glucose").raw)
    transporters = raw["stages"]["absorption"]["transporters"]
    transporters[1]["provenance"]["claim_id"] = transporters[0]["provenance"]["claim_id"]
    result = validate_node(NutrientNode.from_dict(raw))
    assert not result.valid
    assert any("duplicate claim_id" in e for e in result.errors)


def test_unknown_certification_is_rejected():
    raw = copy.deepcopy(load_node("glucose").raw)
    raw["stages"]["absorption"]["fraction"]["provenance"]["certification"] = "verified"
    result = validate_node(NutrientNode.from_dict(raw))
    assert not result.valid


def test_document_provenance_is_not_validated_as_a_claim():
    """The node's own top-level `provenance` describes the extraction, not a claim.

    It has no claim_id and never will. Sweeping it with the claim vocabulary
    would report a permanent false error on every node.
    """
    node = load_node("zinc")
    assert "claim_id" not in node.raw["provenance"]
    assert all(claim.path != "provenance" for claim in node.claims())
    assert validate_node(node).valid


def test_claim_provenance_subschema_is_the_single_definition():
    """The vocabulary lives in the schema file, not duplicated in Python."""
    schema = claim_provenance_schema()
    assert list(schema["properties"]["certification"]["enum"]) == list(CERTIFICATION_ORDER)


def test_scoring_guard_is_present_and_says_why():
    """A node without a scoring guard is a number without a warning label."""
    for nutrient_id in ("zinc", "glucose"):
        guard = load_node(nutrient_id).scoring_guard
        assert guard.get("rationale"), f"{nutrient_id}: scoring_guard needs a rationale"
        assert guard.get("monotonic_safe") is False
