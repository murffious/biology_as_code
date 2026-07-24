"""
digestion_absorption_pathways.py
=================================================================
Macronutrient Digestion & Absorption Pathways

High-level ordered pathways that link the digestive mechanisms
we have already registered into coherent sequences from lumen
to enterocyte / circulation.
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
    LUMEN = "lumen"
    ENTEROCYTE = "enterocyte"
    CIRCULATION = "circulation"
    INTERMEDIATE = "intermediate"


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
    mechanism_id: str = ""          # links to formal MetabolicMechanism when available
    process: str = ""
    location: str = ""
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
        }


class DigestionAbsorptionRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_carb()
        self._build_protein()
        self._build_lipid()
        self._build_brush_border()
        self._build_enterohepatic()
        self._build_bile_acid_synthesis()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    def _build_carb(self) -> None:
        p = MetabolicPathway(
            name="carb_digestion_absorption",
            description="Carbohydrate digestion and absorption from starch/sugars to portal blood glucose."
        )
        p.add_node(MetaboliteNode("starch", "Starch / Glycogen", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("maltose_limit", "Maltose + Limit Dextrins", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("glucose_lumen", "Glucose (lumen)", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("glucose_enterocyte", "Glucose (enterocyte)", PathwayNodeType.ENTEROCYTE))
        p.add_node(MetaboliteNode("glucose_blood", "Glucose (portal blood)", PathwayNodeType.CIRCULATION))

        p.add_edge(ReactionEdge("starch", "maltose_limit", mechanism_id="salivary_amylase",
                                process="Salivary + Pancreatic Amylase", location="Mouth → Duodenum",
                                notes="α-1,4 cleavage. Pancreatic amylase continues in small intestine."))
        p.add_edge(ReactionEdge("maltose_limit", "glucose_lumen",
                                process="Brush-border disaccharidases (maltase, isomaltase, sucrase, lactase)",
                                location="Brush border",
                                notes="Final hydrolysis to monosaccharides."))
        p.add_edge(ReactionEdge("glucose_lumen", "glucose_enterocyte", mechanism_id="sglt1",
                                process="SGLT1", location="Apical membrane",
                                notes="Sodium-glucose cotransport. Primary route for glucose & galactose."))
        p.add_edge(ReactionEdge("glucose_enterocyte", "glucose_blood",
                                process="GLUT2", location="Basolateral membrane",
                                notes="Facilitated exit into portal blood."))

        self.register(p)

    def _build_protein(self) -> None:
        p = MetabolicPathway(
            name="protein_digestion_absorption",
            description="Protein digestion cascade from stomach to amino acid/peptide absorption."
        )
        p.add_node(MetaboliteNode("dietary_protein", "Dietary Protein", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("peptides_stomach", "Large Peptides (stomach)", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("oligopeptides", "Oligopeptides + Amino Acids", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("amino_acids_enterocyte", "Amino Acids / Di-Tri Peptides (enterocyte)", PathwayNodeType.ENTEROCYTE))
        p.add_node(MetaboliteNode("amino_acids_blood", "Amino Acids (portal blood)", PathwayNodeType.CIRCULATION))

        p.add_edge(ReactionEdge("dietary_protein", "peptides_stomach", mechanism_id="pepsin",
                                process="Pepsin", location="Stomach",
                                notes="Acid-stable endopeptidase. Initiates protein digestion."))
        p.add_edge(ReactionEdge("peptides_stomach", "oligopeptides",
                                process="Pancreatic proteases (trypsin, chymotrypsin, elastase, carboxypeptidases)",
                                location="Duodenum / Jejunum",
                                notes="Zymogens activated by enteropeptidase → trypsin cascade."))
        p.add_edge(ReactionEdge("oligopeptides", "amino_acids_enterocyte",
                                process="Brush-border peptidases + PEPT1 + amino acid transporters",
                                location="Brush border + apical membrane",
                                notes="PEPT1 absorbs di/tripeptides; multiple Na⁺-dependent and independent AA transporters."))
        p.add_edge(ReactionEdge("amino_acids_enterocyte", "amino_acids_blood",
                                process="Basolateral amino acid transporters",
                                location="Basolateral membrane",
                                notes="Exit into portal circulation."))

        self.register(p)

    def _build_lipid(self) -> None:
        p = MetabolicPathway(
            name="lipid_digestion_absorption",
            description="Lipid digestion from emulsion to chylomicron export into lymph."
        )
        p.add_node(MetaboliteNode("dietary_tg", "Dietary Triglycerides", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("emulsion", "Emulsified Fat Droplets", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("micelles", "Mixed Micelles", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("ffas_mg", "FFAs + 2-Monoacylglycerol", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("tg_enterocyte", "Re-esterified TG (enterocyte)", PathwayNodeType.ENTEROCYTE))
        p.add_node(MetaboliteNode("chylomicron", "Chylomicron", PathwayNodeType.CIRCULATION,
            "Exported into lacteals → lymph → thoracic duct → blood."))

        p.add_edge(ReactionEdge("dietary_tg", "emulsion",
                                process="Mechanical emulsification + Bile salts",
                                location="Stomach → Duodenum",
                                notes="Bile salts stabilize small emulsion droplets."))
        p.add_edge(ReactionEdge("emulsion", "micelles",
                                process="Bile salt micelle formation",
                                location="Duodenal lumen",
                                notes="Mixed micelles solubilize the products of lipolysis."))
        p.add_edge(ReactionEdge("micelles", "ffas_mg", mechanism_id="pancreatic_lipase",
                                process="Pancreatic lipase + Colipase",
                                location="Oil-water interface of micelles",
                                notes="Requires colipase. Cleaves sn-1 and sn-3 positions."))
        p.add_edge(ReactionEdge("ffas_mg", "tg_enterocyte",
                                process="Passive diffusion + re-esterification (MGAT, DGAT)",
                                location="Enterocyte",
                                notes="FFAs and 2-MG enter by diffusion; re-esterified in smooth ER."))
        p.add_edge(ReactionEdge("tg_enterocyte", "chylomicron",
                                process="Chylomicron assembly (ApoB-48, MTP)",
                                location="Enterocyte → Lacteal",
                                notes="Packaged with ApoB-48 and exported into lymph."))

        self.register(p)

    def _build_brush_border(self) -> None:
        p = MetabolicPathway(
            name="brush_border_final_digestion",
            description="Brush-border disaccharidases and peptidases completing lumen → absorbable monomers.",
        )
        p.add_node(MetaboliteNode("disaccharides", "Disaccharides (maltose, sucrose, lactose)", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("monosaccharides", "Monosaccharides", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("oligopeptides", "Oligopeptides", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("aa_di_tri", "AA + di/tripeptides", PathwayNodeType.LUMEN))
        p.add_edge(ReactionEdge(
            "disaccharides", "monosaccharides",
            process="Maltase, sucrase-isomaltase, lactase",
            location="Brush border",
            notes="Final carb hydrolysis before SGLT1/GLUT5/GLUT2.",
        ))
        p.add_edge(ReactionEdge(
            "oligopeptides", "aa_di_tri",
            process="Brush-border peptidases",
            location="Brush border",
            notes="Exopeptidases finish protein digestion for PEPT1 / AA transporters.",
        ))
        self.register(p)

    def _build_enterohepatic(self) -> None:
        p = MetabolicPathway(
            name="enterohepatic_bile",
            description="Enterohepatic circulation of bile acids: liver → bile → ileum reuptake → portal return.",
        )
        p.add_node(MetaboliteNode("hepatic_bile_acids", "Hepatic bile acids", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("gallbladder_bile", "Stored / secreted bile", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("ileal_lumen", "Bile acids in ileal lumen", PathwayNodeType.LUMEN))
        p.add_node(MetaboliteNode("portal_bile_acids", "Portal bile acids", PathwayNodeType.CIRCULATION))
        p.add_node(MetaboliteNode("fecal_loss", "Fecal bile acid loss (~5%)", PathwayNodeType.INTERMEDIATE))
        p.add_edge(ReactionEdge(
            "hepatic_bile_acids", "gallbladder_bile",
            process="Biliary secretion + gallbladder storage",
            location="Liver → GB → duodenum",
            notes="CCK drives gallbladder contraction on a fatty meal.",
        ))
        p.add_edge(ReactionEdge(
            "gallbladder_bile", "ileal_lumen",
            process="Micelle transit through SI",
            location="SI lumen",
            notes="Bile acids enable fat micelles then reach terminal ileum.",
        ))
        p.add_edge(ReactionEdge(
            "ileal_lumen", "portal_bile_acids",
            process="ASBT / IBAT reuptake",
            location="Terminal ileum",
            notes="~95% recovery; active transport of conjugated bile acids.",
        ))
        p.add_edge(ReactionEdge(
            "portal_bile_acids", "hepatic_bile_acids",
            process="Hepatic extraction",
            location="Portal → hepatocyte",
            notes="Closes enterohepatic loop.",
        ))
        p.add_edge(ReactionEdge(
            "ileal_lumen", "fecal_loss",
            process="Incomplete reabsorption",
            location="Colon / feces",
            notes="Daily fecal loss replaced by de novo bile acid synthesis.",
        ))
        self.register(p)

    def _build_bile_acid_synthesis(self) -> None:
        p = MetabolicPathway(
            name="bile_acid_synthesis",
            description="Classic pathway: cholesterol → primary bile acids (cholic / chenodeoxycholic) in hepatocytes.",
        )
        p.add_node(MetaboliteNode("cholesterol", "Cholesterol", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("7a_hydroxycholesterol", "7α-Hydroxycholesterol", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("primary_bile_acids", "Primary bile acids (CA, CDCA)", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("conjugated_bile_acids", "Glycine/taurine conjugates", PathwayNodeType.INTERMEDIATE))
        p.add_edge(ReactionEdge(
            "cholesterol", "7a_hydroxycholesterol",
            process="CYP7A1 (cholesterol 7α-hydroxylase)",
            location="Hepatocyte",
            notes="Rate-limiting step of classic bile acid synthesis; feedback via FXR/SHP.",
        ))
        p.add_edge(ReactionEdge(
            "7a_hydroxycholesterol", "primary_bile_acids",
            process="Multiple sterol modifications",
            location="Hepatocyte",
            notes="Produces cholic and chenodeoxycholic acids.",
        ))
        p.add_edge(ReactionEdge(
            "primary_bile_acids", "conjugated_bile_acids",
            process="BAAT conjugation",
            location="Hepatocyte",
            notes="Conjugation improves solubility for micelles.",
        ))
        self.register(p)


def get_digestion_absorption_registry() -> DigestionAbsorptionRegistry:
    return DigestionAbsorptionRegistry()


if __name__ == "__main__":
    reg = get_digestion_absorption_registry()
    print("=" * 60)
    print("DIGESTION & ABSORPTION PATHWAYS")
    print("=" * 60)
    for p in reg.list_all():
        print(f"\n{p.name}: {p.summary()['nodes']} nodes, {p.summary()['edges']} edges")
        print(f"  {p.description}")
