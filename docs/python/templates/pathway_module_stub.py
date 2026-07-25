"""
TEMPLATE — copy to src/biology_as_code/pathways/<theme>.py and edit.

Do not import this file from package code. After you implement:

  1. Wire get_<theme>_registry into pathways/registry.py pathway_loaders()
  2. PYTHONPATH=src python3 scripts/export_pathway_packs.py
  3. PYTHONPATH=src python3 scripts/check_pathway_integration.py --pathway <name>
  4. Add tests/test_<theme>.py (see tests/test_ketolysis.py)
  5. Update pathways/packs/COVERAGE.md

Guide: docs/python/ADD_PATHWAY.md
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from biology_as_code.pathways.metabolic_mechanisms import (
        get_metabolic_mechanism_registry,
    )
except ImportError:
    get_metabolic_mechanism_registry = None


class PathwayNodeType(Enum):
    SUBSTRATE = "substrate"
    INTERMEDIATE = "intermediate"
    PRODUCT = "product"


@dataclass
class MetaboliteNode:
    id: str
    name: str
    node_type: PathwayNodeType
    notes: str = ""


@dataclass
class ReactionEdge:
    from_node: str
    to_node: str
    mechanism_id: str = ""
    enzyme: str = ""
    location: str = ""
    regulation: str = ""
    notes: str = ""


class MetabolicPathway:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, MetaboliteNode] = {}
        self.edges: list[ReactionEdge] = []
        self.references: list[str] = []
        self.extra_summary: dict = {}

    def add_node(self, node: MetaboliteNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ReactionEdge) -> None:
        self.edges.append(edge)

    def get_mechanism(self, edge: ReactionEdge):
        if get_metabolic_mechanism_registry is None or not edge.mechanism_id:
            return None
        return get_metabolic_mechanism_registry().get(edge.mechanism_id)

    def summary(self) -> dict:
        out = {
            "name": self.name,
            "description": self.description,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
        }
        out.update(self.extra_summary)
        return out


class ThemeRegistry:  # rename: e.g. HistidineCatabolismRegistry
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_example()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    def _build_example(self) -> None:
        p = MetabolicPathway(
            name="example_pathway",  # CHANGE — unique snake_case
            description=(
                "One-paragraph teaching description. FLOW-level topology, "
                "not a clinical protocol. Name the site and the main product."
            ),
        )
        p.add_node(MetaboliteNode(
            "substrate_a", "Substrate A", PathwayNodeType.SUBSTRATE,
            notes="Starting metabolite.",
        ))
        p.add_node(MetaboliteNode(
            "intermediate_b", "Intermediate B", PathwayNodeType.INTERMEDIATE,
        ))
        p.add_node(MetaboliteNode(
            "product_c", "Product C", PathwayNodeType.PRODUCT,
            notes="Links to …",
        ))

        p.add_edge(ReactionEdge(
            from_node="substrate_a",
            to_node="intermediate_b",
            enzyme="Example enzyme (GENE)",
            # mechanism_id="example_enzyme",  # only if registered in metabolic_mechanisms
            location="Mitochondria / cytosol",
            notes="Teaching note for the step.",
        ))
        p.add_edge(ReactionEdge(
            from_node="intermediate_b",
            to_node="product_c",
            enzyme="Second enzyme",
        ))

        p.references = [
            # Real sources only — textbook chapter, PMC, DOI. Never invent.
            # "Author / title — https://…",
        ]
        p.extra_summary = {
            # "clinical_hook": "…",
            # "main_product": "…",
        }
        self.register(p)


def get_theme_registry() -> ThemeRegistry:  # rename to match module
    return ThemeRegistry()


if __name__ == "__main__":
    reg = get_theme_registry()
    for path in reg.list_all():
        print(path.name, path.summary())
