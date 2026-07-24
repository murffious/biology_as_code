"""
physiological_effects.py
=================================================================
LAYER 4 – Physiological Effect
Organism/organ biological processes and qualities (GO BP, PATO).
=================================================================
"""

from dataclasses import dataclass, field


@dataclass
class PhysiologicalEffect:
    node_id: str
    label: str
    ontology_primary: str
    go: str | None = None
    other_ontologies: list[str] = field(default_factory=list)
    digestive_or_body_site: list[str] = field(default_factory=list)
    # Upstream Layer 3 mechanisms that contribute to this effect
    upstream_mechanisms: list[str] = field(default_factory=list)
    notes: str = ""
    source: str = ""


class PhysiologicalEffectRegistry:
    def __init__(self):
        self.effects: dict[str, PhysiologicalEffect] = {}
        self._build()

    def register(self, e: PhysiologicalEffect):
        self.effects[e.node_id] = e

    def get(self, node_id: str) -> PhysiologicalEffect | None:
        return self.effects.get(node_id)

    def by_mechanism(self, mech_id: str) -> list[PhysiologicalEffect]:
        return [e for e in self.effects.values() if mech_id in e.upstream_mechanisms]

    def list_ids(self) -> list[str]:
        return sorted(self.effects.keys())

    def summary(self) -> dict[str, int]:
        return {"total": len(self.effects)}

    def _build(self):
        data = [
            ("phys.collagen_fibril", "Collagen fibril organization",
             "GO:0030199", "GO:0030199", [], [],
             ["mech.ascorbate_cofactor_hydroxylase"],
             "ascorbate → connective tissue", "ascorbate → connective tissue"),
            ("phys.intestinal_absorption", "Intestinal absorption",
             "GO:0055128", "GO:0055128", [],
             ["comp.small_intestine", "comp.brush_border"],
             ["mech.sglt1_na_glucose", "mech.pept1_peptide", "mech.glut5_fructose"],
             "", "digestive-taxonomy"),
            ("phys.lipid_absorption", "Intestinal lipid absorption",
             "GO:0030300", "GO:0030300", [],
             ["comp.duodenum", "comp.jejunum", "comp.lacteal"],
             ["mech.micelle_partition_fat_soluble"],
             "", "Part 4.3"),
            ("phys.calcium_homeostasis", "Calcium ion homeostasis",
             "GO:0055074", "GO:0055074", [],
             ["comp.duodenum", "tx.trpv6"],
             ["mech.trpv6_calcium", "mech.vdr_ligand_binding"],
             "", "D–Ca axis"),
            ("phys.bone_mineralization", "Bone mineralization",
             "GO:0030282", "GO:0030282", [], [],
             ["mech.vdr_ligand_binding", "mech.trpv6_calcium", "mech.phylloquinone_ggla"],
             "", "Ca / D / K2 teaching"),
            ("phys.glucose_homeostasis", "Glucose homeostasis",
             "GO:0042593", "GO:0042593", [],
             ["comp.small_intestine", "comp.pancreas"],
             ["mech.sglt1_na_glucose"],
             "", "SGLT1 / incretin"),
            ("phys.mps", "Muscle protein synthesis (anabolic)",
             "GO:0006412", "GO:0006412", ["local:mps"], [],
             ["mech.mtor_leucine"],
             "Leucine/mTOR; free-living magnitude often evidence", "C-3 teaching"),
            ("phys.ileal_brake", "Ileal brake / satiety signaling",
             "local:ileal_brake", None, ["GO:0007586"],
             ["comp.ileum", "horm.glp1", "horm.pyy"],
             [],
             "", "Part 6"),
            ("phys.erythropoiesis", "Erythrocyte differentiation / red cell production",
             "GO:0030218", "GO:0030218", [], [],
             ["mech.b12_if_complex", "mech.folate_1c", "mech.dmt1_iron"],
             "", "B12 / folate / iron"),
            ("phys.blood_coagulation", "Blood coagulation",
             "GO:0007596", "GO:0007596", [], [],
             ["mech.phylloquinone_ggla"],
             "", "Vitamin K carboxylation"),
            ("phys.energy_derivation", "Energy derivation by oxidation of organic compounds",
             "GO:0015980", "GO:0015980", [], [],
             ["mech.thiamine_tpp"],
             "", "macros / B vitamins"),
            ("phys.neural_transmission", "Chemical synaptic transmission support",
             "GO:0007268", "GO:0007268", [], [],
             ["mech.thiamine_tpp", "mech.folate_1c"],
             "", "B vitamins / DHA teaching"),
            ("phys.barrier_integrity", "Epithelial barrier integrity",
             "GO:0061436", "GO:0061436", [],
             ["comp.small_intestine", "comp.large_intestine"],
             [],
             "", "fiber / butyrate / zinc teaching"),
            ("phys.hepatic_first_pass", "Hepatic first-pass processing of portal nutrients",
             "GO:0006805", "GO:0006805", [],
             ["comp.liver", "comp.portal_vein"],
             [],
             "", "Part 5"),
            ("phys.thyroid_hormone", "Thyroid hormone generation",
             "GO:0006590", "GO:0006590", [], [],
             [],
             "", "iodine"),
        ]
        for node_id, label, primary, go, other, sites, upstream, notes, source in data:
            self.register(PhysiologicalEffect(
                node_id=node_id, label=label, ontology_primary=primary,
                go=go, other_ontologies=other, digestive_or_body_site=sites,
                upstream_mechanisms=upstream, notes=notes, source=source
            ))


def get_physiological_effect_registry() -> PhysiologicalEffectRegistry:
    return PhysiologicalEffectRegistry()


if __name__ == "__main__":
    reg = get_physiological_effect_registry()
    print("Layer 4 Physiological Effects:", reg.summary()["total"])
    for e in reg.by_mechanism("mech.ascorbate_cofactor_hydroxylase"):
        print(f"  ascorbate mech → {e.node_id}: {e.label}")
