"""
nutrient_sensing.py
=================================================================
Multi-node regulatory graphs for the three master nutrient sensors:
AMPK (energy stress), mTORC1 (growth / anabolic), and SREBP (lipogenic /
sterol). These deepen the scalar proxies in ``pathway_regulation.py`` into
inspectable signed networks — nodes are signaling molecules, edges carry an
``effect`` of "activates" or "inhibits" plus the mechanism.

The famous cross-talk is explicit: AMPK ⊣ mTORC1 (double-negative feedback),
AMPK → ULK1 vs mTORC1 ⊣ ULK1 (the autophagy switch), and mTORC1 → SREBP with
AMPK ⊣ SREBP (the lipogenesis switch).
=================================================================
"""

from dataclasses import dataclass, field


@dataclass
class RegulatoryNode:
    id: str
    name: str
    role: str  # input | sensor | kinase | transcription_factor | effector
    notes: str = ""


@dataclass
class RegulatoryEdge:
    from_node: str
    to_node: str
    effect: str  # "activates" | "inhibits"
    mechanism: str = ""
    notes: str = ""


class RegulatoryPathway:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, RegulatoryNode] = {}
        self.edges: list[RegulatoryEdge] = []
        self.references: list[str] = []

    def add_node(self, node: RegulatoryNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: RegulatoryEdge) -> None:
        self.edges.append(edge)

    def summary(self) -> dict:
        activates = sum(1 for e in self.edges if e.effect == "activates")
        inhibits = sum(1 for e in self.edges if e.effect == "inhibits")
        return {
            "name": self.name,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "activating_edges": activates,
            "inhibiting_edges": inhibits,
        }


_REFERENCES = [
    "New developments in AMPK and mTORC1 cross-talk — Essays in Biochemistry 2024: "
    "PMC12055038 (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12055038/)",
    "AMPK-ULK1-mTORC1 regulatory triangle / autophagy oscillation: "
    "PMC7576158 (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7576158/)",
    "mTORC1, the maestro of cell metabolism and growth — Genes & Development 2025: "
    "https://genesdev.cshlp.org/content/39/1-2/109.full",
]


@dataclass
class NutrientSensingRegistry:
    pathways: dict[str, RegulatoryPathway] = field(default_factory=dict)

    def __post_init__(self):
        self._build()

    def register(self, pathway: RegulatoryPathway) -> None:
        pathway.references = list(_REFERENCES)
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> RegulatoryPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[RegulatoryPathway]:
        return list(self.pathways.values())

    def _build(self) -> None:
        self._build_ampk()
        self._build_mtorc1()
        self._build_srebp()
        self._build_gut_incretin()

    # -- AMPK: the energy-stress sensor ---------------------------------
    def _build_ampk(self) -> None:
        p = RegulatoryPathway(
            name="ampk_network",
            description=(
                "AMPK energy-stress network. A rising AMP/ADP:ATP ratio (plus LKB1 and "
                "Ca²⁺/CaMKK2) activates AMPK, which switches the cell from anabolic to "
                "catabolic: it inhibits ACC and mTORC1/SREBP while activating fatty-acid "
                "oxidation, autophagy (ULK1), and mitochondrial biogenesis (PGC-1α)."
            ),
        )
        for nid, name, role in [
            ("amp_adp_atp", "AMP/ADP : ATP ratio", "input"),
            ("lkb1", "LKB1", "kinase"),
            ("camkk2", "CaMKK2 (Ca²⁺)", "kinase"),
            ("ampk", "AMPK", "sensor"),
            ("acc", "Acetyl-CoA carboxylase (ACC)", "effector"),
            ("fatty_acid_oxidation", "Fatty-acid oxidation", "effector"),
            ("tsc2", "TSC2", "effector"),
            ("mtorc1", "mTORC1", "kinase"),
            ("ulk1", "ULK1 (autophagy initiator)", "effector"),
            ("srebp1c", "SREBP-1c", "transcription_factor"),
            ("pgc1a", "PGC-1α (mito biogenesis)", "transcription_factor"),
        ]:
            p.add_node(RegulatoryNode(nid, name, role))
        for a, b, eff, mech in [
            ("amp_adp_atp", "ampk", "activates", "allosteric AMP binding + protects Thr172"),
            ("lkb1", "ampk", "activates", "Thr172 phosphorylation"),
            ("camkk2", "ampk", "activates", "Ca²⁺-dependent Thr172 phosphorylation"),
            ("ampk", "acc", "inhibits", "phosphorylation → ↓malonyl-CoA"),
            ("acc", "fatty_acid_oxidation", "inhibits", "malonyl-CoA blocks CPT-1"),
            ("ampk", "tsc2", "activates", "phosphorylation activates the mTORC1 brake"),
            ("tsc2", "mtorc1", "inhibits", "Rheb-GAP"),
            ("ampk", "mtorc1", "inhibits", "Raptor phosphorylation (+ via TSC2)"),
            ("ampk", "ulk1", "activates", "Ser317/Ser777 phosphorylation → autophagy"),
            ("ampk", "srebp1c", "inhibits", "Ser372 phosphorylation → ↓lipogenesis"),
            ("ampk", "pgc1a", "activates", "mitochondrial biogenesis program"),
        ]:
            p.add_edge(RegulatoryEdge(a, b, eff, mech))
        self.register(p)

    # -- mTORC1: the growth / anabolic sensor ---------------------------
    def _build_mtorc1(self) -> None:
        p = RegulatoryPathway(
            name="mtorc1_network",
            description=(
                "mTORC1 growth network. Amino acids (leucine via the Rag GTPases) and "
                "insulin/IGF (PI3K→Akt→TSC2→Rheb) converge to activate mTORC1, which drives "
                "protein synthesis (S6K1, 4E-BP1) and lipogenesis (SREBP) while shutting down "
                "autophagy (ULK1). AMPK opposes it (double-negative feedback)."
            ),
        )
        for nid, name, role in [
            ("amino_acids", "Amino acids (leucine)", "input"),
            ("rag_gtpases", "Rag GTPases (lysosome)", "sensor"),
            ("insulin_igf", "Insulin / IGF-1", "input"),
            ("pi3k_akt", "PI3K → Akt", "kinase"),
            ("tsc2", "TSC2", "effector"),
            ("rheb", "Rheb-GTP", "effector"),
            ("mtorc1", "mTORC1", "kinase"),
            ("s6k1", "S6K1", "kinase"),
            ("fourebp1", "4E-BP1", "effector"),
            ("protein_synthesis", "Protein synthesis", "effector"),
            ("srebp", "SREBP-1c/2", "transcription_factor"),
            ("ulk1", "ULK1 (autophagy)", "effector"),
            ("ampk", "AMPK", "sensor"),
        ]:
            p.add_node(RegulatoryNode(nid, name, role))
        for a, b, eff, mech in [
            ("amino_acids", "rag_gtpases", "activates", "leucine sensing (Sestrin2/GATOR)"),
            ("rag_gtpases", "mtorc1", "activates", "recruits mTORC1 to the lysosome"),
            ("insulin_igf", "pi3k_akt", "activates", "receptor → PI3K → Akt"),
            ("pi3k_akt", "tsc2", "inhibits", "Akt phosphorylation releases the brake"),
            ("tsc2", "rheb", "inhibits", "Rheb-GAP keeps Rheb inactive"),
            ("rheb", "mtorc1", "activates", "Rheb-GTP is the direct activator"),
            ("mtorc1", "s6k1", "activates", "phosphorylation"),
            ("s6k1", "protein_synthesis", "activates", "ribosome biogenesis / translation"),
            ("mtorc1", "fourebp1", "inhibits", "phospho-4E-BP1 releases eIF4E"),
            ("fourebp1", "protein_synthesis", "inhibits", "sequesters eIF4E when active"),
            ("mtorc1", "srebp", "activates", "drives lipogenic / sterol transcription"),
            ("mtorc1", "ulk1", "inhibits", "Ser757 phosphorylation blocks autophagy"),
            ("ampk", "mtorc1", "inhibits", "cross-talk brake (Raptor + TSC2)"),
        ]:
            p.add_edge(RegulatoryEdge(a, b, eff, mech))
        self.register(p)

    # -- SREBP: the lipogenic / sterol program --------------------------
    def _build_srebp(self) -> None:
        p = RegulatoryPathway(
            name="srebp_network",
            description=(
                "SREBP lipogenic/sterol network. SREBP-1c (fatty-acid synthesis) is driven by "
                "insulin and mTORC1 and braked by AMPK; SREBP-2 (cholesterol) is sterol-regulated "
                "through SCAP/INSIG. Active SREBPs turn on ACC/FASN and HMGCR/LDLR."
            ),
        )
        for nid, name, role in [
            ("insulin", "Insulin", "input"),
            ("mtorc1", "mTORC1", "kinase"),
            ("ampk", "AMPK", "sensor"),
            ("sterols", "ER cholesterol", "input"),
            ("scap_insig", "SCAP / INSIG", "sensor"),
            ("srebp1c", "SREBP-1c", "transcription_factor"),
            ("srebp2", "SREBP-2", "transcription_factor"),
            ("acc_fasn", "ACC + FASN", "effector"),
            ("hmgcr", "HMG-CoA reductase", "effector"),
            ("ldlr", "LDL receptor", "effector"),
        ]:
            p.add_node(RegulatoryNode(nid, name, role))
        for a, b, eff, mech in [
            ("insulin", "srebp1c", "activates", "transcription + proteolytic maturation"),
            ("mtorc1", "srebp1c", "activates", "nuclear SREBP accumulation"),
            ("ampk", "srebp1c", "inhibits", "phosphorylation blocks cleavage/activity"),
            ("sterols", "scap_insig", "activates", "sterols lock SCAP to INSIG in the ER"),
            ("scap_insig", "srebp2", "inhibits", "retention blocks Golgi processing when sterols high"),
            ("srebp1c", "acc_fasn", "activates", "lipogenic gene transcription"),
            ("srebp2", "hmgcr", "activates", "cholesterol-synthesis gene transcription"),
            ("srebp2", "ldlr", "activates", "LDL-cholesterol uptake"),
        ]:
            p.add_edge(RegulatoryEdge(a, b, eff, mech))
        self.register(p)

    # -- Gut incretin / satiety mini-graph (Wave B2) -------------------------
    def _build_gut_incretin(self) -> None:
        p = RegulatoryPathway(
            name="gut_incretin_network",
            description=(
                "Meal-triggered gut hormone mini-graph: CCK (I cells, fat/protein), "
                "GLP-1 (L cells, carbs/mixed meal), GIP (K cells), and PYY. Teaching "
                "edges to satiety, gallbladder/bile release, and insulin (incretin effect). "
                "FLOW signaling topology — not a full enteroendocrine atlas."
            ),
        )
        for nid, name, role, notes in [
            ("meal_nutrients", "Meal nutrients (lumen / absorbate)", "input", "Fat, protein, carb signals."),
            ("cck", "CCK (cholecystokinin)", "sensor", "I cells; fat/protein dominant."),
            ("glp1", "GLP-1 (glucagon-like peptide-1)", "sensor", "L cells; incretin + satiety."),
            ("gip", "GIP (glucose-dependent insulinotropic peptide)", "sensor", "K cells; incretin."),
            ("pyy", "PYY (peptide YY)", "sensor", "L cells; satiety / ileal brake teaching."),
            ("gallbladder_bile_release", "Gallbladder contraction / bile release", "effector", "CCK-driven."),
            ("pancreatic_enzymes", "Pancreatic enzyme secretion", "effector", "CCK teaching path."),
            ("insulin_secretion", "β-cell insulin secretion", "effector", "Incretin effect (GLP-1, GIP)."),
            ("satiety", "Satiety / reduced intake drive", "effector", "Central + vagal teaching readout."),
            ("gastric_emptying", "Gastric emptying rate", "effector", "Slowed by CCK/GLP-1 teaching."),
        ]:
            p.add_node(RegulatoryNode(nid, name, role, notes))
        for a, b, eff, mech in [
            ("meal_nutrients", "cck", "activates", "fat/protein → I-cell CCK"),
            ("meal_nutrients", "glp1", "activates", "nutrients → L-cell GLP-1"),
            ("meal_nutrients", "gip", "activates", "nutrients → K-cell GIP"),
            ("meal_nutrients", "pyy", "activates", "distal nutrients → L-cell PYY"),
            ("cck", "gallbladder_bile_release", "activates", "CCK → gallbladder contraction"),
            ("cck", "pancreatic_enzymes", "activates", "CCK → acinar secretion"),
            ("cck", "gastric_emptying", "inhibits", "CCK slows emptying"),
            ("cck", "satiety", "activates", "vagal / central satiety"),
            ("glp1", "insulin_secretion", "activates", "incretin effect (glucose-dependent)"),
            ("glp1", "gastric_emptying", "inhibits", "GLP-1 slows emptying"),
            ("glp1", "satiety", "activates", "central satiety / reduced intake"),
            ("gip", "insulin_secretion", "activates", "incretin effect"),
            ("pyy", "satiety", "activates", "ileal brake / satiety"),
            ("pyy", "gastric_emptying", "inhibits", "slows proximal transit teaching"),
        ]:
            p.add_edge(RegulatoryEdge(a, b, eff, mech))
        # Separate references for this graph (override shared AMPK set on register)
        p.references = [
            "Incretin hormones GLP-1 and GIP — standard endocrine/GI physiology.",
            "CCK and gallbladder / pancreatic secretion — GI teaching texts.",
            "PYY and ileal brake — satiety physiology reviews.",
        ]
        self.pathways[p.name.lower()] = p  # register without overwriting AMPK refs


def evaluate_network(
    pathway: RegulatoryPathway,
    inputs: dict[str, float],
    *,
    default_source: float = 0.5,
) -> dict[str, float]:
    """Propagate input activations through a signed graph → per-node activation [0,1].

    Each of these networks is a DAG, so a single topological pass is exact. A node's
    activation is the mean over its incoming edges of ``up`` (activates) or ``1 - up``
    (inhibits). Source nodes take their value from ``inputs`` (or ``default_source``).
    """

    def _clamp(v: float) -> float:
        return 0.0 if v < 0.0 else 1.0 if v > 1.0 else v

    nodes = pathway.nodes
    incoming: dict[str, list[RegulatoryEdge]] = {nid: [] for nid in nodes}
    for e in pathway.edges:
        if e.to_node in incoming:
            incoming[e.to_node].append(e)

    # Kahn topological order (fall back to declaration order for any stray cycle).
    indeg = {nid: len(incoming[nid]) for nid in nodes}
    queue = [nid for nid in nodes if indeg[nid] == 0]
    order: list[str] = []
    while queue:
        n = queue.pop(0)
        order.append(n)
        for e in pathway.edges:
            if e.from_node == n and e.to_node in indeg:
                indeg[e.to_node] -= 1
                if indeg[e.to_node] == 0:
                    queue.append(e.to_node)
    for nid in nodes:
        if nid not in order:
            order.append(nid)

    act: dict[str, float] = {}
    for nid in order:
        if nid in inputs:
            act[nid] = _clamp(float(inputs[nid]))
        elif not incoming[nid]:
            act[nid] = _clamp(float(inputs.get(nid, default_source)))
        else:
            contribs = [
                act.get(e.from_node, default_source)
                if e.effect == "activates"
                else 1.0 - act.get(e.from_node, default_source)
                for e in incoming[nid]
            ]
            act[nid] = _clamp(sum(contribs) / len(contribs))
    return act


def get_nutrient_sensing_registry() -> NutrientSensingRegistry:
    return NutrientSensingRegistry()


if __name__ == "__main__":
    reg = get_nutrient_sensing_registry()
    for name in ("ampk_network", "mtorc1_network", "srebp_network"):
        p = reg.get(name)
        print(p.name, p.summary())
