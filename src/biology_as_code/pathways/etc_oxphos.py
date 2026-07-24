"""
etc_oxphos.py
=================================================================
Electron Transport Chain + Oxidative Phosphorylation

Models the mitochondrial electron transport chain (Complexes I–IV)
and ATP synthase (Complex V / oxidative phosphorylation).

Energy yield (classic textbook approximation):
  ~2.5 ATP per NADH
  ~1.5 ATP per FADH₂
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
    COMPLEX = "complex"
    PRODUCT = "product"
    CARRIER = "carrier"


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
    enzyme_or_complex: str = ""
    protons_pumped: int = 0
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
            "atp_per_nadh": 2.5,
            "atp_per_fadh2": 1.5,
        }


class ETCOXPHOSRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="etc_oxphos",
            description=(
                "Electron Transport Chain + Oxidative Phosphorylation. "
                "Electrons from NADH and FADH₂ flow through Complexes I–IV, "
                "creating a proton gradient that drives ATP synthesis via ATP synthase."
            )
        )

        # Nodes
        p.add_node(MetaboliteNode("nadh", "NADH", PathwayNodeType.SUBSTRATE,
            "Primary electron donor from TCA, β-oxidation, PDH, etc."))
        p.add_node(MetaboliteNode("fadh2", "FADH₂", PathwayNodeType.SUBSTRATE,
            "Electron donor from succinate dehydrogenase (Complex II) and acyl-CoA dehydrogenase."))
        p.add_node(MetaboliteNode("complex_i", "Complex I (NADH Dehydrogenase)", PathwayNodeType.COMPLEX,
            "Accepts electrons from NADH, pumps 4 H⁺."))
        p.add_node(MetaboliteNode("complex_ii", "Complex II (Succinate Dehydrogenase)", PathwayNodeType.COMPLEX,
            "Accepts electrons from FADH₂ / succinate. Does NOT pump protons."))
        p.add_node(MetaboliteNode("coq", "Coenzyme Q (Ubiquinone)", PathwayNodeType.CARRIER,
            "Mobile lipid-soluble carrier. Accepts electrons from I and II."))
        p.add_node(MetaboliteNode("complex_iii", "Complex III (Cytochrome bc₁)", PathwayNodeType.COMPLEX,
            "Transfers electrons from QH₂ to cytochrome c. Pumps 4 H⁺ (Q-cycle)."))
        p.add_node(MetaboliteNode("cyt_c", "Cytochrome c", PathwayNodeType.CARRIER,
            "Mobile peripheral membrane protein. Carries one electron at a time."))
        p.add_node(MetaboliteNode("complex_iv", "Complex IV (Cytochrome c Oxidase)", PathwayNodeType.COMPLEX,
            "Transfers electrons to O₂, forming H₂O. Pumps 2 H⁺."))
        p.add_node(MetaboliteNode("o2", "O₂", PathwayNodeType.SUBSTRATE, "Final electron acceptor."))
        p.add_node(MetaboliteNode("h2o", "H₂O", PathwayNodeType.PRODUCT, "Product of Complex IV."))
        p.add_node(MetaboliteNode("proton_gradient", "Proton Gradient (Δp)", PathwayNodeType.INTERMEDIATE,
            "Electrochemical gradient across the inner mitochondrial membrane (intermembrane space positive/acidic)."))
        p.add_node(MetaboliteNode("atp_synthase", "ATP Synthase (Complex V)", PathwayNodeType.COMPLEX,
            "Uses the proton-motive force to drive ATP synthesis from ADP + Pi."))
        p.add_node(MetaboliteNode("atp", "ATP", PathwayNodeType.PRODUCT, "Final energy currency produced."))

        # Electron flow edges
        p.add_edge(ReactionEdge(
            from_node="nadh", to_node="complex_i",
            enzyme_or_complex="Complex I",
            protons_pumped=4,
            notes="NADH donates 2 electrons. 4 protons pumped to intermembrane space."
        ))
        p.add_edge(ReactionEdge(
            from_node="complex_i", to_node="coq",
            enzyme_or_complex="Complex I → CoQ",
            notes="Electrons transferred to ubiquinone, forming ubiquinol (QH₂)."
        ))
        p.add_edge(ReactionEdge(
            from_node="fadh2", to_node="complex_ii",
            enzyme_or_complex="Complex II",
            protons_pumped=0,
            notes="FADH₂ / succinate electrons enter here. No protons pumped at Complex II."
        ))
        p.add_edge(ReactionEdge(
            from_node="complex_ii", to_node="coq",
            enzyme_or_complex="Complex II → CoQ",
            notes="Electrons from FADH₂ also reduce CoQ."
        ))
        p.add_edge(ReactionEdge(
            from_node="coq", to_node="complex_iii",
            enzyme_or_complex="Complex III (Q-cycle)",
            protons_pumped=4,
            notes="Q-cycle results in 4 protons translocated per 2 electrons."
        ))
        p.add_edge(ReactionEdge(
            from_node="complex_iii", to_node="cyt_c",
            enzyme_or_complex="Complex III → Cyt c",
            notes="One electron at a time is passed to cytochrome c."
        ))
        p.add_edge(ReactionEdge(
            from_node="cyt_c", to_node="complex_iv",
            enzyme_or_complex="Cytochrome c → Complex IV",
            notes="Cyt c delivers electrons to Complex IV."
        ))
        p.add_edge(ReactionEdge(
            from_node="complex_iv", to_node="h2o",
            enzyme_or_complex="Complex IV",
            protons_pumped=2,
            notes="4 electrons + 4 H⁺ + O₂ → 2 H₂O. 2 protons pumped."
        ))
        p.add_edge(ReactionEdge(
            from_node="proton_gradient", to_node="atp_synthase",
            enzyme_or_complex="ATP Synthase (Complex V)",
            notes="Protons flow back into the matrix through ATP synthase, driving ATP synthesis (chemiosmosis)."
        ))
        p.add_edge(ReactionEdge(
            from_node="atp_synthase", to_node="atp",
            enzyme_or_complex="ATP Synthase",
            notes="ADP + Pi → ATP. Approximate yield: 2.5 ATP per NADH, 1.5 ATP per FADH₂."
        ))

        self.register(p)


def get_etc_oxphos_registry() -> ETCOXPHOSRegistry:
    return ETCOXPHOSRegistry()


if __name__ == "__main__":
    reg = get_etc_oxphos_registry()
    etc = reg.get("etc_oxphos")
    print("=" * 65)
    print("ELECTRON TRANSPORT CHAIN + OXIDATIVE PHOSPHORYLATION")
    print("=" * 65)
    print(etc.description)
    print()
    s = etc.summary()
    print(f"Nodes: {s['nodes']}  |  Edges: {s['edges']}")
    print(f"Approx ATP yield: {s['atp_per_nadh']} per NADH, {s['atp_per_fadh2']} per FADH₂")
    print()
    print("Key complexes: I → Q → III → Cyt c → IV → O₂")
    print("               II → Q (no proton pumping)")
    print("Proton gradient drives ATP synthase (Complex V)")
