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
    references: list[str] = field(default_factory=list)  # provenance: gene/EC/PMID/URL — see _MECHANISM_REFERENCES


def _enzyme_ref(name: str, gene: str, ec: str, term: str = "") -> str:
    """One authoritative provenance line: stable gene + EC identifiers (facts, not
    fabricated PMIDs), plus a nutrition-vocabulary term_id when one carries leads."""
    line = (
        f"{name} — gene {gene}: https://www.ncbi.nlm.nih.gov/gene/?term={gene}"
        f" · EC {ec}: https://enzyme.expasy.org/EC/{ec}"
    )
    if term:
        line += f" · {term} (ranked PubMed leads)"
    return line


# Enzyme cogs the cog↔evidence report flags as absent from the nutrition vocabulary.
# Anchored to gene + EC (stable identifiers); the three digestive/glycolytic enzymes
# that DO have a master term link it so they join the evidence spine.
_MECHANISM_REFERENCES: dict[str, list[str]] = {
    # digestive enzymes (have nutrition-vocabulary terms with leads)
    "pancreatic_lipase": [_enzyme_ref("Pancreatic lipase", "PNLIP", "3.1.1.3", "term.lipase")],
    "salivary_amylase": [_enzyme_ref("Salivary α-amylase", "AMY1A", "3.2.1.1", "term.a_amylase")],
    # glycolysis
    "pfk1": [_enzyme_ref("Phosphofructokinase-1", "PFKM", "2.7.1.11", "term.phosphofructokinase")],
    "gapdh": [_enzyme_ref("Glyceraldehyde-3-phosphate dehydrogenase", "GAPDH", "1.2.1.12")],
    "phosphoglycerate_kinase": [_enzyme_ref("Phosphoglycerate kinase", "PGK1", "2.7.2.3")],
    "enolase": [_enzyme_ref("Enolase", "ENO1", "4.2.1.11")],
    "lactate_dehydrogenase": [_enzyme_ref("Lactate dehydrogenase", "LDHA", "1.1.1.27")],
    # TCA cycle
    "citrate_synthase": [_enzyme_ref("Citrate synthase", "CS", "2.3.3.1")],
    "aconitase": [_enzyme_ref("Aconitase", "ACO2", "4.2.1.3")],
    "isocitrate_dehydrogenase": [_enzyme_ref("Isocitrate dehydrogenase (NAD⁺)", "IDH3A", "1.1.1.41")],
    "alpha_ketoglutarate_dehydrogenase": [_enzyme_ref("α-Ketoglutarate dehydrogenase (E1)", "OGDH", "1.2.4.2")],
    "succinyl_coa_synthetase": [_enzyme_ref("Succinyl-CoA synthetase (GTP-forming)", "SUCLG1", "6.2.1.4")],
    "succinate_dehydrogenase": [_enzyme_ref("Succinate dehydrogenase (SDHA)", "SDHA", "1.3.5.1")],
    "fumarase": [_enzyme_ref("Fumarase (fumarate hydratase)", "FH", "4.2.1.2")],
    "malate_dehydrogenase": [_enzyme_ref("Malate dehydrogenase (mitochondrial)", "MDH2", "1.1.1.37")],
    # amino-acid catabolism
    "aminotransferase": [_enzyme_ref("Aminotransferase (e.g. AST)", "GOT1", "2.6.1.1")],
    "glutamate_dehydrogenase": [_enzyme_ref("Glutamate dehydrogenase", "GLUD1", "1.4.1.3")],
    "bckdh": [_enzyme_ref("Branched-chain α-ketoacid dehydrogenase (E1α)", "BCKDHA", "1.2.4.4")],
    "phenylalanine_hydroxylase": [_enzyme_ref("Phenylalanine hydroxylase", "PAH", "1.14.16.1")],
    "methionine_adenosyltransferase": [_enzyme_ref("Methionine adenosyltransferase", "MAT1A", "2.5.1.6")],
    # brush-border ferrireductase (iron path)
    "duodenal_cytochrome_b": [_enzyme_ref("Duodenal cytochrome b (DcytB)", "CYBRD1", "7.2.1.3")],
}


class MetabolicMechanismRegistry:
    """
    Registry of reusable metabolic mechanisms.
    Pathways can look up mechanisms by id and attach them to edges.
    """

    def __init__(self):
        self.mechanisms: dict[str, MetabolicMechanism] = {}
        self._build_core_mechanisms()
        self._attach_references()

    def _attach_references(self) -> None:
        """Attach authoritative provenance to registered mechanisms.

        Enzyme cogs are anchored to stable gene + EC identifiers (facts, not
        fabricated PMIDs). Where a nutrition-vocabulary term already carries
        ranked PubMed leads, that term_id is linked too so the cog joins the
        evidence spine. Absence stays OPEN — nothing is invented.
        """
        for mid, refs in _MECHANISM_REFERENCES.items():
            m = self.mechanisms.get(mid)
            if m is not None:
                m.references = list(refs)

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

        # ------------------------------------------------------------------
        # AMINO-ACID CATABOLISM MECHANISMS
        # ------------------------------------------------------------------
        self.register(MetabolicMechanism(
            id="aminotransferase",
            name="Aminotransferase (Transaminase, PLP)",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Transfers an α-amino group from an amino acid to an α-keto acid "
                "(commonly α-ketoglutarate → glutamate). Requires pyridoxal phosphate (B6)."
            ),
            location="Cytosol and/or mitochondria (isoform-dependent)",
            inputs=["Amino acid", "α-Ketoglutarate"],
            outputs=["α-Keto acid", "Glutamate"],
            cofactors=["Pyridoxal phosphate (PLP / B6)"],
            notes="ALT and AST are the clinically measured liver/muscle isoforms.",
            related_pathways=[
                "aa_nitrogen_disposal",
                "bcaa_catabolism",
                "cori_glucose_alanine",
            ],
        ))

        self.register(MetabolicMechanism(
            id="glutamate_dehydrogenase",
            name="Glutamate Dehydrogenase (GDH)",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Oxidative deamination of glutamate to α-ketoglutarate, releasing free NH₄⁺ "
                "and reducing NAD(P)⁺. Regenerates the α-KG acceptor for transamination."
            ),
            location="Mitochondrial matrix (liver-enriched)",
            inputs=["Glutamate", "NAD(P)+", "H2O"],
            outputs=["α-Ketoglutarate", "NH4+", "NAD(P)H"],
            regulation=["ADP / leucine can activate (species/isoform dependent)"],
            notes="Major route from amino-N to free ammonia for the urea cycle.",
            related_pathways=["aa_nitrogen_disposal", "urea_cycle"],
        ))

        self.register(MetabolicMechanism(
            id="bckdh",
            name="Branched-Chain α-Keto Acid Dehydrogenase (BCKDH)",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Mitochondrial multienzyme complex (PDH-like) that oxidative-decarboxylates "
                "branched-chain α-keto acids from Leu, Ile, and Val. Irreversible committed step."
            ),
            location="Mitochondrial matrix",
            inputs=["Branched-chain α-keto acid", "CoA", "NAD+"],
            outputs=["Branched-chain acyl-CoA", "CO2", "NADH"],
            cofactors=["TPP", "lipoamide", "CoA", "FAD", "NAD+"],
            regulation=[
                "Inactivated by BCKDK phosphorylation",
                "Activated by PPM1K phosphatase",
            ],
            notes="Deficiency causes maple syrup urine disease (MSUD).",
            related_pathways=["bcaa_catabolism"],
        ))

        self.register(MetabolicMechanism(
            id="phenylalanine_hydroxylase",
            name="Phenylalanine Hydroxylase (PAH)",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Hydroxylates phenylalanine to tyrosine using O₂ and tetrahydrobiopterin (BH₄). "
                "The deficient enzyme in classic phenylketonuria (PKU)."
            ),
            location="Liver cytosol",
            inputs=["Phenylalanine", "O2", "BH4"],
            outputs=["Tyrosine", "H2O", "BH2"],
            cofactors=["Tetrahydrobiopterin (BH4)"],
            notes="Irreversible. Dietary Phe restriction is the classic PKU intervention.",
            related_pathways=["phenylalanine_tyrosine_catabolism"],
        ))

        self.register(MetabolicMechanism(
            id="methionine_adenosyltransferase",
            name="Methionine Adenosyltransferase (MAT / SAM synthase)",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Activates methionine with ATP to form S-adenosylmethionine (SAM), "
                "the universal methyl donor."
            ),
            location="Cytosol (liver-enriched MAT1A; ubiquitous MAT2A)",
            inputs=["Methionine", "ATP"],
            outputs=["S-Adenosylmethionine", "PPi", "Pi"],
            notes="Commits methionine into one-carbon / methylation metabolism.",
            related_pathways=["methionine_one_carbon"],
        ))

        # ------------------------------------------------------------------
        # MEAL-CRITICAL ABSORPTION / COLON (queue tier B)
        # ------------------------------------------------------------------
        self.register(MetabolicMechanism(
            id="duodenal_cytochrome_b",
            name="Duodenal Cytochrome B (DcytB) / Brush-Border Fe³⁺ Reduction",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Reduces dietary Fe³⁺ to Fe²⁺ at the duodenal brush border, expanding "
                "the ferrous pool available for DMT1 uptake. Ascorbate and other "
                "reductants support this step."
            ),
            location="Duodenal brush border",
            inputs=["Fe3+", "reductants (e.g. ascorbate)"],
            outputs=["Fe2+"],
            notes="Teaching surface reductase; not the sole reduction route.",
            related_pathways=["iron_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="dmt1",
            name="DMT1 (SLC11A2) Ferrous Iron Uptake",
            category=MechanismCategory.TRANSPORT,
            description=(
                "Proton-coupled transporter that takes up Fe²⁺ (and other divalent metals) "
                "across the apical membrane of duodenal enterocytes."
            ),
            location="Apical membrane (duodenum)",
            inputs=["Fe2+", "H+"],
            outputs=["Fe2+ (enterocyte)"],
            regulation=["Expression increases in iron deficiency"],
            notes="Primary non-haem iron apical uptake path in teaching models.",
            related_pathways=["iron_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="ferroportin",
            name="Ferroportin (SLC40A1) Iron Export",
            category=MechanismCategory.TRANSPORT,
            description=(
                "Basolateral iron exporter from enterocytes (and macrophages). "
                "Exported Fe²⁺ is oxidized and loaded onto transferrin."
            ),
            location="Basolateral membrane (enterocyte)",
            inputs=["Fe2+ (enterocyte)"],
            outputs=["Plasma iron (transferrin-bound after oxidation)"],
            regulation=["Internalized/blocked by hepcidin"],
            notes="Systemic control point for dietary iron absorption.",
            related_pathways=["iron_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="hepcidin_ferroportin",
            name="Hepcidin ⊣ Ferroportin",
            category=MechanismCategory.REGULATORY,
            description=(
                "Hepcidin binds ferroportin, causing internalization and degradation, "
                "which lowers iron export into plasma. Induced by iron repletion and "
                "inflammation (IL-6 teaching path)."
            ),
            location="Enterocyte basolateral membrane / reticuloendothelial system",
            inputs=["Hepcidin", "Ferroportin"],
            outputs=["Reduced iron export"],
            regulation=["High hepcidin when inflamed or iron-replete"],
            notes="Explains anemia of inflammation teaching pole.",
            related_pathways=["iron_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="intrinsic_factor",
            name="Intrinsic Factor–Cobalamin Binding",
            category=MechanismCategory.TRANSPORT,
            description=(
                "Gastric parietal-cell intrinsic factor binds free cobalamin (B12), "
                "forming a complex required for receptor-mediated uptake in the "
                "terminal ileum."
            ),
            location="Stomach / small intestine lumen",
            inputs=["Cobalamin (B12)", "Intrinsic factor"],
            outputs=["IF–B12 complex"],
            notes="IF deficiency → pernicious anemia (failure pole).",
            related_pathways=["cobalamin_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="glut2",
            name="GLUT2 (SLC2A2) Facilitated Hexose Transport",
            category=MechanismCategory.TRANSPORT,
            description=(
                "Facilitated glucose/fructose/galactose transporter; basolateral exit "
                "from enterocytes toward portal blood (also liver/beta-cell roles)."
            ),
            location="Basolateral enterocyte membrane (and other tissues)",
            inputs=["Glucose (enterocyte)"],
            outputs=["Glucose (interstitium / portal)"],
            notes="Complements apical SGLT1 on the absorption path.",
            related_pathways=["glucose_epithelial_transport", "carb_digestion_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="glut5",
            name="GLUT5 (SLC2A5) Fructose Transport",
            category=MechanismCategory.TRANSPORT,
            description="Apical facilitated fructose transporter in small-intestine enterocytes.",
            location="Apical enterocyte membrane",
            inputs=["Fructose (lumen)"],
            outputs=["Fructose (enterocyte)"],
            related_pathways=["glucose_epithelial_transport", "fructose_galactose"],
        ))

        self.register(MetabolicMechanism(
            id="pept1",
            name="PepT1 (SLC15A1) Proton-Coupled Oligopeptide Transport",
            category=MechanismCategory.TRANSPORT,
            description=(
                "Apical uptake of di- and tripeptides into enterocytes, driven by the "
                "proton gradient. Major route for protein nitrogen absorption."
            ),
            location="Apical membrane (small intestine)",
            inputs=["Di/tripeptides", "H+"],
            outputs=["Peptides (enterocyte)"],
            notes="Complements free amino-acid transporters.",
            related_pathways=["protein_digestion_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="colonic_fermentation",
            name="Colonic Microbial Fermentation → SCFA",
            category=MechanismCategory.MICROBIAL,
            description=(
                "Microbiota ferment fiber and resistant starch to short-chain fatty acids "
                "(acetate, propionate, butyrate) in the colon."
            ),
            location="Colon lumen",
            inputs=["Fermentable fiber", "Resistant starch"],
            outputs=["Acetate", "Propionate", "Butyrate", "gases"],
            notes="Taxa- and substrate-dependent yields; FLOW teaching only.",
            related_pathways=["scfa_colonic_production", "prebiotic_probiotic"],
        ))

        # ------------------------------------------------------------------
        # WAVE B2 — bile/micelle, one-carbon, haem iron
        # ------------------------------------------------------------------
        self.register(MetabolicMechanism(
            id="bile_salt_emulsification",
            name="Bile Salt Emulsification",
            category=MechanismCategory.DIGESTIVE,
            description=(
                "Bile salts stabilize fat emulsion droplets in the duodenal lumen, "
                "increasing surface area for pancreatic lipase."
            ),
            location="Duodenal lumen",
            inputs=["Dietary triglyceride", "Bile salts"],
            outputs=["Emulsified fat droplets"],
            notes="Prerequisite for efficient lipolysis; no enzyme catalytic site.",
            related_pathways=["lipid_digestion_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="bile_salt_micelle",
            name="Bile Salt Mixed-Micelle Formation",
            category=MechanismCategory.DIGESTIVE,
            description=(
                "Bile salts form mixed micelles that solubilize fatty acids, "
                "2-monoacylglycerol, and fat-soluble vitamins for delivery to the brush border."
            ),
            location="Duodenal / jejunal lumen",
            inputs=["Bile salts", "FFA", "2-MG", "phospholipids"],
            outputs=["Mixed micelles"],
            notes="Critical fat-vehicle gate for lipophilic cargo.",
            related_pathways=["lipid_digestion_absorption", "enterohepatic_bile"],
        ))

        self.register(MetabolicMechanism(
            id="methionine_synthase",
            name="Methionine Synthase (MTR / MS)",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Remethylates homocysteine to methionine using 5-methyl-THF as methyl donor "
                "and methylcobalamin (B12) as cofactor. Links folate and B12 one-carbon paths."
            ),
            location="Cytosol",
            inputs=["Homocysteine", "5-Methyl-THF"],
            outputs=["Methionine", "THF"],
            cofactors=["Methylcobalamin (B12)"],
            regulation=["B12 deficiency traps folate as 5-methyl-THF (folate trap)"],
            notes="MTR; also called 5-methyltetrahydrofolate-homocysteine methyltransferase.",
            related_pathways=["methionine_one_carbon", "cobalamin_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="hcp1_heme_uptake",
            name="Apical Haem Uptake (HCP1 teaching)",
            category=MechanismCategory.TRANSPORT,
            description=(
                "Apical uptake of intact dietary haem into the enterocyte. Often taught as "
                "HCP1/PCFT-related haem transport; topology is FLOW-level."
            ),
            location="Apical enterocyte membrane (duodenum)",
            inputs=["Dietary haem"],
            outputs=["Haem (enterocyte)"],
            notes="Higher fractional absorption than non-haem iron in many meals.",
            related_pathways=["iron_absorption"],
        ))

        self.register(MetabolicMechanism(
            id="heme_oxygenase_1",
            name="Heme Oxygenase-1 (HO-1)",
            category=MechanismCategory.ENZYMATIC,
            description=(
                "Cleaves haem to release Fe²⁺, biliverdin, and CO inside the enterocyte, "
                "feeding the labile ferrous pool that exits via ferroportin."
            ),
            location="Enterocyte (microsomal)",
            inputs=["Haem", "O2", "NADPH"],
            outputs=["Fe2+", "Biliverdin", "CO"],
            related_pathways=["iron_absorption"],
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
