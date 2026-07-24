"""
food_additives_registry.py
=================================================================
Standalone registry for Food Additives and Non-Nutritive Components
Based on Technical Effects of Food Additives tables
(from the Non-nutritive components of food chapter)
=================================================================

This models the Input Layer of the KIBO machine for substances that
enter the digestive system but are not classical essential nutrients.
"""

from dataclasses import dataclass, field


@dataclass
class FoodAdditiveCategory:
    """One technical effect category of food additives."""
    technical_effect: str
    description: str
    typical_additives: list[str]
    possible_physiological_notes: str = ""
    host_effect_tags: list[str] = field(default_factory=list)
    systems_touched: list[str] = field(default_factory=list)


class FoodAdditivesRegistry:
    """
    Registry of food additive technical effects.
    
    Supports:
    - Lookup by technical effect
    - Search by additive name
    - Full list for ontology browsing
    """

    def __init__(self):
        self.categories: dict[str, FoodAdditiveCategory] = {}
        self._build()

    def register(self, cat: FoodAdditiveCategory) -> None:
        key = cat.technical_effect.lower().strip()
        self.categories[key] = cat

    def get(self, technical_effect: str) -> FoodAdditiveCategory | None:
        return self.categories.get(technical_effect.lower().strip())

    def list_all(self) -> list[FoodAdditiveCategory]:
        return list(self.categories.values())

    def list_effects(self) -> list[str]:
        return [c.technical_effect for c in self.categories.values()]

    def find_by_additive(self, name: str) -> list[FoodAdditiveCategory]:
        """Return all categories that list this additive (case-insensitive partial match)."""
        name_lower = name.lower()
        results = []
        for cat in self.categories.values():
            for additive in cat.typical_additives:
                if name_lower in additive.lower():
                    results.append(cat)
                    break
        return results

    def effects_for_additives(self, names: list[str]) -> dict:
        """Qualitative join: additive name(s) → categories → host_effect_tags."""
        hits: list[dict] = []
        tags: list[str] = []
        systems: list[str] = []
        for name in names:
            for cat in self.find_by_additive(name):
                hits.append(
                    {
                        "query": name,
                        "category": cat.technical_effect,
                        "host_effect_tags": list(cat.host_effect_tags),
                        "systems_touched": list(cat.systems_touched),
                        "notes": cat.possible_physiological_notes,
                    }
                )
                tags.extend(cat.host_effect_tags)
                systems.extend(cat.systems_touched)
        return {
            "tier": "FLOW_open_qualitative",
            "queries": list(names),
            "matches": hits,
            "unique_effect_tags": sorted(set(tags)),
            "unique_systems": sorted(set(systems)),
        }

    def summary(self) -> dict:
        return {
            "total_categories": len(self.categories),
            "effects": self.list_effects()
        }

    @staticmethod
    def _infer_hooks(effect: str, notes: str):
        e = (effect + " " + notes).lower()
        tags: list[str] = []
        systems: list[str] = []
        if "emulsif" in e or "lipid" in e or "micelle" in e:
            tags.append("lipid_absorption_modulation")
            systems.append("Assimilation")
        if "preserv" in e or "microb" in e:
            tags.append("microbiota_modulation")
            systems.append("Defense")
        if "nutrient" in e or "fortif" in e:
            tags.append("nutrient_delivery_increase")
            systems.append("Assimilation")
        if "msg" in e or "flavor enhancer" in e:
            tags.append("excitatory_amino_acid_signal")
            systems.append("Communication")
        if "barrier" in e:
            tags.append("gut_barrier_modulation")
        if not tags:
            tags.append("processing_aid_low_residue")
            systems.append("Assimilation")
        return tags, systems or ["Assimilation"]

    def _build(self) -> None:
        """Populate registry from Technical Effects tables."""

        data = [
            # --- Emulsifiers ---
            (
                "Emulsifiers",
                "Substances that promote the formation and stability of emulsions (oil-in-water or water-in-oil).",
                [
                    "Mono- and diglycerides",
                    "Lecithin",
                    "Propylene glycol monostearate",
                    "Polysorbate 60",
                    "Polysorbate 65",
                    "Polysorbate 80",
                    "Sorbitan monostearate"
                ],
                "Can influence micelle formation and lipid absorption; some may affect gut barrier or microbiota."
            ),
            # --- Enzymes ---
            (
                "Enzymes",
                "Biological catalysts used to modify food components during processing.",
                [
                    "Rennet",
                    "Pepsin",
                    "Pectinase",
                    "Amylases",
                    "Proteases"
                ],
                "Most are inactivated by cooking or digestion; residual activity is usually negligible."
            ),
            # --- Firming agents ---
            (
                "Firming agents",
                "Substances that precipitate residual pectin and strengthen plant tissue structure.",
                [
                    "Aluminum sulfate",
                    "Calcium chloride",
                    "Calcium lactate",
                    "Calcium sulfate",
                    "Calcium citrate"
                ],
                "Calcium salts can contribute to mineral intake and affect intestinal water balance."
            ),
            # --- Flavor enhancers ---
            (
                "Flavor enhancers",
                "Substances that intensify existing flavors without contributing a flavor of their own.",
                [
                    "Monosodium glutamate (MSG)",
                    "Disodium inosinate",
                    "Disodium guanylate"
                ],
                "MSG is an excitatory amino acid; high doses may affect sensitive individuals."
            ),
            # --- Flavoring agents ---
            (
                "Flavoring agents",
                "Substances that impart flavor (natural or synthetic).",
                [
                    "Natural spices and herbs",
                    "Essential oils",
                    "Synthetic flavor chemicals (approx. 1500 identified entities)"
                ],
                "Wide chemical diversity; most are present at low concentrations."
            ),
            # --- Flour-treating agents ---
            (
                "Flour-treating agents",
                "Substances added to flour to improve baking quality, bleaching, or aging.",
                [
                    "Acetone peroxide",
                    "Azodicarbonamide",
                    "Benzoyl peroxide",
                    "Potassium bromate",
                    "Chlorine dioxide"
                ],
                "Some (e.g. potassium bromate) have been restricted in certain jurisdictions due to safety concerns."
            ),
            # --- Freezing agents ---
            (
                "Freezing agents",
                "Substances used for rapid freezing of foods.",
                [
                    "Liquid nitrogen",
                    "Dichlorodifluoromethane",
                    "Liquid carbon dioxide"
                ],
                "Generally leave no residue; primarily processing aids."
            ),
            # --- Fumigants ---
            (
                "Fumigants",
                "Gases used to control pests in stored foods or packaging.",
                [
                    "Methyl bromide",
                    "Ethylene oxide",
                    "Phosphine"
                ],
                "Residues are tightly regulated; potential toxicological concern if limits exceeded."
            ),
            # --- Humectants ---
            (
                "Humectants",
                "Substances that retain moisture and prevent drying.",
                [
                    "Sorbitol",
                    "Propylene glycol",
                    "Glycerine",
                    "Sodium tripolyphosphate"
                ],
                "Can affect osmotic balance and intestinal water content; some are fermentable (e.g. sorbitol)."
            ),
            # --- Ion-exchange resins ---
            (
                "Ion-exchange resins",
                "Insoluble polymers used to modify ionic composition of foods or process water.",
                [
                    "Acrylamide resins",
                    "Sulfonated copolymers of styrene and divinylbenzene"
                ],
                "Primarily processing aids; minimal residual presence in final food."
            ),
            # --- Leavening agents ---
            (
                "Leavening agents",
                "Substances that produce gas to lighten the texture of baked goods.",
                [
                    "Yeast",
                    "Sodium bicarbonate",
                    "Monocalcium phosphate",
                    "Sodium acid pyrophosphate"
                ],
                "Generally regarded as safe; contribute minor mineral load."
            ),
            # --- Lubricants and release agents ---
            (
                "Lubricants and release agents",
                "Substances that prevent food from sticking to equipment or packaging.",
                [
                    "Mineral oil",
                    "Stearic acid",
                    "Calcium stearate",
                    "Magnesium stearate"
                ],
                "Usually present at very low residual levels."
            ),
            # --- Maturing agents ---
            (
                "Maturing agents",
                "Substances that accelerate the aging of flour to improve baking performance.",
                [
                    "Potassium bromate",
                    "Azodicarbonamide",
                    "Chlorine dioxide"
                ],
                "Overlaps with flour-treating agents; some have regulatory restrictions."
            ),
            # --- Nutrient supplements ---
            (
                "Nutrient supplements",
                "Vitamins, minerals, or amino acids added to fortify foods.",
                [
                    "Vitamins (various)",
                    "Minerals (various)",
                    "Amino acids"
                ],
                "Directly increase nutrient delivery; bioavailability depends on form and food matrix."
            ),
            # --- Oxidizing and reducing agents ---
            (
                "Oxidizing and reducing agents",
                "Substances that alter the oxidation-reduction state of food components.",
                [
                    "Hydrogen peroxide",
                    "Sulfur dioxide",
                    "Ascorbic acid",
                    "Potassium bromate"
                ],
                "Sulfur dioxide can affect sensitive individuals (asthmatics); ascorbic acid is also a nutrient."
            ),
            # --- pH control agents ---
            (
                "pH control agents",
                "Acids, bases, and buffers used to adjust or maintain acidity.",
                [
                    "Vinegar (acetic acid)",
                    "Citric acid",
                    "Lactic acid",
                    "Sodium bicarbonate",
                    "Phosphates"
                ],
                "Can influence mineral solubility, enzyme activity, and microbial growth in the gut."
            ),
            # --- Preservatives / antimicrobial agents ---
            (
                "Preservatives / antimicrobial agents",
                "Substances that inhibit growth of microorganisms or delay spoilage.",
                [
                    "Sodium benzoate",
                    "Calcium propionate",
                    "Potassium sorbate",
                    "Sodium nitrite",
                    "Sulfur dioxide"
                ],
                "Can alter gut microbiota composition; some (nitrites) have complex risk-benefit profiles."
            ),
            # --- Processing aids ---
            (
                "Processing aids",
                "Substances used during manufacturing that are not intended to remain in the final product.",
                [
                    "Enzymes",
                    "Activated charcoal",
                    "Filtering aids",
                    "Clarifying agents"
                ],
                "Residues are expected to be negligible if good manufacturing practices are followed."
            ),
            # --- Propellants and aerating agents ---
            (
                "Propellants and aerating agents",
                "Gases used to expel products from containers or to aerate foods.",
                [
                    "Nitrogen",
                    "Carbon dioxide",
                    "Nitrous oxide"
                ],
                "Generally inert and leave no residue."
            ),
            # --- Sequestrants ---
            (
                "Sequestrants",
                "Substances that bind metal ions to prevent oxidation, discoloration, or off-flavors.",
                [
                    "Citric acid",
                    "EDTA (ethylenediaminetetraacetic acid)",
                    "Calcium disodium EDTA",
                    "Phosphoric acid",
                    "Sodium metaphosphate"
                ],
                "Can reduce bioavailability of minerals (iron, zinc, calcium) by chelation."
            ),
            # --- Solvents and vehicles ---
            (
                "Solvents and vehicles",
                "Liquids used to dissolve or carry other food additives or flavors.",
                [
                    "Ethyl alcohol",
                    "Propylene glycol",
                    "Glycerine",
                    "Triethyl citrate"
                ],
                "Most are metabolized or excreted; propylene glycol has known metabolic pathways."
            ),
            # --- Stabilizers and thickeners ---
            (
                "Stabilizers and thickeners",
                "Substances that increase viscosity or stabilize emulsions and suspensions.",
                [
                    "Modified food starches",
                    "Guar gum",
                    "Acacia (gum arabic)",
                    "Carob bean gum (locust bean gum)",
                    "Carrageenan",
                    "Xanthan gum"
                ],
                "Many are fermentable by colonic microbiota and contribute to SCFA production or gas."
            ),
            # --- Surface-active agents ---
            (
                "Surface-active agents",
                "Substances that modify surface tension (related to emulsifiers and defoamers).",
                [
                    "Dioctyl sodium sulfosuccinate",
                    "Sodium lauryl sulfate",
                    "Dimethyl polysiloxane"
                ],
                "Generally used at low levels; some may affect mucosal surfaces."
            ),
            # --- Surface-finishing agents ---
            (
                "Surface-finishing agents",
                "Substances applied to the surface of foods to improve appearance, protect, or seal.",
                [
                    "Beeswax",
                    "Carnauba wax",
                    "Shellac",
                    "Oxidized polyethylene",
                    "Gum acacia"
                ],
                "Mostly poorly digested; may pass through the GI tract largely intact."
            ),
            # --- Synergists ---
                (
                "Synergists",
                "Substances that enhance the effect of other additives (especially antioxidants).",
                [
                    "Citric acid",
                    "Tricalcium phosphate",
                    "Other phosphates"
                ],
                "Often act via metal chelation (overlap with sequestrants)."
            ),
            # --- Texturizers ---
            (
                "Texturizers",
                "Substances that modify the mouthfeel or physical texture of foods.",
                [
                    "Sodium bicarbonate",
                    "Glycerine",
                    "Corn syrup",
                    "Modified food starch"
                ],
                "Can influence gastric emptying and intestinal transit."
            ),
            # --- Washing-peeling aids ---
            (
                "Washing-peeling aids",
                "Substances used to clean or remove peels from fruits and vegetables.",
                [
                    "Sodium hydroxide (lye)",
                    "Sodium metasilicate",
                    "Sodium hypochlorite",
                    "Oxalic acid"
                ],
                "Residues are rinsed off; residual alkali or oxidant is minimized by good practice."
            ),
        ]

        for effect, description, additives, notes in data:
            tags, systems = self._infer_hooks(effect, notes)
            self.register(
                FoodAdditiveCategory(
                    technical_effect=effect,
                    description=description,
                    typical_additives=additives,
                    possible_physiological_notes=notes,
                    host_effect_tags=list(tags),
                    systems_touched=list(systems),
                )
            )


def get_food_additives_registry() -> FoodAdditivesRegistry:
    """Factory function for the registry."""
    return FoodAdditivesRegistry()


if __name__ == "__main__":
    reg = get_food_additives_registry()
    print("Food Additives Registry loaded")
    print(f"Total categories: {reg.summary()['total_categories']}")
    print("\nAvailable technical effects:")
    for effect in reg.list_effects():
        print(f"  • {effect}")

    print("\n--- Example lookup: Emulsifiers ---")
    emuls = reg.get("Emulsifiers")
    if emuls:
        print(f"Description: {emuls.description}")
        print(f"Typical additives: {', '.join(emuls.typical_additives[:4])}...")
        print(f"Physiological notes: {emuls.possible_physiological_notes}")

    print("\n--- Search for 'citric acid' ---")
    matches = reg.find_by_additive("citric acid")
    for m in matches:
        print(f"  Found in: {m.technical_effect}")
