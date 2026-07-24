"""
beta_oxidation.py
=================================================================
β-Oxidation of Fatty Acids

Models the mitochondrial spiral that shortens fatty acyl-CoA by
2 carbons each cycle, producing acetyl-CoA, NADH, and FADH₂.

Key points:
  - Activation costs 2 ATP equivalents
  - Carnitine shuttle required for long-chain FA entry
  - Each cycle: 1 FADH₂ + 1 NADH + 1 Acetyl-CoA
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
    nadh_cost: int = 0
    fadh2_cost: int = 0
    regulation: str = ""
    notes: str = ""


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
            "per_cycle": "1 NADH + 1 FADH₂ + 1 Acetyl-CoA",
            "activation_cost": "2 ATP equivalents",
        }


class BetaOxidationRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="beta_oxidation",
            description=(
                "β-Oxidation of fatty acids. Mitochondrial spiral that removes "
                "2-carbon units as acetyl-CoA. Each cycle yields 1 NADH + 1 FADH₂ + 1 Acetyl-CoA."
            )
        )

        # Nodes
        p.add_node(MetaboliteNode("fatty_acid", "Fatty Acid (cytosol)", PathwayNodeType.SUBSTRATE,
            "Free fatty acid released by lipolysis."))
        p.add_node(MetaboliteNode("acyl_coa_cyto", "Fatty Acyl-CoA (cytosol)", PathwayNodeType.INTERMEDIATE,
            "Activated form. Costs 2 ATP equivalents (ATP → AMP + PPi)."))
        p.add_node(MetaboliteNode("acyl_carnitine", "Acyl-Carnitine", PathwayNodeType.INTERMEDIATE,
            "Transport form that crosses the inner mitochondrial membrane."))
        p.add_node(MetaboliteNode("acyl_coa_mito", "Fatty Acyl-CoA (mitochondrial matrix)", PathwayNodeType.INTERMEDIATE,
            "Re-formed inside the matrix, ready for β-oxidation."))
        p.add_node(MetaboliteNode("enoyl_coa", "trans-Δ²-Enoyl-CoA", PathwayNodeType.INTERMEDIATE,
            "Product of the first dehydrogenation."))
        p.add_node(MetaboliteNode("hydroxyacyl_coa", "L-3-Hydroxyacyl-CoA", PathwayNodeType.INTERMEDIATE,
            "Product of hydration."))
        p.add_node(MetaboliteNode("ketoacyl_coa", "3-Ketoacyl-CoA", PathwayNodeType.INTERMEDIATE,
            "Product of the second dehydrogenation."))
        p.add_node(MetaboliteNode("acetyl_coa", "Acetyl-CoA", PathwayNodeType.PRODUCT,
            "Released each cycle. Enters TCA cycle."))
        p.add_node(MetaboliteNode("shorter_acyl_coa", "Shortened Acyl-CoA (n-2)", PathwayNodeType.INTERMEDIATE,
            "Re-enters the spiral until fully converted to acetyl-CoA."))

        # Edges
        p.add_edge(ReactionEdge(
            from_node="fatty_acid",
            to_node="acyl_coa_cyto",
            enzyme="Acyl-CoA synthetase (thiokinase)",
            notes="Activation step. ATP → AMP + PPi (effectively costs 2 ATP). Occurs on outer mitochondrial membrane."
        ))
        p.add_edge(ReactionEdge(
            from_node="acyl_coa_cyto",
            to_node="acyl_carnitine",
            enzyme="CPT-I (Carnitine palmitoyltransferase I)",
            regulation="Inhibited by malonyl-CoA (prevents simultaneous synthesis and oxidation).",
            notes="Rate-limiting step for long-chain fatty acid entry into mitochondria."
        ))
        p.add_edge(ReactionEdge(
            from_node="acyl_carnitine",
            to_node="acyl_coa_mito",
            enzyme="CACT + CPT-II",
            notes="Translocase moves acyl-carnitine in; CPT-II reforms acyl-CoA in the matrix."
        ))
        p.add_edge(ReactionEdge(
            from_node="acyl_coa_mito",
            to_node="enoyl_coa",
            enzyme="Acyl-CoA dehydrogenase (ACAD)",
            fadh2_cost=-1,
            notes="First step of the spiral. Produces FADH₂. Different isoforms for different chain lengths."
        ))
        p.add_edge(ReactionEdge(
            from_node="enoyl_coa",
            to_node="hydroxyacyl_coa",
            enzyme="Enoyl-CoA hydratase",
            notes="Hydration across the double bond."
        ))
        p.add_edge(ReactionEdge(
            from_node="hydroxyacyl_coa",
            to_node="ketoacyl_coa",
            enzyme="3-Hydroxyacyl-CoA dehydrogenase",
            nadh_cost=-1,
            notes="Second dehydrogenation. Produces NADH."
        ))
        p.add_edge(ReactionEdge(
            from_node="ketoacyl_coa",
            to_node="acetyl_coa",
            enzyme="Thiolase (3-ketoacyl-CoA thiolase)",
            notes="Cleaves off one acetyl-CoA. The remaining acyl-CoA is two carbons shorter and re-enters the spiral."
        ))
        p.add_edge(ReactionEdge(
            from_node="ketoacyl_coa",
            to_node="shorter_acyl_coa",
            enzyme="Thiolase",
            notes="The shortened acyl-CoA continues β-oxidation until only acetyl-CoA remains."
        ))

        self.register(p)


def get_beta_oxidation_registry() -> BetaOxidationRegistry:
    return BetaOxidationRegistry()


if __name__ == "__main__":
    reg = get_beta_oxidation_registry()
    path = reg.get("beta_oxidation")
    print("=" * 65)
    print("β-OXIDATION OF FATTY ACIDS")
    print("=" * 65)
    print(path.description)
    print()
    s = path.summary()
    print(f"Nodes: {s['nodes']}  |  Edges: {s['edges']}")
    print(f"Per cycle: {s['per_cycle']}")
    print(f"Activation cost: {s['activation_cost']}")
    print()
    print("Key control point: CPT-I (inhibited by malonyl-CoA)")
    print("Each spiral shortens the chain by 2 carbons and feeds acetyl-CoA to the TCA cycle.")
