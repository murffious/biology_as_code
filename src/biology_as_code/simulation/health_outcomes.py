"""
health_outcomes.py
=================================================================
LAYER 5 – Health Outcome
Disease / deficiency poles (MONDO, DOID, HPO) and Wellness poles.
Dual poles prevent one-sided marketing claims.
=================================================================
"""

from dataclasses import dataclass, field


@dataclass
class HealthOutcome:
    node_id: str
    label: str
    pole: str                          # "disease" | "wellness"
    ontology_primary: str
    mondo: str | None = None
    doid: str | None = None
    hpo: list[str] = field(default_factory=list)
    go: str | None = None
    pato: str | None = None
    tier_hint: str = "evidence"        # law_possible | law_truncated | evidence | open
    dual_of: list[str] = field(default_factory=list)
    related_outcomes: list[str] = field(default_factory=list)
    # Upstream Layer 4 effects that contribute
    upstream_effects: list[str] = field(default_factory=list)
    notes: str = ""
    source: str = ""


class HealthOutcomeRegistry:
    def __init__(self):
        self.outcomes: dict[str, HealthOutcome] = {}
        self._build()

    def register(self, o: HealthOutcome):
        self.outcomes[o.node_id] = o

    def get(self, node_id: str) -> HealthOutcome | None:
        return self.outcomes.get(node_id)

    def by_pole(self, pole: str) -> list[HealthOutcome]:
        return [o for o in self.outcomes.values() if o.pole == pole]

    def by_effect(self, effect_id: str) -> list[HealthOutcome]:
        return [o for o in self.outcomes.values() if effect_id in o.upstream_effects]

    def duals_of(self, node_id: str) -> list[HealthOutcome]:
        return [o for o in self.outcomes.values() if node_id in o.dual_of]

    def list_ids(self) -> list[str]:
        return sorted(self.outcomes.keys())

    def summary(self) -> dict[str, int]:
        return {
            "total": len(self.outcomes),
            "disease": len(self.by_pole("disease")),
            "wellness": len(self.by_pole("wellness")),
        }

    def _build(self):
        # ----- Disease poles -----
        disease = [
            ("out.scurvy", "Scurvy", "MONDO:0009412", "MONDO:0009412", "DOID:13724",
             ["HP:0000978", "HP:0000979"], "law_possible",
             ["phys.collagen_fibril"],
             "Ascorbate essentiality → collagen failure", "golden scurvy fixture"),
            ("out.rickets", "Rickets", "MONDO:0005520", "MONDO:0005520", "DOID:10609",
             [], "law_truncated_or_evidence",
             ["phys.bone_mineralization", "phys.calcium_homeostasis"],
             "Bone softening; often vit D / Ca / P", "classical deficiency"),
            ("out.osteomalacia", "Osteomalacia", "MONDO:0001068", "MONDO:0001068", "DOID:10573",
             [], "evidence",
             ["phys.bone_mineralization"],
             "Adult bone softening; commonly vit D–related", "D/Ca"),
            ("out.beriberi", "Beriberi (thiamine deficiency)", "MONDO:0006676", "MONDO:0006676", "DOID:0070313",
             [], "law_possible",
             ["phys.energy_derivation", "phys.neural_transmission"],
             "Thiamine (B1) deficiency disease", "B1"),
            ("out.pellagra", "Pellagra", "MONDO:0019975", "MONDO:0019975", "DOID:8457",
             [], "law_possible", [], "Niacin deficiency disease", "niacin"),
            ("out.b12_deficiency", "Vitamin B12 deficiency", "MONDO:0020696", "MONDO:0020696", "DOID:0050731",
             ["HP:0001872", "HP:0002060"], "law_truncated",
             ["phys.erythropoiesis", "phys.neural_transmission"],
             "Cobalamin deficiency; multi-gate absorption", "B12 relay"),
            ("out.neural_tube_defect", "Neural tube defect risk (folate-related)", "MONDO:0018075", "MONDO:0018075", None,
             ["HP:0002143"], "evidence",
             ["phys.neural_transmission"],
             "NTD risk reduced by periconceptional folate", "folate"),
            ("out.iron_deficiency_anemia", "Iron deficiency anemia", "MONDO:0001356", "MONDO:0001356", "DOID:11758",
             ["HP:0001903"], "law_truncated",
             ["phys.erythropoiesis"],
             "Iron deficiency anemia", "iron"),
            ("out.xerophthalmia", "Xerophthalmia / vitamin A deficiency eye disease", "MONDO:0000948", "MONDO:0000948", "DOID:10138",
             [], "law_possible", [], "Vitamin A deficiency eye disease", "vitamin A"),
            ("out.bleeding_vitk", "Vitamin K deficiency bleeding", "MONDO:0001244", "MONDO:0001244", None,
             ["HP:0001892"], "law_truncated",
             ["phys.blood_coagulation"],
             "Vitamin K deficiency hemorrhagic disease", "vitamin K"),
            ("out.goiter", "Iodine deficiency–related goiter", "MONDO:0006742", "MONDO:0006742", "DOID:13198",
             [], "law_truncated",
             ["phys.thyroid_hormone"],
             "Endemic goiter — iodine-deficiency-related", "iodine"),
            ("out.vitamin_d_deficiency", "Vitamin D deficiency", "MONDO:0100471", "MONDO:0100471", None,
             [], "law_truncated",
             ["phys.calcium_homeostasis", "phys.bone_mineralization"],
             "Low 25-OH-D status", "OLS MONDO"),
            ("out.magnesium_deficiency", "Magnesium deficiency", "MONDO:0006844", "MONDO:0006844", None,
             ["HP:0002917"], "evidence", [], "Nutritional Mg deficiency", "OLS"),
            ("out.zinc_deficiency_status", "Zinc deficiency (status / serum)", "HP:0031831", None, None,
             ["HP:0031831"], "evidence",
             ["phys.barrier_integrity"],
             "Dietary Zn deficiency; phenotype decreased serum zinc", "OLS HP"),
            ("out.folate_deficiency_anemia", "Folic acid deficiency anemia", "MONDO:0001860", "MONDO:0001860", None,
             [], "law_truncated",
             ["phys.erythropoiesis"],
             "Folate-deficient megaloblastic anemia", "OLS"),
        ]
        for node_id, label, primary, mondo, doid, hpo, tier, upstream, notes, source in disease:
            self.register(HealthOutcome(
                node_id=node_id, label=label, pole="disease",
                ontology_primary=primary, mondo=mondo, doid=doid, hpo=hpo,
                tier_hint=tier, upstream_effects=upstream, notes=notes, source=source
            ))

        # ----- Wellness poles (duals) -----
        wellness = [
            ("out.collagen_integrity", "Adequate collagen / connective-tissue integrity",
             "local:collagen_integrity", "GO:0030199", "PATO:0000161",
             "law_truncated", ["out.scurvy"],
             ["phys.collagen_fibril"],
             "Positive dual of scurvy", "dual pole of scurvy"),
            ("out.bone_mineral_adequacy", "Adequate bone mineralization",
             "local:bone_mineral_adequacy", "GO:0030282", None,
             "evidence", ["out.rickets", "out.osteomalacia"],
             ["phys.bone_mineralization"],
             "Positive dual of rickets/osteomalacia", "dual pole of D–Ca bone disease"),
            ("out.hemostasis_adequacy", "Adequate hemostasis (vitamin K–dependent)",
             "local:hemostasis_adequacy", "GO:0007596", None,
             "law_truncated", ["out.bleeding_vitk"],
             ["phys.blood_coagulation"],
             "Positive dual of vitamin K deficiency bleeding", "dual pole of vit K bleeding"),
            ("out.erythropoiesis_adequacy", "Adequate erythropoiesis / red-cell production",
             "local:erythropoiesis_adequacy", "GO:0030218", None,
             "law_truncated", ["out.iron_deficiency_anemia", "out.b12_deficiency"],
             ["phys.erythropoiesis"],
             "Positive dual of iron/B12 deficiency anemias", "dual pole of anemia outcomes"),
            ("out.vision_adequacy", "Adequate vision / ocular surface (vitamin A–related)",
             "local:vision_adequacy", None, None,
             "law_truncated", ["out.xerophthalmia"],
             [], "Positive dual of xerophthalmia", "dual pole of vitamin A disease"),
            ("out.thyroid_adequacy", "Adequate thyroid hormone production (iodine-replete)",
             "local:thyroid_adequacy", "GO:0031641", None,
             "law_truncated", ["out.goiter"],
             ["phys.thyroid_hormone"],
             "Positive dual of iodine-deficiency goiter", "dual pole of goiter"),
            ("out.vitamin_d_adequacy", "Vitamin D–replete status (adequacy dual)",
             "local:vitamin_d_adequacy", None, None,
             "evidence", ["out.vitamin_d_deficiency", "out.rickets", "out.osteomalacia"],
             ["phys.calcium_homeostasis", "phys.bone_mineralization"],
             "Positive dual of D deficiency cluster", "dual pole of vitamin D disease cluster"),
            ("out.folate_adequacy", "Folate-replete status (adequacy dual)",
             "local:folate_adequacy", None, None,
             "evidence", ["out.folate_deficiency_anemia", "out.neural_tube_defect"],
             ["phys.erythropoiesis", "phys.neural_transmission"],
             "Positive dual of folate endpoints", "dual pole of folate endpoints"),
            ("out.energy", "Energy / metabolic energy availability",
             "local:energy", "GO:0015980", None,
             "open", [], ["phys.energy_derivation"],
             "Multi-factor organism-level energy", "notebook chart"),
            ("out.body_composition", "Body composition (lean mass, adiposity, bone mass pattern)",
             "local:body_composition", None, "PATO:0000128",
             "open", [], ["phys.mps"],
             "MPS / energy balance multi-factor", "notebook chart"),
        ]
        for node_id, label, primary, go, pato, tier, dual_of, upstream, notes, source in wellness:
            self.register(HealthOutcome(
                node_id=node_id, label=label, pole="wellness",
                ontology_primary=primary, go=go, pato=pato,
                tier_hint=tier, dual_of=dual_of if isinstance(dual_of, list) else [dual_of],
                upstream_effects=upstream, notes=notes, source=source
            ))


def get_health_outcome_registry() -> HealthOutcomeRegistry:
    return HealthOutcomeRegistry()


if __name__ == "__main__":
    reg = get_health_outcome_registry()
    print("Layer 5 Health Outcomes:", reg.summary())
    print("\nDuals of scurvy:")
    for o in reg.duals_of("out.scurvy"):
        print(f"  {o.node_id}: {o.label}")
