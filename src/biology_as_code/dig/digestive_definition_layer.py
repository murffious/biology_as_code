"""
digestive_definition_layer.py
=================================================================
DEFINITION LAYER (Static / Declarative Taxonomy)
Full Digestive System – Existence Types, Properties, Capabilities

This module contains ONLY:
  - What structures exist
  - Their multi-system roles
  - Hierarchical relationships & anatomical connections
  - Molecular / cellular inventory present on each node
  - Time-invariant attributes and capabilities

NO kinetics, rate laws, temporal derivatives, or state changes.
Those belong in the Mechanism Layer.

Architecture follows the two-layer principle:
  Definition  = data model / schema / ontology
  Mechanism   = algorithms that operate on the defined structures
=================================================================
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class SystemRole(Enum):
    """Strength of a structure's participation in a physiological system."""
    PRIMARY    = "primary"
    SECONDARY  = "secondary"
    SUPPORTING = "supporting"
    PRESENT    = "present"
    NONE       = "none"


class AnatomicalSystem(Enum):
    DIGESTIVE       = "digestive"
    ENDOCRINE       = "endocrine"
    IMMUNE          = "immune"
    NERVOUS         = "nervous"
    CIRCULATORY     = "circulatory"
    LYMPHATIC       = "lymphatic"
    MICROBIOME_HOST = "microbiome_host"
    MUSCULOSKELETAL = "musculoskeletal"


class StructureCategory(Enum):
    MACRO_SEGMENT        = "macro_segment"
    ACCESSORY_ORGAN      = "accessory_organ"
    MICRO_STRUCTURE      = "micro_structure"
    CELL_TYPE            = "cell_type"
    MOLECULAR_COMPONENT  = "molecular_component"
    JUNCTION             = "junction"
    REGION               = "region"
    MICROBIOME_COMPONENT = "microbiome_component"


@dataclass
class Structure:
    """Pure definition of one digestive-system entity."""
    id: str
    name: str
    category: StructureCategory
    location: str
    systems: dict[AnatomicalSystem, SystemRole] = field(default_factory=dict)
    components: list[str] = field(default_factory=list)
    connections: list[str] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    synonyms: list[str] = field(default_factory=list)

    def has_system_role(self, system: AnatomicalSystem,
                        min_role: SystemRole = SystemRole.SUPPORTING) -> bool:
        role = self.systems.get(system, SystemRole.NONE)
        order = [SystemRole.NONE, SystemRole.PRESENT, SystemRole.SUPPORTING,
                 SystemRole.SECONDARY, SystemRole.PRIMARY]
        return order.index(role) >= order.index(min_role)


class DigestiveDefinitionRegistry:
    """Central registry of all defined structures (Definition Layer)."""

    def __init__(self):
        self.structures: dict[str, Structure] = {}
        self._build_full_taxonomy()

    def register(self, structure: Structure):
        self.structures[structure.id] = structure

    def get(self, structure_id: str) -> Structure | None:
        return self.structures.get(structure_id)

    def by_category(self, category: StructureCategory) -> list[Structure]:
        return [s for s in self.structures.values() if s.category == category]

    def by_system(self, system: AnatomicalSystem,
                  min_role: SystemRole = SystemRole.SECONDARY) -> list[Structure]:
        return [s for s in self.structures.values() if s.has_system_role(system, min_role)]

    def list_ids(self) -> list[str]:
        return sorted(self.structures.keys())

    def summary(self) -> dict[str, int]:
        counts = {cat.value: len(self.by_category(cat)) for cat in StructureCategory}
        counts["total"] = len(self.structures)
        return counts

    def _build_full_taxonomy(self):
        # ------------------------------------------------------------------
        # MACRO SEGMENTS
        # ------------------------------------------------------------------
        self.register(Structure(
            id="oral_cavity", name="Oral Cavity",
            category=StructureCategory.MACRO_SEGMENT,
            location="Head – beginning of alimentary canal",
            systems={
                AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                AnatomicalSystem.NERVOUS: SystemRole.SECONDARY,
                AnatomicalSystem.IMMUNE: SystemRole.SUPPORTING,
                AnatomicalSystem.MUSCULOSKELETAL: SystemRole.SECONDARY,
            },
            components=["tongue", "teeth", "salivary_glands", "taste_buds", "oral_mucosa"],
            connections=["pharynx"],
            attributes={"mechanical_breakdown": True, "initial_starch_digestion": True,
                        "initial_lipid_digestion": True, "taste_sensing": True},
            description="Site of mastication, bolus formation, and initial enzymatic digestion."
        ))

        self.register(Structure(
            id="pharynx", name="Pharynx",
            category=StructureCategory.MACRO_SEGMENT,
            location="Throat – shared respiratory/digestive pathway",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.NERVOUS: SystemRole.SECONDARY,
                     AnatomicalSystem.MUSCULOSKELETAL: SystemRole.SECONDARY},
            connections=["oral_cavity", "esophagus"],
            attributes={"swallowing_reflex": True},
            description="Conduit for bolus transfer during deglutition."
        ))

        self.register(Structure(
            id="esophagus", name="Esophagus",
            category=StructureCategory.MACRO_SEGMENT,
            location="Mediastinum – connects pharynx to stomach",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.NERVOUS: SystemRole.SECONDARY,
                     AnatomicalSystem.MUSCULOSKELETAL: SystemRole.SECONDARY},
            components=["upper_esophageal_sphincter", "lower_esophageal_sphincter"],
            connections=["pharynx", "stomach"],
            attributes={"peristalsis": True, "no_significant_absorption": True,
                        "stratified_squamous_epithelium": True},
            description="Muscular tube that propels bolus to the stomach via peristalsis."
        ))

        self.register(Structure(
            id="stomach", name="Stomach",
            category=StructureCategory.MACRO_SEGMENT,
            location="Left upper quadrant – J-shaped reservoir",
            systems={
                AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                AnatomicalSystem.ENDOCRINE: SystemRole.SECONDARY,
                AnatomicalSystem.IMMUNE: SystemRole.SUPPORTING,
                AnatomicalSystem.NERVOUS: SystemRole.SECONDARY,
            },
            components=["cardia", "fundus", "body_of_stomach", "antrum", "pylorus",
                        "parietal_cells", "chief_cells", "g_cells", "ecl_cells", "d_cells"],
            connections=["esophagus", "duodenum"],
            attributes={"acid_secretion": True, "pepsinogen_secretion": True,
                        "intrinsic_factor_secretion": True, "mechanical_churning": True,
                        "reservoir_function": True, "ghrelin_production": True},
            description="Reservoir for mechanical and chemical digestion; produces acid, pepsin, intrinsic factor, and hormones."
        ))

        for region, desc in [("cardia", "Entry region near esophagus"),
                             ("fundus", "Superior dome"),
                             ("body_of_stomach", "Main central region"),
                             ("antrum", "Distal region; gastrin production"),
                             ("pylorus", "Outflow region controlling emptying")]:
            self.register(Structure(
                id=region, name=region.replace("_", " ").title(),
                category=StructureCategory.REGION, location=f"Stomach – {desc}",
                systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
                connections=["stomach"], description=desc
            ))

        self.register(Structure(
            id="duodenum", name="Duodenum",
            category=StructureCategory.MACRO_SEGMENT,
            location="Retroperitoneal – first 25–30 cm of small intestine",
            systems={
                AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                AnatomicalSystem.ENDOCRINE: SystemRole.PRIMARY,
                AnatomicalSystem.IMMUNE: SystemRole.SECONDARY,
                AnatomicalSystem.NERVOUS: SystemRole.SECONDARY,
                AnatomicalSystem.CIRCULATORY: SystemRole.SECONDARY,
            },
            components=["brunners_glands", "villi", "crypts", "i_cells", "s_cells", "k_cells"],
            connections=["stomach", "jejunum", "pancreas", "gallbladder", "liver"],
            attributes={"receives_bile": True, "receives_pancreatic_juice": True,
                        "micelle_formation": True, "major_fat_digestion_site": True,
                        "incretin_release": True, "acid_neutralization": True},
            description="Mixing chamber for chyme, bile, and pancreatic secretions; major fat digestion and incretin release site."
        ))

        self.register(Structure(
            id="jejunum", name="Jejunum",
            category=StructureCategory.MACRO_SEGMENT,
            location="Upper abdominal cavity – proximal 2/5 of small intestine",
            systems={
                AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                AnatomicalSystem.ENDOCRINE: SystemRole.SECONDARY,
                AnatomicalSystem.IMMUNE: SystemRole.SECONDARY,
                AnatomicalSystem.CIRCULATORY: SystemRole.SECONDARY,
                AnatomicalSystem.NERVOUS: SystemRole.SECONDARY,
            },
            components=["villi", "crypts", "enterocytes", "goblet_cells", "paneth_cells",
                        "lacteals", "brush_border", "glycocalyx"],
            connections=["duodenum", "ileum"],
            attributes={"primary_absorption_site": True, "high_surface_area": True,
                        "dense_villi": True, "expresses_SGLT1": True,
                        "expresses_PEPT1": True, "expresses_GLUT2": True},
            description="Primary site of nutrient absorption (carbohydrates, amino acids, most vitamins and minerals)."
        ))

        self.register(Structure(
            id="ileum", name="Ileum",
            category=StructureCategory.MACRO_SEGMENT,
            location="Lower abdominal cavity – distal 3/5 of small intestine",
            systems={
                AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                AnatomicalSystem.ENDOCRINE: SystemRole.SECONDARY,
                AnatomicalSystem.IMMUNE: SystemRole.PRIMARY,
                AnatomicalSystem.CIRCULATORY: SystemRole.SECONDARY,
                AnatomicalSystem.LYMPHATIC: SystemRole.SECONDARY,
                AnatomicalSystem.MICROBIOME_HOST: SystemRole.SECONDARY,
            },
            components=["villi", "crypts", "peyers_patches", "m_cells", "l_cells",
                        "bile_acid_transporters"],
            connections=["jejunum", "cecum"],
            attributes={"bile_acid_reabsorption": True, "vitamin_b12_absorption": True,
                        "peyers_patches_present": True, "ileal_brake": True,
                        "expresses_ASBT": True},
            description="Terminal small intestine; specialized for bile-acid and B12 absorption and immune surveillance."
        ))

        self.register(Structure(
            id="cecum", name="Cecum",
            category=StructureCategory.MACRO_SEGMENT,
            location="Right iliac fossa – beginning of large intestine",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.IMMUNE: SystemRole.SECONDARY,
                     AnatomicalSystem.MICROBIOME_HOST: SystemRole.PRIMARY},
            components=["appendix", "ileocecal_valve"],
            connections=["ileum", "ascending_colon"],
            attributes={"fermentation_begins": True},
            description="Blind pouch receiving ileal contents; transition to microbial fermentation."
        ))

        for cid, cname, loc in [
            ("ascending_colon", "Ascending Colon", "Right side of abdomen"),
            ("transverse_colon", "Transverse Colon", "Crosses upper abdomen"),
            ("descending_colon", "Descending Colon", "Left side of abdomen"),
            ("sigmoid_colon", "Sigmoid Colon", "Pelvic brim to rectum"),
        ]:
            self.register(Structure(
                id=cid, name=cname, category=StructureCategory.MACRO_SEGMENT, location=loc,
                systems={
                    AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                    AnatomicalSystem.MICROBIOME_HOST: SystemRole.PRIMARY,
                    AnatomicalSystem.ENDOCRINE: SystemRole.SECONDARY,
                    AnatomicalSystem.IMMUNE: SystemRole.SECONDARY,
                },
                components=["crypts", "goblet_cells", "colonocytes", "l_cells", "mucus_layer"],
                attributes={"water_electrolyte_absorption": True, "scfa_production": True,
                            "butyrate_preferred_fuel": True, "dense_microbiota": True,
                            "mucus_barrier": True},
                description=f"{cname}: major site of water reabsorption and microbial fermentation of fiber/RS to SCFAs."
            ))

        self.register(Structure(
            id="rectum", name="Rectum",
            category=StructureCategory.MACRO_SEGMENT,
            location="Pelvis – terminal reservoir",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.NERVOUS: SystemRole.SECONDARY},
            components=["internal_anal_sphincter", "external_anal_sphincter"],
            connections=["sigmoid_colon", "anal_canal"],
            attributes={"fecal_storage": True, "defecation_reflex": True},
            description="Temporary storage of feces and initiation of defecation reflex."
        ))

        self.register(Structure(
            id="anal_canal", name="Anal Canal",
            category=StructureCategory.MACRO_SEGMENT,
            location="Perineum – final outflow tract",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.NERVOUS: SystemRole.PRIMARY,
                     AnatomicalSystem.MUSCULOSKELETAL: SystemRole.PRIMARY},
            connections=["rectum"],
            attributes={"continence": True, "voluntary_control": True},
            description="Final segment providing continence via internal and external sphincters."
        ))

        # ------------------------------------------------------------------
        # ACCESSORY ORGANS
        # ------------------------------------------------------------------
        self.register(Structure(
            id="liver", name="Liver",
            category=StructureCategory.ACCESSORY_ORGAN,
            location="Right upper quadrant",
            systems={
                AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                AnatomicalSystem.ENDOCRINE: SystemRole.SECONDARY,
                AnatomicalSystem.IMMUNE: SystemRole.SECONDARY,
                AnatomicalSystem.CIRCULATORY: SystemRole.PRIMARY,
            },
            components=["hepatocytes", "kupffer_cells", "stellate_cells", "bile_canaliculi"],
            connections=["gallbladder", "duodenum"],
            attributes={"bile_synthesis": True, "first_pass_metabolism": True,
                        "nutrient_processing": True, "detoxification": True,
                        "glucose_homeostasis": True},
            description="Central metabolic hub; produces bile, processes absorbed nutrients, detoxifies."
        ))

        self.register(Structure(
            id="gallbladder", name="Gallbladder",
            category=StructureCategory.ACCESSORY_ORGAN,
            location="Inferior surface of liver",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.NERVOUS: SystemRole.SECONDARY},
            connections=["liver", "duodenum"],
            attributes={"bile_storage": True, "bile_concentration": True, "cck_responsive": True},
            description="Stores and concentrates bile; contracts in response to CCK."
        ))

        self.register(Structure(
            id="pancreas", name="Pancreas",
            category=StructureCategory.ACCESSORY_ORGAN,
            location="Retroperitoneal – head in duodenal curve",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.ENDOCRINE: SystemRole.PRIMARY},
            components=["acinar_cells", "ductal_cells", "islets_of_langerhans",
                        "alpha_cells", "beta_cells", "delta_cells"],
            connections=["duodenum"],
            attributes={"exocrine_enzyme_secretion": True, "bicarbonate_secretion": True,
                        "insulin_secretion": True, "glucagon_secretion": True,
                        "secretin_responsive": True, "cck_responsive": True},
            description="Dual exocrine (enzymes + HCO3) and endocrine (insulin, glucagon) organ."
        ))

        self.register(Structure(
            id="salivary_glands", name="Salivary Glands",
            category=StructureCategory.ACCESSORY_ORGAN,
            location="Head – parotid, submandibular, sublingual",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.IMMUNE: SystemRole.SECONDARY},
            attributes={"salivary_amylase": True, "lubrication": True, "antimicrobial": True},
            description="Produce saliva containing amylase, mucus, and antimicrobial factors."
        ))

        # ------------------------------------------------------------------
        # MICRO-STRUCTURES
        # ------------------------------------------------------------------
        self.register(Structure(
            id="villus", name="Villus",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Small intestinal mucosa",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.CIRCULATORY: SystemRole.SECONDARY,
                     AnatomicalSystem.LYMPHATIC: SystemRole.SECONDARY},
            components=["enterocytes", "goblet_cells", "lacteal", "brush_border", "glycocalyx"],
            attributes={"surface_amplification": True, "absorptive": True, "contains_lacteal": True},
            description="Finger-like mucosal projection that massively increases absorptive surface area."
        ))

        self.register(Structure(
            id="crypt_of_lieberkuhn", name="Crypt of Lieberkühn",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Base of villi / colonic mucosa",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.IMMUNE: SystemRole.SECONDARY},
            components=["stem_cells", "paneth_cells", "goblet_cells", "enteroendocrine_cells"],
            attributes={"stem_cell_niche": True, "paneth_cell_antimicrobial": True, "cell_renewal": True},
            description="Intestinal gland housing stem cells and specialized secretory cells."
        ))

        self.register(Structure(
            id="peyers_patch", name="Peyer's Patch",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Ileum (antimesenteric border)",
            systems={AnatomicalSystem.IMMUNE: SystemRole.PRIMARY,
                     AnatomicalSystem.LYMPHATIC: SystemRole.PRIMARY,
                     AnatomicalSystem.MICROBIOME_HOST: SystemRole.SECONDARY},
            components=["m_cells", "follicles", "dome_region"],
            attributes={"antigen_sampling": True, "inductive_site": True, "m_cell_transcytosis": True},
            description="Organized lymphoid follicle specialized for antigen sampling via M cells."
        ))

        self.register(Structure(
            id="brush_border", name="Brush Border (Microvilli)",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Apical surface of enterocytes",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
            attributes={"surface_amplification": True, "membrane_digestion": True,
                        "expresses_SGLT1": True, "expresses_PEPT1": True},
            description="Dense array of microvilli carrying membrane-bound digestive enzymes."
        ))

        self.register(Structure(
            id="glycocalyx", name="Glycocalyx",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Apical surface of enterocytes",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.SECONDARY,
                     AnatomicalSystem.IMMUNE: SystemRole.SECONDARY,
                     AnatomicalSystem.MICROBIOME_HOST: SystemRole.SECONDARY},
            attributes={"molecular_sieve": True, "enzyme_anchoring": True, "protection": True},
            description="Carbohydrate-rich coat that acts as molecular sieve and enzyme anchor."
        ))

        self.register(Structure(
            id="mucus_layer", name="Mucus Layer",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Throughout GI tract (esp. stomach and colon)",
            systems={AnatomicalSystem.IMMUNE: SystemRole.PRIMARY,
                     AnatomicalSystem.MICROBIOME_HOST: SystemRole.PRIMARY,
                     AnatomicalSystem.DIGESTIVE: SystemRole.SECONDARY},
            attributes={"physical_barrier": True, "lubrication": True,
                        "microbiome_habitat": True, "inner_sterile_layer": True},
            description="Protective gel layer; critical barrier and microbiome interface."
        ))

        self.register(Structure(
            id="tight_junction", name="Tight Junction",
            category=StructureCategory.JUNCTION,
            location="Apical junctional complex of epithelial cells",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                     AnatomicalSystem.IMMUNE: SystemRole.SECONDARY},
            components=["claudins", "occludin", "ZO_proteins"],
            attributes={"paracellular_barrier": True, "selective_permeability": True,
                        "regulated_by_cytokines": True, "regulated_by_butyrate": True},
            description="Sealing complex controlling paracellular permeability."
        ))

        self.register(Structure(
            id="enteric_nervous_system", name="Enteric Nervous System",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Within the wall of the GI tract",
            systems={AnatomicalSystem.NERVOUS: SystemRole.PRIMARY,
                     AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
            components=["myenteric_plexus", "submucosal_plexus", "enteric_neurons",
                        "enteric_glial_cells", "interstitial_cells_of_cajal"],
            attributes={"autonomous_motility_control": True, "secretory_control": True,
                        "second_brain": True, "glia_present": True},
            description="Intrinsic neural network capable of autonomous control of motility and secretion."
        ))

        self.register(Structure(
            id="enteric_glial_cell", name="Enteric Glial Cell",
            category=StructureCategory.CELL_TYPE,
            location="Enteric nervous system and mucosa",
            systems={AnatomicalSystem.NERVOUS: SystemRole.PRIMARY,
                     AnatomicalSystem.IMMUNE: SystemRole.SECONDARY},
            attributes={"barrier_regulation": True, "neuroimmune_crosstalk": True},
            description="Glial cells of the ENS that regulate barrier function and immune signaling."
        ))

        # ------------------------------------------------------------------
        # CELL TYPES
        # ------------------------------------------------------------------
        for cid, cname, cdesc, csys, cattr in [
            ("enterocyte", "Enterocyte", "Primary absorptive epithelial cell",
             {AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
             {"absorptive": True, "expresses_SGLT1": True, "expresses_PEPT1": True}),
            ("colonocyte", "Colonocyte", "Absorptive cell of colon; prefers butyrate",
             {AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY, AnatomicalSystem.MICROBIOME_HOST: SystemRole.SECONDARY},
             {"butyrate_preferred_fuel": True, "water_absorption": True}),
            ("goblet_cell", "Goblet Cell", "Mucus-secreting cell",
             {AnatomicalSystem.DIGESTIVE: SystemRole.SECONDARY, AnatomicalSystem.IMMUNE: SystemRole.SECONDARY},
             {"mucin_secretion": True}),
            ("paneth_cell", "Paneth Cell", "Antimicrobial peptide-secreting cell in crypts",
             {AnatomicalSystem.IMMUNE: SystemRole.PRIMARY},
             {"defensin_secretion": True, "lysozyme_secretion": True, "stem_cell_support": True}),
            ("stem_cell_lgr5", "Lgr5+ Intestinal Stem Cell", "Crypt-base stem cell",
             {AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
             {"self_renewal": True, "multipotent": True}),
            ("m_cell", "M Cell", "Antigen-sampling cell over Peyer's patches",
             {AnatomicalSystem.IMMUNE: SystemRole.PRIMARY},
             {"antigen_transcytosis": True}),
            ("tuft_cell", "Tuft Cell", "Chemosensory cell for type-2 immunity",
             {AnatomicalSystem.IMMUNE: SystemRole.SECONDARY},
             {"chemosensory": True, "il25_production": True}),
        ]:
            self.register(Structure(id=cid, name=cname, category=StructureCategory.CELL_TYPE,
                                    location="Intestinal epithelium", systems=csys,
                                    attributes=cattr, description=cdesc))

        for cid, cname, cloc, cdesc, cattr in [
            ("g_cell", "G Cell", "Stomach antrum", "Gastrin secretion", {"gastrin": True}),
            ("d_cell", "D Cell", "Stomach & intestine", "Somatostatin secretion", {"somatostatin": True}),
            ("ecl_cell", "ECL Cell", "Stomach", "Histamine secretion", {"histamine": True}),
            ("i_cell", "I Cell", "Duodenum/jejunum", "CCK secretion", {"cck": True}),
            ("s_cell", "S Cell", "Duodenum", "Secretin secretion", {"secretin": True}),
            ("k_cell", "K Cell", "Duodenum/jejunum", "GIP secretion", {"gip": True}),
            ("l_cell", "L Cell", "Distal ileum & colon", "GLP-1 and PYY secretion", {"glp1": True, "pyy": True}),
            ("enterochromaffin_cell", "Enterochromaffin Cell", "Throughout GI", "Serotonin secretion", {"serotonin": True}),
        ]:
            self.register(Structure(
                id=cid, name=cname, category=StructureCategory.CELL_TYPE, location=cloc,
                systems={AnatomicalSystem.ENDOCRINE: SystemRole.PRIMARY,
                         AnatomicalSystem.DIGESTIVE: SystemRole.SECONDARY},
                attributes=cattr, description=cdesc
            ))

        # ------------------------------------------------------------------
        # MOLECULAR COMPONENTS
        # ------------------------------------------------------------------
        for tid, tname, tdesc, tattr in [
            ("sglt1", "SGLT1 (SLC5A1)", "Apical glucose/galactose-Na+ cotransporter",
             {"glucose_uptake": True, "sodium_dependent": True}),
            ("glut2", "GLUT2 (SLC2A2)", "Basolateral facilitated glucose transporter",
             {"glucose_exit": True}),
            ("pept1", "PEPT1 (SLC15A1)", "Apical H+-coupled peptide transporter",
             {"peptide_uptake": True}),
            ("npc1l1", "NPC1L1", "Apical cholesterol transporter",
             {"cholesterol_uptake": True}),
            ("asbt", "ASBT (SLC10A2)", "Apical Na+-dependent bile acid transporter (ileum)",
             {"bile_acid_reabsorption": True}),
            ("cftr", "CFTR", "Chloride/bicarbonate channel",
             {"chloride_secretion": True, "bicarbonate_secretion": True}),
        ]:
            self.register(Structure(
                id=tid, name=tname, category=StructureCategory.MOLECULAR_COMPONENT,
                location="Epithelial membranes",
                systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
                attributes=tattr, description=tdesc
            ))

        for rid, rname, rdesc in [
            ("cck1r", "CCK1 Receptor", "Mediates CCK effects on gallbladder and pancreas"),
            ("tgr5", "TGR5 (GPBAR1)", "Bile-acid receptor on enteroendocrine and immune cells"),
            ("gpr41", "GPR41 (FFAR3)", "SCFA receptor (propionate/acetate)"),
            ("gpr43", "GPR43 (FFAR2)", "SCFA receptor (acetate/propionate)"),
            ("gpr109a", "GPR109A (HCAR2)", "Butyrate/niacin receptor – anti-inflammatory"),
            ("tlr4", "TLR4", "Pattern-recognition receptor for LPS"),
            ("tlr5", "TLR5", "Pattern-recognition receptor for flagellin"),
        ]:
            self.register(Structure(
                id=rid, name=rname, category=StructureCategory.MOLECULAR_COMPONENT,
                location="Cell surfaces throughout GI tract",
                systems={AnatomicalSystem.ENDOCRINE: SystemRole.SECONDARY,
                         AnatomicalSystem.IMMUNE: SystemRole.SECONDARY},
                description=rdesc
            ))

        # ------------------------------------------------------------------
        # SPHINCTERS / REGIONS
        # ------------------------------------------------------------------
        for sid, sname, sloc in [
            ("upper_esophageal_sphincter", "Upper Esophageal Sphincter", "Pharynx–esophagus"),
            ("lower_esophageal_sphincter", "Lower Esophageal Sphincter", "Esophagus–stomach"),
            ("pyloric_sphincter", "Pyloric Sphincter", "Stomach–duodenum"),
            ("sphincter_of_oddi", "Sphincter of Oddi", "Bile/pancreatic flow into duodenum"),
            ("ileocecal_valve", "Ileocecal Valve", "Ileum–cecum"),
            ("internal_anal_sphincter", "Internal Anal Sphincter", "Involuntary continence"),
            ("external_anal_sphincter", "External Anal Sphincter", "Voluntary continence"),
        ]:
            self.register(Structure(
                id=sid, name=sname, category=StructureCategory.REGION, location=sloc,
                systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY,
                         AnatomicalSystem.NERVOUS: SystemRole.SECONDARY},
                attributes={"controls_flow": True},
                description=f"Controls passage at {sloc}."
            ))


        # ==============================================================
        # PRIORITY EXPANSIONS (Part 4 alignment)
        # ==============================================================
        # Ion transporters
        self.register(Structure(
            id="nhe3", name="NHE3 (SLC9A3)",
            category=StructureCategory.MOLECULAR_COMPONENT,
            location="Apical membrane of small-intestinal and colonic epithelium",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
            attributes={"sodium_absorption": True, "proton_exchange": True, "electroneutral": True},
            description="Apical Na+/H+ exchanger – major route of electroneutral sodium absorption."
        ))
        self.register(Structure(
            id="dra", name="DRA (SLC26A3)",
            category=StructureCategory.MOLECULAR_COMPONENT,
            location="Apical membrane of ileal and colonic epithelium",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
            attributes={"chloride_absorption": True, "bicarbonate_secretion": True, "electroneutral": True},
            description="Apical Cl-/HCO3- exchanger – pairs with NHE3 for electroneutral NaCl absorption."
        ))
        self.register(Structure(
            id="mct1", name="MCT1 (SLC16A1)",
            category=StructureCategory.MOLECULAR_COMPONENT,
            location="Colonocyte membranes",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY, AnatomicalSystem.MICROBIOME_HOST: SystemRole.SECONDARY},
            attributes={"scfa_uptake": True},
            description="Monocarboxylate transporter for SCFA uptake."
        ))
        self.register(Structure(
            id="aquaporin_3", name="Aquaporin-3 (AQP3)",
            category=StructureCategory.MOLECULAR_COMPONENT,
            location="Basolateral membrane of colonocytes",
            systems={AnatomicalSystem.DIGESTIVE: SystemRole.SECONDARY},
            attributes={"water_channel": True},
            description="Water channel contributing to colonic water absorption."
        ))

        # Mucus bilayer
        self.register(Structure(
            id="inner_mucus_layer_colon", name="Inner Firm Mucus Layer (Colon)",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Colon – directly overlying epithelium",
            systems={AnatomicalSystem.IMMUNE: SystemRole.PRIMARY, AnatomicalSystem.MICROBIOME_HOST: SystemRole.PRIMARY},
            attributes={"sterile": True, "firmly_adherent": True, "muc2_dominant": True},
            description="Firmly adherent, essentially sterile mucus layer separating bacteria from epithelium."
        ))
        self.register(Structure(
            id="outer_mucus_layer_colon", name="Outer Loose Mucus Layer (Colon)",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Colon – luminal to inner mucus layer",
            systems={AnatomicalSystem.MICROBIOME_HOST: SystemRole.PRIMARY},
            attributes={"colonized": True, "loose": True, "microbial_habitat": True},
            description="Loose mucus layer that serves as habitat for commensal microbiota."
        ))

        # ENS plexuses + ICC
        self.register(Structure(
            id="myenteric_plexus", name="Myenteric (Auerbach) Plexus",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Between circular and longitudinal muscle layers",
            systems={AnatomicalSystem.NERVOUS: SystemRole.PRIMARY, AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
            attributes={"motility_control": True, "primarily_motor": True},
            description="Primary motility-controlling plexus of the ENS."
        ))
        self.register(Structure(
            id="submucosal_plexus", name="Submucosal (Meissner) Plexus",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Submucosa",
            systems={AnatomicalSystem.NERVOUS: SystemRole.PRIMARY, AnatomicalSystem.DIGESTIVE: SystemRole.SECONDARY},
            attributes={"secretory_control": True, "local_blood_flow_control": True},
            description="ENS plexus controlling secretion and local blood flow."
        ))
        self.register(Structure(
            id="interstitial_cells_of_cajal", name="Interstitial Cells of Cajal (ICC)",
            category=StructureCategory.CELL_TYPE,
            location="Within muscularis and around myenteric plexus",
            systems={AnatomicalSystem.NERVOUS: SystemRole.PRIMARY, AnatomicalSystem.DIGESTIVE: SystemRole.PRIMARY},
            attributes={"pacemaker": True, "slow_wave_generation": True},
            description="Pacemaker cells generating electrical slow waves."
        ))

        # Lacteal + lamina propria
        self.register(Structure(
            id="lacteal", name="Central Lacteal",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Core of each small-intestinal villus",
            systems={AnatomicalSystem.LYMPHATIC: SystemRole.PRIMARY, AnatomicalSystem.DIGESTIVE: SystemRole.SECONDARY},
            attributes={"chylomicron_uptake": True, "blind_ended_lymphatic": True},
            description="Blind-ended lymphatic capillary that absorbs chylomicrons."
        ))
        self.register(Structure(
            id="lamina_propria", name="Lamina Propria",
            category=StructureCategory.MICRO_STRUCTURE,
            location="Beneath epithelium throughout GI tract",
            systems={AnatomicalSystem.IMMUNE: SystemRole.PRIMARY, AnatomicalSystem.CIRCULATORY: SystemRole.SECONDARY},
            attributes={"immune_cell_rich": True, "contains_capillaries": True},
            description="Loose connective tissue containing immune cells, capillaries and lymphatics."
        ))


        # Wire topology
        conn = {
            "oral_cavity": ["pharynx"], "pharynx": ["oral_cavity", "esophagus"],
            "esophagus": ["pharynx", "stomach"], "stomach": ["esophagus", "duodenum"],
            "duodenum": ["stomach", "jejunum", "pancreas", "gallbladder"],
            "jejunum": ["duodenum", "ileum"], "ileum": ["jejunum", "cecum"],
            "cecum": ["ileum", "ascending_colon"],
            "ascending_colon": ["cecum", "transverse_colon"],
            "transverse_colon": ["ascending_colon", "descending_colon"],
            "descending_colon": ["transverse_colon", "sigmoid_colon"],
            "sigmoid_colon": ["descending_colon", "rectum"],
            "rectum": ["sigmoid_colon", "anal_canal"], "anal_canal": ["rectum"],
        }
        for sid, clist in conn.items():
            if sid in self.structures:
                self.structures[sid].connections = clist
        self._register_extra_molecular()


    def _register_extra_molecular(self) -> None:
        """Register EXTRA_MOLECULAR dicts (was previously dead module-level data)."""
        role_map = {
            "primary": SystemRole.PRIMARY,
            "secondary": SystemRole.SECONDARY,
            "supporting": SystemRole.SUPPORTING,
            "present": SystemRole.PRESENT,
        }
        sys_map = {s.value: s for s in AnatomicalSystem}
        cat_map = {c.value: c for c in StructureCategory}
        for raw in EXTRA_MOLECULAR:
            sid = raw["id"]
            if sid in self.structures:
                continue
            systems = {}
            for k, v in (raw.get("systems") or {}).items():
                sk = sys_map.get(k) or sys_map.get(k.replace("-", "_"))
                if sk is None:
                    # try uppercase enum name style
                    for a in AnatomicalSystem:
                        if a.value == k or a.name.lower() == k.lower():
                            sk = a
                            break
                rk = role_map.get(str(v).lower(), SystemRole.PRESENT)
                if sk is not None:
                    systems[sk] = rk
            cat = cat_map.get(raw.get("category", "molecular_component"), StructureCategory.MOLECULAR_COMPONENT)
            self.register(Structure(
                id=sid,
                name=raw.get("name", sid),
                category=cat,
                location=raw.get("location", ""),
                systems=systems,
                attributes=dict(raw.get("attributes") or {}),
                description=raw.get("description", ""),
            ))



EXTRA_MOLECULAR = [
    {
        "id": "nhe3",
        "name": "NHE3 (Sodium-Hydrogen Exchanger 3)",
        "category": "molecular_component",
        "location": "Apical membrane of enterocytes and colonocytes (especially ileum & proximal colon)",
        "systems": {"digestive": "primary", "circulatory": "secondary"},
        "attributes": {"ion_transport": True, "electroneutral_Na_absorption": True, "regulated_by_cAMP": True},
        "description": "Major route for electroneutral Na+ absorption coupled to H+ secretion."
    },
    {
        "id": "dra",
        "name": "DRA / SLC26A3 (Down-Regulated in Adenoma)",
        "category": "molecular_component",
        "location": "Apical membrane of ileal and colonic epithelium",
        "systems": {"digestive": "primary"},
        "attributes": {"cl_hco3_exchange": True, "electrogenic": False},
        "description": "Cl-/HCO3- exchanger critical for electroneutral NaCl absorption and stool hydration."
    },
    {
        "id": "mct1",
        "name": "MCT1 (Monocarboxylate Transporter 1)",
        "category": "molecular_component",
        "location": "Apical and basolateral membranes of colonocytes",
        "systems": {"digestive": "primary", "microbiome_host": "primary"},
        "attributes": {"scfa_transport": True, "butyrate_uptake": True},
        "description": "Primary transporter for SCFA (especially butyrate) uptake into colonocytes."
    },
    {
        "id": "occludin",
        "name": "Occludin",
        "category": "molecular_component",
        "location": "Tight junction complex of all intestinal epithelium",
        "systems": {"digestive": "primary", "immune": "secondary"},
        "attributes": {"barrier_integrity": True, "regulated_by_phosphorylation": True},
        "description": "Transmembrane tight-junction protein that seals the paracellular pathway."
    },
    {
        "id": "zo1",
        "name": "ZO-1 (Zonula Occludens-1)",
        "category": "molecular_component",
        "location": "Cytoplasmic face of tight junctions",
        "systems": {"digestive": "primary", "immune": "secondary"},
        "attributes": {"scaffold_protein": True, "links_to_actin": True},
        "description": "Intracellular scaffold that anchors occludin and claudins to the actin cytoskeleton."
    },
    {
        "id": "claudin2",
        "name": "Claudin-2",
        "category": "molecular_component",
        "location": "Tight junctions (higher in crypts and under inflammatory conditions)",
        "systems": {"digestive": "primary", "immune": "secondary"},
        "attributes": {"cation_pore": True, "leak_pathway": True, "inflammation_inducible": True},
        "description": "Pore-forming claudin that increases paracellular cation and water permeability."
    },
]


def get_digestive_definition_registry() -> DigestiveDefinitionRegistry:
    return DigestiveDefinitionRegistry()


if __name__ == "__main__":
    reg = get_digestive_definition_registry()
    print("=== Digestive Definition Layer Summary ===")
    for cat, count in reg.summary().items():
        print(f"  {cat:25s}: {count:3d}")
    print(f"\nTotal structures defined: {len(reg.list_ids())}")
    print("\nSample – Jejunum:")
    jej = reg.get("jejunum")
    if jej:
        for sys, role in jej.systems.items():
            print(f"  {sys.value:20s} → {role.value}")
        print(f"  Key attributes: {list(jej.attributes.keys())}")


