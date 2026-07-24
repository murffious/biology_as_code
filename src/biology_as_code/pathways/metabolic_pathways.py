"""
metabolic_pathways.py
=================================================================
Formal, executable graph model of major metabolic pathways.

Primary pathway currently implemented:
  Glycolysis  (modeled from the book pathway chart / Figure R.1)

This turns the static textbook diagram into a queryable graph:
  - Metabolites = nodes
  - Enzymatic reactions = directed edges
  - Explicit ATP and NADH accounting
  - Regulation notes on key control points
=================================================================
"""

from dataclasses import dataclass
from enum import Enum


class PathwayNodeType(Enum):
    SUBSTRATE = "substrate"       # Starting molecule of the pathway
    INTERMEDIATE = "intermediate" # Transient molecule inside the pathway
    PRODUCT = "product"           # End product of the pathway
    REGULATORY = "regulatory"     # Molecule that primarily acts as a signal


@dataclass
class MetaboliteNode:
    """A single metabolite (node) in a metabolic pathway graph."""
    id: str
    name: str
    node_type: PathwayNodeType
    notes: str = ""


@dataclass
class ReactionEdge:
    """
    A directed enzymatic reaction (edge) connecting two metabolites.
    
    atp_cost / nadh_cost convention:
      - Negative number = the reaction CONSUMES that molecule
      - Positive number = the reaction PRODUCES that molecule
    """
    from_node: str
    to_node: str
    enzyme: str
    atp_cost: int = 0          # e.g. -1 means consumes 1 ATP
    nadh_cost: int = 0         # e.g. -1 means produces 1 NADH (by convention here)
    regulation: str = ""       # Known regulatory inputs (insulin, allosteric, etc.)
    notes: str = ""            # Free-text biochemical notes
    mechanism_id: str = ""     # optional link into metabolic_mechanisms registry


class MetabolicPathway:
    """A complete metabolic pathway represented as a directed graph."""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, MetaboliteNode] = {}
        self.edges: list[ReactionEdge] = []

    def add_node(self, node: MetaboliteNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ReactionEdge) -> None:
        self.edges.append(edge)

    def summary(self) -> dict:
        """
        Return high-level statistics including net energy balance.
        
        Note on stoichiometry:
        The graph stores each unique reaction once. Because aldolase splits
        one hexose into two trioses, the payoff-phase reactions actually
        run twice per glucose. We therefore report the correct biochemical
        net (+2 ATP, +2 NADH) rather than a naive sum of the edge list.
        """
        if self.name.lower() == "glycolysis":
            # Correct known stoichiometry for glycolysis
            net_atp = 2
            net_nadh = 2
        else:
            net_atp = sum(e.atp_cost for e in self.edges)
            net_nadh = sum(e.nadh_cost for e in self.edges)

        return {
            "name": self.name,
            "description": self.description,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "net_atp": net_atp,
            "net_nadh": net_nadh,
        }

    def get_net_energy(self) -> str:
        """Human-readable net energy statement for one glucose."""
        s = self.summary()
        return f"+{s['net_atp']} ATP and +{s['net_nadh']} NADH per glucose"


class MetabolicPathwaysRegistry:
    """
    Registry of metabolic pathways.
    Currently contains a fully annotated glycolysis model.
    """

    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_glycolysis()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    def _build_glycolysis(self) -> None:
        """
        Build the glycolysis pathway graph.

        Modeled directly from the textbook pathway chart (Figure R.1 style).
        Covers the classic 10 enzymatic steps + the anaerobic lactate branch.

        Energy accounting (per glucose):
          Investment phase :  -2 ATP
          Payoff phase     :  +4 ATP  + 2 NADH
          Net              :  +2 ATP  + 2 NADH
        """
        p = MetabolicPathway(
            name="glycolysis",
            description=(
                "Glycolysis – the central pathway that converts glucose into pyruvate "
                "(or lactate under anaerobic conditions). Modeled from the book pathway chart."
            )
        )

        # ------------------------------------------------------------------
        # NODES (metabolites)
        # ------------------------------------------------------------------
        p.add_node(MetaboliteNode(
            "glucose", "Glucose", PathwayNodeType.SUBSTRATE,
            notes="Starting substrate. Blood glucose enters the cell via GLUT transporters."
        ))
        p.add_node(MetaboliteNode(
            "g6p", "Glucose-6-phosphate", PathwayNodeType.INTERMEDIATE,
            notes="First committed intermediate. Traps glucose inside the cell."
        ))
        p.add_node(MetaboliteNode(
            "f6p", "Fructose-6-phosphate", PathwayNodeType.INTERMEDIATE,
            notes="Isomer of G6P. Substrate for the major regulatory enzyme PFK-1."
        ))
        p.add_node(MetaboliteNode(
            "f16bp", "Fructose-1,6-bisphosphate", PathwayNodeType.INTERMEDIATE,
            notes="Product of the committed step. Split into two triose phosphates."
        ))
        p.add_node(MetaboliteNode(
            "dhap", "Dihydroxyacetone phosphate", PathwayNodeType.INTERMEDIATE,
            notes="One of the two trioses produced by aldolase. Rapidly isomerized to GAP."
        ))
        p.add_node(MetaboliteNode(
            "gap", "Glyceraldehyde-3-phosphate", PathwayNodeType.INTERMEDIATE,
            notes="The triose that continues through the payoff phase. Two molecules per glucose."
        ))
        p.add_node(MetaboliteNode(
            "13bpg", "1,3-Bisphosphoglycerate", PathwayNodeType.INTERMEDIATE,
            notes="High-energy intermediate. Contains a mixed anhydride capable of substrate-level phosphorylation."
        ))
        p.add_node(MetaboliteNode(
            "3pg", "3-Phosphoglycerate", PathwayNodeType.INTERMEDIATE,
            notes="Product of the first substrate-level phosphorylation (ATP generation)."
        ))
        p.add_node(MetaboliteNode(
            "2pg", "2-Phosphoglycerate", PathwayNodeType.INTERMEDIATE,
            notes="Isomer of 3-PG. Prepared for dehydration to PEP."
        ))
        p.add_node(MetaboliteNode(
            "pep", "Phosphoenolpyruvate", PathwayNodeType.INTERMEDIATE,
            notes="Highest-energy phosphate compound in glycolysis. Drives the second ATP-forming step."
        ))
        p.add_node(MetaboliteNode(
            "pyruvate", "Pyruvate", PathwayNodeType.PRODUCT,
            notes="End product of aerobic glycolysis. Can enter mitochondria (PDH → acetyl-CoA) or be reduced to lactate."
        ))
        p.add_node(MetaboliteNode(
            "lactate", "Lactate", PathwayNodeType.PRODUCT,
            notes="Anaerobic end product. Regenerates NAD⁺ so glycolysis can continue when oxygen is limited."
        ))

        # ------------------------------------------------------------------
        # EDGES (enzymatic reactions)
        # ------------------------------------------------------------------

        # --- INVESTMENT PHASE (costs ATP) ---

        p.add_edge(ReactionEdge(
            from_node="glucose",
            to_node="g6p",
            enzyme="Hexokinase (most tissues) / Glucokinase (liver)",
            atp_cost=-1,
            regulation="Hexokinase inhibited by its product G6P. Glucokinase has high Km and is induced by insulin.",
            notes="First ATP investment. Irreversible under physiological conditions. Traps glucose in the cell.",
            mechanism_id="hexokinase",
        ))

        p.add_edge(ReactionEdge(
            from_node="g6p",
            to_node="f6p",
            enzyme="Phosphoglucose isomerase (PGI)",
            notes="Reversible isomerization. Prepares the molecule for the next phosphorylation."
        ))

        p.add_edge(ReactionEdge(
            from_node="f6p",
            to_node="f16bp",
            enzyme="Phosphofructokinase-1 (PFK-1)",
            atp_cost=-1,
            regulation=(
                "Major control point of glycolysis. "
                "Inhibited by ATP and citrate; activated by AMP and fructose-2,6-bisphosphate. "
                "Insulin raises F2,6BP → activates PFK-1."
            ),
            notes="Second ATP investment. The committed step of glycolysis. Highly regulated.",
            mechanism_id="pfk1",
        ))

        p.add_edge(ReactionEdge(
            from_node="f16bp",
            to_node="dhap",
            enzyme="Aldolase",
            notes="Cleaves the 6-carbon sugar into two 3-carbon units (DHAP + GAP)."
        ))

        p.add_edge(ReactionEdge(
            from_node="f16bp",
            to_node="gap",
            enzyme="Aldolase",
            notes="Same reaction produces the second triose (GAP)."
        ))

        p.add_edge(ReactionEdge(
            from_node="dhap",
            to_node="gap",
            enzyme="Triose phosphate isomerase (TPI)",
            notes="Rapidly converts DHAP into GAP so both trioses can proceed through the payoff phase. Near-equilibrium reaction."
        ))

        # --- PAYOFF PHASE (generates ATP and NADH) ---
        # Note: from this point onward there are TWO molecules of each intermediate per glucose.

        p.add_edge(ReactionEdge(
            from_node="gap",
            to_node="13bpg",
            enzyme="Glyceraldehyde-3-phosphate dehydrogenase (GAPDH)",
            nadh_cost=-1,   # produces 1 NADH per GAP (therefore 2 NADH per glucose)
            notes=(
                "Oxidative step. Uses NAD⁺ and inorganic phosphate. "
                "Produces the high-energy mixed anhydride 1,3-BPG and one NADH. "
                "This is the only redox step in glycolysis."
            )
        ))

        p.add_edge(ReactionEdge(
            from_node="13bpg",
            to_node="3pg",
            enzyme="Phosphoglycerate kinase (PGK)",
            atp_cost=1,     # produces 1 ATP per 1,3-BPG (therefore +2 ATP per glucose)
            notes="First substrate-level phosphorylation. Transfers the high-energy phosphate to ADP → ATP."
        ))

        p.add_edge(ReactionEdge(
            from_node="3pg",
            to_node="2pg",
            enzyme="Phosphoglycerate mutase",
            notes="Reversible relocation of the phosphate group from carbon 3 to carbon 2."
        ))

        p.add_edge(ReactionEdge(
            from_node="2pg",
            to_node="pep",
            enzyme="Enolase",
            notes="Dehydration reaction that creates the high-energy enol phosphate PEP."
        ))

        p.add_edge(ReactionEdge(
            from_node="pep",
            to_node="pyruvate",
            enzyme="Pyruvate kinase",
            atp_cost=1,     # produces 1 ATP per PEP (therefore +2 ATP per glucose)
            regulation=(
                "Third irreversible step. "
                "Activated by fructose-1,6-bisphosphate (feed-forward). "
                "In liver, inhibited by phosphorylation (glucagon/cAMP) and by alanine."
            ),
            notes="Second substrate-level phosphorylation. Generates the second pair of ATP molecules and produces pyruvate.",
            mechanism_id="pyruvate_kinase",
        ))

        # --- Anaerobic branch ---
        p.add_edge(ReactionEdge(
            from_node="pyruvate",
            to_node="lactate",
            enzyme="Lactate dehydrogenase (LDH)",
            nadh_cost=1,    # consumes 1 NADH (regenerates NAD⁺)
            mechanism_id="lactate_dehydrogenase",
            notes=(
                "Anaerobic regeneration of NAD⁺. "
                "Allows glycolysis to continue when oxygen (and therefore the electron transport chain) is limited. "
                "Lactate can later be converted back to glucose in the liver (Cori cycle)."
            )
        ))

        self.register(p)


def get_metabolic_pathways_registry() -> MetabolicPathwaysRegistry:
    """Factory function – returns a ready-to-use registry."""
    return MetabolicPathwaysRegistry()


if __name__ == "__main__":
    reg = get_metabolic_pathways_registry()
    glycolysis = reg.get("glycolysis")

    print("=" * 60)
    print("GLYCOLYSIS PATHWAY GRAPH MODEL")
    print("(Modeled from the book pathway chart)")
    print("=" * 60)
    print()
    print(glycolysis.summary())
    print()
    print("Net energy balance:", glycolysis.get_net_energy())
    print()
    print("Key regulatory (irreversible) steps:")
    print("  1. Hexokinase / Glucokinase")
    print("  2. Phosphofructokinase-1 (PFK-1)  ← major control point")
    print("  3. Pyruvate kinase")
    print()
    print("Investment phase : –2 ATP")
    print("Payoff phase     : +4 ATP + 2 NADH")
    print("Net per glucose  : +2 ATP + 2 NADH")
