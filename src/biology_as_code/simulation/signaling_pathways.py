"""
signaling_pathways.py
=================================================================
Major Signaling Pathways of the Gut–Brain–Metabolic Axis

Formal registry of the key communication pathways that implement
SYS-03 COMMUNICATION and link the digestive Definition/Mechanism
layers to systemic physiology.

Pathways are declarative: they declare sensors, transmitters,
targets, and effects. They do not contain kinetic rate laws
(those remain in the Mechanism Layer).
=================================================================
"""

from dataclasses import dataclass, field
from enum import Enum


class PathwayCategory(Enum):
    ENTEROENDOCRINE   = "enteroendocrine"    # classic gut hormones
    SCFA_RECEPTOR     = "scfa_receptor"      # microbial metabolite sensing
    NEURAL            = "neural"             # ENS + vagal + spinal
    METABOLIC         = "metabolic"          # insulin, mTOR, AMPK, etc.
    IMMUNE_BARRIER    = "immune_barrier"     # TLRs, cytokines, permeability
    GUT_BRAIN         = "gut_brain"          # bidirectional axis pathways


class Directionality(Enum):
    AFFERENT   = "afferent"     # gut → brain / periphery
    EFFERENT   = "efferent"     # brain → gut
    LOCAL      = "local"        # within gut wall
    BIDIRECTIONAL = "bidirectional"


@dataclass
class SignalingPathway:
    """One formalized signaling pathway."""
    id: str
    name: str
    category: PathwayCategory
    direction: Directionality
    description: str

    # Biological participants (preferably Definition Layer IDs)
    sensors: list[str] = field(default_factory=list)          # cells or receptors that detect the signal
    transmitters: list[str] = field(default_factory=list)     # hormones, neurotransmitters, metabolites
    targets: list[str] = field(default_factory=list)          # downstream structures / organs
    effects: list[str] = field(default_factory=list)

    # Links into the rest of the architecture
    related_mechanisms: list[str] = field(default_factory=list)   # Mechanism Layer process IDs
    functional_systems: list[str] = field(default_factory=list)   # SYS-01 … SYS-07
    notes: str = ""


class SignalingPathwayRegistry:
    """Registry of major gut–brain–metabolic signaling pathways."""

    def __init__(self):
        self.pathways: dict[str, SignalingPathway] = {}
        self._build_pathways()

    def register(self, pathway: SignalingPathway):
        self.pathways[pathway.id] = pathway

    def get(self, pathway_id: str) -> SignalingPathway | None:
        return self.pathways.get(pathway_id)

    def by_category(self, category: PathwayCategory) -> list[SignalingPathway]:
        return [p for p in self.pathways.values() if p.category == category]

    def list_ids(self) -> list[str]:
        return sorted(self.pathways.keys())

    def summary(self) -> dict[str, int]:
        counts = {cat.value: len(self.by_category(cat)) for cat in PathwayCategory}
        counts["total"] = len(self.pathways)
        return counts

    def _build_pathways(self):
        # ==================================================================
        # ENTEROENDOCRINE
        # ==================================================================
        self.register(SignalingPathway(
            id="gastrin_pathway",
            name="Gastrin Pathway",
            category=PathwayCategory.ENTEROENDOCRINE,
            direction=Directionality.LOCAL,
            description="G-cell release of gastrin stimulates acid and mucosal growth.",
            sensors=["g_cell"],
            transmitters=["gastrin"],
            targets=["parietal_cells", "ecl_cells", "stomach"],
            effects=["increase_acid_secretion", "stimulate_mucosal_growth", "histamine_release_from_ECL"],
            related_mechanisms=["gastrin_release", "gastric_acid_secretion"],
            functional_systems=["SYS-01"]
        ))

        self.register(SignalingPathway(
            id="cck_pathway",
            name="CCK Pathway",
            category=PathwayCategory.ENTEROENDOCRINE,
            direction=Directionality.BIDIRECTIONAL,
            description="I-cell CCK coordinates bile/enzyme delivery, slows gastric emptying, and signals satiety via vagal afferents.",
            sensors=["i_cell"],
            transmitters=["cck"],
            targets=["gallbladder", "pancreas", "pyloric_sphincter", "vagal_afferents", "brain"],
            effects=["gallbladder_contraction", "pancreatic_enzyme_secretion", "delay_gastric_emptying", "satiety"],
            related_mechanisms=["cck_release", "bile_secretion_and_release", "pancreatic_enzyme_secretion"],
            functional_systems=["SYS-01", "SYS-03"]
        ))

        self.register(SignalingPathway(
            id="secretin_pathway",
            name="Secretin Pathway",
            category=PathwayCategory.ENTEROENDOCRINE,
            direction=Directionality.LOCAL,
            description="S-cell secretin drives bicarbonate secretion to neutralize duodenal acid.",
            sensors=["s_cell"],
            transmitters=["secretin"],
            targets=["pancreas", "bile_ducts", "stomach"],
            effects=["bicarbonate_secretion", "inhibit_acid", "protect_duodenal_mucosa"],
            related_mechanisms=["secretin_release", "bicarbonate_secretion_duodenum"],
            functional_systems=["SYS-01"]
        ))

        self.register(SignalingPathway(
            id="incretin_pathway",
            name="Incretin Pathway (GIP + GLP-1)",
            category=PathwayCategory.ENTEROENDOCRINE,
            direction=Directionality.AFFERENT,
            description="K-cell GIP and L-cell GLP-1 amplify glucose-stimulated insulin secretion and slow gastric emptying. Strongly rate-of-arrival sensitive.",
            sensors=["k_cell", "l_cell"],
            transmitters=["gip", "glp1"],
            targets=["pancreatic_beta_cells", "stomach", "brain", "heart"],
            effects=["potentiate_insulin_secretion", "slow_gastric_emptying", "satiety", "glucagon_suppression"],
            related_mechanisms=["incretin_release", "incretin_rate_of_arrival_sensing"],
            functional_systems=["SYS-03", "SYS-06"],
            notes="Classic example of rate-sensitive rather than purely concentration-sensitive signaling."
        ))

        self.register(SignalingPathway(
            id="pyy_ileal_brake",
            name="PYY / Ileal Brake Pathway",
            category=PathwayCategory.ENTEROENDOCRINE,
            direction=Directionality.AFFERENT,
            description="L-cell PYY (with GLP-1) implements the ileal brake and contributes to satiety.",
            sensors=["l_cell"],
            transmitters=["pyy", "glp1"],
            targets=["stomach", "jejunum", "brain", "ens"],
            effects=["slow_gastric_emptying", "slow_small_bowel_transit", "satiety"],
            related_mechanisms=["pyy_release", "ileal_brake"],
            functional_systems=["SYS-03", "SYS-01"]
        ))

        self.register(SignalingPathway(
            id="ghrelin_pathway",
            name="Ghrelin Pathway",
            category=PathwayCategory.ENTEROENDOCRINE,
            direction=Directionality.AFFERENT,
            description="Stomach-derived ghrelin rises in fasting and drives hunger via hypothalamic circuits.",
            sensors=["stomach"],
            transmitters=["ghrelin"],
            targets=["hypothalamus", "pituitary", "vagus"],
            effects=["increase_hunger", "stimulate_gh_secretion", "modulate_reward"],
            related_mechanisms=[],
            functional_systems=["SYS-03", "SYS-06"]
        ))

        # ==================================================================
        # SCFA RECEPTOR + MICROBIAL
        # ==================================================================
        self.register(SignalingPathway(
            id="gpr41_pathway",
            name="GPR41 (FFAR3) Pathway",
            category=PathwayCategory.SCFA_RECEPTOR,
            direction=Directionality.AFFERENT,
            description="Propionate/acetate sensing via GPR41 influences enteroendocrine release and sympathetic tone.",
            sensors=["gpr41", "l_cell"],
            transmitters=["propionate", "acetate"],
            targets=["enteroendocrine_cells", "sympathetic_neurons", "adipose"],
            effects=["pyy_glp1_release", "modulate_sympathetic_tone", "energy_homeostasis"],
            related_mechanisms=["gpr_scfa_signaling", "microbial_fermentation_scfa"],
            functional_systems=["SYS-03", "SYS-06"]
        ))

        self.register(SignalingPathway(
            id="gpr43_pathway",
            name="GPR43 (FFAR2) Pathway",
            category=PathwayCategory.SCFA_RECEPTOR,
            direction=Directionality.AFFERENT,
            description="Acetate/propionate sensing via GPR43 links microbial fermentation to immune and metabolic regulation.",
            sensors=["gpr43"],
            transmitters=["acetate", "propionate"],
            targets=["immune_cells", "adipocytes", "enteroendocrine_cells"],
            effects=["anti_inflammatory", "glp1_modulation", "energy_homeostasis"],
            related_mechanisms=["gpr_scfa_signaling"],
            functional_systems=["SYS-03", "SYS-04", "SYS-06"]
        ))

        self.register(SignalingPathway(
            id="gpr109a_hdac_pathway",
            name="GPR109A + Butyrate HDAC Pathway",
            category=PathwayCategory.SCFA_RECEPTOR,
            direction=Directionality.LOCAL,
            description="Butyrate acts via GPR109A and via HDAC inhibition to reinforce barrier integrity and suppress inflammation.",
            sensors=["gpr109a", "colonocyte"],
            transmitters=["butyrate"],
            targets=["colonocyte", "immune_cells", "tight_junction"],
            effects=["anti_inflammatory", "barrier_reinforcement", "colonocyte_energy_supply", "epigenetic_modulation"],
            related_mechanisms=["gpr_scfa_signaling", "tight_junction_regulation", "microbial_fermentation_scfa"],
            functional_systems=["SYS-04", "SYS-03", "SYS-06"],
            notes="One of the strongest microbial → host defense communication routes."
        ))

        # ==================================================================
        # NEURAL / GUT–BRAIN
        # ==================================================================
        self.register(SignalingPathway(
            id="vagal_afferent_pathway",
            name="Vagal Afferent Pathway",
            category=PathwayCategory.GUT_BRAIN,
            direction=Directionality.AFFERENT,
            description="Primary gut → brain communication route. Senses stretch, nutrients, CCK, GLP-1, 5-HT and relays to the nucleus tractus solitarius.",
            sensors=["vagal_afferents", "enterochromaffin_cell", "i_cell", "l_cell"],
            transmitters=["cck", "glp1", "serotonin", "stretch"],
            targets=["nucleus_tractus_solitarius", "brainstem", "hypothalamus"],
            effects=["satiety", "nausea", "motility_modulation", "pancreatic_and_biliary_reflexes"],
            related_mechanisms=["cck_release", "incretin_release"],
            functional_systems=["SYS-03"]
        ))

        self.register(SignalingPathway(
            id="vagal_efferent_pathway",
            name="Vagal Efferent (Cephalic & Digestive) Pathway",
            category=PathwayCategory.GUT_BRAIN,
            direction=Directionality.EFFERENT,
            description="Brain → gut parasympathetic drive that initiates cephalic-phase responses and modulates secretion/motility.",
            sensors=["brainstem", "hypothalamus"],
            transmitters=["acetylcholine", "vagal_efferent_activity"],
            targets=["salivary_glands", "stomach", "pancreas", "enteric_nervous_system"],
            effects=["cephalic_phase_secretion", "increase_acid", "increase_pancreatic_juice", "modulate_motility"],
            related_mechanisms=["salivary_secretion", "gastric_acid_secretion", "pancreatic_enzyme_secretion"],
            functional_systems=["SYS-03", "SYS-01"]
        ))

        self.register(SignalingPathway(
            id="ens_local_circuitry",
            name="Enteric Nervous System Local Circuitry",
            category=PathwayCategory.NEURAL,
            direction=Directionality.LOCAL,
            description="Autonomous ENS circuits (myenteric + submucosal) that control motility, secretion and local blood flow without requiring the CNS.",
            sensors=["enteric_neurons", "interstitial_cells_of_cajal", "enterochromaffin_cell"],
            transmitters=["acetylcholine", "nitric_oxide", "vip", "substance_p", "serotonin"],
            targets=["smooth_muscle", "epithelium", "submucosal_vessels"],
            effects=["peristalsis", "segmentation", "secretion_control", "local_blood_flow"],
            related_mechanisms=["segmentation_small_intestine", "migrating_motor_complex", "gastric_churning"],
            functional_systems=["SYS-03", "SYS-01"]
        ))

        self.register(SignalingPathway(
            id="serotonin_ec_cell_pathway",
            name="Enterochromaffin Cell Serotonin Pathway",
            category=PathwayCategory.NEURAL,
            direction=Directionality.BIDIRECTIONAL,
            description="EC cells release ~95% of body serotonin in response to chemical and mechanical stimuli; acts on ENS and vagal afferents.",
            sensors=["enterochromaffin_cell"],
            transmitters=["serotonin"],
            targets=["enteric_neurons", "vagal_afferents"],
            effects=["initiate_peristaltic_reflex", "modulate_secretion", "nausea_and_vomiting_signals"],
            related_mechanisms=[],
            functional_systems=["SYS-03"]
        ))

        # ==================================================================
        # METABOLIC
        # ==================================================================
        self.register(SignalingPathway(
            id="insulin_pathway",
            name="Insulin Pathway",
            category=PathwayCategory.METABOLIC,
            direction=Directionality.AFFERENT,
            description="β-cell insulin is the master anabolic signal for glucose uptake, glycogen synthesis and protein synthesis.",
            sensors=["pancreatic_beta_cells"],
            transmitters=["insulin"],
            targets=["muscle", "adipose", "liver", "brain"],
            effects=["glucose_uptake", "glycogen_synthesis", "protein_synthesis", "lipogenesis", "suppress_gluconeogenesis"],
            related_mechanisms=["incretin_release"],
            functional_systems=["SYS-06", "SYS-07"]
        ))

        self.register(SignalingPathway(
            id="glucagon_pathway",
            name="Glucagon Pathway",
            category=PathwayCategory.METABOLIC,
            direction=Directionality.AFFERENT,
            description="α-cell glucagon drives hepatic glucose output during fasting or protein meals.",
            sensors=["pancreatic_alpha_cells"],
            transmitters=["glucagon"],
            targets=["liver"],
            effects=["glycogenolysis", "gluconeogenesis", "raise_blood_glucose"],
            related_mechanisms=[],
            functional_systems=["SYS-06"]
        ))

        self.register(SignalingPathway(
            id="mtor_pathway",
            name="mTORC1 Nutrient Sensing Pathway",
            category=PathwayCategory.METABOLIC,
            direction=Directionality.LOCAL,
            description="mTORC1 integrates amino-acid (especially leucine) and insulin signals to gate protein synthesis and cell growth.",
            sensors=["mTORC1", "amino_acid_sensors"],
            transmitters=["leucine", "insulin", "growth_factors"],
            targets=["ribosome", "translation_machinery"],
            effects=["protein_synthesis", "cell_growth", "inhibit_autophagy"],
            related_mechanisms=[],
            functional_systems=["SYS-07", "SYS-06"],
            notes="Anabolic threshold: insufficient leucine prevents full mTOR activation even if total protein is adequate."
        ))

        self.register(SignalingPathway(
            id="ampk_pathway",
            name="AMPK Energy-Sensing Pathway",
            category=PathwayCategory.METABOLIC,
            direction=Directionality.LOCAL,
            description="AMPK is activated by rising AMP:ATP and initiates catabolic and mitochondrial programs.",
            sensors=["AMPK"],
            transmitters=["amp", "adp"],
            targets=["mitochondria", "glucose_transporters", "lipid_metabolism"],
            effects=["increase_glucose_uptake", "fatty_acid_oxidation", "mitochondrial_biogenesis", "autophagy"],
            related_mechanisms=[],
            functional_systems=["SYS-06"]
        ))

        self.register(SignalingPathway(
            id="bhb_signaling",
            name="β-Hydroxybutyrate Signaling Pathway",
            category=PathwayCategory.METABOLIC,
            direction=Directionality.BIDIRECTIONAL,
            description=(
                "Beyond fuel (see the ketolysis pathway), β-hydroxybutyrate is a signaling "
                "molecule: it activates the GPR109A/HCAR2 receptor, inhibits class I HDACs, "
                "and directly blocks the NLRP3 inflammasome. Acetoacetate does not share most "
                "of these actions."
            ),
            sensors=["gpr109a_hcar2", "gpr41_ffar3", "class_I_hdac", "nlrp3_inflammasome"],
            transmitters=["beta_hydroxybutyrate"],
            targets=["adipocytes", "macrophages", "neurons", "sympathetic_ganglia", "heart"],
            effects=[
                "gpr109a_agonism_antilipolytic",
                "class_I_hdac_inhibition_raises_histone_acetylation",  # FOXO3 / oxidative-stress genes
                "nlrp3_inhibition_lowers_IL1b_IL18_caspase1",          # anti-inflammatory, GPR109A-independent
                "gpr41_antagonism_suppresses_sympathetic_tone",
            ],
            related_mechanisms=["ketone_body_oxidation"],
            functional_systems=["SYS-03", "SYS-04"],
            notes=(
                "FLOW teaching signaling (not fuel arithmetic; ketolysis handles ATP yield). "
                "BHB-specific vs acetoacetate. Sources: Metabolic and Signaling Roles of Ketone "
                "Bodies, PMC8922216 (https://pmc.ncbi.nlm.nih.gov/articles/PMC8922216/); "
                "Youm et al. 2015 NLRP3 inhibition, PMID 25686106."
            ),
        ))

        # ==================================================================
        # IMMUNE / BARRIER
        # ==================================================================
        self.register(SignalingPathway(
            id="tlr_barrier_pathway",
            name="TLR – Barrier / Inflammation Pathway",
            category=PathwayCategory.IMMUNE_BARRIER,
            direction=Directionality.LOCAL,
            description="Pattern-recognition receptors (TLR4, TLR5, etc.) detect microbial products and can increase epithelial permeability via cytokine cascades.",
            sensors=["tlr4", "tlr5", "immune_cells"],
            transmitters=["lps", "flagellin", "cytokines"],
            targets=["tight_junction", "epithelial_cells", "immune_cells"],
            effects=["increase_permeability", "inflammatory_signaling", "recruit_immune_cells"],
            related_mechanisms=["tight_junction_regulation", "m_cell_antigen_sampling"],
            functional_systems=["SYS-04"]
        ))

        self.register(SignalingPathway(
            id="butyrate_barrier_pathway",
            name="Butyrate – Barrier Reinforcement Pathway",
            category=PathwayCategory.IMMUNE_BARRIER,
            direction=Directionality.LOCAL,
            description="Butyrate strengthens tight junctions and fuels colonocytes, opposing inflammatory permeability increases.",
            sensors=["gpr109a", "colonocyte"],
            transmitters=["butyrate"],
            targets=["tight_junction", "colonocyte", "immune_cells"],
            effects=["increase_teer", "reduce_permeability", "anti_inflammatory", "colonocyte_energy"],
            related_mechanisms=["tight_junction_regulation", "gpr_scfa_signaling", "mucus_turnover"],
            functional_systems=["SYS-04", "SYS-06"]
        ))


def get_signaling_pathway_registry() -> SignalingPathwayRegistry:
    return SignalingPathwayRegistry()



# ==============================================================================
# Additional pathways: CRF/stress and Tryptophan metabolism
# ==============================================================================

def _register_extended_gut_brain_pathways(registry: "SignalingPathwayRegistry"):
    """Extra pathways requested for deeper gut–brain coverage."""
    registry.register(SignalingPathway(
        id="crf_stress_permeability_pathway",
        name="CRF / Stress → Gut Permeability Pathway",
        category=PathwayCategory.GUT_BRAIN,
        direction=Directionality.EFFERENT,
        description=(
            "Psychological or physiological stress activates central and peripheral CRF systems, "
            "increasing epithelial permeability, altering motility, and changing mucosal immune tone."
        ),
        sensors=["brain", "hypothalamus", "central_crf_neurons"],
        transmitters=["crf", "crh", "cortisol", "sympathetic_activity"],
        targets=["tight_junction", "mast_cells", "enteric_nervous_system", "epithelium"],
        effects=[
            "increase_epithelial_permeability",
            "mast_cell_activation",
            "alter_motility",
            "visceral_hypersensitivity",
            "shift_microbiome_signals"
        ],
        related_mechanisms=["tight_junction_regulation", "mucus_turnover"],
        functional_systems=["SYS-03", "SYS-04"],
        notes="Key route by which chronic stress degrades barrier function and amplifies gut–brain feedback."
    ))

    registry.register(SignalingPathway(
        id="tryptophan_serotonin_kynurenine_pathway",
        name="Tryptophan → Serotonin / Kynurenine Branch",
        category=PathwayCategory.GUT_BRAIN,
        direction=Directionality.BIDIRECTIONAL,
        description=(
            "Dietary tryptophan is partitioned between host serotonin synthesis (via TPH1 in EC cells) "
            "and the kynurenine pathway (IDO/TDO). Microbial activity and inflammation strongly influence the balance. "
            "Downstream metabolites affect mood, immune tone, and blood–brain barrier."
        ),
        sensors=["enterochromaffin_cell", "immune_cells", "liver"],
        transmitters=["tryptophan", "serotonin", "kynurenine", "kynurenic_acid", "quinolinic_acid"],
        targets=["enteric_neurons", "vagal_afferents", "brain", "immune_cells", "blood_brain_barrier"],
        effects=[
            "serotonin_availability",
            "kynurenine_pathway_activation",
            "modulate_mood_and_inflammation",
            "influence_bbb_integrity",
            "alter_ens_signaling"
        ],
        related_mechanisms=["serotonin_peristaltic_reflex"],
        functional_systems=["SYS-03", "SYS-04"],
        notes="Inflammation up-regulates IDO → shifts tryptophan toward kynurenine at the expense of serotonin."
    ))


# ------------------------------------------------------------------------------
# Compact Gut–Brain Axis summary object
# ------------------------------------------------------------------------------

@dataclass
class GutBrainAxis:
    """
    Compact grouping of all pathways that constitute the gut–brain axis.
    Provides a single entry point for SYS-03 COMMUNICATION analysis.
    """
    afferent_pathways: list[str] = field(default_factory=list)
    efferent_pathways: list[str] = field(default_factory=list)
    local_neural_pathways: list[str] = field(default_factory=list)
    endocrine_pathways: list[str] = field(default_factory=list)
    microbial_metabolite_pathways: list[str] = field(default_factory=list)
    immune_barrier_pathways: list[str] = field(default_factory=list)
    stress_pathways: list[str] = field(default_factory=list)
    metabolic_crosstalk: list[str] = field(default_factory=list)

    def all_pathway_ids(self) -> list[str]:
        ids = set()
        for lst in [
            self.afferent_pathways, self.efferent_pathways, self.local_neural_pathways,
            self.endocrine_pathways, self.microbial_metabolite_pathways,
            self.immune_barrier_pathways, self.stress_pathways, self.metabolic_crosstalk
        ]:
            ids.update(lst)
        return sorted(ids)

    def summary(self) -> dict[str, int]:
        return {
            "afferent": len(self.afferent_pathways),
            "efferent": len(self.efferent_pathways),
            "local_neural": len(self.local_neural_pathways),
            "endocrine": len(self.endocrine_pathways),
            "microbial_metabolite": len(self.microbial_metabolite_pathways),
            "immune_barrier": len(self.immune_barrier_pathways),
            "stress": len(self.stress_pathways),
            "metabolic_crosstalk": len(self.metabolic_crosstalk),
            "total_unique": len(self.all_pathway_ids()),
        }


def get_gut_brain_axis() -> GutBrainAxis:
    """Return a pre-populated Gut–Brain Axis summary object."""
    return GutBrainAxis(
        afferent_pathways=[
            "vagal_afferent_pathway",
            "incretin_pathway",
            "pyy_ileal_brake",
            "cck_pathway",
            "ghrelin_pathway",
            "gpr41_pathway",
            "gpr43_pathway",
        ],
        efferent_pathways=[
            "vagal_efferent_pathway",
            "crf_stress_permeability_pathway",
        ],
        local_neural_pathways=[
            "ens_local_circuitry",
            "serotonin_ec_cell_pathway",
        ],
        endocrine_pathways=[
            "gastrin_pathway",
            "cck_pathway",
            "secretin_pathway",
            "incretin_pathway",
            "pyy_ileal_brake",
            "ghrelin_pathway",
        ],
        microbial_metabolite_pathways=[
            "gpr41_pathway",
            "gpr43_pathway",
            "gpr109a_hdac_pathway",
            "tryptophan_serotonin_kynurenine_pathway",
        ],
        immune_barrier_pathways=[
            "tlr_barrier_pathway",
            "butyrate_barrier_pathway",
            "crf_stress_permeability_pathway",
        ],
        stress_pathways=[
            "crf_stress_permeability_pathway",
        ],
        metabolic_crosstalk=[
            "insulin_pathway",
            "glucagon_pathway",
            "ampk_pathway",
            "mtor_pathway",
        ],
    )


# Patch the registry factory so new pathways are always present
_original_get_signaling = get_signaling_pathway_registry

def get_signaling_pathway_registry() -> SignalingPathwayRegistry:
    reg = _original_get_signaling()
    if "crf_stress_permeability_pathway" not in reg.pathways:
        _register_extended_gut_brain_pathways(reg)
    return reg


if __name__ == "__main__":
    reg = get_signaling_pathway_registry()
    print("=== Signaling Pathway Registry ===")
    for cat, count in reg.summary().items():
        print(f"  {cat:20s}: {count:3d}")
    print(f"\nTotal pathways: {len(reg.list_ids())}")
    print("\n--- Gut–Brain Axis pathways ---")
    for p in reg.by_category(PathwayCategory.GUT_BRAIN) + reg.by_category(PathwayCategory.NEURAL):
        print(f"  {p.id:30s} [{p.direction.value}]")
