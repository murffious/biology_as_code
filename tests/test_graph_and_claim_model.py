"""
Tests for the property graph and the claim model.

The tests that matter here are the refusal tests. Anyone can check that a
classifier returns a label; the question for this system is whether it declines
to return one when it should, and whether the store refuses a write that would
break the constitution.
"""

from __future__ import annotations

import pytest

from biology_as_code.claim_model import Court, EvidenceGradeModel, parse
from biology_as_code.graph import GraphError, GraphStore, build
from biology_as_code.graph.export import to_cypher, to_graphml, to_turtle


@pytest.fixture(scope="module")
def graph():
    return build()


@pytest.fixture(scope="module")
def court(graph):
    return Court(graph, EvidenceGradeModel.train_from_graph(graph, seed=0))


# ------------------------------------------------------------------ store

def test_register_loads_completely(graph):
    laws = list(graph.nodes("Law"))
    assert len(laws) == 47
    assert {n.id for n in graph.nodes("FunctionalSystem")}  # seats exist
    assert all(law.props.get("statement") is None for law in laws[:1])  # name holds it


def test_relation_enum_is_closed():
    g = GraphStore.open(":memory:")
    g.add_node("a", "Law", "A")
    g.add_node("b", "Law", "B")
    with pytest.raises(GraphError):
        g.add_edge("a", "CAUSES", "b")          # not in the ENUM


def test_node_label_is_closed():
    g = GraphStore.open(":memory:")
    with pytest.raises(GraphError):
        g.add_node("x", "Vibe", "not a label")


def test_magnitude_without_evidence_is_refused():
    """The core fail-closed rule, enforced by the database not the caller."""
    g = GraphStore.open(":memory:")
    g.add_node("a", "Law", "A")
    g.add_node("b", "Bound", "12 mg/day")
    with pytest.raises(GraphError):
        g.add_edge("a", "EXPANDS_BOUND", "b", asserts_magnitude=True)


def test_magnitude_with_evidence_is_accepted():
    g = GraphStore.open(":memory:")
    g.add_node("a", "Law", "A")
    g.add_node("b", "Bound", "12 mg/day")
    g.add_node("c", "Contribution", "PMID 123")
    g.add_edge("a", "EXPANDS_BOUND", "b", asserts_magnitude=True, evidence="c", strength=4)
    assert len(list(g.edges("EXPANDS_BOUND"))) == 1


def test_gate_may_not_carry_a_magnitude():
    """gate != bound, enforced structurally rather than by convention."""
    g = GraphStore.open(":memory:")
    with pytest.raises(GraphError):
        g.add_node("gate:x", "Gate", "fat co-presence", magnitude=12.0)


def test_upsert_does_not_destroy_edges():
    """Regression: INSERT OR REPLACE cascaded and silently deleted edges."""
    g = GraphStore.open(":memory:")
    g.add_node("f", "Food", "Apple")
    g.add_node("c", "Compound", "pectin")
    g.add_edge("f", "CONTAINS", "c")
    g.add_node("c", "Compound", "pectin", note="re-added")   # upsert
    assert len(g.neighbors("f", rel="CONTAINS")) == 1


def test_integrity_report_counts_unsourced_bounds(graph):
    report = graph.integrity_report()
    assert report["laws"] == 47
    # the register is largely unsourced; the report must say so rather than hide it
    assert report["laws_with_unsourced_bound"] > 0
    assert report["laws_without_categorical_gate"] > 0


# ----------------------------------------------------------------- rosetta

@pytest.mark.parametrize(
    "text,expected_class",
    [
        ("Iron supports energy", "soft"),
        ("This superfood detoxifies the liver", "marketing"),
        ("Vitamin C increases iron absorption", "bound_increase"),
        ("Phytate blocks zinc absorption", "gate"),
        ("Oats prevent heart disease", "disease_claim"),
        ("Fibre is associated with regularity", "hedge"),
    ],
)
def test_rosetta_types_surface_verbs(text, expected_class):
    assert parse(text).verb_class == expected_class


def test_hedging_is_a_modifier_not_a_class():
    """"may increase" is still a bound claim, asserted tentatively."""
    p = parse("Fibre may improve regularity")
    assert p.verb_class == "bound_increase"
    assert p.hedged is True


def test_rosetta_returns_the_token_it_matched():
    """Every decision must be inspectable, not just correct."""
    p = parse("Vitamin C increases iron absorption")
    assert p.surface_verb == "increases"
    assert p.relation == "EXPANDS_BOUND"


def test_soft_language_never_types_to_a_mechanism():
    assert parse("supports immunity").relation == "MALFORMED_MECHANISM"
    assert parse("supports immunity").typed is False


def test_alias_slash_is_not_a_claim_boundary():
    assert len(parse("vitamin A / carotenoids increase absorption").atomized) == 1


# ------------------------------------------------------------------- court

def test_gold_fixtures_reproduce_hand_adjudication(graph, court):
    """The two hand-ruled fixtures are the only ground truth we have."""
    gold = [n for n in graph.nodes("Claim") if n.props.get("gold")]
    assert gold, "gold fixtures missing from graph"
    for node in gold:
        ruling = court.adjudicate(node.name)
        assert ruling.verdict == node.props["verdict"], (
            f"{node.name!r}: expected {node.props['verdict']}, got {ruling.verdict}\n"
            f"{ruling.explain()}"
        )


def test_marketing_claim_is_refused(court):
    assert court.adjudicate("This superfood boosts immunity").verdict == "REFUSE"


def test_disease_claim_without_mechanism_is_refused(court):
    r = court.adjudicate("Eating oats prevents heart disease")
    assert r.verdict == "REFUSE"


def test_malformed_mechanism_can_never_be_confirmed(court):
    """
    Regression: naming molecules the register knows is not naming a pathway.
    A malformed mechanism that resolves to real laws was being Confirmed.
    """
    for text in [
        "Eating oats prevents heart disease",
        "Spinach and carotenoids prevent deficiency disease",
    ]:
        r = court.adjudicate(text)
        assert r.verdict not in {"Confirmed", "Plausible"}, r.explain()


def test_ungrounded_claim_is_unevaluable_not_guessed(court):
    """The rule the whole design exists for: say 'I cannot evaluate that'."""
    r = court.adjudicate("Quercetin may modulate telomere maintenance")
    assert r.verdict == "UNEVALUABLE"
    assert r.gate_check == "unevaluable"


def test_closed_gate_busts_the_claim(court):
    r = court.adjudicate("Phytate blocks zinc absorption")
    assert r.verdict == "Busted"
    assert r.gate_check == "fail"


def test_stated_absence_closes_a_gate_that_requires_it(court):
    """'fat-free' against a law gated on fat co-presence must fail the gate."""
    r = court.adjudicate(
        "Fat-free spinach salad delivers carotenoids to prevent deficiency disease"
    )
    assert r.gate_check == "fail"
    assert r.verdict == "Busted"


def test_weakest_atom_sets_the_verdict(court):
    """A compound claim is only as good as its worst assertion."""
    r = court.adjudicate("Vitamin C increases iron absorption and boosts vitality")
    assert r.verdict == "REFUSE"
    assert len(r.atomized) > 1


def test_verbless_fragment_does_not_dominate(court):
    """Regression: a noun phrase outranked the actual assertion."""
    r = court.adjudicate("Eat spinach salad, vitamin C increases iron absorption")
    assert r.verdict != "UNEVALUABLE"


def test_adjudication_serialises_to_the_repo_schema(court):
    fixture = court.adjudicate("Iron supports energy").to_fixture()
    assert set(fixture) >= {"id", "surface_claim", "verdict", "rosetta"}
    assert fixture["verdict"] in {
        "Busted", "Plausible", "Confirmed", "UNEVALUABLE", "REFUSE"
    }


def test_court_works_without_a_model(graph):
    """The model is optional; the constitution is not."""
    bare = Court(graph)
    assert bare.adjudicate("This superfood boosts immunity").verdict == "REFUSE"


# ------------------------------------------------------------------- model

def test_model_beats_majority_baseline(graph):
    m = EvidenceGradeModel.train_from_graph(graph, seed=0)
    assert m.metrics["accuracy"] > m.metrics["majority_baseline"]


def test_model_is_deterministic(graph):
    a = EvidenceGradeModel.train_from_graph(graph, seed=7)
    b = EvidenceGradeModel.train_from_graph(graph, seed=7)
    assert a.metrics["accuracy"] == b.metrics["accuracy"]


def test_model_roundtrips(graph, tmp_path):
    m = EvidenceGradeModel.train_from_graph(graph, seed=0)
    path = tmp_path / "m.json"
    m.save(path)
    again = EvidenceGradeModel.load(path)
    text = "Blunts postprandial glucose response"
    assert again.predict(text)[0] == m.predict(text)[0]


def test_model_cannot_emit_a_verdict(graph):
    """
    Structural guarantee: the learned component's output space is evidence
    grades only. It has no path to Confirmed.
    """
    m = EvidenceGradeModel.train_from_graph(graph, seed=0)
    assert set(m.classes) == {"A", "B", "C", "D"}
    grade, probs = m.predict("anything at all")
    assert grade in {"A", "B", "C", "D"}
    assert not set(probs) & {"Confirmed", "Plausible", "Busted"}


# ------------------------------------------------------------------ export

def test_exports_are_non_empty_and_well_formed(graph):
    cypher = to_cypher(graph)
    assert "CREATE CONSTRAINT" in cypher and "CREATE (:Law" in cypher

    ttl = to_turtle(graph)
    assert ttl.startswith("@prefix bac:") and "rdf:type bac:Law" in ttl

    gml = to_graphml(graph)
    assert gml.startswith("<?xml") and "</graphml>" in gml


def test_graphml_parses(graph):
    import xml.etree.ElementTree as ET
    ET.fromstring(to_graphml(graph))
