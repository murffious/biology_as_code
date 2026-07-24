"""
cholesterol_pathway.py
=================================================================
Executable graph model of Cholesterol Biosynthesis + Lipoprotein
Transport

Modeled in the same style as the glycolysis pathway graph.
Based on standard nutritional biochemistry (mevalonate pathway +
lipoprotein metabolism chapters).

Key educational points:
  - HMG-CoA reductase is the rate-limiting and most regulated step
  - This is the primary target of statin drugs
  - Cholesterol is both a membrane component and a precursor for
    bile acids, steroid hormones, and vitamin D
  - Lipoproteins move cholesterol between tissues
=================================================================
"""

from dataclasses import dataclass
from enum import Enum


class PathwayNodeType(Enum):
    SUBSTRATE = "substrate"
    INTERMEDIATE = "intermediate"
    PRODUCT = "product"
    LIPOPROTEIN = "lipoprotein"
    REGULATORY = "regulatory"


@dataclass
class MetaboliteNode:
    """A single metabolite or particle (node) in the pathway graph."""
    id: str
    name: str
    node_type: PathwayNodeType
    notes: str = ""


@dataclass
class ReactionEdge:
    """
    A directed reaction or transport step.
    
    Convention for atp_cost / nadh_cost / nadph_cost:
      Negative = consumed
      Positive = produced
    """
    from_node: str
    to_node: str
    enzyme_or_process: str
    atp_cost: int = 0
    nadph_cost: int = 0
    regulation: str = ""
    notes: str = ""
    mechanism_id: str = ""


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
        return {
            "name": self.name,
            "description": self.description,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
        }


class CholesterolPathwayRegistry:
    """
    Registry containing the cholesterol biosynthesis pathway
    and key lipoprotein transport relationships.
    """

    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_cholesterol_biosynthesis()
        self._build_lipoprotein_transport()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    def _build_cholesterol_biosynthesis(self) -> None:
        """
        Cholesterol biosynthesis via the mevalonate pathway.

        Simplified high-level graph focusing on the major regulatory
        and educationally important steps. Full pathway has >20 enzymatic
        steps; we keep the key control points and intermediates.
        """
        p = MetabolicPathway(
            name="cholesterol_biosynthesis",
            description=(
                "Cholesterol biosynthesis (mevalonate pathway). "
                "Starts from acetyl-CoA and produces cholesterol. "
                "HMG-CoA reductase is the rate-limiting step and primary statin target."
            )
        )

        # ------------------------------------------------------------------
        # NODES
        # ------------------------------------------------------------------
        p.add_node(MetaboliteNode(
            "acetyl_coa", "Acetyl-CoA", PathwayNodeType.SUBSTRATE,
            notes="Starting substrate. Comes from pyruvate (via PDH), fatty acid oxidation, or ketogenic amino acids."
        ))
        p.add_node(MetaboliteNode(
            "acetoacetyl_coa", "Acetoacetyl-CoA", PathwayNodeType.INTERMEDIATE,
            notes="Two-carbon units condensed. Also an intermediate in ketone body synthesis."
        ))
        p.add_node(MetaboliteNode(
            "hmg_coa", "HMG-CoA (3-Hydroxy-3-methylglutaryl-CoA)", PathwayNodeType.INTERMEDIATE,
            notes="Key branch-point intermediate. Can go to ketone bodies (liver mitochondria) or to mevalonate (cytosol) for sterol synthesis."
        ))
        p.add_node(MetaboliteNode(
            "mevalonate", "Mevalonate", PathwayNodeType.INTERMEDIATE,
            notes="First committed intermediate of the sterol pathway. Product of the rate-limiting enzyme."
        ))
        p.add_node(MetaboliteNode(
            "ipp", "Isopentenyl pyrophosphate (IPP)", PathwayNodeType.INTERMEDIATE,
            notes="Five-carbon building block (isoprene unit). Requires 3 ATP equivalents to form from mevalonate."
        ))
        p.add_node(MetaboliteNode(
            "dmap", "Dimethylallyl pyrophosphate (DMAPP)", PathwayNodeType.INTERMEDIATE,
            notes="Isomer of IPP. Condenses with IPP to form longer chains."
        ))
        p.add_node(MetaboliteNode(
            "geranyl_pp", "Geranyl pyrophosphate (C10)", PathwayNodeType.INTERMEDIATE,
            notes="10-carbon intermediate."
        ))
        p.add_node(MetaboliteNode(
            "farnesyl_pp", "Farnesyl pyrophosphate (C15)", PathwayNodeType.INTERMEDIATE,
            notes="15-carbon intermediate. Two molecules condense to form squalene. Also used for protein prenylation."
        ))
        p.add_node(MetaboliteNode(
            "squalene", "Squalene", PathwayNodeType.INTERMEDIATE,
            notes="30-carbon linear hydrocarbon. First dedicated sterol precursor."
        ))
        p.add_node(MetaboliteNode(
            "lanosterol", "Lanosterol", PathwayNodeType.INTERMEDIATE,
            notes="First sterol in the pathway (contains the four-ring steroid nucleus). Undergoes many modifications to become cholesterol."
        ))
        p.add_node(MetaboliteNode(
            "cholesterol", "Cholesterol", PathwayNodeType.PRODUCT,
            notes=(
                "Final product. Essential membrane component, precursor of bile acids, "
                "steroid hormones (cortisol, aldosterone, sex steroids), and vitamin D."
            )
        ))

        # ------------------------------------------------------------------
        # EDGES (key reactions)
        # ------------------------------------------------------------------

        p.add_edge(ReactionEdge(
            from_node="acetyl_coa",
            to_node="acetoacetyl_coa",
            enzyme_or_process="Thiolase (Acetoacetyl-CoA thiolase)",
            notes="Condensation of two acetyl-CoA molecules."
        ))

        p.add_edge(ReactionEdge(
            from_node="acetoacetyl_coa",
            to_node="hmg_coa",
            enzyme_or_process="HMG-CoA synthase",
            notes="Adds a third acetyl-CoA. Occurs in cytosol for sterol synthesis (mitochondrial isoform is for ketogenesis)."
        ))

        p.add_edge(ReactionEdge(
            from_node="hmg_coa",
            to_node="mevalonate",
            enzyme_or_process="HMG-CoA reductase",
            nadph_cost=-2,   # consumes 2 NADPH
            mechanism_id="hmg_coa_reductase",
            regulation=(
                "RATE-LIMITING STEP of cholesterol biosynthesis. "
                "Strongly inhibited by cholesterol, mevalonate-derived products, and statin drugs. "
                "Transcriptionally activated by SREBP-2 when cellular cholesterol is low. "
                "Also regulated by phosphorylation (AMPK inhibits it) and by insulin/glucagon."
            ),
            notes=(
                "Most important regulatory enzyme in the entire pathway. "
                "Primary target of statin medications used to lower LDL cholesterol. "
                "This step commits HMG-CoA to the sterol pathway rather than ketone bodies."
            )
        ))

        p.add_edge(ReactionEdge(
            from_node="mevalonate",
            to_node="ipp",
            enzyme_or_process="Mevalonate kinase + phosphomevalonate kinase + mevalonate diphosphate decarboxylase",
            atp_cost=-3,
            notes="Three ATP-dependent steps convert mevalonate into the activated isoprene unit IPP."
        ))

        p.add_edge(ReactionEdge(
            from_node="ipp",
            to_node="dmap",
            enzyme_or_process="Isopentenyl pyrophosphate isomerase",
            notes="Reversible isomerization to the allylic isomer DMAPP."
        ))

        p.add_edge(ReactionEdge(
            from_node="dmap",
            to_node="geranyl_pp",
            enzyme_or_process="Geranyl pyrophosphate synthase",
            notes="Condensation of DMAPP + IPP → C10 intermediate."
        ))

        p.add_edge(ReactionEdge(
            from_node="geranyl_pp",
            to_node="farnesyl_pp",
            enzyme_or_process="Farnesyl pyrophosphate synthase",
            notes="Adds another IPP to form the C15 intermediate. Farnesyl-PP is also used for protein prenylation."
        ))

        p.add_edge(ReactionEdge(
            from_node="farnesyl_pp",
            to_node="squalene",
            enzyme_or_process="Squalene synthase",
            nadph_cost=-1,
            notes="Head-to-head condensation of two farnesyl-PP molecules. First committed step unique to sterols (vs. other isoprenoids)."
        ))

        p.add_edge(ReactionEdge(
            from_node="squalene",
            to_node="lanosterol",
            enzyme_or_process="Squalene epoxidase + oxidosqualene cyclase",
            notes="Epoxidation and cyclization create the four-ring steroid nucleus (lanosterol)."
        ))

        p.add_edge(ReactionEdge(
            from_node="lanosterol",
            to_node="cholesterol",
            enzyme_or_process="Multiple enzymes (≈19 steps: demethylations, desaturations, isomerizations, reductions)",
            notes=(
                "Complex series of modifications that remove three methyl groups, "
                "reduce double bonds, and rearrange the structure to produce cholesterol. "
                "Many of these steps are also regulated."
            )
        ))

        self.register(p)

    def _build_lipoprotein_transport(self) -> None:
        """
        High-level lipoprotein transport relationships.
        These are not classical enzymatic reactions but are essential
        for understanding how cholesterol moves between tissues.
        """
        p = MetabolicPathway(
            name="lipoprotein_transport",
            description=(
                "Lipoprotein-mediated transport of cholesterol and triglycerides. "
                "VLDL carries cholesterol out of the liver; LDL delivers it to tissues; "
                "HDL performs reverse cholesterol transport back to the liver."
            )
        )

        # Nodes – lipoprotein particles
        p.add_node(MetaboliteNode(
            "chylomicron", "Chylomicron", PathwayNodeType.LIPOPROTEIN,
            notes="Intestine-derived. Carries dietary fat and cholesterol. ApoB-48."
        ))
        p.add_node(MetaboliteNode(
            "vldl", "VLDL (Very Low Density Lipoprotein)", PathwayNodeType.LIPOPROTEIN,
            notes="Liver-derived. Carries endogenously synthesized triglycerides and cholesterol. ApoB-100."
        ))
        p.add_node(MetaboliteNode(
            "idl", "IDL (Intermediate Density Lipoprotein)", PathwayNodeType.LIPOPROTEIN,
            notes="Remnant of VLDL after partial triglyceride removal by lipoprotein lipase."
        ))
        p.add_node(MetaboliteNode(
            "ldl", "LDL (Low Density Lipoprotein)", PathwayNodeType.LIPOPROTEIN,
            notes=(
                "Major cholesterol-carrying particle in plasma. "
                "Delivers cholesterol to peripheral tissues via LDL receptor. "
                "Elevated LDL is a major risk factor for atherosclerosis."
            )
        ))
        p.add_node(MetaboliteNode(
            "hdl", "HDL (High Density Lipoprotein)", PathwayNodeType.LIPOPROTEIN,
            notes=(
                "Reverse cholesterol transport particle. "
                "Collects excess cholesterol from peripheral cells and returns it to the liver "
                "(for excretion as bile acids or biliary cholesterol)."
            )
        ))
        p.add_node(MetaboliteNode(
            "peripheral_cell", "Peripheral Cell", PathwayNodeType.PRODUCT,
            notes="Extrahepatic cells that take up LDL cholesterol for membrane synthesis or steroidogenesis."
        ))
        p.add_node(MetaboliteNode(
            "liver", "Liver", PathwayNodeType.PRODUCT,
            notes="Central organ of cholesterol homeostasis. Synthesizes cholesterol, packages it into VLDL, and excretes it via bile."
        ))

        # Transport / conversion edges
        p.add_edge(ReactionEdge(
            from_node="liver",
            to_node="vldl",
            enzyme_or_process="VLDL assembly and secretion",
            notes="Liver packages triglycerides + cholesterol esters + ApoB-100 into VLDL particles."
        ))

        p.add_edge(ReactionEdge(
            from_node="vldl",
            to_node="idl",
            enzyme_or_process="Lipoprotein lipase (LPL) + hepatic lipase",
            notes="Progressive removal of triglycerides converts VLDL → IDL → LDL."
        ))

        p.add_edge(ReactionEdge(
            from_node="idl",
            to_node="ldl",
            enzyme_or_process="Hepatic lipase + further lipolysis",
            notes="Final conversion to the cholesterol-rich LDL particle."
        ))

        p.add_edge(ReactionEdge(
            from_node="ldl",
            to_node="peripheral_cell",
            enzyme_or_process="LDL receptor-mediated endocytosis",
            regulation="LDL receptor expression is down-regulated by high cellular cholesterol (SREBP pathway).",
            notes="Primary route of cholesterol delivery to extrahepatic tissues. Defects in this receptor cause familial hypercholesterolemia."
        ))

        p.add_edge(ReactionEdge(
            from_node="peripheral_cell",
            to_node="hdl",
            enzyme_or_process="ABCA1 / ABCG1 transporters + LCAT",
            notes="Reverse cholesterol transport begins. Free cholesterol is transferred to nascent HDL and esterified by LCAT."
        ))

        p.add_edge(ReactionEdge(
            from_node="hdl",
            to_node="liver",
            enzyme_or_process="SR-BI receptor + CETP-mediated pathways",
            notes="HDL delivers cholesterol back to the liver for excretion into bile or conversion to bile acids."
        ))

        self.register(p)


def get_cholesterol_pathway_registry() -> CholesterolPathwayRegistry:
    """Factory function."""
    return CholesterolPathwayRegistry()


if __name__ == "__main__":
    reg = get_cholesterol_pathway_registry()

    print("=" * 65)
    print("CHOLESTEROL BIOSYNTHESIS + LIPOPROTEIN TRANSPORT MODEL")
    print("=" * 65)

    for name in ["cholesterol_biosynthesis", "lipoprotein_transport"]:
        pathway = reg.get(name)
        print(f"\n--- {pathway.name.upper()} ---")
        print(pathway.description)
        print(f"Nodes: {pathway.summary()['nodes']}  |  Edges: {pathway.summary()['edges']}")

    print("\n" + "=" * 65)
    print("KEY REGULATORY POINT")
    print("=" * 65)
    print("HMG-CoA reductase (HMGCR)")
    print("  • Rate-limiting enzyme of cholesterol biosynthesis")
    print("  • Primary target of statin drugs")
    print("  • Strongly feedback-inhibited by cholesterol")
    print("  • Transcriptionally controlled by SREBP-2")
    print("  • Also regulated by AMPK phosphorylation and insulin/glucagon")
