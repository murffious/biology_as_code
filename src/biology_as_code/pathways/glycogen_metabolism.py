"""
glycogen_metabolism.py
=================================================================
Glycogen Metabolism (Glycogenesis + Glycogenolysis)

Glycogenesis:   Glucose → Glycogen (storage)
Glycogenolysis: Glycogen → Glucose-6-P (or free glucose in liver)

Strong reciprocal regulation by insulin vs glucagon/epinephrine.
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
    POLYMER = "polymer"


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
    regulation: str = ""
    notes: str = ""
    direction: str = ""          # "synthesis" or "breakdown"


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
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "synthesis_key_enzyme": "Glycogen synthase",
            "breakdown_key_enzyme": "Glycogen phosphorylase",
        }


class GlycogenMetabolismRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="glycogen_metabolism",
            description=(
                "Glycogen synthesis (glycogenesis) and breakdown (glycogenolysis). "
                "Reciprocally regulated so that both processes are not active at the same time."
            )
        )

        # Nodes
        p.add_node(MetaboliteNode("glucose", "Glucose", PathwayNodeType.SUBSTRATE))
        p.add_node(MetaboliteNode("g6p", "Glucose-6-phosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("g1p", "Glucose-1-phosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("udp_glucose", "UDP-Glucose", PathwayNodeType.INTERMEDIATE,
            "Activated form of glucose for glycogen synthesis."))
        p.add_node(MetaboliteNode("glycogen", "Glycogen", PathwayNodeType.POLYMER,
            "Branched polymer of glucose (α-1,4 linkages with α-1,6 branches)."))
        p.add_node(MetaboliteNode("limit_dextrin", "Limit Dextrin", PathwayNodeType.INTERMEDIATE,
            "Glycogen with branches exposed after phosphorylase action."))

        # Glycogenesis (synthesis)
        p.add_edge(ReactionEdge(
            from_node="glucose", to_node="g6p",
            enzyme="Hexokinase / Glucokinase",
            direction="synthesis",
            notes="Same as first step of glycolysis."
        ))
        p.add_edge(ReactionEdge(
            from_node="g6p", to_node="g1p",
            enzyme="Phosphoglucomutase",
            direction="synthesis",
            notes="Reversible."
        ))
        p.add_edge(ReactionEdge(
            from_node="g1p", to_node="udp_glucose",
            enzyme="UDP-glucose pyrophosphorylase",
            direction="synthesis",
            notes="Activates glucose. UTP + G1P → UDP-glucose + PPi."
        ))
        p.add_edge(ReactionEdge(
            from_node="udp_glucose", to_node="glycogen",
            enzyme="Glycogen synthase + Branching enzyme",
            direction="synthesis",
            regulation=(
                "Glycogen synthase is active when dephosphorylated (insulin state). "
                "Inactivated by phosphorylation (glucagon/epinephrine via PKA)."
            ),
            notes="Key regulated step of glycogenesis. Branching enzyme creates α-1,6 branches."
        ))

        # Glycogenolysis (breakdown)
        p.add_edge(ReactionEdge(
            from_node="glycogen", to_node="g1p",
            enzyme="Glycogen phosphorylase + Debranching enzyme",
            direction="breakdown",
            regulation=(
                "Glycogen phosphorylase is activated by phosphorylation "
                "(glucagon/epinephrine → cAMP → PKA → phosphorylase kinase). "
                "Inactivated by dephosphorylation (insulin). "
                "Also allosterically activated by AMP in muscle."
            ),
            notes="Key regulated step of glycogenolysis. Produces G1P (not free glucose)."
        ))
        p.add_edge(ReactionEdge(
            from_node="g1p", to_node="g6p",
            enzyme="Phosphoglucomutase",
            direction="breakdown",
            notes="Reversible. G6P can enter glycolysis (muscle) or be dephosphorylated to free glucose (liver)."
        ))
        p.add_edge(ReactionEdge(
            from_node="g6p", to_node="glucose",
            enzyme="Glucose-6-phosphatase",
            direction="breakdown",
            notes="Liver (and kidney) only. Allows free glucose to be released into the blood."
        ))

        self.register(p)


def get_glycogen_metabolism_registry() -> GlycogenMetabolismRegistry:
    return GlycogenMetabolismRegistry()


if __name__ == "__main__":
    reg = get_glycogen_metabolism_registry()
    path = reg.get("glycogen_metabolism")
    print("=" * 60)
    print("GLYCOGEN METABOLISM")
    print("=" * 60)
    print(path.description)
    print()
    print(path.summary())
    print()
    print("Glycogenesis key enzyme : Glycogen synthase (active when dephosphorylated)")
    print("Glycogenolysis key enzyme: Glycogen phosphorylase (active when phosphorylated)")
    print("Reciprocal regulation prevents futile cycling.")
