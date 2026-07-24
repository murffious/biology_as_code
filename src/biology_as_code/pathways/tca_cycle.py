"""
tca_cycle.py
=================================================================
Executable graph model of the TCA / Citric Acid Cycle (Krebs Cycle)

Modeled in the same rich annotated style as glycolysis and cholesterol.
Edges formally reference MetabolicMechanism objects by ID.

Key educational points:
  - Amphibolic pathway (both catabolic and anabolic)
  - 3 NADH + 1 FADH₂ + 1 GTP per acetyl-CoA
  - Three irreversible, regulated steps
  - Regenerates oxaloacetate so the cycle can continue
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
    REGULATORY = "regulatory"


@dataclass
class MetaboliteNode:
    id: str
    name: str
    node_type: PathwayNodeType
    notes: str = ""


@dataclass
class ReactionEdge:
    """Directed reaction with formal link to a MetabolicMechanism."""
    from_node: str
    to_node: str
    mechanism_id: str = ""
    enzyme: str = ""
    nadh_cost: int = 0          # negative = produced
    fadh2_cost: int = 0         # negative = produced
    gtp_cost: int = 0           # positive = produced (substrate-level)
    co2_produced: int = 0
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
        reg = get_metabolic_mechanism_registry()
        return reg.get(edge.mechanism_id)

    def summary(self) -> dict:
        # Per acetyl-CoA (one turn of the cycle)
        return {
            "name": self.name,
            "description": self.description,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "nadh_per_acetyl_coa": 3,
            "fadh2_per_acetyl_coa": 1,
            "gtp_per_acetyl_coa": 1,
            "approx_atp_equivalents": 10,  # classic textbook approximation
        }


class TCACycleRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_tca_cycle()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    def _build_tca_cycle(self) -> None:
        """
        Classic TCA / Citric Acid Cycle (Krebs Cycle).

        One turn oxidizes one acetyl-CoA to two CO₂ and regenerates
        oxaloacetate. Energy captured as 3 NADH + 1 FADH₂ + 1 GTP.
        """
        p = MetabolicPathway(
            name="tca_cycle",
            description=(
                "TCA / Citric Acid Cycle (Krebs Cycle). "
                "Central amphibolic pathway that oxidizes acetyl-CoA to CO₂ "
                "while generating reducing equivalents (NADH, FADH₂) and one GTP. "
                "Edges are formally linked to MetabolicMechanism objects."
            )
        )

        # ------------------------------------------------------------------
        # NODES
        # ------------------------------------------------------------------
        p.add_node(MetaboliteNode(
            "acetyl_coa", "Acetyl-CoA", PathwayNodeType.SUBSTRATE,
            "Two-carbon unit entering the cycle. Comes from pyruvate (PDH), β-oxidation, or ketogenic amino acids."
        ))
        p.add_node(MetaboliteNode(
            "oxaloacetate", "Oxaloacetate", PathwayNodeType.INTERMEDIATE,
            "Four-carbon acceptor that is regenerated each turn. Also an important anaplerotic / gluconeogenic intermediate."
        ))
        p.add_node(MetaboliteNode(
            "citrate", "Citrate", PathwayNodeType.INTERMEDIATE,
            "Six-carbon product of the first condensation. Can also signal high energy and inhibit glycolysis (PFK-1)."
        ))
        p.add_node(MetaboliteNode(
            "isocitrate", "Isocitrate", PathwayNodeType.INTERMEDIATE,
            "Isomer of citrate. Substrate for the first oxidative decarboxylation."
        ))
        p.add_node(MetaboliteNode(
            "alpha_ketoglutarate", "α-Ketoglutarate", PathwayNodeType.INTERMEDIATE,
            "Five-carbon intermediate. Important precursor for glutamate and other amino acids (amphibolic)."
        ))
        p.add_node(MetaboliteNode(
            "succinyl_coa", "Succinyl-CoA", PathwayNodeType.INTERMEDIATE,
            "High-energy thioester. Precursor for porphyrins / heme. Also regulates its own production."
        ))
        p.add_node(MetaboliteNode(
            "succinate", "Succinate", PathwayNodeType.INTERMEDIATE,
            "Four-carbon intermediate. Substrate of the only membrane-bound TCA enzyme (Complex II)."
        ))
        p.add_node(MetaboliteNode(
            "fumarate", "Fumarate", PathwayNodeType.INTERMEDIATE,
            "Four-carbon unsaturated intermediate."
        ))
        p.add_node(MetaboliteNode(
            "malate", "Malate", PathwayNodeType.INTERMEDIATE,
            "Four-carbon intermediate. Can also be exported for gluconeogenesis (malate-aspartate shuttle)."
        ))

        # ------------------------------------------------------------------
        # EDGES (8 classic steps) – with formal mechanism links
        # ------------------------------------------------------------------

        # 1. Citrate synthase
        p.add_edge(ReactionEdge(
            from_node="acetyl_coa",
            to_node="citrate",
            mechanism_id="citrate_synthase",
            enzyme="Citrate synthase",
            regulation="Inhibited by ATP, NADH, succinyl-CoA, and citrate itself.",
            notes=(
                "Condenses the 2-carbon acetyl group with 4-carbon oxaloacetate. "
                "Highly exergonic / irreversible. Commits acetyl-CoA to the cycle."
            )
        ))

        # Note: the reaction is acetyl-CoA + oxaloacetate → citrate
        # We model the main carbon flow from acetyl-CoA; oxaloacetate is regenerated.

        # 2. Aconitase
        p.add_edge(ReactionEdge(
            from_node="citrate",
            to_node="isocitrate",
            mechanism_id="aconitase",
            enzyme="Aconitase",
            notes="Isomerization via cis-aconitate. Iron-sulfur cluster enzyme."
        ))

        # 3. Isocitrate dehydrogenase (major control point)
        p.add_edge(ReactionEdge(
            from_node="isocitrate",
            to_node="alpha_ketoglutarate",
            mechanism_id="isocitrate_dehydrogenase",
            enzyme="Isocitrate dehydrogenase",
            nadh_cost=-1,
            co2_produced=1,
            regulation=(
                "MAJOR CONTROL POINT. Activated by ADP. "
                "Inhibited by ATP and NADH. Matches cycle flux to energy demand."
            ),
            notes="First oxidative decarboxylation. Produces NADH and releases the first CO₂."
        ))

        # 4. α-Ketoglutarate dehydrogenase complex
        p.add_edge(ReactionEdge(
            from_node="alpha_ketoglutarate",
            to_node="succinyl_coa",
            mechanism_id="alpha_ketoglutarate_dehydrogenase",
            enzyme="α-Ketoglutarate dehydrogenase complex",
            nadh_cost=-1,
            co2_produced=1,
            regulation=(
                "Inhibited by succinyl-CoA, NADH, and high energy charge. "
                "Mechanistically similar to the pyruvate dehydrogenase complex."
            ),
            notes="Second oxidative decarboxylation. Produces NADH and the second CO₂. Irreversible."
        ))

        # 5. Succinyl-CoA synthetase (substrate-level phosphorylation)
        p.add_edge(ReactionEdge(
            from_node="succinyl_coa",
            to_node="succinate",
            mechanism_id="succinyl_coa_synthetase",
            enzyme="Succinyl-CoA synthetase",
            gtp_cost=1,
            notes=(
                "Only substrate-level phosphorylation in the TCA cycle. "
                "Produces GTP (which can be converted to ATP). High-energy thioester is used."
            )
        ))

        # 6. Succinate dehydrogenase (also Complex II)
        p.add_edge(ReactionEdge(
            from_node="succinate",
            to_node="fumarate",
            mechanism_id="succinate_dehydrogenase",
            enzyme="Succinate dehydrogenase",
            fadh2_cost=-1,
            notes=(
                "Only membrane-bound TCA enzyme. Functions as Complex II of the electron transport chain. "
                "Produces FADH₂ instead of NADH."
            )
        ))

        # 7. Fumarase
        p.add_edge(ReactionEdge(
            from_node="fumarate",
            to_node="malate",
            mechanism_id="fumarase",
            enzyme="Fumarase",
            notes="Hydration reaction. Reversible and near equilibrium."
        ))

        # 8. Malate dehydrogenase (regenerates oxaloacetate)
        p.add_edge(ReactionEdge(
            from_node="malate",
            to_node="oxaloacetate",
            mechanism_id="malate_dehydrogenase",
            enzyme="Malate dehydrogenase",
            nadh_cost=-1,
            notes=(
                "Regenerates oxaloacetate so the cycle can continue. "
                "Highly endergonic; pulled forward by continuous use of oxaloacetate by citrate synthase. "
                "Produces the third NADH."
            )
        ))

        self.register(p)


def get_tca_cycle_registry() -> TCACycleRegistry:
    return TCACycleRegistry()


if __name__ == "__main__":
    reg = get_tca_cycle_registry()
    tca = reg.get("tca_cycle")

    print("=" * 65)
    print("TCA / CITRIC ACID CYCLE – WITH FORMAL MECHANISM LINKS")
    print("=" * 65)
    print(tca.description)
    print()
    s = tca.summary()
    print(f"Nodes: {s['nodes']}  |  Edges: {s['edges']}")
    print(f"Per acetyl-CoA: {s['nadh_per_acetyl_coa']} NADH + {s['fadh2_per_acetyl_coa']} FADH₂ + {s['gtp_per_acetyl_coa']} GTP")
    print(f"Approximate ATP equivalents: ~{s['approx_atp_equivalents']}")
    print()

    print("Formally linked mechanisms:")
    for edge in tca.edges:
        if edge.mechanism_id:
            mech = tca.get_mechanism(edge)
            print(f"  {edge.from_node:20} → {edge.to_node:20}  [{edge.mechanism_id}]")
            if mech:
                print(f"      {mech.name}")

    print()
    print("Key regulatory (irreversible) steps:")
    print("  1. Citrate synthase")
    print("  2. Isocitrate dehydrogenase   ← major control point")
    print("  3. α-Ketoglutarate dehydrogenase complex")
    print()
    print("The cycle is amphibolic: it is both catabolic (energy) and anabolic")
    print("(provides precursors for gluconeogenesis, amino acids, porphyrins, etc.).")
