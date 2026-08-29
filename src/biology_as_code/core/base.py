"""
Structural contracts for Biology as Code.

These Protocols describe **what we already ship**:
  - teaching pathway *graphs* (nodes + edges + optional mechanism_id)
  - meal *compile* simulation (FoodPayload → report)

They intentionally do **not** require:
  - stoichiometry matrices
  - ODE time-stepping (duration/dt)
  - kinetic rate laws as the primary model

If a full kinetic ODE layer is needed later, put it under a separate
``biology_as_code.kinetic`` package rather than renaming dig/pathway modules.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class StructuralNode:
    """Normalized view of a graph node (maps from existing MetaboliteNode-like objects)."""

    id: str
    name: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StructuralEdge:
    """Normalized view of a graph edge (maps from existing ReactionEdge-like objects)."""

    from_node: str
    to_node: str
    mechanism_id: str = ""
    label: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class PathwaySummary:
    """Small summary bag — not a product meal score."""

    name: str
    nodes: int
    edges: int
    extras: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class GraphPathwayLike(Protocol):
    """
    Existing registry pathways already satisfy this if they have:
      .name, .nodes (dict), .edges (list), optional .summary()
    """

    name: str
    nodes: dict[str, Any]
    edges: list[Any]

    def summary(self) -> dict[str, Any]: ...


@runtime_checkable
class MealSimulatorLike(Protocol):
    """
    Meal compile surface — MealEngine / UnifiedFacade style.

    Not a continuous-time ODE runner.
    """

    def simulate_payload(self, payload: Any, **kwargs: Any) -> dict[str, Any]: ...


def as_structural_nodes(pathway: Any) -> list[StructuralNode]:
    """Best-effort normalize pathway.nodes → StructuralNode list."""
    nodes = getattr(pathway, "nodes", {}) or {}
    out: list[StructuralNode] = []
    for nid, node in nodes.items():
        name = getattr(node, "name", None) or getattr(node, "id", None) or str(nid)
        out.append(StructuralNode(id=str(nid), name=str(name)))
    return out


def as_structural_edges(pathway: Any) -> list[StructuralEdge]:
    edges = getattr(pathway, "edges", []) or []
    out: list[StructuralEdge] = []
    for e in edges:
        out.append(
            StructuralEdge(
                from_node=str(getattr(e, "from_node", "")),
                to_node=str(getattr(e, "to_node", "")),
                mechanism_id=str(getattr(e, "mechanism_id", "") or ""),
                label=str(
                    getattr(e, "enzyme", None)
                    or getattr(e, "process", None)
                    or getattr(e, "mechanism_id", "")
                    or ""
                ),
            )
        )
    return out


def pathway_summary(pathway: Any) -> PathwaySummary:
    if hasattr(pathway, "summary") and callable(pathway.summary):
        s = pathway.summary() or {}
        return PathwaySummary(
            name=str(s.get("name") or getattr(pathway, "name", "")),
            nodes=int(s.get("nodes") or len(getattr(pathway, "nodes", {}) or {})),
            edges=int(s.get("edges") or len(getattr(pathway, "edges", []) or {})),
            extras={
                k: v
                for k, v in s.items()
                if k not in ("name", "description", "nodes", "edges")
            },
        )
    return PathwaySummary(
        name=str(getattr(pathway, "name", "")),
        nodes=len(getattr(pathway, "nodes", {}) or {}),
        edges=len(getattr(pathway, "edges", []) or {}),
    )
