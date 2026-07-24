"""
digestive_mechanism_layer.py
=================================================================
MECHANISM LAYER (Dynamic / Process / Executable)
Full Digestive System – Processes that operate on the Definition Layer

This module contains ONLY:
  - Named physiological processes
  - Preconditions / triggers
  - Rate laws or qualitative transition rules
  - Effects on state
  - References to Structure IDs from the Definition Layer

It never redefines what a structure *is*. It only describes
how defined structures behave under conditions.

Architecture:
  Definition Layer  →  existence + capabilities (static)
  Mechanism Layer   →  processes that use those capabilities (dynamic)
  Runtime State     →  concentrations, activation levels, fluxes, etc.
=================================================================
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ProcessCategory(Enum):
    MECHANICAL        = "mechanical"         # mastication, peristalsis, segmentation, churning
    SECRETORY         = "secretory"          # acid, enzymes, mucus, hormones, bile
    ENZYMATIC         = "enzymatic"          # luminal + membrane digestion
    ABSORPTIVE        = "absorptive"         # transporter-mediated + passive uptake
    ENDOCRINE         = "endocrine"          # hormone release and cascades
    MOTILITY          = "motility"           # ENS-driven patterns, sphincters
    MICROBIAL         = "microbial"          # fermentation, SCFA production, colonization resistance
    BARRIER           = "barrier"            # tight-junction regulation, mucus dynamics
    IMMUNE            = "immune"             # antigen sampling, antimicrobial secretion
    HEPATOBILIARY     = "hepatobiliary"      # bile synthesis, storage, enterohepatic circulation
    NEURAL            = "neural"             # vagal, ENS, spinal reflexes


class TemporalNature(Enum):
    INSTANTANEOUS     = "instantaneous"      # discrete event
    CONTINUOUS        = "continuous"         # ongoing rate
    PULSATILE         = "pulsatile"
    FEEDBACK_CONTROLLED = "feedback_controlled"


@dataclass
class Process:
    """
    One executable physiological mechanism.
    All structure references are IDs from the Definition Layer.
    """
    id: str
    name: str
    category: ProcessCategory
    description: str

    # Structures this process acts on or requires (Definition Layer IDs)
    primary_structures: list[str] = field(default_factory=list)
    supporting_structures: list[str] = field(default_factory=list)

    # Preconditions / triggers
    triggers: list[str] = field(default_factory=list)          # e.g. "nutrients_in_duodenum", "vagal_ACh"
    inhibitors: list[str] = field(default_factory=list)

    # Qualitative or symbolic rate law (no hardcoded numbers required)
    rate_law: str = ""                 # human-readable or symbolic
    temporal_nature: TemporalNature = TemporalNature.CONTINUOUS

    # What the process changes in the runtime State
    effects: list[str] = field(default_factory=list)

    # Optional quantitative placeholders (can be filled later)
    parameters: dict[str, Any] = field(default_factory=dict)

    # Cross-references
    related_processes: list[str] = field(default_factory=list)
    notes: str = ""


class DigestiveMechanismRegistry:
    """Registry of all defined mechanisms (Mechanism Layer)."""

    def __init__(self):
        self.processes: dict[str, Process] = {}
        self._build_core_mechanisms()

    def register(self, process: Process):
        self.processes[process.id] = process

    def get(self, process_id: str) -> Process | None:
        return self.processes.get(process_id)

    def by_category(self, category: ProcessCategory) -> list[Process]:
        return [p for p in self.processes.values() if p.category == category]

    def involving_structure(self, structure_id: str) -> list[Process]:
        return [p for p in self.processes.values()
                if structure_id in p.primary_structures or structure_id in p.supporting_structures]

    def list_ids(self) -> list[str]:
        return sorted(self.processes.keys())

    def summary(self) -> dict[str, int]:
        counts = {cat.value: len(self.by_category(cat)) for cat in ProcessCategory}
        counts["total"] = len(self.processes)
        return counts

    # ------------------------------------------------------------------
    # CORE MECHANISM CATALOG
    # ------------------------------------------------------------------
    def _build_core_mechanisms(self):

        # ==============================================================
        # MECHANICAL
        # ==============================================================
        self.register(Process(
            id="mastication",
            name="Mastication",
            category=ProcessCategory.MECHANICAL,
            description="Mechanical breakdown of food into bolus by teeth and tongue.",
            primary_structures=["oral_cavity"],
            triggers=["food_in_mouth", "voluntary_motor_command"],
            rate_law="particle_size_reduction_rate = f(bite_force, chewing_cycles, food_hardness)",
            temporal_nature=TemporalNature.CONTINUOUS,
            effects=["reduce_particle_size", "increase_surface_area", "form_bolus", "mix_with_saliva"]
        ))

        self.register(Process(
            id="peristalsis_esophagus",
            name="Esophageal Peristalsis",
            category=ProcessCategory.MECHANICAL,
            description="Coordinated contraction wave that propels bolus from pharynx to stomach.",
            primary_structures=["esophagus"],
            supporting_structures=["upper_esophageal_sphincter", "lower_esophageal_sphincter"],
            triggers=["swallowing_reflex", "bolus_in_esophagus"],
            rate_law="propagation_velocity ≈ 3–5 cm/s; LES relaxation precedes bolus arrival",
            temporal_nature=TemporalNature.PULSATILE,
            effects=["propel_bolus_distally", "les_relaxation"]
        ))

        self.register(Process(
            id="gastric_churning",
            name="Gastric Churning & Retropulsion",
            category=ProcessCategory.MECHANICAL,
            description="Antral peristalsis and retropulsion that grind solids into chyme.",
            primary_structures=["stomach", "antrum", "pylorus"],
            triggers=["gastric_distension", "vagal_input", "gastrin"],
            inhibitors=["duodenal_distension", "low_duodenal_pH", "CCK", "PYY"],
            rate_law="grinding_rate = f(antral_contraction_strength, pyloric_tone)",
            temporal_nature=TemporalNature.CONTINUOUS,
            effects=["reduce_particle_size", "mix_with_acid_and_pepsin", "control_emptying"]
        ))

        self.register(Process(
            id="segmentation_small_intestine",
            name="Small-Intestinal Segmentation",
            category=ProcessCategory.MECHANICAL,
            description="Stationary contractions that mix chyme and enhance contact with mucosa.",
            primary_structures=["duodenum", "jejunum", "ileum"],
            supporting_structures=["enteric_nervous_system"],
            triggers=["local_distension", "ENS_circuitry"],
            rate_law="frequency decreases aborally (≈12/min duodenum → 8–9/min ileum)",
            temporal_nature=TemporalNature.CONTINUOUS,
            effects=["mix_chyme", "increase_mucosal_contact", "slow_transit"]
        ))

        self.register(Process(
            id="migrating_motor_complex",
            name="Migrating Motor Complex (MMC)",
            category=ProcessCategory.MOTILITY,
            description="Interdigestive housekeeper wave that clears residual content.",
            primary_structures=["stomach", "duodenum", "jejunum", "ileum"],
            supporting_structures=["enteric_nervous_system"],
            triggers=["fasting_state", "motilin_peak"],
            inhibitors=["feeding", "nutrients_in_lumen"],
            rate_law="Cycle period ≈ 90–120 min in humans; Phase III is the activity front",
            temporal_nature=TemporalNature.PULSATILE,
            effects=["clear_residual_debris", "prevent_bacterial_overgrowth"]
        ))

        # ==============================================================
        # SECRETORY
        # ==============================================================
        self.register(Process(
            id="salivary_secretion",
            name="Salivary Secretion",
            category=ProcessCategory.SECRETORY,
            description="Production of saliva containing amylase, mucus, electrolytes, and IgA.",
            primary_structures=["salivary_glands", "oral_cavity"],
            triggers=["cephalic_phase", "taste", "mastication", "parasympathetic_ACh"],
            rate_law="flow_rate = f(parasympathetic_tone); amylase content higher in stimulated saliva",
            effects=["lubricate_bolus", "initiate_starch_digestion", "antimicrobial_action"]
        ))

        self.register(Process(
            id="gastric_acid_secretion",
            name="Gastric Acid Secretion",
            category=ProcessCategory.SECRETORY,
            description="HCl secretion by parietal cells via H+/K+-ATPase.",
            primary_structures=["stomach", "parietal_cells"],
            supporting_structures=["ecl_cells", "g_cells", "d_cells"],
            triggers=["histamine_H2", "gastrin_CCK2R", "ACh_M3", "cephalic_phase", "gastric_distension"],
            inhibitors=["somatostatin", "low_pH_feedback", "prostaglandins", "secretin", "CCK"],
            rate_law="H+ secretion rate controlled by insertion of H+/K+-ATPase into canalicular membrane",
            temporal_nature=TemporalNature.FEEDBACK_CONTROLLED,
            effects=["lower_gastric_pH", "activate_pepsinogen", "denature_proteins", "kill_microbes"],
            related_processes=["pepsinogen_secretion", "intrinsic_factor_secretion"]
        ))

        self.register(Process(
            id="pepsinogen_secretion",
            name="Pepsinogen Secretion & Activation",
            category=ProcessCategory.SECRETORY,
            description="Chief-cell release of pepsinogen; autoactivated to pepsin at low pH.",
            primary_structures=["stomach", "chief_cells"],
            triggers=["ACh", "gastrin", "low_pH"],
            effects=["protein_digestion_begins"],
            related_processes=["gastric_acid_secretion"]
        ))

        self.register(Process(
            id="intrinsic_factor_secretion",
            name="Intrinsic Factor Secretion",
            category=ProcessCategory.SECRETORY,
            description="Parietal-cell secretion of intrinsic factor required for B12 absorption.",
            primary_structures=["stomach"],
            triggers=["same_as_acid_secretion"],
            effects=["enable_B12_absorption_in_ileum"],
            related_processes=["b12_absorption"]
        ))

        self.register(Process(
            id="bicarbonate_secretion_duodenum",
            name="Duodenal & Pancreatic Bicarbonate Secretion",
            category=ProcessCategory.SECRETORY,
            description="HCO3- secretion that neutralizes gastric acid in the duodenal lumen.",
            primary_structures=["duodenum", "pancreas", "brunners_glands"],
            triggers=["secretin", "low_duodenal_pH"],
            rate_law="HCO3- output ≈ proportional to secretin concentration (within physiological range)",
            effects=["raise_duodenal_pH", "protect_mucosa", "optimize_enzyme_pH"]
        ))

        self.register(Process(
            id="bile_secretion_and_release",
            name="Bile Synthesis, Storage & CCK-triggered Release",
            category=ProcessCategory.HEPATOBILIARY,
            description="Hepatocyte bile formation → gallbladder concentration → CCK-mediated ejection.",
            primary_structures=["liver", "gallbladder", "sphincter_of_oddi", "duodenum"],
            triggers=["CCK", "fatty_acids_and_amino_acids_in_duodenum"],
            inhibitors=["somatostatin", "fasting"],
            rate_law="Gallbladder ejection fraction increases with CCK; bile flow also has a continuous hepatic component",
            effects=["deliver_bile_acids", "enable_micelle_formation", "excrete_bilirubin_and_cholesterol"],
            related_processes=["micelle_formation", "enterohepatic_circulation"]
        ))

        self.register(Process(
            id="pancreatic_enzyme_secretion",
            name="Pancreatic Acinar Enzyme Secretion",
            category=ProcessCategory.SECRETORY,
            description="CCK- and ACh-stimulated release of zymogens and active enzymes.",
            primary_structures=["pancreas"],
            triggers=["CCK", "ACh", "cephalic_and_intestinal_phases"],
            rate_law="Enzyme output rises steeply with CCK in physiological range",
            effects=["deliver_amylase", "deliver_lipase_colipase", "deliver_proteases", "deliver_nucleases"]
        ))

        # ==============================================================
        # ENZYMATIC DIGESTION
        # ==============================================================
        self.register(Process(
            id="luminal_starch_digestion",
            name="Luminal Starch Digestion",
            category=ProcessCategory.ENZYMATIC,
            description="α-Amylase (salivary + pancreatic) cleaves starch to maltose, maltotriose, limit dextrins.",
            primary_structures=["oral_cavity", "duodenum", "jejunum"],
            triggers=["starch_present", "amylase_activity"],
            rate_law="Hydrolysis rate depends on enzyme concentration and starch accessibility (particle size, RS content)",
            effects=["produce_maltose", "produce_maltotriose", "produce_limit_dextrins"]
        ))

        self.register(Process(
            id="brush_border_carbohydrate_digestion",
            name="Brush-Border Carbohydrate Digestion",
            category=ProcessCategory.ENZYMATIC,
            description="Membrane-bound disaccharidases (maltase, sucrase-isomaltase, lactase) produce monosaccharides.",
            primary_structures=["brush_border", "enterocyte", "jejunum", "duodenum"],
            triggers=["disaccharides_or_limit_dextrins_present"],
            effects=["produce_glucose", "produce_galactose", "produce_fructose"]
        ))

        self.register(Process(
            id="luminal_protein_digestion",
            name="Luminal Protein Digestion",
            category=ProcessCategory.ENZYMATIC,
            description="Pepsin + pancreatic proteases (trypsin, chymotrypsin, elastase, carboxypeptidases) generate oligopeptides and amino acids.",
            primary_structures=["stomach", "duodenum", "jejunum"],
            triggers=["protein_present", "active_proteases"],
            effects=["produce_oligopeptides", "produce_free_amino_acids"]
        ))

        self.register(Process(
            id="brush_border_peptide_digestion",
            name="Brush-Border Peptide Digestion",
            category=ProcessCategory.ENZYMATIC,
            description="Membrane peptidases complete digestion of oligopeptides to absorbable forms.",
            primary_structures=["brush_border", "enterocyte"],
            effects=["produce_di_tri_peptides", "produce_free_amino_acids"]
        ))

        self.register(Process(
            id="fat_digestion_and_micelle_formation",
            name="Fat Digestion & Micelle Formation",
            category=ProcessCategory.ENZYMATIC,
            description="Pancreatic lipase + colipase + bile acids → 2-monoglycerides + free fatty acids packaged into mixed micelles.",
            primary_structures=["duodenum", "jejunum", "liver", "gallbladder"],
            triggers=["triglyceride_present", "bile_acids", "pancreatic_lipase"],
            rate_law="Lipolysis rate limited by interfacial area and bile-acid concentration; colipase overcomes inhibition by bile acids",
            effects=["produce_2_monoglycerides", "produce_free_fatty_acids", "form_mixed_micelles"],
            related_processes=["bile_secretion_and_release"]
        ))

        # ==============================================================
        # ABSORPTIVE
        # ==============================================================
        self.register(Process(
            id="sglt1_glucose_uptake",
            name="SGLT1-Mediated Glucose/Galactose Uptake",
            category=ProcessCategory.ABSORPTIVE,
            description="Secondary active transport of glucose and galactose across apical membrane via SGLT1.",
            primary_structures=["sglt1", "enterocyte", "jejunum", "duodenum"],
            triggers=["glucose_or_galactose_in_lumen", "transmural_Na_gradient"],
            rate_law="J = Jmax * [S] / (Km + [S]) * f(Na_gradient); saturates at high luminal glucose",
            temporal_nature=TemporalNature.CONTINUOUS,
            effects=["apical_glucose_influx", "increase_enterocyte_glucose", "indirect_water_absorption"],
            parameters={"Km_glucose_approx_mM": 0.5, "notes": "Highly efficient at low concentrations"}
        ))

        self.register(Process(
            id="glut2_basolateral_exit",
            name="GLUT2-Mediated Basolateral Glucose Exit",
            category=ProcessCategory.ABSORPTIVE,
            description="Facilitated diffusion of glucose out of enterocyte into capillary blood.",
            primary_structures=["glut2", "enterocyte"],
            triggers=["elevated_enterocyte_glucose"],
            rate_law="Facilitated diffusion; net flux driven by concentration gradient",
            effects=["deliver_glucose_to_portal_blood"]
        ))

        self.register(Process(
            id="pept1_peptide_uptake",
            name="PEPT1-Mediated Di/Tripeptide Uptake",
            category=ProcessCategory.ABSORPTIVE,
            description="H+-coupled uptake of di- and tripeptides via PEPT1.",
            primary_structures=["pept1", "enterocyte", "jejunum"],
            triggers=["di_tri_peptides_in_lumen", "apical_proton_gradient"],
            rate_law="Proton-coupled cotransport; broad substrate specificity",
            effects=["peptide_influx", "subsequent_cytosolic_hydrolysis"]
        ))

        self.register(Process(
            id="fat_absorption_via_micelles",
            name="Micellar Delivery & Fat Absorption",
            category=ProcessCategory.ABSORPTIVE,
            description="Mixed micelles ferry lipid digestion products across the unstirred layer; lipids then enter enterocytes.",
            primary_structures=["duodenum", "jejunum", "enterocyte"],
            triggers=["mixed_micelles_present"],
            effects=["fatty_acid_and_monoglyceride_uptake", "cholesterol_uptake_via_NPC1L1", "chylomicron_assembly"],
            related_processes=["fat_digestion_and_micelle_formation", "npc1l1_cholesterol_uptake"]
        ))

        self.register(Process(
            id="npc1l1_cholesterol_uptake",
            name="NPC1L1-Mediated Cholesterol Uptake",
            category=ProcessCategory.ABSORPTIVE,
            description="Apical cholesterol absorption via NPC1L1 (ezetimibe target).",
            primary_structures=["npc1l1", "enterocyte", "jejunum"],
            effects=["cholesterol_influx"]
        ))

        self.register(Process(
            id="b12_absorption",
            name="Vitamin B12 (Cobalamin) Absorption",
            category=ProcessCategory.ABSORPTIVE,
            description="IF–B12 complex binds cubam receptor in ileum and is absorbed by endocytosis.",
            primary_structures=["ileum", "stomach"],
            triggers=["IF_B12_complex_present", "ileal_cubam_receptor"],
            effects=["B12_uptake"],
            related_processes=["intrinsic_factor_secretion"],
            notes="Requires both gastric intrinsic factor and intact terminal ileum."
        ))

        self.register(Process(
            id="bile_acid_reabsorption",
            name="Ileal Bile Acid Reabsorption (ASBT)",
            category=ProcessCategory.ABSORPTIVE,
            description="Apical sodium-dependent bile acid transport in terminal ileum; first step of enterohepatic circulation.",
            primary_structures=["asbt", "ileum"],
            triggers=["bile_acids_in_ileal_lumen"],
            rate_law="Secondary active Na+-coupled transport; high capacity in healthy ileum",
            effects=["bile_acid_uptake", "initiate_enterohepatic_circulation"],
            related_processes=["enterohepatic_circulation"]
        ))

        self.register(Process(
            id="scfa_absorption",
            name="SCFA Absorption in Colon",
            category=ProcessCategory.ABSORPTIVE,
            description="Absorption of acetate, propionate, butyrate by colonocytes (monocarboxylate transporters + diffusion).",
            primary_structures=["colonocyte", "ascending_colon", "transverse_colon", "descending_colon"],
            triggers=["SCFAs_produced_by_fermentation"],
            effects=["scfa_uptake", "colonocyte_energy_supply", "systemic_scfa_delivery"],
            related_processes=["microbial_fermentation_scfa"]
        ))

        # ==============================================================
        # ENDOCRINE CASCADES
        # ==============================================================
        self.register(Process(
            id="gastrin_release",
            name="Gastrin Release",
            category=ProcessCategory.ENDOCRINE,
            description="G-cell secretion of gastrin in response to peptides, amino acids, distension, and vagal input.",
            primary_structures=["g_cell", "antrum", "stomach"],
            triggers=["peptides_amino_acids", "gastric_distension", "vagal_GRP"],
            inhibitors=["low_pH", "somatostatin"],
            effects=["stimulate_acid_secretion", "stimulate_mucosal_growth", "stimulate_ECL_histamine"],
            related_processes=["gastric_acid_secretion"]
        ))

        self.register(Process(
            id="cck_release",
            name="CCK Release",
            category=ProcessCategory.ENDOCRINE,
            description="I-cell secretion of cholecystokinin in response to fatty acids and amino acids.",
            primary_structures=["i_cell", "duodenum", "jejunum"],
            triggers=["fatty_acids", "amino_acids", "monitor_peptide"],
            effects=["gallbladder_contraction", "sphincter_of_oddi_relaxation",
                     "pancreatic_enzyme_secretion", "gastric_emptying_delay", "satiety"],
            related_processes=["bile_secretion_and_release", "pancreatic_enzyme_secretion"]
        ))

        self.register(Process(
            id="secretin_release",
            name="Secretin Release",
            category=ProcessCategory.ENDOCRINE,
            description="S-cell secretion of secretin in response to low duodenal pH.",
            primary_structures=["s_cell", "duodenum"],
            triggers=["duodenal_pH < 4.5"],
            effects=["pancreatic_bicarbonate_secretion", "bile_duct_bicarbonate", "inhibit_acid"],
            related_processes=["bicarbonate_secretion_duodenum"]
        ))

        self.register(Process(
            id="incretin_release",
            name="Incretin Release (GIP + GLP-1)",
            category=ProcessCategory.ENDOCRINE,
            description="K-cell (GIP) and L-cell (GLP-1) secretion in response to nutrient arrival; amplifies insulin secretion.",
            primary_structures=["k_cell", "l_cell", "duodenum", "jejunum", "ileum"],
            triggers=["glucose", "fat", "protein", "rate_of_nutrient_arrival"],
            rate_law="Response is stronger with faster rate of nutrient appearance, not only absolute load",
            effects=["amplify_glucose_stimulated_insulin", "slow_gastric_emptying", "satiety", "glucagon_suppression"],
            notes="Classic example of rate-sensitive (not just concentration-sensitive) sensing."
        ))

        self.register(Process(
            id="pyy_release",
            name="PYY Release",
            category=ProcessCategory.ENDOCRINE,
            description="L-cell secretion of peptide YY; contributes to ileal brake and satiety.",
            primary_structures=["l_cell", "ileum", "colon"],
            triggers=["fat", "protein", "SCFAs"],
            effects=["ileal_brake", "slow_transit", "satiety"]
        ))

        # ==============================================================
        # MICROBIAL / FERMENTATION
        # ==============================================================
        self.register(Process(
            id="microbial_fermentation_scfa",
            name="Microbial Fermentation → SCFA Production",
            category=ProcessCategory.MICROBIAL,
            description="Anaerobic fermentation of fiber and resistant starch by colonic microbiota yielding acetate, propionate, butyrate.",
            primary_structures=["ascending_colon", "transverse_colon", "descending_colon",
                                "cecum", "colonocyte"],
            triggers=["fermentable_fiber_or_RS_present", "anaerobic_conditions", "active_microbiota"],
            rate_law="SCFA yield and ratio depend on substrate type (RS2/RS3 favor butyrate) and microbiome composition",
            temporal_nature=TemporalNature.CONTINUOUS,
            effects=["produce_acetate", "produce_propionate", "produce_butyrate",
                     "lower_luminal_pH", "supply_colonocyte_energy"],
            related_processes=["scfa_absorption", "gpr_scfa_signaling"]
        ))

        self.register(Process(
            id="gpr_scfa_signaling",
            name="SCFA Receptor Signaling (GPR41/43/109A)",
            category=ProcessCategory.MICROBIAL,
            description="Activation of SCFA sensors leading to hormone release, immune modulation, and anti-inflammatory effects.",
            primary_structures=["gpr41", "gpr43", "gpr109a", "l_cell", "colonocyte"],
            triggers=["acetate", "propionate", "butyrate"],
            effects=["glp1_pyy_release", "anti_inflammatory_signaling", "barrier_support"],
            related_processes=["microbial_fermentation_scfa", "incretin_release"]
        ))

        # ==============================================================
        # BARRIER & IMMUNE
        # ==============================================================
        self.register(Process(
            id="tight_junction_regulation",
            name="Tight-Junction Permeability Regulation",
            category=ProcessCategory.BARRIER,
            description="Dynamic control of paracellular permeability by cytokines, butyrate, myosin light-chain kinase, etc.",
            primary_structures=["tight_junction", "enterocyte", "colonocyte", "enteric_glial_cell"],
            triggers=["cytokines", "pathogen_products", "butyrate", "ethanol", "stress"],
            effects=["modulate_paracellular_flux", "barrier_integrity_change"]
        ))

        self.register(Process(
            id="mucus_layer_dynamics",
            name="Mucus Layer Secretion & Turnover",
            category=ProcessCategory.BARRIER,
            description="Goblet-cell mucin secretion forming inner (sterile) and outer (colonized) mucus layers in colon.",
            primary_structures=["goblet_cell", "mucus_layer", "colon"],
            triggers=["local_irritation", "microbial_products", "acetylcholine"],
            effects=["maintain_physical_barrier", "provide_microbial_habitat"]
        ))

        self.register(Process(
            id="m_cell_antigen_sampling",
            name="M-Cell Antigen Sampling",
            category=ProcessCategory.IMMUNE,
            description="Transcytosis of luminal antigens by M cells into Peyer’s patches for immune induction.",
            primary_structures=["m_cell", "peyers_patch", "ileum"],
            triggers=["luminal_antigen_or_microbe_contact"],
            effects=["deliver_antigen_to_immune_cells", "initiate_mucosal_immune_response"]
        ))

        self.register(Process(
            id="paneth_cell_defensin_release",
            name="Paneth Cell Antimicrobial Secretion",
            category=ProcessCategory.IMMUNE,
            description="Release of α-defensins, lysozyme, and phospholipase A2 that shape the crypt microbiome.",
            primary_structures=["paneth_cell", "crypt_of_lieberkuhn"],
            triggers=["microbial_products", "cholinergic_stimuli"],
            effects=["kill_or_inhibit_bacteria", "protect_stem_cell_niche"]
        ))

        # ==============================================================
        # ENTEROHEPATIC & SPECIAL
        # ==============================================================
        self.register(Process(
            id="enterohepatic_circulation",
            name="Enterohepatic Circulation of Bile Acids",
            category=ProcessCategory.HEPATOBILIARY,
            description="Cyclical pathway: hepatic synthesis → bile → intestine → ileal reabsorption → portal return → liver re-uptake.",
            primary_structures=["liver", "gallbladder", "ileum", "asbt"],
            triggers=["bile_acid_secretion", "ileal_ASBT_activity"],
            rate_law=">90% of bile acids are reabsorbed each cycle in healthy humans; fecal loss is the main route of cholesterol excretion",
            effects=["conserve_bile_acids", "regulate_hepatic_cholesterol_and_bile_acid_synthesis"],
            related_processes=["bile_secretion_and_release", "bile_acid_reabsorption"]
        ))

        self.register(Process(
            id="ileal_brake",
            name="Ileal Brake",
            category=ProcessCategory.MOTILITY,
            description="Nutrient-induced slowing of proximal transit and gastric emptying mediated by PYY, GLP-1, and neural pathways.",
            primary_structures=["ileum", "l_cell", "stomach", "jejunum"],
            triggers=["fat_or_protein_in_ileum", "PYY", "GLP1"],
            effects=["slow_gastric_emptying", "slow_small_bowel_transit", "increase_satiety"]
        ))

def _register_priority_expansions(registry: DigestiveMechanismRegistry):
    registry.register(Process(
        id="electroneutral_nacl_absorption",
        name="Electroneutral NaCl Absorption (NHE3 + DRA)",
        category=ProcessCategory.ABSORPTIVE,
        description="Coupled apical Na+/H+ (NHE3) and Cl-/HCO3- (DRA) exchange – bulk electroneutral NaCl absorption.",
        primary_structures=["nhe3", "dra", "jejunum", "ileum", "colonocyte"],
        triggers=["luminal_sodium", "luminal_chloride"],
        rate_law="Parallel NHE3 + DRA activity; net NaCl absorption without generating transepithelial voltage",
        effects=["sodium_absorption", "chloride_absorption", "bicarbonate_secretion_into_lumen"]
    ))
    registry.register(Process(
        id="enterogastric_reflex",
        name="Enterogastric Reflex",
        category=ProcessCategory.MOTILITY,
        description="Duodenal feedback inhibiting gastric emptying and acid secretion.",
        primary_structures=["duodenum", "stomach", "pyloric_sphincter"],
        triggers=["low_duodenal_pH", "duodenal_distension", "fatty_acids_in_duodenum"],
        effects=["slow_gastric_emptying", "reduce_acid_secretion", "increase_pyloric_tone"],
        related_processes=["cck_release", "secretin_release"]
    ))
    registry.register(Process(
        id="mucus_turnover",
        name="Mucus Layer Turnover & Bilayer Maintenance",
        category=ProcessCategory.BARRIER,
        description="Continuous secretion, expansion and shedding of inner firm and outer loose mucus layers.",
        primary_structures=["goblet_cell", "inner_mucus_layer_colon", "outer_mucus_layer_colon"],
        triggers=["local_irritation", "microbial_products", "acetylcholine"],
        rate_law="Inner layer remains largely sterile; outer layer is continuously generated from inner layer and colonized",
        effects=["maintain_physical_barrier", "provide_microbial_habitat"]
    ))
    registry.register(Process(
        id="incretin_rate_of_arrival_sensing",
        name="Incretin Response to Rate-of-Nutrient-Arrival",
        category=ProcessCategory.ENDOCRINE,
        description="GLP-1/GIP release is markedly stronger when nutrients arrive rapidly versus a slow continuous load.",
        primary_structures=["l_cell", "k_cell", "duodenum", "jejunum", "ileum"],
        triggers=["rapid_glucose_or_fat_appearance"],
        rate_law="Non-linear with respect to rate-of-appearance; same total load → larger incretin release when delivered faster",
        temporal_nature=TemporalNature.FEEDBACK_CONTROLLED,
        effects=["amplified_glp1_gip_release", "stronger_insulin_potentiation", "stronger_gastric_emptying_delay"]
    ))

def _register_signaling_linked_mechanisms(registry: DigestiveMechanismRegistry):
    extras = [
        Process(
            id="vagal_afferent_signaling",
            name="Vagal Afferent Signaling",
            category=ProcessCategory.NEURAL,
            description="Transmission of gut-derived mechanical, nutrient and hormonal signals to the nucleus tractus solitarius.",
            primary_structures=["enteric_nervous_system", "i_cell", "l_cell", "enterochromaffin_cell"],
            triggers=["stretch", "cck", "glp1", "serotonin", "nutrients"],
            effects=["satiety_signaling", "nausea_signaling", "reflex_modulation_of_motility_and_secretion"],
            related_processes=["cck_release", "incretin_release"]
        ),
        Process(
            id="cephalic_phase_response",
            name="Cephalic Phase Response",
            category=ProcessCategory.NEURAL,
            description="Brain-initiated (vagal) preparatory secretion of saliva, acid and pancreatic juice before food reaches the stomach.",
            primary_structures=["salivary_glands", "stomach", "pancreas"],
            triggers=["sight_smell_taste_of_food", "thought_of_food", "vagal_efferent_activity"],
            effects=["increase_salivary_flow", "increase_acid_secretion", "increase_pancreatic_secretion"],
            related_processes=["salivary_secretion", "gastric_acid_secretion", "pancreatic_enzyme_secretion"]
        ),
        Process(
            id="serotonin_peristaltic_reflex",
            name="Serotonin-Initiated Peristaltic Reflex",
            category=ProcessCategory.NEURAL,
            description="EC-cell 5-HT release activates intrinsic primary afferent neurons and initiates ascending contraction / descending relaxation.",
            primary_structures=["enterochromaffin_cell", "enteric_nervous_system", "myenteric_plexus"],
            triggers=["mucosal_stroking", "chemical_stimuli", "pressure"],
            effects=["initiate_peristalsis", "coordinate_ascending_and_descending_limbs"],
            related_processes=["segmentation_small_intestine"]
        ),
        Process(
            id="butyrate_hdac_barrier_effect",
            name="Butyrate HDAC Inhibition & Barrier Effect",
            category=ProcessCategory.BARRIER,
            description="Butyrate inhibits histone deacetylases and activates GPR109A, reinforcing tight junctions and suppressing inflammatory tone.",
            primary_structures=["colonocyte", "gpr109a", "tight_junction"],
            triggers=["butyrate"],
            effects=["hdac_inhibition", "increase_barrier_integrity", "anti_inflammatory_gene_expression"],
            related_processes=["gpr_scfa_signaling", "tight_junction_regulation", "microbial_fermentation_scfa"]
        ),
    ]
    for p in extras:
        if p.id not in registry.processes:
            registry.register(p)

def _register_gut_brain_mechanisms(registry: DigestiveMechanismRegistry):
    extras = [
        Process(
            id="crf_stress_barrier_response",
            name="CRF / Stress → Barrier Response",
            category=ProcessCategory.BARRIER,
            description="Central and peripheral CRF signaling increases epithelial permeability and alters motility under stress.",
            primary_structures=["tight_junction", "enteric_nervous_system", "epithelium"],
            triggers=["psychological_stress", "crf", "cortisol", "sympathetic_activation"],
            effects=["increase_permeability", "mast_cell_activation", "visceral_hypersensitivity", "alter_motility"],
            related_processes=["tight_junction_regulation", "mucus_turnover"]
        ),
        Process(
            id="tryptophan_metabolic_branching",
            name="Tryptophan → Serotonin vs Kynurenine Branching",
            category=ProcessCategory.NEURAL,
            description="Partitioning of tryptophan between EC-cell serotonin synthesis and the IDO/TDO kynurenine pathway; inflammation shifts flux toward kynurenine.",
            primary_structures=["enterochromaffin_cell", "immune_cells"],
            triggers=["dietary_tryptophan", "inflammatory_cytokines", "ido_activity"],
            effects=["serotonin_production", "kynurenine_production", "modulate_ens_and_mood_signaling"],
            related_processes=["serotonin_peristaltic_reflex"]
        ),
    ]
    for p in extras:
        if p.id not in registry.processes:
            registry.register(p)


def get_digestive_mechanism_registry() -> DigestiveMechanismRegistry:
    """Return a fully populated Mechanism Layer registry (single factory)."""
    reg = DigestiveMechanismRegistry()
    _register_priority_expansions(reg)
    _register_signaling_linked_mechanisms(reg)
    _register_gut_brain_mechanisms(reg)
    return reg


if __name__ == "__main__":
    reg = get_digestive_mechanism_registry()
    print("=== Digestive Mechanism Layer Summary ===")
    for cat, count in reg.summary().items():
        print(f"  {cat:20s}: {count:3d}")
    print(f"\nTotal processes defined: {len(reg.list_ids())}")

