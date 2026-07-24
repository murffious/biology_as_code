"""
system_interaction_principles.py
=================================================================
PART 4 – Principles for System Interaction
Dual-Lens Architecture + The 7 Kingdoms + Mechanism Modifiers

This module formalizes the higher-order architecture that sits
above the Definition Layer and Mechanism Layer.

Lens A  = Immutable Hardware  (Definition Layer + fixed mechanisms)
Lens B  = Runtime Parameters  (Operating Environment + inputs)

System Output = Hardware (Lens A) × Runtime Parameters (Lens B)
=================================================================
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Lens(Enum):
    HARDWARE = "hardware"          # Lens A – immutable biological engine
    RUNTIME  = "runtime"           # Lens B – variable operating conditions


class KingdomID(Enum):
    INGESTION       = 1
    ACID_REACTOR    = 2
    EMULSIFICATION  = 3
    ASSIMILATION    = 4
    FERMENTATION    = 5
    TRANSPORT       = 6
    ENERGY_STRUCTURE = 7


@dataclass
class Kingdom:
    """One of the Seven Kingdoms – a spatially bounded domain with its own reigning law."""
    id: KingdomID
    name: str
    organ_seat: str
    reigning_law: str
    gate: str                          # prerequisite / switch
    bound: str                         # failure envelope
    definition_structures: list[str] = field(default_factory=list)   # Definition Layer IDs
    key_mechanisms: list[str] = field(default_factory=list)          # Mechanism Layer IDs
    description: str = ""


@dataclass
class MechanismModifier:
    """A factor that alters the capacity limits of a mechanism without changing the underlying law."""
    id: str
    name: str
    modifier_type: str                 # "negative" | "positive"
    category: str                      # genetic | drug | environmental | nutritional_synergy
    affects_structures: list[str] = field(default_factory=list)
    affects_mechanisms: list[str] = field(default_factory=list)
    effect_description: str = ""
    typical_magnitude: str = ""        # qualitative or quantitative note


@dataclass
class RuntimeParameter:
    """A controllable or environmental variable that constitutes Lens B."""
    id: str
    name: str
    category: str                      # activity | sleep | stress | toxin | nutritional_input | circadian
    description: str = ""
    affects_kingdoms: list[KingdomID] = field(default_factory=list)


class SystemInteractionRegistry:
    """
    High-level registry for Part 4 principles.
    Maps the Dual-Lens view onto the existing Definition + Mechanism layers.
    """

    def __init__(self):
        self.kingdoms: dict[KingdomID, Kingdom] = {}
        self.modifiers: dict[str, MechanismModifier] = {}
        self.runtime_parameters: dict[str, RuntimeParameter] = {}
        self._build_seven_kingdoms()
        self._build_core_modifiers()
        self._build_runtime_parameters()

    def _build_seven_kingdoms(self):
        self.kingdoms[KingdomID.INGESTION] = Kingdom(
            id=KingdomID.INGESTION,
            name="Ingestion",
            organ_seat="Mouth, Teeth, Salivary glands",
            reigning_law="Surface-Area Kinetics",
            gate="Mechanical mastication (bolus formation)",
            bound="Salivary saturation / insufficient particle-size reduction",
            definition_structures=["oral_cavity", "salivary_glands", "pharynx"],
            key_mechanisms=["mastication", "salivary_secretion"],
            description="First mechanical and enzymatic processing. Surface area must be increased for subsequent chemical attack."
        )

        self.kingdoms[KingdomID.ACID_REACTOR] = Kingdom(
            id=KingdomID.ACID_REACTOR,
            name="Acid Reactor",
            organ_seat="Stomach",
            reigning_law="pH-gated Activation",
            gate="Gastric pH < ~2.0",
            bound="pH capacity (>4.0 largely halts pepsin activity)",
            definition_structures=["stomach", "cardia", "fundus", "body_of_stomach", "antrum", "pylorus",
                                   "parietal_cells", "chief_cells", "g_cells", "ecl_cells"],
            key_mechanisms=["gastric_acid_secretion", "pepsinogen_secretion", "intrinsic_factor_secretion",
                            "gastric_churning"],
            description="Sterilization and protein unfolding. Pepsinogen → pepsin only when sufficiently acidic."
        )

        self.kingdoms[KingdomID.EMULSIFICATION] = Kingdom(
            id=KingdomID.EMULSIFICATION,
            name="Emulsification",
            organ_seat="Liver, Gallbladder, Pancreas",
            reigning_law="Detergent Chemistry",
            gate="CCK release + presence of fat",
            bound="Micellar saturation / insufficient bile acids",
            definition_structures=["liver", "gallbladder", "pancreas", "duodenum", "sphincter_of_oddi"],
            key_mechanisms=["bile_secretion_and_release", "pancreatic_enzyme_secretion",
                            "bicarbonate_secretion_duodenum", "fat_digestion_and_micelle_formation",
                            "cck_release"],
            description="Bile salts act as biological detergents. Without adequate emulsification, lipid-soluble nutrients bypass absorption."
        )

        self.kingdoms[KingdomID.ASSIMILATION] = Kingdom(
            id=KingdomID.ASSIMILATION,
            name="Assimilation",
            organ_seat="Small Intestine (Duodenum, Jejunum, Ileum)",
            reigning_law="Carrier-Mediated Transport",
            gate="Co-factors + transporter state + electrochemical gradients",
            bound="Transporter saturation (fixed bandwidth)",
            definition_structures=["duodenum", "jejunum", "ileum", "enterocyte", "brush_border",
                                   "glycocalyx", "villus", "sglt1", "glut2", "pept1", "npc1l1", "asbt"],
            key_mechanisms=["sglt1_glucose_uptake", "glut2_basolateral_exit", "pept1_peptide_uptake",
                            "fat_absorption_via_micelles", "npc1l1_cholesterol_uptake",
                            "b12_absorption", "bile_acid_reabsorption",
                            "brush_border_carbohydrate_digestion", "brush_border_peptide_digestion"],
            description="The workhorse kingdom. Active, regulated passage through specific transporters. Excess beyond capacity remains luminal."
        )

        self.kingdoms[KingdomID.FERMENTATION] = Kingdom(
            id=KingdomID.FERMENTATION,
            name="Fermentation",
            organ_seat="Colon (Cecum → Sigmoid)",
            reigning_law="Anaerobic Fermentation",
            gate="Arrival of fermentable fiber / resistant starch",
            bound="Microbial carrying capacity",
            definition_structures=["cecum", "ascending_colon", "transverse_colon", "descending_colon",
                                   "sigmoid_colon", "colonocyte", "mucus_layer", "goblet_cell"],
            key_mechanisms=["microbial_fermentation_scfa", "scfa_absorption", "gpr_scfa_signaling",
                            "mucus_layer_dynamics"],
            description="Host enzymes are largely finished. Microbiota convert non-digestible polysaccharides into SCFAs."
        )

        self.kingdoms[KingdomID.TRANSPORT] = Kingdom(
            id=KingdomID.TRANSPORT,
            name="Transport",
            organ_seat="Blood (Portal Vein) + Lymph (Lacteals → Thoracic Duct)",
            reigning_law="Physical Partitioning by Solubility",
            gate="Enterocyte packaging (chylomicron assembly vs portal release)",
            bound="Lipid clearance rate / hepatic first-pass capacity",
            definition_structures=["lacteal", "liver"],
            key_mechanisms=["fat_absorption_via_micelles", "enterohepatic_circulation"],
            description="Water-soluble cargo → portal vein → liver. Fat-soluble cargo → lymph → systemic circulation (bypasses first-pass)."
        )

        self.kingdoms[KingdomID.ENERGY_STRUCTURE] = Kingdom(
            id=KingdomID.ENERGY_STRUCTURE,
            name="Energy & Structure",
            organ_seat="Cell, Mitochondria, Ribosome",
            reigning_law="Thermodynamics / Stoichiometry",
            gate="ATP:ADP ratio, amino-acid thresholds (e.g. leucine for mTOR), redox state",
            bound="Anabolic threshold / energy charge limits",
            definition_structures=[],  # cellular – outside pure GI definition layer
            key_mechanisms=[],
            description="Final execution. Payload is oxidized for ATP or used for macromolecular synthesis. Thresholds must be met or the cascade does not fire."
        )

    def _build_core_modifiers(self):
        """Mechanism Modifiers – alter capacity limits without changing the underlying law."""
        self.modifiers["lactase_nonpersistence"] = MechanismModifier(
            id="lactase_nonpersistence",
            name="Lactase Non-Persistence",
            modifier_type="negative",
            category="genetic",
            affects_structures=["brush_border", "jejunum"],
            affects_mechanisms=["brush_border_carbohydrate_digestion"],
            effect_description="Lactase expression declines after weaning in most humans. Lactose remains undigested.",
            typical_magnitude="Micro-bound for lactose → near 0 in affected adults"
        )

        self.modifiers["ppi_hypochlorhydria"] = MechanismModifier(
            id="ppi_hypochlorhydria",
            name="PPI-induced Hypochlorhydria",
            modifier_type="negative",
            category="drug",
            affects_structures=["stomach", "parietal_cells"],
            affects_mechanisms=["gastric_acid_secretion", "pepsinogen_secretion"],
            effect_description="Proton-pump inhibitors raise gastric pH, impairing pepsin activation and B12 liberation.",
            typical_magnitude="Gastric pH often >4; proteolytic efficiency collapses"
        )

        self.modifiers["butyrate_barrier_synergy"] = MechanismModifier(
            id="butyrate_barrier_synergy",
            name="Butyrate–Barrier Synergy",
            modifier_type="positive",
            category="nutritional_synergy",
            affects_structures=["tight_junction", "colonocyte", "gpr109a"],
            affects_mechanisms=["tight_junction_regulation", "gpr_scfa_signaling"],
            effect_description="Butyrate strengthens tight junctions and fuels colonocytes, expanding safe barrier capacity.",
            typical_magnitude="Improved TEER / reduced permeability in presence of adequate butyrate"
        )

        self.modifiers["vitamin_d_transporter_support"] = MechanismModifier(
            id="vitamin_d_transporter_support",
            name="Vitamin D – Calcium Absorption Synergy",
            modifier_type="positive",
            category="nutritional_synergy",
            affects_structures=["enterocyte", "duodenum", "jejunum"],
            affects_mechanisms=[],  # would link to calcium absorption process when added
            effect_description="Active vitamin D up-regulates TRPV6 and calbindin, increasing active calcium absorption capacity.",
            typical_magnitude="Substantial increase in active Ca2+ transport capacity"
        )

    def _build_runtime_parameters(self):
        """Lens B – controllable / environmental variables."""
        self.runtime_parameters["sleep_quality"] = RuntimeParameter(
            id="sleep_quality",
            name="Sleep Quality & Duration",
            category="sleep",
            description="Affects cortisol rhythm, insulin sensitivity, ghrelin/leptin balance, and recovery capacity.",
            affects_kingdoms=[KingdomID.ENERGY_STRUCTURE, KingdomID.ASSIMILATION]
        )
        self.runtime_parameters["stress_load"] = RuntimeParameter(
            id="stress_load",
            name="Psychological & Physiological Stress",
            category="stress",
            description="Chronic sympathetic activation alters motility, permeability, and visceral sensitivity.",
            affects_kingdoms=[KingdomID.ACID_REACTOR, KingdomID.ASSIMILATION, KingdomID.FERMENTATION]
        )
        self.runtime_parameters["activity_level"] = RuntimeParameter(
            id="activity_level",
            name="Physical Activity / NEAT / Exercise",
            category="activity",
            description="Influences insulin sensitivity, transit time, energy charge, and substrate partitioning.",
            affects_kingdoms=[KingdomID.TRANSPORT, KingdomID.ENERGY_STRUCTURE]
        )
        self.runtime_parameters["toxic_load"] = RuntimeParameter(
            id="toxic_load",
            name="Xenobiotic & Inflammatory Load",
            category="toxin",
            description="Alcohol, ultra-processed emulsifiers, excess LPS, etc., degrade barrier and hepatic capacity.",
            affects_kingdoms=[KingdomID.ASSIMILATION, KingdomID.FERMENTATION, KingdomID.TRANSPORT]
        )
        self.runtime_parameters["circadian_alignment"] = RuntimeParameter(
            id="circadian_alignment",
            name="Circadian Alignment",
            category="circadian",
            description="Feeding and light timing relative to the internal clock modulate metabolic efficiency.",
            affects_kingdoms=[KingdomID.ACID_REACTOR, KingdomID.ASSIMILATION, KingdomID.ENERGY_STRUCTURE]
        )

    def get_kingdom(self, kid: KingdomID) -> Kingdom | None:
        return self.kingdoms.get(kid)

    def summary(self) -> dict[str, Any]:
        return {
            "kingdoms": len(self.kingdoms),
            "modifiers": len(self.modifiers),
            "runtime_parameters": len(self.runtime_parameters),
            "kingdom_names": [k.name for k in self.kingdoms.values()]
        }


def get_system_interaction_registry() -> SystemInteractionRegistry:
    return SystemInteractionRegistry()


if __name__ == "__main__":
    reg = get_system_interaction_registry()
    print("=== Part 4 – System Interaction Principles ===")
    print(reg.summary())
    print("\n--- The 7 Kingdoms ---")
    for kid, k in reg.kingdoms.items():
        print(f"  {kid.value}. {k.name:20s} | Law: {k.reigning_law}")
        print(f"       Gate: {k.gate}")
        print(f"       Bound: {k.bound}")
