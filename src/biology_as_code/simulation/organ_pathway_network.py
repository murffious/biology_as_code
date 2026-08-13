"""
organ_pathway_network.py
Expanded organ laws and metabolic pathway network for the engine.
Captures multi-organ interactions, pathway dependencies,
and lever/limit constraints derived from textbook physiology.
"""

import copy
from dataclasses import dataclass, field
from enum import StrEnum


class Organ(StrEnum):
    LIVER = "liver"
    GUT = "gut"
    PANCREAS = "pancreas"
    KIDNEY = "kidney"
    HEART = "heart"
    MUSCLE = "muscle"
    ADIPOSE = "adipose"
    BRAIN = "brain"
    IMMUNE = "immune"


class Pathway(StrEnum):
    GLYCOLYSIS = "glycolysis"
    GLUCONEOGENESIS = "gluconeogenesis"
    TCA = "tca"
    BETA_OXIDATION = "beta_oxidation"
    KETOGENESIS = "ketogenesis"
    LIPOGENESIS = "lipogenesis"
    PROTEIN_SYNTHESIS = "protein_synthesis"
    UREA_CYCLE = "urea_cycle"
    GLYCOGEN_SYNTHESIS = "glycogen_synthesis"
    GLYCOGENOLYSIS = "glycogenolysis"
    PENTOSE_PHOSPHATE = "pentose_phosphate"
    CHOLESTEROL_SYNTHESIS = "cholesterol_synthesis"
    BILE_ACID_SYNTHESIS = "bile_acid_synthesis"
    ANTIOXIDANT_DEFENSE = "antioxidant_defense"
    INFLAMMATION = "inflammation"
    INSULIN_SIGNALING = "insulin_signaling"
    AMPK_SIGNALING = "ampk_signaling"
    MTOR_SIGNALING = "mtor_signaling"


@dataclass
class OrganLaw:
    organ: Organ
    description: str
    capacity: float = 1.0               # 0.0–1.5 typical range
    energy_cost: float = 0.05           # relative energy cost of high activity
    primary_pathways: list[Pathway] = field(default_factory=list)
    inhibited_by: list[str] = field(default_factory=list)   # e.g. "inflammation", "hypoxia"
    stimulated_by: list[str] = field(default_factory=list)


@dataclass
class PathwayNode:
    pathway: Pathway
    base_rate: float = 1.0
    organs: list[Organ] = field(default_factory=list)
    requires_vitamins: list[str] = field(default_factory=list)  # coenzyme dependencies
    requires_energy: bool = True
    produces_energy: bool = False
    inhibited_by: list[str] = field(default_factory=list)
    stimulated_by: list[str] = field(default_factory=list)


# Core organ laws (expanded)
DEFAULT_ORGAN_LAWS: dict[Organ, OrganLaw] = {
    Organ.LIVER: OrganLaw(
        organ=Organ.LIVER,
        description="Central metabolic hub – detox, glucose regulation, lipid handling, bile production",
        capacity=1.0,
        energy_cost=0.12,
        primary_pathways=[
            Pathway.GLUCONEOGENESIS, Pathway.TCA, Pathway.BETA_OXIDATION,
            Pathway.KETOGENESIS, Pathway.UREA_CYCLE, Pathway.BILE_ACID_SYNTHESIS,
            Pathway.CHOLESTEROL_SYNTHESIS, Pathway.LIPOGENESIS
        ],
        inhibited_by=["inflammation", "hypoxia", "toxin_load"],
        stimulated_by=["glucagon", "cortisol", "fasting"]
    ),
    Organ.GUT: OrganLaw(
        organ=Organ.GUT,
        description="Digestion, absorption, barrier integrity, SCFA sensing, immune interface",
        capacity=1.0,
        energy_cost=0.08,
        primary_pathways=[Pathway.GLYCOLYSIS, Pathway.ANTIOXIDANT_DEFENSE],
        inhibited_by=["inflammation", "dysbiosis", "low_butyrate"],
        stimulated_by=["fiber", "scfa", "glp1"]
    ),
    Organ.PANCREAS: OrganLaw(
        organ=Organ.PANCREAS,
        description="Enzyme secretion + endocrine (insulin/glucagon) control",
        capacity=1.0,
        energy_cost=0.04,
        primary_pathways=[Pathway.INSULIN_SIGNALING],
        inhibited_by=["inflammation", "high_fat_toxicity"],
        stimulated_by=["glucose", "amino_acids", "incretins"]
    ),
    Organ.KIDNEY: OrganLaw(
        organ=Organ.KIDNEY,
        description="Filtration, electrolyte balance, gluconeogenesis (minor), acid-base",
        capacity=1.0,
        energy_cost=0.10,
        primary_pathways=[Pathway.GLUCONEOGENESIS, Pathway.TCA],
        inhibited_by=["dehydration", "inflammation"],
        stimulated_by=["high_protein", "acidosis"]
    ),
    Organ.HEART: OrganLaw(
        organ=Organ.HEART,
        description="Circulatory delivery of oxygen and nutrients; high ATP demand",
        capacity=1.0,
        energy_cost=0.15,
        primary_pathways=[Pathway.TCA, Pathway.BETA_OXIDATION],
        inhibited_by=["hypoxia", "inflammation"],
        stimulated_by=["exercise", "catecholamines"]
    ),
    Organ.MUSCLE: OrganLaw(
        organ=Organ.MUSCLE,
        description="Major site of glucose disposal, glycogen storage, protein turnover",
        capacity=1.0,
        energy_cost=0.20,
        primary_pathways=[
            Pathway.GLYCOLYSIS, Pathway.GLYCOGEN_SYNTHESIS, Pathway.GLYCOGENOLYSIS,
            Pathway.TCA, Pathway.BETA_OXIDATION, Pathway.PROTEIN_SYNTHESIS,
            Pathway.AMPK_SIGNALING, Pathway.MTOR_SIGNALING
        ],
        inhibited_by=["inflammation", "inactivity"],
        stimulated_by=["exercise", "insulin", "amino_acids"]
    ),
    Organ.ADIPOSE: OrganLaw(
        organ=Organ.ADIPOSE,
        description="Energy storage, adipokine secretion (leptin, adiponectin), lipolysis",
        capacity=1.0,
        energy_cost=0.03,
        primary_pathways=[Pathway.LIPOGENESIS, Pathway.BETA_OXIDATION],
        inhibited_by=["inflammation"],
        stimulated_by=["insulin", "cortisol"]
    ),
    Organ.BRAIN: OrganLaw(
        organ=Organ.BRAIN,
        description="Glucose (and ketone) dependent; high continuous energy demand",
        capacity=1.0,
        energy_cost=0.18,
        primary_pathways=[Pathway.GLYCOLYSIS, Pathway.TCA],
        inhibited_by=["hypoglycemia", "hypoxia"],
        stimulated_by=["glucose", "ketones"]
    ),
    Organ.IMMUNE: OrganLaw(
        organ=Organ.IMMUNE,
        description="Inflammatory tone, cytokine production, barrier surveillance",
        capacity=1.0,
        energy_cost=0.06,
        primary_pathways=[Pathway.INFLAMMATION, Pathway.ANTIOXIDANT_DEFENSE, Pathway.GLYCOLYSIS],
        inhibited_by=["butyrate", "anti_inflammatory_signals"],
        stimulated_by=["dysbiosis", "pathogen", "tissue_damage"]
    ),
}


# Pathway dependency network (simplified)
DEFAULT_PATHWAYS: dict[Pathway, PathwayNode] = {
    Pathway.GLYCOLYSIS: PathwayNode(
        pathway=Pathway.GLYCOLYSIS,
        base_rate=1.0,
        organs=[Organ.MUSCLE, Organ.BRAIN, Organ.GUT, Organ.LIVER],
        requires_vitamins=["b1", "b2", "b3"],
        produces_energy=True
    ),
    Pathway.GLUCONEOGENESIS: PathwayNode(
        pathway=Pathway.GLUCONEOGENESIS,
        base_rate=0.3,
        organs=[Organ.LIVER, Organ.KIDNEY],
        requires_vitamins=["b3", "b6", "b7"],
        requires_energy=True
    ),
    Pathway.TCA: PathwayNode(
        pathway=Pathway.TCA,
        base_rate=1.0,
        organs=[Organ.LIVER, Organ.MUSCLE, Organ.HEART, Organ.BRAIN],
        requires_vitamins=["b1", "b2", "b3", "b5"],
        produces_energy=True
    ),
    Pathway.BETA_OXIDATION: PathwayNode(
        pathway=Pathway.BETA_OXIDATION,
        base_rate=0.6,
        organs=[Organ.LIVER, Organ.MUSCLE, Organ.HEART],
        requires_vitamins=["b2", "b3", "b5"],
        produces_energy=True
    ),
    Pathway.KETOGENESIS: PathwayNode(
        pathway=Pathway.KETOGENESIS,
        base_rate=0.2,
        organs=[Organ.LIVER],
        requires_vitamins=["b3"],
        produces_energy=False
    ),
    Pathway.INSULIN_SIGNALING: PathwayNode(
        pathway=Pathway.INSULIN_SIGNALING,
        base_rate=1.0,
        organs=[Organ.MUSCLE, Organ.ADIPOSE, Organ.LIVER],
        requires_vitamins=[],
        inhibited_by=["inflammation", "lipotoxicity"]
    ),
    Pathway.AMPK_SIGNALING: PathwayNode(
        pathway=Pathway.AMPK_SIGNALING,
        base_rate=0.5,
        organs=[Organ.MUSCLE, Organ.LIVER],
        requires_vitamins=[],
        stimulated_by=["exercise", "fasting", "low_energy"]
    ),
    Pathway.MTOR_SIGNALING: PathwayNode(
        pathway=Pathway.MTOR_SIGNALING,
        base_rate=0.7,
        organs=[Organ.MUSCLE],
        requires_vitamins=[],
        stimulated_by=["amino_acids", "insulin", "resistance_exercise"]
    ),
    Pathway.ANTIOXIDANT_DEFENSE: PathwayNode(
        pathway=Pathway.ANTIOXIDANT_DEFENSE,
        base_rate=0.8,
        organs=[Organ.LIVER, Organ.GUT, Organ.IMMUNE],
        requires_vitamins=["c", "e", "selenium", "zinc"]
    ),
    Pathway.INFLAMMATION: PathwayNode(
        pathway=Pathway.INFLAMMATION,
        base_rate=0.3,
        organs=[Organ.IMMUNE, Organ.GUT, Organ.ADIPOSE],
        requires_vitamins=[],
        inhibited_by=["butyrate", "omega3", "anti_inflammatory"]
    ),
}


class OrganPathwayNetwork:
    """Runtime network that tracks capacity and pathway rates."""

    def __init__(self):
        # Deep-copy the module-global defaults so per-instance mutations
        # (set_organ_capacity / apply_inflammation) never leak across engines.
        self.organs: dict[Organ, OrganLaw] = {k: copy.deepcopy(v) for k, v in DEFAULT_ORGAN_LAWS.items()}
        self.pathways: dict[Pathway, PathwayNode] = {k: copy.deepcopy(v) for k, v in DEFAULT_PATHWAYS.items()}
        self.pathway_rates: dict[Pathway, float] = {p: node.base_rate for p, node in self.pathways.items()}

    def set_organ_capacity(self, organ: Organ, capacity: float):
        if organ in self.organs:
            self.organs[organ].capacity = max(0.1, min(1.5, capacity))

    def apply_vitamin_cofactors(self, vitamin_adequacy: dict[str, float]):
        """Scale pathway rates by required vitamin cofactors."""
        for pathway, node in self.pathways.items():
            if not node.requires_vitamins:
                continue
            factors = [vitamin_adequacy.get(v, 1.0) for v in node.requires_vitamins]
            if factors:
                avg_factor = sum(factors) / len(factors)
                self.pathway_rates[pathway] *= max(0.4, avg_factor)

    def apply_inflammation(self, inflammation_score: float):
        """High inflammation reduces capacity of sensitive organs and pathways."""
        for law in self.organs.values():
            if "inflammation" in law.inhibited_by:
                law.capacity *= max(0.5, 1.0 - inflammation_score * 0.5)

        for pathway, node in self.pathways.items():
            if "inflammation" in node.inhibited_by:
                self.pathway_rates[pathway] *= max(0.4, 1.0 - inflammation_score * 0.6)

    def get_energy_support(self) -> float:
        """Rough aggregate energy-producing capacity."""
        energy_pathways = [Pathway.TCA, Pathway.BETA_OXIDATION, Pathway.GLYCOLYSIS]
        total = sum(self.pathway_rates.get(p, 0.5) for p in energy_pathways)
        return total / len(energy_pathways)

    def summary(self) -> dict:
        return {
            "organ_capacities": {o.value: round(law.capacity, 3) for o, law in self.organs.items()},
            "key_pathway_rates": {
                p.value: round(rate, 3)
                for p, rate in self.pathway_rates.items()
                if p in [Pathway.TCA, Pathway.GLYCOLYSIS, Pathway.GLUCONEOGENESIS,
                         Pathway.BETA_OXIDATION, Pathway.INSULIN_SIGNALING,
                         Pathway.AMPK_SIGNALING, Pathway.INFLAMMATION]
            },
            "energy_support": round(self.get_energy_support(), 3)
        }


if __name__ == "__main__":
    net = OrganPathwayNetwork()
    print("Default energy support:", net.get_energy_support())
    net.apply_inflammation(0.6)
    net.apply_vitamin_cofactors({"b1": 0.5, "b3": 0.7, "c": 0.4})
    print("After inflammation + low vitamins:")
    print(net.summary())
