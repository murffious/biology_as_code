"""
urea_cycle.py
=================================================================
Urea Cycle (Ornithine Cycle)

Disposes of excess nitrogen as urea.
Occurs primarily in the liver.
Costs 4 ATP equivalents per urea molecule formed.
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
    location: str = ""          # mitochondrial or cytosolic
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

    def atp_cost_total(self) -> int:
        """ATP equivalents spent per turn, summed from the edges.

        Co-substrate edges (a second reactant entering the same reaction) carry
        atp_cost=0 so the cost is counted once per reaction, not once per edge.
        """
        return abs(sum(e.atp_cost for e in self.edges))

    def orphan_nodes(self) -> list[str]:
        """Declared nodes that no edge touches — a node here means the prose
        describes biology the graph does not contain."""
        touched = {n for e in self.edges for n in (e.from_node, e.to_node)}
        return sorted(set(self.nodes) - touched)

    def summary(self) -> dict:
        return {
            "name": self.name,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "atp_per_urea": self.atp_cost_total(),
            "main_site": "Liver",
        }


class UreaCycleRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="urea_cycle",
            description=(
                "Urea Cycle (Ornithine Cycle). Converts toxic ammonia into urea "
                "for safe excretion. Occurs mainly in the liver. Costs ~4 ATP equivalents per urea."
            )
        )

        # Nodes
        p.add_node(MetaboliteNode("nh4", "Ammonia (NH₄⁺)", PathwayNodeType.SUBSTRATE,
            "Toxic nitrogen waste from amino acid catabolism."))
        p.add_node(MetaboliteNode("co2", "CO₂ / HCO₃⁻", PathwayNodeType.SUBSTRATE,
            "Source of the carbon atom in urea. Hydrated to bicarbonate before CPS1 uses it."))
        p.add_node(MetaboliteNode("carbamoyl_phosphate", "Carbamoyl Phosphate", PathwayNodeType.INTERMEDIATE,
            "Formed in mitochondria. First committed intermediate."))
        p.add_node(MetaboliteNode("ornithine", "Ornithine", PathwayNodeType.INTERMEDIATE,
            "Carrier molecule that is regenerated each turn."))
        p.add_node(MetaboliteNode("citrulline", "Citrulline", PathwayNodeType.INTERMEDIATE,
            "Exported from mitochondria to cytosol."))
        p.add_node(MetaboliteNode("aspartate", "Aspartate", PathwayNodeType.SUBSTRATE,
            "Donates the second nitrogen atom."))
        p.add_node(MetaboliteNode("argininosuccinate", "Argininosuccinate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("arginine", "Arginine", PathwayNodeType.INTERMEDIATE,
            "Immediate precursor of urea."))
        p.add_node(MetaboliteNode("fumarate", "Fumarate", PathwayNodeType.PRODUCT,
            "Released when argininosuccinate is cleaved. Links to TCA cycle."))
        p.add_node(MetaboliteNode("urea", "Urea", PathwayNodeType.PRODUCT,
            "Non-toxic nitrogen waste excreted by the kidney."))

        # Edges
        p.add_edge(ReactionEdge(
            from_node="nh4",
            to_node="carbamoyl_phosphate",
            enzyme="Carbamoyl phosphate synthetase I (CPS1)",
            atp_cost=-2,
            location="Mitochondria",
            regulation="Activated by N-acetylglutamate (NAG). Rate-limiting step.",
            notes="Requires 2 ATP. Most important regulatory enzyme of the urea cycle."
        ))
        p.add_edge(ReactionEdge(
            from_node="co2",
            to_node="carbamoyl_phosphate",
            enzyme="Carbamoyl phosphate synthetase I (CPS1)",
            atp_cost=0,  # co-substrate of the CPS1 edge above; cost counted there
            location="Mitochondria",
            notes="Bicarbonate is the carbon donor. Contributes the carbonyl carbon of urea."
        ))
        p.add_edge(ReactionEdge(
            from_node="carbamoyl_phosphate",
            to_node="citrulline",
            enzyme="Ornithine transcarbamoylase (OTC)",
            location="Mitochondria",
            notes="Transfers carbamoyl group to ornithine. Citrulline is then exported to cytosol."
        ))
        p.add_edge(ReactionEdge(
            from_node="citrulline",
            to_node="argininosuccinate",
            enzyme="Argininosuccinate synthetase",
            atp_cost=-2,  # ATP → AMP + PPi is 2 high-energy equivalents
            location="Cytosol",
            notes="Condenses citrulline with aspartate. Costs 2 ATP equivalents."
        ))
        p.add_edge(ReactionEdge(
            from_node="aspartate",
            to_node="argininosuccinate",
            enzyme="Argininosuccinate synthetase",
            atp_cost=0,  # co-substrate of the ARGSS edge above; cost counted there
            location="Cytosol",
            notes="Donates the second nitrogen atom of urea."
        ))
        p.add_edge(ReactionEdge(
            from_node="argininosuccinate",
            to_node="arginine",
            enzyme="Argininosuccinate lyase",
            location="Cytosol",
            notes="Cleaves argininosuccinate into arginine + fumarate."
        ))
        p.add_edge(ReactionEdge(
            from_node="argininosuccinate",
            to_node="fumarate",
            enzyme="Argininosuccinate lyase",
            location="Cytosol",
            notes="Second product of the lyase step. Carries the cycle's carbon skeleton "
                  "into the TCA cycle, where it is reoxidised to oxaloacetate and "
                  "transaminated back to aspartate."
        ))
        p.add_edge(ReactionEdge(
            from_node="arginine",
            to_node="urea",
            enzyme="Arginase",
            location="Cytosol",
            notes="Hydrolyzes arginine to urea + ornithine. Ornithine re-enters mitochondria."
        ))
        p.add_edge(ReactionEdge(
            from_node="arginine",
            to_node="ornithine",
            enzyme="Arginase",
            location="Cytosol",
            notes="Ornithine is regenerated and returns to the mitochondria to continue the cycle."
        ))

        self.register(p)


def get_urea_cycle_registry() -> UreaCycleRegistry:
    return UreaCycleRegistry()


if __name__ == "__main__":
    reg = get_urea_cycle_registry()
    path = reg.get("urea_cycle")
    print("=" * 60)
    print("UREA CYCLE")
    print("=" * 60)
    print(path.description)
    print()
    print(path.summary())
    print()
    print("Key points:")
    print("  • Rate-limiting enzyme: CPS1 (activated by N-acetylglutamate)")
    print("  • 2 nitrogen atoms in urea: one from NH₄⁺, one from aspartate")
    print("  • Cost: ~4 ATP equivalents per urea")
    print("  • Fumarate links the urea cycle to the TCA cycle")
