"""
fatty_acid_synthesis.py
=================================================================
De Novo Fatty Acid Synthesis (Lipogenesis)

Occurs mainly in the cytosol of liver and adipose tissue.
Primary product is palmitate (C16:0).
Requires NADPH (from pentose phosphate pathway and malic enzyme).
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
    nadph_cost: int = 0
    atp_cost: int = 0
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
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "main_product": "Palmitate (C16:0)",
            "nadph_required": "14 per palmitate",
            "atp_required": "7 per palmitate",
        }


class FattyAcidSynthesisRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="fatty_acid_synthesis",
            description=(
                "De novo fatty acid synthesis. Cytosolic pathway that builds palmitate "
                "from acetyl-CoA. Requires NADPH and is highly regulated at ACC."
            )
        )

        p.add_node(MetaboliteNode("acetyl_coa_mito", "Acetyl-CoA (mitochondria)", PathwayNodeType.SUBSTRATE,
            "Cannot cross the inner mitochondrial membrane directly."))
        p.add_node(MetaboliteNode("citrate", "Citrate", PathwayNodeType.INTERMEDIATE,
            "Shuttle form that carries acetyl units to the cytosol."))
        p.add_node(MetaboliteNode("acetyl_coa_cyto", "Acetyl-CoA (cytosol)", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("malonyl_coa", "Malonyl-CoA", PathwayNodeType.INTERMEDIATE,
            "Activated 3-carbon donor. Key regulatory intermediate."))
        p.add_node(MetaboliteNode("acyl_acp", "Growing Acyl-ACP chain", PathwayNodeType.INTERMEDIATE,
            "Attached to Acyl Carrier Protein during synthesis."))
        p.add_node(MetaboliteNode("palmitate", "Palmitate (C16:0)", PathwayNodeType.PRODUCT,
            "Primary end product of mammalian FAS."))

        # Citrate shuttle
        p.add_edge(ReactionEdge(
            from_node="acetyl_coa_mito", to_node="citrate",
            enzyme="Citrate synthase",
            notes="Acetyl-CoA + OAA → Citrate (same as TCA entry). Citrate is exported when energy is high."
        ))
        p.add_edge(ReactionEdge(
            from_node="citrate", to_node="acetyl_coa_cyto",
            enzyme="ATP-citrate lyase",
            atp_cost=-1,
            notes="Cytosolic cleavage of citrate regenerates acetyl-CoA + OAA."
        ))

        # Activation to malonyl-CoA (rate-limiting)
        p.add_edge(ReactionEdge(
            from_node="acetyl_coa_cyto", to_node="malonyl_coa",
            enzyme="Acetyl-CoA carboxylase (ACC)",
            atp_cost=-1,
            regulation=(
                "RATE-LIMITING STEP. Activated by citrate and dephosphorylation (insulin). "
                "Inhibited by palmitoyl-CoA and phosphorylation (AMPK, glucagon)."
            ),
            notes="Requires biotin. Malonyl-CoA also inhibits CPT-I, preventing simultaneous β-oxidation."
        ))

        # FAS complex (repeated cycles)
        p.add_edge(ReactionEdge(
            from_node="malonyl_coa", to_node="acyl_acp",
            enzyme="Fatty Acid Synthase (FAS) complex",
            nadph_cost=-2,  # per 2-carbon addition
            notes=(
                "Multifunctional enzyme. Each cycle: condensation → reduction → dehydration → reduction. "
                "Adds 2 carbons per cycle. Requires 2 NADPH per cycle."
            )
        ))
        p.add_edge(ReactionEdge(
            from_node="acyl_acp", to_node="palmitate",
            enzyme="Thioesterase (part of FAS)",
            notes="Releases free palmitate when the chain reaches 16 carbons."
        ))

        self.register(p)


def get_fatty_acid_synthesis_registry() -> FattyAcidSynthesisRegistry:
    return FattyAcidSynthesisRegistry()


if __name__ == "__main__":
    reg = get_fatty_acid_synthesis_registry()
    path = reg.get("fatty_acid_synthesis")
    print("=" * 60)
    print("DE NOVO FATTY ACID SYNTHESIS")
    print("=" * 60)
    print(path.description)
    print()
    print(path.summary())
    print()
    print("Key regulated enzyme: Acetyl-CoA carboxylase (ACC)")
    print("Malonyl-CoA inhibits CPT-I → coordinates synthesis vs oxidation")
