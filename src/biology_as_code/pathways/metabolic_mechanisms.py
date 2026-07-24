"""
metabolic_mechanisms.py
=================================================================
Formal MetabolicMechanism class + registry

This is the bridge between:
  - Digestive / metabolic mechanisms (individual processes)
  - Pathways (ordered sequences of those processes)

A MetabolicMechanism is a reusable, well-documented process that can
be referenced by multiple pathways.
=================================================================
"""

from dataclasses import dataclass, field
from enum import Enum


class MechanismCategory(Enum):
    DIGESTIVE = "digestive"              # Hydrolysis, emulsification, etc.
    TRANSPORT = "transport"              # Membrane transporters, shuttles
    ENZYMATIC = "enzymatic"              # Classic metabolic enzymes
    REGULATORY = "regulatory"            # Kinases, transcription factors, etc.
    MICROBIAL = "microbial"              # Gut microbiome processes
    SIGNALING = "signaling"              # Hormone / receptor actions


@dataclass
class MetabolicMechanism:
    """
    A single, reusable biochemical or physiological process.
    
    This is the formal 'verb' that pathways can reference.
    """
    id: str
    name: str
    category: MechanismCategory
    description: str
    location: str = ""                   # e.g. "cytosol", "mitochondrial matrix", "duodenal lumen"
    inputs: list[str] = field(default_factory=list)
    outputs: list[str] = field(default_factory=list)
    cofactors: list[str] = field(default_factory=list)
    regulation: list[str] = field(default_factory=list)
    notes: str = ""
    related_pathways: list[str] = field(default_factory=list)  # names of pathways that use this mechanism


class MetabolicMechanismRegistry:
    """
    Registry of reusable metabolic mechanisms.
    Pathways can look up mechanisms by id and attach them to edges.
    """

    def __init__(self):
        self.mechanisms: dict[str, MetabolicMechanism] = {}
        self._build_core_mechanisms()

    def register(self, mech: MetabolicMechanism) -> None:
        self.mechanisms[mech.id] = mech

    def get(self, mechanism_id: str) -> MetabolicMechanism | None:
        return self.mechanisms.get(mechanism_id)

    def list_all(self) -> list[MetabolicMechanism]:
        return list(self.mechanisms.values())

    def list_by_category(self, category: MechanismCategory) -> list[MetabolicMechanism]:
        return [m for m in self.mechanisms.values() if m.category == category]

    def summary(self) -> dict:
        return {
            "total_mechanisms": len(self.mechanisms),
            "by_category": {
                cat.value: len(self.list_by_category(cat))
                for cat in MechanismCategory
            }
        }

    def _build_core_mechanisms(self) -> None:
        """Populate with key mechanisms we have already discussed."""

        # ------------------------------------------------------------------
        # DIGESTIVE MECHANISMS
        # ------------------------------------------------------------------
        self.register(MetabolicMechanism(
            id="pancreatic_lipase",
            name="Pancreatic Lipase Hydrolysis",
            category=MechanismCategory.DIGESTIVE,
            description="Hydrolyzes triglycerides at the sn-1 and sn-3 positions within mixed micelles.",
            location="Duodenal lumen (requires colipase and bile salts)",
            inputs=["Triglyceride", "H2O"],
            outputs=["2-Monoacylglycerol", "Fatty acid", "Fatty acid"],
            cofactors=["Colipase", "Bile salts"],
            regulation=["Requires colipase to anchor at the oil-water interface"],
            notes="Primary enzyme for dietary fat digestion. Inactive without colipase and bile salts.",
            related_pathways=["lipid_digestion_absorption"]
        ))

        self.register(MetabolicMechanism(
            id="salivary_amylase",
            name="Salivary Amylase (Ptyalin)",
            category=MechanismCategory.DIGESTIVE,
            description="Endoglycosidase that cleaves α-1,4 glycosidic bonds in starch.",
            location="Oral cavity and proximal stomach",
            inputs=["Starch (amylose/amylopectin)", "H2O"],
            outputs=["Maltose", "Maltotriose", "Limit dextrins"],
            notes="Inactivated by low pH in the stomach. Continues briefly in the bolus center.",
            related_pathways=["carbohydrate_digestion"]
        ))

        self.register(MetabolicMechanism(
            id="pepsin",
            name="Pepsin Proteolysis",
            category=MechanismCategory.DIGESTIVE,
            description="Acid-stable endopeptidase that cleaves proteins preferentially at aromatic residues.",
            location="Stomach lumen",
            inputs=["Protein", "H2O"],
            outputs=["Peptides"],
            regulation=["Secreted as pepsinogen; activated by HCl and by pepsin itself"],
            notes="Optimal pH ~1.5–2.0. Initiates protein digestion.",
            related_pathways=["protein_digestion"]
        ))

        # ------------------------------------------------------------------
        # KEY METABOLIC ENZYMES
        # ------------------------------------------------------------------
        self.register(MetabolicMechanism(
            id="hmg_coa_reductase",
            name="HMG-CoA Reductase",
            category=MechanismCategory.ENZYMATIC,
            description="Reduces HMG-CoA to mevalonate using 2 NADPH. Rate-limiting step of cholesterol biosynthesis.",
            location="Cytosol (primarily liver)",
            inputs=["HMG-CoA", "2 NADPH", "2 H+"],
            outputs=["Mevalonate", "CoA", "2 NADP+"],
            cofactors=["NADPH"],
            regulation=[
                "Strongly inhibited by cholesterol and oxysterols",
                "Inhibited by statin drugs (competitive inhibitors)",
                "Transcriptionally activated by SREBP-2 when cholesterol is low",
                "Inactivated by AMPK-mediated phosphorylation",
                "Induced by insulin, repressed by glucagon"
            ],
            notes="Primary pharmacological target for lowering LDL cholesterol. Commits carbon flux into the sterol pathway.",
            related_pathways=["cholesterol_biosynthesis"]
        ))

        self.register(MetabolicMechanism(
            id="hexokinase",
            name="Hexokinase / Glucokinase",
            category=MechanismCategory.ENZYMATIC,
            description="Phosphorylates glucose to glucose-6-phosphate, trapping it inside the cell.",
            location="Cytosol (hexokinase in most tissues; glucokinase in liver and β-cells)",
            inputs=["Glucose", "ATP"],
            outputs=["Glucose-6-phosphate", "ADP"],
            regulation=[
                "Hexokinase inhibited by its product G6P",
                "Glucokinase has high Km (low affinity) and is induced by insulin"
            ],
            notes="First irreversible step of glycolysis. Different isoforms serve different physiological roles.",
            related_pathways=["glycolysis"]
        ))

        self.register(MetabolicMechanism(
            id="pfk1",
            name="Phosphofructokinase-1 (PFK-1)",
            category=MechanismCategory.ENZYMATIC,
            description="Phosphorylates fructose-6-phosphate to fructose-1,6-bisphosphate. Major control point of glycolysis.",
            location="Cytosol",
            inputs=["Fructose-6-phosphate", "ATP"],
            outputs=["Fructose-1,6-bisphosphate", "ADP"],
            regulation=[
                "Inhibited by ATP and citrate",
                "Activated by AMP and fructose-2,6-bisphosphate",
                "Insulin raises fructose-2,6-bisphosphate → activates PFK-1"
            ],
            notes="The committed step of glycolysis. Most important regulatory enzyme in the pathway.",
            related_pathways=["glycolysis"]
        ))

        self.register(MetabolicMechanism(
            id="pyruvate_kinase",
            name="Pyruvate Kinase",
            category=MechanismCategory.ENZYMATIC,
            description="Transfers phosphate from phosphoenolpyruvate to ADP, forming pyruvate and ATP.",
            location="Cytosol",
            inputs=["Phosphoenolpyruvate", "ADP"],
            outputs=["Pyruvate", "ATP"],
            regulation=[
                "Activated by fructose-1,6-bisphosphate (feed-forward)",
                "In liver: inhibited by phosphorylation (glucagon/cAMP) and by alanine"
            ],
            notes="Third irreversible step of glycolysis. Second substrate-level phosphorylation.",
            related_pathways=["glycolysis"]
        ))

        self.register(MetabolicMechanism(
            id="gapdh",
            name="Glyceraldehyde-3-Phosphate Dehydrogenase (GAPDH)",
            category=MechanismCategory.ENZYMATIC,
            description="Oxidizes glyceraldehyde-3-phosphate and reduces NAD+ while forming the high-energy intermediate 1,3-bisphosphoglycerate.",
            location="Cytosol",
            inputs=["Glyceraldehyde-3-phosphate", "NAD+", "Pi"],
            outputs=["1,3-Bisphosphoglycerate", "NADH", "H+"],
            cofactors=["NAD+"],
            notes="Only redox step in glycolysis. Produces NADH that can feed the electron transport chain (aerobic) or be reoxidized by LDH (anaerobic).",
            related_pathways=["glycolysis"]
        ))

        self.register(MetabolicMechanism(
            id="phosphoglycerate_kinase",
            name="Phosphoglycerate Kinase",
            category=MechanismCategory.ENZYMATIC,
            description="Transfers the high-energy phosphate from 1,3-bisphosphoglycerate to ADP, forming ATP and 3-phosphoglycerate.",
            location="Cytosol",
            inputs=["1,3-Bisphosphoglycerate", "ADP"],
            outputs=["3-Phosphoglycerate", "ATP"],
            notes="First substrate-level phosphorylation in glycolysis. Occurs twice per glucose.",
            related_pathways=["glycolysis"]
        ))

        self.register(MetabolicMechanism(
            id="enolase",
            name="Enolase",
            category=MechanismCategory.ENZYMATIC,
            description="Dehydrates 2-phosphoglycerate to form the high-energy compound phosphoenolpyruvate (PEP).",
            location="Cytosol",
            inputs=["2-Phosphoglycerate"],
            outputs=["Phosphoenolpyruvate", "H2O"],
            notes="Creates the second high-energy phosphate intermediate of glycolysis.",
            related_pathways=["glycolysis"]
        ))

        self.register(MetabolicMechanism(
            id="lactate_dehydrogenase",
            name="Lactate Dehydrogenase (LDH)",
            category=MechanismCategory.ENZYMATIC,
            description="Reduces pyruvate to lactate while regenerating NAD+ from NADH.",
            location="Cytosol",
            inputs=["Pyruvate", "NADH", "H+"],
            outputs=["Lactate", "NAD+"],
            notes="Allows glycolysis to continue under anaerobic conditions by regenerating NAD+. Part of the Cori cycle.",
            related_pathways=["glycolysis", "cori_cycle"]
        ))

        # ------------------------------------------------------------------
        # TRANSPORT MECHANISMS
        # ------------------------------------------------------------------
        self.register(MetabolicMechanism(
            id="sglt1",
            name="SGLT1 (Sodium-Glucose Linked Transporter 1)",
            category=MechanismCategory.TRANSPORT,
            description="Secondary active transport of glucose (and galactose) driven by the sodium gradient.",
            location="Apical membrane of enterocytes (small intestine)",
            inputs=["Glucose (or galactose)", "2 Na+"],
            outputs=["Glucose (or galactose) inside enterocyte", "2 Na+ inside"],
            notes="Primary route of dietary glucose absorption. High affinity, low capacity.",
            related_pathways=["carbohydrate_absorption"]
        ))

        self.register(MetabolicMechanism(
            id="ldl_receptor",
            name="LDL Receptor-Mediated Endocytosis",
            category=MechanismCategory.TRANSPORT,
            description="Binds ApoB-100 on LDL particles and internalizes them via clathrin-coated pits.",
            location="Plasma membrane of hepatocytes and peripheral cells",
            inputs=["LDL particle"],
            outputs=["Cholesterol esters (released after lysosomal hydrolysis)", "ApoB-100 (degraded)"],
            regulation=["Receptor expression is down-regulated by high cellular cholesterol via SREBP"],
            notes="Major route of cholesterol delivery to cells. Defects cause familial hypercholesterolemia.",
            related_pathways=["lipoprotein_transport", "cholesterol_homeostasis"]
        ))

        # ------------------------------------------------------------------
        # TCA CYCLE MECHANISMS
        # ------------------------------------------------------------------
        self.register(MetabolicMechanism(
            id="citrate_synthase",
            name="Citrate Synthase",
            category=MechanismCategory.ENZYMATIC,
            description="Condenses acetyl-CoA with oxaloacetate to form citrate. First step of the TCA cycle.",
            location="Mitochondrial matrix",
            inputs=["Acetyl-CoA", "Oxaloacetate", "H2O"],
            outputs=["Citrate", "CoA"],
            regulation=[
                "Inhibited by ATP, NADH, succinyl-CoA, and citrate",
                "High energy charge slows the cycle at the entry point"
            ],
            notes="Commits acetyl-CoA to the TCA cycle. Highly exergonic and irreversible under physiological conditions.",
            related_pathways=["tca_cycle"]
        ))

        self.register(MetabolicMechanism(
            id="aconitase",
            name="Aconitase",
            category=MechanismCategory.ENZYMATIC,
            description="Isomerizes citrate to isocitrate via cis-aconitate.",
            location="Mitochondrial matrix",
            inputs=["Citrate"],
            outputs=["Isocitrate"],
            notes="Contains an iron-sulfur cluster. Also acts as an iron sensor in the cytosol (IRP1).",
            related_pathways=["tca_cycle"]
        ))

        self.register(MetabolicMechanism(
            id="isocitrate_dehydrogenase",
            name="Isocitrate Dehydrogenase",
            category=MechanismCategory.ENZYMATIC,
            description="Oxidative decarboxylation of isocitrate to α-ketoglutarate. Produces NADH and CO₂.",
            location="Mitochondrial matrix",
            inputs=["Isocitrate", "NAD+"],
            outputs=["α-Ketoglutarate", "NADH", "CO₂"],
            regulation=[
                "Major control point of the TCA cycle",
                "Activated by ADP",
                "Inhibited by ATP and NADH"
            ],
            notes="One of the three irreversible steps. Critical for matching cycle flux to energy demand.",
            related_pathways=["tca_cycle"]
        ))

        self.register(MetabolicMechanism(
            id="alpha_ketoglutarate_dehydrogenase",
            name="α-Ketoglutarate Dehydrogenase Complex",
            category=MechanismCategory.ENZYMATIC,
            description="Oxidative decarboxylation of α-ketoglutarate to succinyl-CoA. Produces NADH and CO₂.",
            location="Mitochondrial matrix",
            inputs=["α-Ketoglutarate", "CoA", "NAD+"],
            outputs=["Succinyl-CoA", "NADH", "CO₂"],
            regulation=[
                "Inhibited by succinyl-CoA, NADH, and high energy charge",
                "Similar regulation to the pyruvate dehydrogenase complex"
            ],
            notes="Second irreversible decarboxylation. Shares mechanistic similarity with PDH complex.",
            related_pathways=["tca_cycle"]
        ))

        self.register(MetabolicMechanism(
            id="succinyl_coa_synthetase",
            name="Succinyl-CoA Synthetase (Succinyl-CoA Ligase)",
            category=MechanismCategory.ENZYMATIC,
            description="Converts succinyl-CoA to succinate while forming GTP (or ATP) by substrate-level phosphorylation.",
            location="Mitochondrial matrix",
            inputs=["Succinyl-CoA", "GDP (or ADP)", "Pi"],
            outputs=["Succinate", "GTP (or ATP)", "CoA"],
            notes="Only substrate-level phosphorylation step in the TCA cycle. GTP can be converted to ATP by nucleoside diphosphate kinase.",
            related_pathways=["tca_cycle"]
        ))

        self.register(MetabolicMechanism(
            id="succinate_dehydrogenase",
            name="Succinate Dehydrogenase",
            category=MechanismCategory.ENZYMATIC,
            description="Oxidizes succinate to fumarate and reduces FAD to FADH₂. Also functions as Complex II of the electron transport chain.",
            location="Inner mitochondrial membrane",
            inputs=["Succinate", "FAD"],
            outputs=["Fumarate", "FADH₂"],
            notes="Only membrane-bound enzyme of the TCA cycle. Directly feeds electrons into the ETC.",
            related_pathways=["tca_cycle", "electron_transport_chain"]
        ))

        self.register(MetabolicMechanism(
            id="fumarase",
            name="Fumarase (Fumarate Hydratase)",
            category=MechanismCategory.ENZYMATIC,
            description="Hydrates fumarate to form L-malate.",
            location="Mitochondrial matrix",
            inputs=["Fumarate", "H2O"],
            outputs=["Malate"],
            notes="Reversible, near-equilibrium reaction.",
            related_pathways=["tca_cycle"]
        ))

        self.register(MetabolicMechanism(
            id="malate_dehydrogenase",
            name="Malate Dehydrogenase",
            category=MechanismCategory.ENZYMATIC,
            description="Oxidizes malate to oxaloacetate while reducing NAD+ to NADH. Regenerates the oxaloacetate needed to continue the cycle.",
            location="Mitochondrial matrix",
            inputs=["Malate", "NAD+"],
            outputs=["Oxaloacetate", "NADH", "H+"],
            notes="Highly endergonic; pulled forward by the continuous consumption of oxaloacetate by citrate synthase.",
            related_pathways=["tca_cycle"]
        ))


def get_metabolic_mechanism_registry() -> MetabolicMechanismRegistry:
    """Factory function."""
    return MetabolicMechanismRegistry()


if __name__ == "__main__":
    reg = get_metabolic_mechanism_registry()
    print("=" * 60)
    print("METABOLIC MECHANISM REGISTRY")
    print("=" * 60)
    print(f"Total mechanisms: {reg.summary()['total_mechanisms']}")
    print("\nBy category:")
    for cat, count in reg.summary()["by_category"].items():
        print(f"  {cat:12} : {count}")

    print("\n--- Example: HMG-CoA Reductase ---")
    hmg = reg.get("hmg_coa_reductase")
    if hmg:
        print(f"Name       : {hmg.name}")
        print(f"Location   : {hmg.location}")
        print(f"Inputs     : {', '.join(hmg.inputs)}")
        print(f"Outputs    : {', '.join(hmg.outputs)}")
        print("Regulation :")
        for r in hmg.regulation:
            print(f"  • {r}")
        print(f"Notes      : {hmg.notes}")
