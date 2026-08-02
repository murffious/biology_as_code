"""
The nutrient-requirement edge: pathways that answer a dietary question.

Every other field on ``ReactionEdge`` tracks carbon or energy. ``requires_nutrient``
tracks which micronutrient the step cannot run without, which is what turns a
biochemical graph into something a nutrition model can query. These two pathways
exist to exercise it.

The compatibility test matters as much as the feature tests: sixteen legacy
pathway modules declare their own edge dataclasses with no such field, and the
accessor has to keep reading them without complaint.
"""

from __future__ import annotations

from biology_as_code.pathways._types import ReactionEdge, edge_label, edge_nutrients
from biology_as_code.pathways.micronutrient_cofactor_pathways import (
    get_micronutrient_cofactor_registry,
)
from biology_as_code.pathways.registry import get_pathway, list_pathways


def test_both_pathways_are_publicly_reachable():
    names = {n.lower() for n in list_pathways()}
    assert {"tryptophan_niacin", "carnitine_synthesis"} <= names
    for name in ("tryptophan_niacin", "carnitine_synthesis"):
        pathway = get_pathway(name)
        assert pathway is not None
        assert pathway.nodes and pathway.edges


def test_no_orphan_nodes():
    """A declared node no edge touches is prose pretending to be a graph."""
    for pathway in get_micronutrient_cofactor_registry().list_all():
        assert pathway.orphan_nodes() == [], f"{pathway.name} has orphan nodes"


def test_both_pathways_cite_their_source():
    for pathway in get_micronutrient_cofactor_registry().list_all():
        assert pathway.references
        assert any("Berdanier" in ref for ref in pathway.references)


def test_carnitine_needs_five_nutrient_families_on_one_chain():
    """The load-bearing claim: a shortfall anywhere on the chain stops the whole thing.

    Five families across seven steps, and the chain is linear — there is no
    alternate route around a missing cofactor. This is the case that a per-nutrient
    score cannot represent, because the pathway's output is set by the *minimum*
    across five axes rather than by any of them independently.
    """
    pathway = get_pathway("carnitine_synthesis")
    deps = pathway.nutrient_dependencies()

    families = {n.split(" (")[0] for n in deps}
    assert families == {"methionine", "folate", "vitamin B12", "iron", "vitamin C",
                        "vitamin B6", "niacin"}

    # Every step from lysine to carnitine requires something.
    backbone = [e for e in pathway.edges if e.process != "co-product release"
                and e.from_node != "SAM"]
    assert all(edge_nutrients(e) for e in backbone), (
        "a backbone step with no declared cofactor is either wrong or unfinished"
    )


def test_b6_is_the_tryptophan_niacin_bottleneck():
    """Niacin from tryptophan runs through PLP-dependent steps and cannot avoid them."""
    pathway = get_pathway("tryptophan_niacin")
    deps = pathway.nutrient_dependencies()
    assert "vitamin B6 (PLP)" in deps
    assert len(deps["vitamin B6 (PLP)"]) == 4

    kynureninase = [e for e in pathway.edges if e.enzyme == "kynureninase"]
    assert len(kynureninase) == 2
    assert all("vitamin B6 (PLP)" in edge_nutrients(e) for e in kynureninase)


def test_b6_shortfall_reaches_both_pathways():
    """One deficiency, two unrelated end-products. That is the whole argument."""
    index = get_micronutrient_cofactor_registry().nutrient_index()
    b6_steps = index["vitamin B6 (PLP)"]
    touched = {step.split("::")[0] for step in b6_steps}
    assert touched == {"tryptophan_niacin", "carnitine_synthesis"}


def test_requires_nutrient_reaches_the_rendered_label():
    """If it does not render, the exported mermaid silently drops the dependency."""
    edge = ReactionEdge(
        from_node="A", to_node="B", enzyme="kynureninase",
        requires_nutrient=["vitamin B6 (PLP)"],
    )
    label = edge_label(edge)
    assert "kynureninase" in label
    assert "vitamin B6 (PLP)" in label


def test_edges_without_the_field_are_unaffected():
    """Legacy per-module edge classes have no requires_nutrient. They must still read."""

    class LegacyEdge:
        from_node = "A"
        to_node = "B"
        enzyme = "hexokinase"
        atp_cost = -1

    legacy = LegacyEdge()
    assert edge_nutrients(legacy) == []
    assert "⟨" not in edge_label(legacy)
    assert "hexokinase" in edge_label(legacy)


def test_default_requires_nutrient_is_not_shared_between_edges():
    """A mutable default on a dataclass would alias every edge to one list."""
    first = ReactionEdge(from_node="A", to_node="B")
    second = ReactionEdge(from_node="C", to_node="D")
    first.requires_nutrient.append("iron")
    assert second.requires_nutrient == []


def test_niacin_equivalent_ratio_is_not_attributed_to_the_map():
    """The 60:1 convention is a DRI figure, not something printed on Map 6.

    Anchoring it to the textbook page the topology came from would be a citation
    that does not support the claim.
    """
    pathway = get_pathway("tryptophan_niacin")
    dri_refs = [r for r in pathway.references if "Dietary Reference Intakes" in r]
    assert len(dri_refs) == 1
    assert "UNVERIFIED" in dri_refs[0], (
        "the DRI accession is carried but unconfirmed; it must say so until resolved"
    )
