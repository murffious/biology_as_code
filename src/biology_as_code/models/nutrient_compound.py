"""
nutrient_compound.py
=================================================================
Thin Nutrient / Compound layer.
Links FoodPayload → ChEBI (or local) ID → Layer 3 Biochemical Mechanisms.
=================================================================
"""

from dataclasses import dataclass, field


@dataclass
class NutrientCompound:
    """A molecular nutrient or bioactive compound."""
    id: str                          # e.g. chebi:ascorbate or local:leucine
    label: str
    chebi: str | None = None
    common_names: list[str] = field(default_factory=list)
    category: str = "micronutrient"  # macronutrient | micronutrient | bioactive | mineral
    # Layer 3 mechanisms this compound participates in
    participates_in: list[str] = field(default_factory=list)
    notes: str = ""


class NutrientCompoundRegistry:
    def __init__(self):
        self.compounds: dict[str, NutrientCompound] = {}
        self._build()

    def register(self, c: NutrientCompound):
        self.compounds[c.id] = c

    def get(self, compound_id: str) -> NutrientCompound | None:
        return self.compounds.get(compound_id)

    def by_mechanism(self, mech_id: str) -> list[NutrientCompound]:
        return [c for c in self.compounds.values() if mech_id in c.participates_in]

    def list_ids(self) -> list[str]:
        return sorted(self.compounds.keys())

    def summary(self) -> dict[str, int]:
        return {"total": len(self.compounds)}

    def _build(self):
        data = [
            ("chebi:ascorbate", "Ascorbate (Vitamin C)", "CHEBI:38290",
             ["vitamin C", "ascorbic acid"], "micronutrient",
             ["mech.ascorbate_cofactor_hydroxylase", "mech.gulo_absent_human"]),
            ("chebi:vitamin_c", "Vitamin C", "CHEBI:29073",
             ["ascorbate"], "micronutrient",
             ["mech.ascorbate_cofactor_hydroxylase", "mech.gulo_absent_human"]),
            ("chebi:calcitriol", "Calcitriol (1,25-dihydroxyvitamin D3)", "CHEBI:17823",
             ["active vitamin D"], "micronutrient",
             ["mech.vdr_ligand_binding"]),
            ("chebi:vitamin_d", "Vitamin D", "CHEBI:27300",
             ["cholecalciferol", "D3"], "micronutrient",
             ["mech.vdr_ligand_binding"]),
            ("chebi:cobalamin", "Cobalamin (Vitamin B12)", "CHEBI:30411",
             ["vitamin B12"], "micronutrient",
             ["mech.b12_if_complex"]),
            ("chebi:vitamin_b12", "Vitamin B12", "CHEBI:30411",
             ["cobalamin"], "micronutrient",
             ["mech.b12_if_complex"]),
            ("chebi:glucose", "Glucose", "CHEBI:17234",
             ["D-glucose"], "macronutrient",
             ["mech.sglt1_na_glucose"]),
            ("chebi:galactose", "Galactose", "CHEBI:28260",
             [], "macronutrient",
             ["mech.sglt1_na_glucose"]),
            ("chebi:fructose", "Fructose", "CHEBI:15824",
             [], "macronutrient",
             ["mech.glut5_fructose"]),
            ("chebi:leucine", "Leucine", "CHEBI:15603",
             ["L-leucine"], "macronutrient",
             ["mech.mtor_leucine"]),
            ("chebi:folate", "Folate", "CHEBI:27470",
             ["folic acid", "vitamin B9"], "micronutrient",
             ["mech.folate_1c"]),
            ("chebi:folic_acid", "Folic acid", "CHEBI:27470",
             ["folate"], "micronutrient",
             ["mech.folate_1c"]),
            ("chebi:thiamine", "Thiamine (Vitamin B1)", "CHEBI:18385",
             ["vitamin B1"], "micronutrient",
             ["mech.thiamine_tpp"]),
            ("chebi:vitamin_b1", "Vitamin B1", "CHEBI:18385",
             ["thiamine"], "micronutrient",
             ["mech.thiamine_tpp"]),
            ("chebi:phylloquinone", "Phylloquinone (Vitamin K1)", "CHEBI:18067",
             ["vitamin K1"], "micronutrient",
             ["mech.phylloquinone_ggla"]),
            ("chebi:vitamin_k", "Vitamin K", "CHEBI:28384",
             ["phylloquinone", "menaquinone"], "micronutrient",
             ["mech.phylloquinone_ggla"]),
            ("chebi:iron", "Iron", "CHEBI:18248",
             ["Fe", "Fe2+", "Fe3+"], "mineral",
             ["mech.dmt1_iron", "mech.hepcidin_ferroportin"]),
            ("chebi:fe2", "Iron(2+)", "CHEBI:29033",
             ["ferrous iron"], "mineral",
             ["mech.dmt1_iron"]),
            ("chebi:calcium", "Calcium", "CHEBI:22984",
             ["Ca2+"], "mineral",
             ["mech.trpv6_calcium"]),
            ("local:di_tri_peptides", "Di- and Tri-peptides", None,
             ["oligopeptides"], "macronutrient",
             ["mech.pept1_peptide"]),
            ("local:fat_soluble_vitamins", "Fat-soluble vitamins (A/D/E/K class)", None,
             [], "micronutrient",
             ["mech.micelle_partition_fat_soluble"]),
            ("chebi:bile_acids", "Bile acids", "CHEBI:3098",
             [], "bioactive",
             ["mech.micelle_partition_fat_soluble"]),
        ]
        for cid, label, chebi, names, cat, mechs in data:
            self.register(NutrientCompound(
                id=cid, label=label, chebi=chebi,
                common_names=names, category=cat,
                participates_in=mechs
            ))


def get_nutrient_compound_registry() -> NutrientCompoundRegistry:
    return NutrientCompoundRegistry()


if __name__ == "__main__":
    reg = get_nutrient_compound_registry()
    print("Nutrient/Compound registry:", reg.summary()["total"])
    c = reg.get("chebi:ascorbate")
    if c:
        print(f"  {c.label} participates in: {c.participates_in}")
