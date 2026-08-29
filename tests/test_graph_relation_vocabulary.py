"""
The two relation vocabularies must not diverge silently.

There are two of them, and that is fine:

- ``engine.laws.models.RelationType`` — what a law may assert.
- ``graph.build._REL_ALIASES`` — what the graph can represent as an edge, plus
  edge kinds the law model has no use for.

They legitimately differ. What is *not* fine is a law carrying a determinate
structural relation that the graph cannot represent, because ``load_laws``
handles that by emitting nothing: ``_REL_ALIASES.get(...)`` returns ``None``,
the ``if rel and ...`` guard fails, and the law loses its self-declared edge
without a warning.

That is exactly what happened when LAW-039 was retyped from ``EXPANDS_BOUND``
to ``CONSERVES``. The law model gained the value; this map did not; the edge
disappeared from the graph and every test stayed green. These tests close it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from biology_as_code.engine.laws.models import RelationType
from biology_as_code.engine.laws.registry import load_system_bound_registry
from biology_as_code.graph.build import _REL_ALIASES, build

REPO_ROOT = Path(__file__).resolve().parents[1]
SUBSET_SCHEMA = REPO_ROOT / "schemas" / "relation_enums.subset.json"

#: Law-model relations that assert nothing an edge could carry. A law typed with
#: one of these is *not* expected to appear in the graph vocabulary.
#:
#: ``MIXED`` is the registry's "could not determine" fallback, ``FRAMEWORK``
#: says the law is not executable, and ``STATE_FUNCTION`` describes a property
#: rather than a directed relation between two things.
NON_STRUCTURAL = frozenset({"MIXED", "FRAMEWORK", "STATE_FUNCTION"})


def _law_model_relations() -> set[str]:
    import typing

    return set(typing.get_args(RelationType))


def test_every_determinate_law_relation_is_representable_in_the_graph():
    """The guard that would have caught the LAW-039 edge loss."""
    determinate = _law_model_relations() - NON_STRUCTURAL
    missing = sorted(r for r in determinate if r not in _REL_ALIASES)
    assert not missing, (
        f"law-model relations with no graph representation: {missing}. "
        "A law typed with one of these silently emits no self-declared edge "
        "(graph/build.py: `rel = _REL_ALIASES.get(...)` then `if rel and ...`). "
        "Add it to _REL_ALIASES, or add it to NON_STRUCTURAL if it genuinely "
        "asserts nothing an edge could carry."
    )


def test_every_relation_actually_used_by_a_law_resolves():
    """
    Stronger and narrower: whatever the registry really contains must resolve.

    Catches the failure even if someone adds a relation to the law model and
    forgets to classify it here at all.
    """
    reg = load_system_bound_registry()
    unresolved = sorted(
        {
            law.relation_type
            for law in reg.all()
            if law.relation_expression.strip()
            and law.relation_type not in NON_STRUCTURAL
            and law.relation_type not in _REL_ALIASES
        }
    )
    assert not unresolved, (
        f"laws in the registry carry relations the graph cannot represent: {unresolved}"
    )


def test_the_published_subset_schema_matches_the_graph_vocabulary():
    """``schemas/relation_enums.subset.json`` is the public copy of this map."""
    published = set(json.loads(SUBSET_SCHEMA.read_text(encoding="utf-8"))["RelationType"])
    assert published == set(_REL_ALIASES), (
        "the published relation enum subset has drifted from the graph vocabulary; "
        f"only in schema: {sorted(published - set(_REL_ALIASES))}; "
        f"only in code: {sorted(set(_REL_ALIASES) - published)}"
    )


@pytest.mark.parametrize(
    ("law_id", "expected_relation"),
    [
        ("LAW-039", "CONSERVES"),
        ("LAW-004", "EXPANDS_BOUND"),
    ],
)
def test_a_law_with_a_determinate_relation_emits_a_self_declared_edge(law_id, expected_relation):
    """
    The regression itself, pinned on the real graph.

    LAW-039 emitted an ``EXPANDS_BOUND`` self-edge before it was retyped, and
    emitted nothing afterwards. LAW-004 is the control that never moved.
    """
    graph = build(":memory:", include_foods=False)
    self_declared = [
        edge for edge in graph.edges() if edge.src == law_id and edge.dst == law_id
    ]
    assert self_declared, (
        f"{law_id} emits no self-declared relation edge — its relation_type is not "
        "in the graph vocabulary"
    )
    assert expected_relation in {edge.rel for edge in self_declared}
