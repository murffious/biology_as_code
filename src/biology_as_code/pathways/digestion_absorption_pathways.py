"""
digestion_absorption_pathways.py
=================================================================
Macronutrient Digestion & Absorption Pathways

High-level ordered pathways that link the digestive mechanisms
we have already registered into coherent sequences from lumen
to enterocyte / circulation.
=================================================================
"""


try:
    from biology_as_code.pathways.metabolic_mechanisms import (
        MetabolicMechanism,
        get_metabolic_mechanism_registry,
    )
except ImportError:
    get_metabolic_mechanism_registry = None
    MetabolicMechanism = None


from biology_as_code.pathways._types import (
    MetabolicPathway as _BasePathway,
)
from biology_as_code.pathways._types import (
    MetaboliteNode,
    PathwayNodeType,
    ReactionEdge,
)


class MetabolicPathway(_BasePathway):
    """Shared graph type; only this module's own summary differs."""

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
        p.add_node(MetaboliteNode(id="starch", name="Starch / Glycogen", node_type=PathwayNodeType.SUBSTRATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="maltose_limit", name="Maltose + Limit Dextrins", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="glucose_lumen", name="Glucose (lumen)", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="glucose_enterocyte", name="Glucose (enterocyte)", node_type=PathwayNodeType.INTERMEDIATE, compartment="enterocyte"))
        p.add_node(MetaboliteNode(id="glucose_blood", name="Glucose (portal blood)", node_type=PathwayNodeType.PRODUCT, compartment="circulation"))

        p.add_edge(ReactionEdge(from_node="starch", to_node="maltose_limit", mechanism_id="salivary_amylase",
                                process="Salivary + Pancreatic Amylase", location="Mouth → Duodenum",
                                notes="α-1,4 cleavage. Pancreatic amylase continues in small intestine."))
        p.add_edge(ReactionEdge(from_node="maltose_limit", to_node="glucose_lumen",
                                process="Brush-border disaccharidases (maltase, isomaltase, sucrase, lactase)",
                                location="Brush border",
                                notes="Final hydrolysis to monosaccharides."))
        p.add_edge(ReactionEdge(from_node="glucose_lumen", to_node="glucose_enterocyte", mechanism_id="sglt1",
                                process="SGLT1", location="Apical membrane",
                                notes="Sodium-glucose cotransport. Primary route for glucose & galactose."))
        p.add_edge(ReactionEdge(from_node="glucose_enterocyte", to_node="glucose_blood",
                                process="GLUT2", location="Basolateral membrane",
                                notes="Facilitated exit into portal blood."))

        self.register(p)

    def _build_protein(self) -> None:
        p = MetabolicPathway(
            name="protein_digestion_absorption",
            description="Protein digestion cascade from stomach to amino acid/peptide absorption."
        )
        p.add_node(MetaboliteNode(id="dietary_protein", name="Dietary Protein", node_type=PathwayNodeType.SUBSTRATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="peptides_stomach", name="Large Peptides (stomach)", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="oligopeptides", name="Oligopeptides + Amino Acids", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="amino_acids_enterocyte", name="Amino Acids / Di-Tri Peptides (enterocyte)", node_type=PathwayNodeType.INTERMEDIATE, compartment="enterocyte"))
        p.add_node(MetaboliteNode(id="amino_acids_blood", name="Amino Acids (portal blood)", node_type=PathwayNodeType.PRODUCT, compartment="circulation"))

        p.add_edge(ReactionEdge(from_node="dietary_protein", to_node="peptides_stomach", mechanism_id="pepsin",
                                process="Pepsin", location="Stomach",
                                notes="Acid-stable endopeptidase. Initiates protein digestion."))
        p.add_edge(ReactionEdge(from_node="peptides_stomach", to_node="oligopeptides",
                                process="Pancreatic proteases (trypsin, chymotrypsin, elastase, carboxypeptidases)",
                                location="Duodenum / Jejunum",
                                notes="Zymogens activated by enteropeptidase → trypsin cascade."))
        # Wave B2: explicit PepT1 apical peptide uptake (di/tripeptides)
        p.add_edge(ReactionEdge(
            from_node="oligopeptides", to_node="amino_acids_enterocyte",
            mechanism_id="pept1",
            process="PepT1 (SLC15A1) proton-coupled di/tripeptide uptake",
            location="Apical membrane",
            notes="Major nitrogen absorption route for di/tripeptides; free AA transporters run in parallel.",
        ))
        p.add_edge(ReactionEdge(from_node="amino_acids_enterocyte", to_node="amino_acids_blood",
                                process="Basolateral amino acid transporters",
                                location="Basolateral membrane",
                                notes="Exit into portal circulation."))

        self.register(p)

    def _build_lipid(self) -> None:
        p = MetabolicPathway(
            name="lipid_digestion_absorption",
            description="Lipid digestion from emulsion to chylomicron export into lymph."
        )
        p.add_node(MetaboliteNode(id="dietary_tg", name="Dietary Triglycerides", node_type=PathwayNodeType.SUBSTRATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="emulsion", name="Emulsified Fat Droplets", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="micelles", name="Mixed Micelles", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="ffas_mg", name="FFAs + 2-Monoacylglycerol", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="tg_enterocyte", name="Re-esterified TG (enterocyte)", node_type=PathwayNodeType.INTERMEDIATE, compartment="enterocyte"))
        p.add_node(MetaboliteNode(id="chylomicron", name="Chylomicron", node_type=PathwayNodeType.PRODUCT, compartment="circulation",
            notes="Exported into lacteals → lymph → thoracic duct → blood."))

        p.add_edge(ReactionEdge(from_node="dietary_tg", to_node="emulsion",
                                mechanism_id="bile_salt_emulsification",
                                process="Mechanical emulsification + Bile salts",
                                location="Stomach → Duodenum",
                                notes="Bile salts stabilize small emulsion droplets."))
        p.add_edge(ReactionEdge(from_node="emulsion", to_node="micelles",
                                mechanism_id="bile_salt_micelle",
                                process="Bile salt mixed-micelle formation",
                                location="Duodenal lumen",
                                notes="Mixed micelles solubilize the products of lipolysis."))
        p.add_edge(ReactionEdge(from_node="micelles", to_node="ffas_mg", mechanism_id="pancreatic_lipase",
                                process="Pancreatic lipase + Colipase",
                                location="Oil-water interface of micelles",
                                notes="Requires colipase. Cleaves sn-1 and sn-3 positions."))
        p.add_edge(ReactionEdge(from_node="ffas_mg", to_node="tg_enterocyte",
                                process="Passive diffusion + re-esterification (MGAT, DGAT)",
                                location="Enterocyte",
                                notes="FFAs and 2-MG enter by diffusion; re-esterified in smooth ER."))
        p.add_edge(ReactionEdge(from_node="tg_enterocyte", to_node="chylomicron",
                                process="Chylomicron assembly (ApoB-48, MTP)",
                                location="Enterocyte → Lacteal",
                                notes="Packaged with ApoB-48 and exported into lymph."))

        self.register(p)

    def _build_brush_border(self) -> None:
        p = MetabolicPathway(
            name="brush_border_final_digestion",
            description="Brush-border disaccharidases and peptidases completing lumen → absorbable monomers.",
        )
        p.add_node(MetaboliteNode(id="disaccharides", name="Disaccharides (maltose, sucrose, lactose)", node_type=PathwayNodeType.SUBSTRATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="monosaccharides", name="Monosaccharides", node_type=PathwayNodeType.PRODUCT, compartment="lumen"))
        p.add_node(MetaboliteNode(id="oligopeptides", name="Oligopeptides", node_type=PathwayNodeType.SUBSTRATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="aa_di_tri", name="AA + di/tripeptides", node_type=PathwayNodeType.PRODUCT, compartment="lumen"))
        p.add_edge(ReactionEdge(
            from_node="disaccharides", to_node="monosaccharides",
            process="Maltase, sucrase-isomaltase, lactase",
            location="Brush border",
            notes="Final carb hydrolysis before SGLT1/GLUT5/GLUT2.",
        ))
        p.add_edge(ReactionEdge(
            from_node="oligopeptides", to_node="aa_di_tri",
            process="Brush-border peptidases",
            location="Brush border",
            notes="Exopeptidases finish protein digestion for PepT1 / AA transporters "
                  "(PepT1 uptake edge lives on protein_digestion_absorption).",
        ))
        self.register(p)

    def _build_enterohepatic(self) -> None:
        p = MetabolicPathway(
            name="enterohepatic_bile",
            description="Enterohepatic circulation of bile acids: liver → bile → ileum reuptake → portal return.",
        )
        p.add_node(MetaboliteNode(id="hepatic_bile_acids", name="Hepatic bile acids", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode(id="gallbladder_bile", name="Stored / secreted bile", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="ileal_lumen", name="Bile acids in ileal lumen", node_type=PathwayNodeType.INTERMEDIATE, compartment="lumen"))
        p.add_node(MetaboliteNode(id="portal_bile_acids", name="Portal bile acids", node_type=PathwayNodeType.INTERMEDIATE, compartment="circulation"))
        p.add_node(MetaboliteNode(id="fecal_loss", name="Fecal bile acid loss (~5%)", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_edge(ReactionEdge(
            from_node="hepatic_bile_acids", to_node="gallbladder_bile",
            process="Biliary secretion + gallbladder storage",
            location="Liver → GB → duodenum",
            notes="CCK drives gallbladder contraction on a fatty meal.",
        ))
        p.add_edge(ReactionEdge(
            from_node="gallbladder_bile", to_node="ileal_lumen",
            process="Micelle transit through SI",
            location="SI lumen",
            notes="Bile acids enable fat micelles then reach terminal ileum.",
        ))
        p.add_edge(ReactionEdge(
            from_node="ileal_lumen", to_node="portal_bile_acids",
            process="ASBT / IBAT reuptake",
            location="Terminal ileum",
            notes="~95% recovery; active transport of conjugated bile acids.",
        ))
        p.add_edge(ReactionEdge(
            from_node="portal_bile_acids", to_node="hepatic_bile_acids",
            process="Hepatic extraction",
            location="Portal → hepatocyte",
            notes="Closes enterohepatic loop.",
        ))
        p.add_edge(ReactionEdge(
            from_node="ileal_lumen", to_node="fecal_loss",
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
        p.add_node(MetaboliteNode(id="cholesterol", name="Cholesterol", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode(id="7a_hydroxycholesterol", name="7α-Hydroxycholesterol", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode(id="primary_bile_acids", name="Primary bile acids (CA, CDCA)", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode(id="conjugated_bile_acids", name="Glycine/taurine conjugates", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_edge(ReactionEdge(
            from_node="cholesterol", to_node="7a_hydroxycholesterol",
            process="CYP7A1 (cholesterol 7α-hydroxylase)",
            location="Hepatocyte",
            notes="Rate-limiting step of classic bile acid synthesis; feedback via FXR/SHP.",
        ))
        p.add_edge(ReactionEdge(
            from_node="7a_hydroxycholesterol", to_node="primary_bile_acids",
            process="Multiple sterol modifications",
            location="Hepatocyte",
            notes="Produces cholic and chenodeoxycholic acids.",
        ))
        p.add_edge(ReactionEdge(
            from_node="primary_bile_acids", to_node="conjugated_bile_acids",
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
