"""
Compartment is a place, not a role (Phase 4).

digestion_absorption_pathways and meal_critical_pathways used to declare LUMEN /
ENTEROCYTE / CIRCULATION as PathwayNodeType members, so one field meant "role" in
fourteen modules and "place" in two. These tests keep the two axes separate and
keep the compartment vocabulary from drifting into free text
(Mitochondria vs m vs mito).

See docs/python/PATHWAY_TYPES_REFACTOR.md Phase 4.
"""

from __future__ import annotations

import sys
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from biology_as_code.pathways._types import COMPARTMENTS, PathwayNodeType  # noqa: E402
from biology_as_code.pathways.registry import _all_pathways  # noqa: E402

# Roles only. A place must never reappear here.
FORBIDDEN_AS_ROLE = {"LUMEN", "ENTEROCYTE", "CIRCULATION", "COMPARTMENT"}


def _metabolite_nodes():
    """(pathway, node) for nodes that carry a node_type. nutrient_sensing uses a
    separate RegulatoryNode shape and is out of scope here."""
    for name, pathway in _all_pathways():
        for node in (getattr(pathway, "nodes", {}) or {}).values():
            if getattr(node, "node_type", None) is not None:
                yield name, node


def test_node_type_enum_contains_no_places():
    offenders = {m.name for m in PathwayNodeType} & FORBIDDEN_AS_ROLE
    assert not offenders, (
        f"PathwayNodeType must describe role, not location. Found: {sorted(offenders)}. "
        "Anatomical position belongs in MetaboliteNode.compartment."
    )


def test_every_compartment_is_in_the_catalog():
    unknown = sorted(
        {
            (name, node.id, node.compartment)
            for name, node in _metabolite_nodes()
            if getattr(node, "compartment", "") and node.compartment not in COMPARTMENTS
        }
    )
    assert not unknown, (
        f"compartment values outside the catalog: {unknown}. "
        f"Allowed: {sorted(COMPARTMENTS)} (or '' for not stated)."
    )


def test_absorptive_graphs_actually_carry_compartments():
    """The two migrated modules are the reason this axis exists; if their
    compartments vanished, the migration silently regressed to role-only."""
    seen = {
        node.compartment
        for name, node in _metabolite_nodes()
        if name in {"carb_digestion_absorption", "iron_absorption"}
        and getattr(node, "compartment", "")
    }
    assert {"lumen", "enterocyte", "circulation"} <= seen, (
        f"expected the absorptive scale to be present, got {sorted(seen)}"
    )


def test_transport_edges_cross_compartments():
    """A transport step is an edge whose endpoints sit in different compartments.
    That is the property compartment-on-node exists to make expressible."""
    crossings = []
    for name, pathway in _all_pathways():
        nodes = getattr(pathway, "nodes", {}) or {}
        for edge in getattr(pathway, "edges", []) or []:
            a, b = nodes.get(edge.from_node), nodes.get(edge.to_node)
            ca = getattr(a, "compartment", "") if a else ""
            cb = getattr(b, "compartment", "") if b else ""
            if ca and cb and ca != cb:
                crossings.append((name, edge.from_node, edge.to_node, ca, cb))
    assert crossings, "no compartment-crossing edge found; absorption should produce some"
