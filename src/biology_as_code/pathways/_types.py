"""
_types.py
=================================================================
Shared graph types for the teaching pathway modules.

Sixteen modules under `pathways/` each declared their own copies of
`PathwayNodeType`, `MetaboliteNode`, `ReactionEdge` and `MetabolicPathway`.
Because there was no shared contract, the one cross-cutting consumer
(`scripts/export_pathway_packs.py`) had to guess at field names and silently
dropped whatever it did not recognise. This module is that contract.

Nothing is required to migrate at once: `edge_enzyme()` and `edge_yields()`
read *any* edge object via getattr, so they work on the legacy per-module
dataclasses and on the shared `ReactionEdge` below.

See docs/python/PATHWAY_TYPES_REFACTOR.md.
=================================================================
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# --------------------------------------------------------------------------
# Cofactor sign conventions
# --------------------------------------------------------------------------
# The legacy modules use two OPPOSITE sign conventions, consistently, and it is
# genuinely easy to misread:
#
#   atp_cost = -1  ->  one ATP was CONSUMED   (glycolysis hexokinase)
#   atp_cost = +1  ->  one ATP was PRODUCED   (glycolysis PGK)
#   nadh_cost = -1 ->  one NADH was PRODUCED  (glycolysis GAPDH, TCA IDH)
#   nadh_cost = +1 ->  one NADH was CONSUMED  (glycolysis LDH)
#
# The redox fields are not tracking the reduced carrier at all — they track its
# OXIDISED partner (NAD+, FAD, NADP+), so their sign is inverted relative to the
# phosphate fields. Rendering `nadh_cost` raw prints "NADH-1" on a step that
# makes NADH, which reads as the exact opposite of the biology.
#
# `edge_yields()` below normalises all of it to one rule:
#
#                    POSITIVE = PRODUCED, NEGATIVE = CONSUMED
#
# Field name -> (display species, multiplier to apply to reach that rule).
PHOSPHATE_YIELDS = {"atp_cost": ("ATP", +1), "gtp_cost": ("GTP", +1)}
REDOX_YIELDS = {
    "nadh_cost": ("NADH", -1),
    "fadh2_cost": ("FADH2", -1),
    "nadph_cost": ("NADPH", -1),
}
COUNT_YIELDS = {"co2_produced": ("CO2", +1), "protons_pumped": ("H+", +1)}
YIELD_FIELDS = {**PHOSPHATE_YIELDS, **REDOX_YIELDS, **COUNT_YIELDS}

# One concept, historically three names. Order is precedence.
ENZYME_FIELDS = ("enzyme", "enzyme_or_complex", "enzyme_or_process", "process")


class PathwayNodeType(Enum):
    """Metabolic role of a node. Anatomical position is `MetaboliteNode.compartment`."""

    SUBSTRATE = "substrate"
    INTERMEDIATE = "intermediate"
    PRODUCT = "product"
    # domain extras, unioned from the per-module enums
    SIGNAL = "signal"
    REGULATORY = "regulatory"
    CARRIER = "carrier"
    COMPLEX = "complex"
    POLYMER = "polymer"
    LIPOPROTEIN = "lipoprotein"


@dataclass
class MetaboliteNode:
    id: str
    name: str
    node_type: PathwayNodeType
    notes: str = ""
    compartment: str = ""  # e.g. "m" / "c" / "e", or "lumen" / "enterocyte"


@dataclass
class ReactionEdge:
    from_node: str
    to_node: str
    mechanism_id: str = ""
    enzyme: str = ""
    notes: str = ""

    # cofactor bookkeeping — see the sign conventions above
    atp_cost: int = 0
    gtp_cost: int = 0
    nadh_cost: int = 0
    fadh2_cost: int = 0
    nadph_cost: int = 0
    co2_produced: int = 0
    protons_pumped: int = 0

    #: Micronutrients this step cannot run without — the vitamin or mineral that
    #: is the enzyme's cofactor, not a substrate. Every other field on this edge
    #: tracks carbon and energy; this is the only one that tracks *nutrition*, and
    #: it is the edge that makes these graphs answer a dietary question rather
    #: than a biochemical one. Carnitine synthesis is the worked case: five
    #: distinct dependencies on one linear chain, so a shortfall at any single
    #: step stops the whole pathway. Scoring those five nutrients independently
    #: cannot represent that.
    requires_nutrient: list[str] = field(default_factory=list)

    # descriptors, all optional
    process: str = ""  # non-enzymatic step ("passive diffusion"); distinct from `enzyme`
    location: str = ""
    regulation: str = ""
    phase: str = ""
    direction: str = ""
    effect: str = ""
    is_bypass: bool = False

    def label(self) -> str:
        return edge_label(self)

    def yields(self) -> list[tuple[str, int]]:
        return edge_yields(self)


def edge_enzyme(edge: Any) -> str:
    """The enzyme/complex/process name, whichever of the legacy fields holds it."""
    for name in ENZYME_FIELDS:
        value = getattr(edge, name, "") or ""
        if value:
            return str(value)
    return ""


def edge_yields(edge: Any) -> list[tuple[str, int]]:
    """Cofactor changes as (species, delta), normalised so positive = produced.

    Works on legacy per-module edges and on the shared ReactionEdge alike.
    """
    out: list[tuple[str, int]] = []
    for name, (species, sign) in YIELD_FIELDS.items():
        raw = getattr(edge, name, 0)
        if not isinstance(raw, (int, float)) or not raw:
            continue
        out.append((species, int(raw * sign)))
    return out


def edge_label(edge: Any) -> str:
    """Display label for one edge: what catalyses it, then what it costs or makes."""
    effect = getattr(edge, "effect", "") or ""
    if effect:
        mech = getattr(edge, "mechanism", "") or getattr(edge, "mechanism_id", "") or ""
        return f"{effect}: {mech}"[:48] if mech else str(effect)

    parts: list[str] = []
    mechanism_id = getattr(edge, "mechanism_id", "") or ""
    if mechanism_id:
        parts.append(str(mechanism_id))
    else:
        enzyme = edge_enzyme(edge)
        if enzyme:
            parts.append(enzyme[:40])
    parts.extend(f"{species}{delta:+g}" for species, delta in edge_yields(edge))
    required = edge_nutrients(edge)
    if required:
        parts.append("⟨" + ", ".join(required) + "⟩")
    return "<br/>".join(parts) if parts else "step"


def edge_nutrients(edge: Any) -> list[str]:
    """Micronutrients this step requires. Empty for edges that declare none.

    Read via getattr like the other accessors here, so legacy per-module edge
    dataclasses (which have no such field) keep working untouched.
    """
    required = getattr(edge, "requires_nutrient", None) or []
    return [str(n) for n in required]


class MetabolicPathway:
    """A teaching graph: metabolite nodes joined by reaction edges.

    Subclasses override `summary()` to add pathway-specific totals; call
    `super().summary()` to keep the common keys.
    """

    def __init__(self, name: str, description: str = "") -> None:
        self.name = name
        self.description = description
        self.nodes: dict[str, MetaboliteNode] = {}
        self.edges: list[ReactionEdge] = []
        self.references: list[str] = []

    def add_node(self, node: MetaboliteNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ReactionEdge) -> None:
        self.edges.append(edge)

    def get_mechanism(self, edge: ReactionEdge) -> Optional[Any]:
        try:
            from biology_as_code.pathways.metabolic_mechanisms import (
                get_metabolic_mechanism_registry,
            )
        except ImportError:
            return None
        if not getattr(edge, "mechanism_id", ""):
            return None
        return get_metabolic_mechanism_registry().get(edge.mechanism_id)

    def orphan_nodes(self) -> list[str]:
        """Declared nodes that no edge touches — prose describing biology the
        graph does not actually contain."""
        touched = {n for e in self.edges for n in (e.from_node, e.to_node)}
        return sorted(set(self.nodes) - touched)

    def net_yields(self) -> dict[str, int]:
        """Summed cofactor deltas across the graph, positive = produced."""
        totals: dict[str, int] = {}
        for edge in self.edges:
            for species, delta in edge_yields(edge):
                totals[species] = totals.get(species, 0) + delta
        return {k: v for k, v in totals.items() if v}

    def nutrient_dependencies(self) -> dict[str, list[str]]:
        """Which steps need which micronutrient — the query a diagram cannot answer.

        A rendered pathway shows the dependency as a label next to one arrow. It
        cannot answer "which steps stop if this person is short on B6", which is
        the question a nutrition model actually has. Returns nutrient -> the steps
        that require it, each named by enzyme where one is declared.
        """
        deps: dict[str, list[str]] = {}
        for edge in self.edges:
            step = edge_enzyme(edge) or f"{edge.from_node}→{edge.to_node}"
            for nutrient in edge_nutrients(edge):
                deps.setdefault(nutrient, []).append(step)
        return deps

    def summary(self) -> dict:
        return {
            "name": self.name,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
        }
