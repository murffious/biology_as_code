"""
gluconeogenesis.py
=================================================================
Gluconeogenesis – synthesis of glucose from non-carbohydrate precursors

Bypasses the three irreversible steps of glycolysis using unique enzymes.
Mainly occurs in liver and kidney cortex.

Energy cost: 6 ATP equivalents per glucose formed.
=================================================================
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from biology_as_code.pathways.metabolic_mechanisms import (
        MetabolicMechanism,
        get_metabolic_mechanism_registry,
    )
except ImportError:
    get_metabolic_mechanism_registry = None
    MetabolicMechanism = None


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
    atp_cost: int = 0
    gtp_cost: int = 0
    regulation: str = ""
    notes: str = ""
    is_bypass: bool = False


class MetabolicPathway:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, MetaboliteNode] = {}
        self.edges: list[ReactionEdge] = []

    def add_node(self, node: MetaboliteNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ReactionEdge) -> None:
        self.edges.append(edge)

    def get_mechanism(self, edge: ReactionEdge) -> Optional["MetabolicMechanism"]:
        if get_metabolic_mechanism_registry is None or not edge.mechanism_id:
            return None
        return get_metabolic_mechanism_registry().get(edge.mechanism_id)

    def summary(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "atp_equivalents_per_glucose": 6,
            "main_sites": "Liver and kidney cortex",
        }


class GluconeogenesisRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="gluconeogenesis",
            description=(
                "Gluconeogenesis – synthesis of glucose from non-carbohydrate precursors "
                "(lactate, glycerol, glucogenic amino acids). Bypasses the three irreversible "
                "steps of glycolysis. Costs 6 ATP equivalents per glucose."
            )
        )

        # Nodes (focusing on the unique bypasses + key shared intermediates)
        p.add_node(MetaboliteNode("pyruvate", "Pyruvate", PathwayNodeType.SUBSTRATE,
            "Major precursor (from lactate via LDH, or from alanine via transamination)."))
        p.add_node(MetaboliteNode("oaa", "Oxaloacetate", PathwayNodeType.INTERMEDIATE,
            "Mitochondrial intermediate. Also links to TCA cycle."))
        p.add_node(MetaboliteNode("pep", "Phosphoenolpyruvate", PathwayNodeType.INTERMEDIATE,
            "Product of the first bypass (via PEPCK)."))
        p.add_node(MetaboliteNode("2pg", "2-Phosphoglycerate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("3pg", "3-Phosphoglycerate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("13bpg", "1,3-Bisphosphoglycerate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("gap", "Glyceraldehyde-3-phosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("dhap", "Dihydroxyacetone phosphate", PathwayNodeType.INTERMEDIATE,
            "Also derived from glycerol."))
        p.add_node(MetaboliteNode("f16bp", "Fructose-1,6-bisphosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("f6p", "Fructose-6-phosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("g6p", "Glucose-6-phosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("glucose", "Glucose", PathwayNodeType.PRODUCT,
            "Released into blood by the liver (and kidney) to maintain euglycemia."))

        # Bypass 1: Pyruvate → OAA → PEP
        p.add_edge(ReactionEdge(
            from_node="pyruvate",
            to_node="oaa",
            enzyme="Pyruvate carboxylase",
            atp_cost=-1,
            is_bypass=True,
            regulation="Activated by acetyl-CoA. Requires biotin.",
            notes="First unique enzyme of gluconeogenesis. Occurs in mitochondria. Important anaplerotic reaction."
        ))
        p.add_edge(ReactionEdge(
            from_node="oaa",
            to_node="pep",
            enzyme="PEP carboxykinase (PEPCK)",
            gtp_cost=-1,
            is_bypass=True,
            regulation="Induced by glucagon / cAMP; repressed by insulin.",
            notes="Second part of the first bypass. Cytosolic and mitochondrial isoforms exist."
        ))

        # Shared reversible steps (abbreviated)
        p.add_edge(ReactionEdge(
            from_node="pep", to_node="2pg",
            enzyme="Enolase (reverse)",
            notes="Shared with glycolysis (reversible)."
        ))
        p.add_edge(ReactionEdge(
            from_node="2pg", to_node="3pg",
            enzyme="Phosphoglycerate mutase (reverse)",
            notes="Shared with glycolysis."
        ))
        p.add_edge(ReactionEdge(
            from_node="3pg", to_node="13bpg",
            enzyme="Phosphoglycerate kinase (reverse)",
            atp_cost=-1,
            notes="Shared. Consumes ATP in the gluconeogenic direction."
        ))
        p.add_edge(ReactionEdge(
            from_node="13bpg", to_node="gap",
            enzyme="GAPDH (reverse)",
            notes="Shared. Requires NADH."
        ))
        p.add_edge(ReactionEdge(
            from_node="gap", to_node="dhap",
            enzyme="Triose phosphate isomerase",
            notes="Shared."
        ))
        p.add_edge(ReactionEdge(
            from_node="gap", to_node="f16bp",
            enzyme="Aldolase (reverse)",
            notes="Shared. Condenses GAP + DHAP."
        ))

        # Bypass 2: F1,6BP → F6P
        p.add_edge(ReactionEdge(
            from_node="f16bp",
            to_node="f6p",
            enzyme="Fructose-1,6-bisphosphatase",
            is_bypass=True,
            regulation=(
                "Inhibited by AMP and fructose-2,6-bisphosphate. "
                "Activated when energy is high and F2,6BP is low (glucagon state)."
            ),
            notes="Second unique bypass. Reciprocal regulation with PFK-1."
        ))

        p.add_edge(ReactionEdge(
            from_node="f6p", to_node="g6p",
            enzyme="Phosphoglucose isomerase (reverse)",
            notes="Shared with glycolysis."
        ))

        # Bypass 3: G6P → Glucose
        p.add_edge(ReactionEdge(
            from_node="g6p",
            to_node="glucose",
            enzyme="Glucose-6-phosphatase",
            is_bypass=True,
            regulation="Primarily expressed in liver and kidney. Induced in fasting.",
            notes=(
                "Final unique enzyme. Located in the endoplasmic reticulum. "
                "Allows free glucose to be released into the blood."
            )
        ))

        self.register(p)


def get_gluconeogenesis_registry() -> GluconeogenesisRegistry:
    return GluconeogenesisRegistry()


if __name__ == "__main__":
    reg = get_gluconeogenesis_registry()
    path = reg.get("gluconeogenesis")
    print("=" * 65)
    print("GLUCONEOGENESIS")
    print("=" * 65)
    print(path.description)
    print()
    s = path.summary()
    print(f"Nodes: {s['nodes']}  |  Edges: {s['edges']}")
    print(f"Energy cost: {s['atp_equivalents_per_glucose']} ATP equivalents per glucose")
    print(f"Main sites: {s['main_sites']}")
    print()
    print("Three unique bypasses of irreversible glycolytic steps:")
    print("  1. Pyruvate carboxylase + PEPCK")
    print("  2. Fructose-1,6-bisphosphatase")
    print("  3. Glucose-6-phosphatase")
    print()
    print("Reciprocal regulation with glycolysis prevents futile cycling.")
