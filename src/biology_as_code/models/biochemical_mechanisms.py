"""
biochemical_mechanisms.py
=================================================================
LAYER 3 – Biochemical Mechanism
Molecular functions and reactions (GO MF, Rhea, Reactome).

Join key: nutrient.chebi → participates_in → mechanism
=================================================================
"""

from dataclasses import dataclass, field


@dataclass
class BiochemicalMechanism:
    node_id: str
    label: str
    ontology_primary: str
    go: str | None = None
    other_ontologies: list[str] = field(default_factory=list)
    reactome: list[str] = field(default_factory=list)
    notes: str = ""
    source: str = ""
    # Nutrients/compounds that participate in this mechanism (ChEBI or local IDs)
    participants: list[str] = field(default_factory=list)


class BiochemicalMechanismRegistry:
    def __init__(self):
        self.mechanisms: dict[str, BiochemicalMechanism] = {}
        self._build()

    def register(self, m: BiochemicalMechanism):
        self.mechanisms[m.node_id] = m

    def get(self, node_id: str) -> BiochemicalMechanism | None:
        return self.mechanisms.get(node_id)

    def by_participant(self, nutrient_id: str) -> list[BiochemicalMechanism]:
        return [m for m in self.mechanisms.values() if nutrient_id in m.participants]

    def list_ids(self) -> list[str]:
        return sorted(self.mechanisms.keys())

    def summary(self) -> dict[str, int]:
        return {"total": len(self.mechanisms)}

    def _build(self):
        data = [
            ("mech.ascorbate_cofactor_hydroxylase",
             "Ascorbate as cofactor for 2-oxoglutarate-dependent dioxygenases",
             "GO:0016706", "GO:0016706", ["GO:0005506", "RHEA:16501"],
             ["R-HSA-1474244"],
             "Collagen prolyl/lysyl hydroxylases; zero ascorbate → enzyme lockout",
             "scurvy / P4H chemistry",
             ["chebi:ascorbate", "chebi:vitamin_c"]),
            ("mech.vdr_ligand_binding",
             "Vitamin D receptor ligand binding",
             "GO:0008270", "GO:0008270", ["GO:0000981"],
             ["R-HSA-196791", "R-HSA-549127"],
             "Calcitriol–VDR transcriptional program",
             "Reactome vitamin D metabolism",
             ["chebi:calcitriol", "chebi:vitamin_d"]),
            ("mech.micelle_partition_fat_soluble",
             "Partition into mixed micelles (fat-soluble cargo)",
             "GO:0034197", "GO:0034197", [],
             [],
             "Physical chemistry; requires bile + lipid phase",
             "digestive proc.micelle_assembly",
             ["chebi:bile_acids", "local:fat_soluble_vitamins"]),
            ("mech.b12_if_complex",
             "Intrinsic factor–cobalamin complex formation and cubam uptake",
             "GO:0015889", "GO:0015889", [],
             ["R-HSA-196741"],
             "",
             "B12 relay",
             ["chebi:cobalamin", "chebi:vitamin_b12"]),
            ("mech.sglt1_na_glucose",
             "Sodium–glucose symport (SGLT1)",
             "GO:0005412", "GO:0005412", [],
             ["R-HSA-189200"],
             "",
             "Part 4.1",
             ["chebi:glucose", "chebi:galactose"]),
            ("mech.glut5_fructose",
             "Facilitated fructose transport (GLUT5)",
             "GO:0015755", "GO:0015755", [],
             [],
             "",
             "Part 4.1",
             ["chebi:fructose"]),
            ("mech.pept1_peptide",
             "Proton-coupled oligopeptide transport (PepT1)",
             "GO:0015198", "GO:0015198", [],
             [],
             "",
             "Part 4.2",
             ["local:di_tri_peptides"]),
            ("mech.dmt1_iron",
             "Divalent metal ion transport (DMT1)",
             "GO:0006826", "GO:0006826", [],
             [],
             "",
             "Part 4.5",
             ["chebi:fe2", "chebi:iron"]),
            ("mech.trpv6_calcium",
             "Calcium ion transmembrane transport (TRPV6)",
             "GO:0070588", "GO:0070588", [],
             [],
             "",
             "Part 4.5",
             ["chebi:calcium"]),
            ("mech.mtor_leucine",
             "Leucine sensing / mTORC1 activation (molecular)",
             "GO:0038202", "GO:0038202", [],
             ["R-HSA-165159"],
             "Mechanism real; free-living magnitude is evidence-tier",
             "kiboAnabolicGraph",
             ["chebi:leucine"]),
            ("mech.gulo_absent_human",
             "Human GULO pseudogene — no endogenous ascorbate synthesis",
             "local:gulo_pseudogene", None, ["GO:0006570"],
             [],
             "Declared constant for all humans — essentiality context",
             "scurvy law fixture",
             ["chebi:ascorbate"]),
            ("mech.folate_1c",
             "One-carbon transfer (folate coenzyme)",
             "GO:0006730", "GO:0006730", [],
             ["R-HSA-196757"],
             "",
             "folate biochemistry",
             ["chebi:folate", "chebi:folic_acid"]),
            ("mech.thiamine_tpp",
             "Thiamine diphosphate as cofactor",
             "GO:0000287", "GO:0000287", [],
             [],
             "",
             "B1 biochemistry",
             ["chebi:thiamine", "chebi:vitamin_b1"]),
            ("mech.phylloquinone_ggla",
             "Vitamin K–dependent gamma-carboxylation",
             "GO:0006471", "GO:0006471", [],
             ["R-HSA-159740"],
             "",
             "K cycle",
             ["chebi:phylloquinone", "chebi:vitamin_k"]),
            ("mech.hepcidin_ferroportin",
             "Hepcidin regulation of ferroportin",
             "GO:0033212", "GO:0033212", [],
             [],
             "",
             "Part 4.5 iron",
             ["chebi:iron", "local:hepcidin"]),
        ]
        for node_id, label, primary, go, other, reactome, notes, source, participants in data:
            self.register(BiochemicalMechanism(
                node_id=node_id, label=label, ontology_primary=primary,
                go=go, other_ontologies=other, reactome=reactome,
                notes=notes, source=source, participants=participants
            ))


def get_biochemical_mechanism_registry() -> BiochemicalMechanismRegistry:
    return BiochemicalMechanismRegistry()


if __name__ == "__main__":
    reg = get_biochemical_mechanism_registry()
    print("Layer 3 Biochemical Mechanisms:", reg.summary()["total"])
    for m in reg.by_participant("chebi:ascorbate"):
        print(f"  ascorbate → {m.node_id}: {m.label}")
