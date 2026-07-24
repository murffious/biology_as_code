"""
kibo_nutrition_ontology.py
Master nutritional topic registry extracted from textbook indices
(Encyclopedia of Human Nutrition 2nd ed., Handbook of Nutrition and Food,
 Advanced Nutrition and Human Metabolism chapters 4, 7, 8, 9).
"""

from biology_as_code.utils.logging import get_logger

log = get_logger(__name__)

from dataclasses import dataclass, field
from enum import StrEnum


class NutritionCategory(StrEnum):
    ENERGY_AND_METABOLISM = "energy_and_metabolism"
    MACRONUTRIENTS = "macronutrients"
    MICRONUTRIENTS = "micronutrients"
    DIGESTION_ABSORPTION_GASTROINTESTINAL = "digestion_absorption_gastrointestinal"
    BODY_COMPOSITION_AND_ANTHROPOMETRY = "body_composition_and_anthropometry"
    HORMONAL_AND_REGULATORY_CONTROL = "hormonal_and_regulatory_control"
    CLINICAL_AND_PATHOLOGICAL_NUTRITION = "clinical_and_pathological_nutrition"
    LIFE_CYCLE_AND_SPECIAL_POPULATIONS = "life_cycle_and_special_populations"
    ASSESSMENT_AND_DIETARY_METHODS = "assessment_and_dietary_methods"
    BIOACTIVE_COMPOUNDS_AND_OTHER = "bioactive_compounds_and_other"
    FOOD_LABELING_AND_REGULATORY = "food_labeling_and_regulatory"


@dataclass
class NutritionTerm:
    name: str
    category: NutritionCategory
    synonyms: list[str] = field(default_factory=list)
    node_type: str = "topic"  # nutrient | process | disease | method | population
    description: str = ""


class KiboNutritionOntology:
    """Central registry of every nutrition topic term."""

    _terms: dict[str, NutritionTerm] = {}
    _by_category: dict[NutritionCategory, list[str]] = {}
    _all_terms: set[str] = set()

    @classmethod
    def load_master(cls):
        if cls._terms:
            return

        master_data = {
            NutritionCategory.ENERGY_AND_METABOLISM: [
                "Energy", "Energy balance", "Energy expenditure", "Basal metabolic rate",
                "Resting metabolic rate", "Thermic effect of food", "Diet-induced thermogenesis",
                "ATP", "Oxidative phosphorylation", "Glycolysis", "Gluconeogenesis",
                "Beta-oxidation", "Ketogenesis", "TCA cycle", "Respiratory quotient"
            ],
            NutritionCategory.MACRONUTRIENTS: [
                "Carbohydrate", "Glucose", "Fiber", "Resistant starch", "Lipids",
                "Fatty acids", "Omega-3 fatty acids", "Protein", "Amino acids",
                "Cholesterol", "Triglycerides", "Chylomicrons"
            ],
            NutritionCategory.MICRONUTRIENTS: [
                "Vitamin C", "Ascorbic acid", "Thiamin", "Riboflavin", "Niacin",
                "Vitamin B6", "Folate", "Vitamin B12", "Cobalamin", "Biotin",
                "Calcium", "Iron", "Zinc", "Copper", "Selenium", "Iodine",
                "Chromium", "Choline", "Vitamin A", "Vitamin D", "Vitamin E", "Vitamin K"
            ],
            NutritionCategory.DIGESTION_ABSORPTION_GASTROINTESTINAL: [
                "Absorption", "Digestion", "Bile", "Bile acids", "Micelles",
                "Brush border", "Lactase", "Pancreatic lipase", "Colipase",
                "Enterohepatic circulation", "Gut microbiota", "Short-chain fatty acids",
                "Fermentation", "Intrinsic factor"
            ],
            NutritionCategory.BODY_COMPOSITION_AND_ANTHROPOMETRY: [
                "Body composition", "Body mass index", "Anthropometry",
                "Skinfold thickness", "DEXA", "Lean body mass"
            ],
            NutritionCategory.HORMONAL_AND_REGULATORY_CONTROL: [
                "Insulin", "Glucagon", "Leptin", "Ghrelin", "Adiponectin",
                "Cortisol", "GLP-1", "PYY", "CCK", "Secretin"
            ],
            NutritionCategory.CLINICAL_AND_PATHOLOGICAL_NUTRITION: [
                "Anemia", "Scurvy", "Beriberi", "Pellagra", "Kwashiorkor",
                "Marasmus", "Diabetes mellitus", "Metabolic syndrome",
                "Osteoporosis", "Celiac disease", "Inflammatory bowel disease"
            ],
            NutritionCategory.LIFE_CYCLE_AND_SPECIAL_POPULATIONS: [
                "Pregnancy", "Lactation", "Infant nutrition", "Elderly",
                "Athletes", "Sports nutrition"
            ],
            NutritionCategory.ASSESSMENT_AND_DIETARY_METHODS: [
                "Dietary Reference Intakes", "RDA", "EAR", "AI", "UL",
                "24-hour recall", "Food frequency questionnaire"
            ],
            NutritionCategory.BIOACTIVE_COMPOUNDS_AND_OTHER: [
                "Antioxidants", "Phytochemicals", "Flavonoids", "Polyphenols",
                "Reactive oxygen species", "Oxidative stress"
            ],
            NutritionCategory.FOOD_LABELING_AND_REGULATORY: [
                "Nutrition Facts Panel", "Health claims", "Nutrient content claims",
                "Daily Value"
            ],
        }

        for category, term_list in master_data.items():
            cls._by_category[category] = term_list
            for name in term_list:
                key = name.lower().replace(" ", "_").replace("-", "_")
                cls._terms[key] = NutritionTerm(
                    name=name,
                    category=category,
                    synonyms=[name.lower()]
                )
                cls._all_terms.add(name)

        log.debug(f"✅ Ontology loaded with {len(cls._terms)} terms")

    @classmethod
    def get_term(cls, name: str) -> NutritionTerm | None:
        key = name.lower().replace(" ", "_").replace("-", "_")
        return cls._terms.get(key)

    @classmethod
    def get_terms_by_category(cls, category: NutritionCategory) -> list[str]:
        return cls._by_category.get(category, [])

    @classmethod
    def all_terms(cls) -> list[str]:
        return sorted(cls._all_terms)

    @classmethod
    def search(cls, query: str) -> list[NutritionTerm]:
        query = query.lower()
        return [t for t in cls._terms.values() if query in t.name.lower()]


# Auto-load on import
KiboNutritionOntology.load_master()


if __name__ == "__main__":
    print("Total terms:", len(KiboNutritionOntology.all_terms()))
    print("Sample search 'vitamin':", [t.name for t in KiboNutritionOntology.search("vitamin")[:5]])
