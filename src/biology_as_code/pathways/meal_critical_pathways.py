"""
meal_critical_pathways.py
=================================================================
Tier-B meal-path teaching graphs (Assimilation → Transport → Bioenergetics
hooks). Maps high-value cogs from MAP_COG_QUEUE — not the full encyclopedia.

Graphs:
  1. iron_absorption           — non-haem lumen → DMT1 → ferroportin / hepcidin
  2. cobalamin_absorption      — B12 + intrinsic factor → ileal uptake
  3. glucose_epithelial_transport — SGLT1 apical + GLUT2 basolateral
  4. scfa_colonic_production   — fermentable fiber → acetate/propionate/butyrate

FLOW teaching. Gate/bound magnitudes stay in law/unit paths (e.g. iron UNIT).
=================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

try:
    from biology_as_code.pathways.metabolic_mechanisms import (
        get_metabolic_mechanism_registry,
    )
except ImportError:
    get_metabolic_mechanism_registry = None


class PathwayNodeType(Enum):
    SUBSTRATE = "substrate"
    INTERMEDIATE = "intermediate"
    PRODUCT = "product"
    SIGNAL = "signal"
    LUMEN = "lumen"
    ENTEROCYTE = "enterocyte"
    CIRCULATION = "circulation"


@dataclass
class MetaboliteNode:
    id: str
    name: str
    node_type: PathwayNodeType
    notes: str = ""


@dataclass
class ReactionEdge:
    from_node: str
    to_node: str
    mechanism_id: str = ""
    enzyme: str = ""
    process: str = ""
    location: str = ""
    regulation: str = ""
    notes: str = ""
    effect: str = ""  # signed edge marker, e.g. "⊣" (inhibition) — rendered in the label


class MetabolicPathway:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, MetaboliteNode] = {}
        self.edges: list[ReactionEdge] = []
        self.references: list[str] = []
        self.extra_summary: dict = {}

    def add_node(self, node: MetaboliteNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ReactionEdge) -> None:
        self.edges.append(edge)

    def get_mechanism(self, edge: ReactionEdge):
        if get_metabolic_mechanism_registry is None or not edge.mechanism_id:
            return None
        return get_metabolic_mechanism_registry().get(edge.mechanism_id)

    def summary(self) -> dict:
        out = {
            "name": self.name,
            "description": self.description,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
        }
        out.update(self.extra_summary)
        return out


class MealCriticalPathwaysRegistry:
    """High-value meal-path graphs (queue tier B)."""

    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_iron_absorption()
        self._build_cobalamin_absorption()
        self._build_glucose_epithelial_transport()
        self._build_scfa_colonic_production()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    # ------------------------------------------------------------------
    # 1. Iron absorption (non-haem teaching path)
    # ------------------------------------------------------------------
    def _build_iron_absorption(self) -> None:
        p = MetabolicPathway(
            name="iron_absorption",
            description=(
                "Iron absorption teaching path with parallel non-haem and haem branches. "
                "Non-haem: Fe³⁺ reduction → DMT1 apical uptake → ferroportin export "
                "(hepcidin block). Haem: HCP1-like apical uptake → HO-1 releases Fe²⁺ into "
                "the enterocyte pool → same ferroportin exit. Ascorbate co-occupation favors "
                "the ferrous lumen pool. FLOW topology — magnitude bounds live in iron UNIT / laws."
            ),
        )
        for nid, name, nt, notes in [
            ("dietary_nonheme_fe3", "Dietary non-haem Fe³⁺", PathwayNodeType.LUMEN,
             "Label iron is not absorbed iron. Form + co-occupants matter."),
            ("dietary_heme", "Dietary haem iron", PathwayNodeType.LUMEN,
             "Higher fractional absorption than non-haem; separate apical path."),
            ("heme_enterocyte", "Haem (enterocyte)", PathwayNodeType.ENTEROCYTE,
             "Intact haem after apical uptake; cleaved by HO-1."),
            ("fe2_lumen", "Fe²⁺ (lumen pool)", PathwayNodeType.LUMEN,
             "Ascorbate / reducing surface expands usable ferrous pool."),
            ("fe2_enterocyte", "Fe²⁺ (enterocyte)", PathwayNodeType.ENTEROCYTE,
             "Cytosolic labile iron; shared by non-haem and haem branches."),
            ("plasma_transferrin_fe", "Transferrin-bound Fe (plasma)", PathwayNodeType.CIRCULATION,
             "Systemic transport form after basolateral export + oxidation."),
            ("hepcidin", "Hepcidin", PathwayNodeType.SIGNAL,
             "Liver peptide; internalizes/blocks ferroportin."),
            ("ascorbate_meal", "Meal ascorbate (enhancer)", PathwayNodeType.SIGNAL,
             "Same-meal co-occupation gate — not daily average."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge(
            from_node="dietary_nonheme_fe3", to_node="fe2_lumen",
            mechanism_id="duodenal_cytochrome_b",
            enzyme="DcytB / brush-border reductases",
            location="Duodenal lumen / brush border",
            notes="Fe³⁺ → Fe²⁺. Supported by reducing agents including ascorbate.",
        ))
        p.add_edge(ReactionEdge(
            from_node="ascorbate_meal", to_node="fe2_lumen",
            process="Reductant co-occupation",
            location="Lumen",
            regulation="Gate-shaped: partner must share the meal",
            notes="Teaching link: ascorbate expands ferrous pool (not a second substrate edge).",
        ))
        p.add_edge(ReactionEdge(
            from_node="fe2_lumen", to_node="fe2_enterocyte",
            mechanism_id="dmt1",
            enzyme="DMT1 (SLC11A2)",
            location="Apical membrane (duodenum)",
            regulation="Expression rises in iron deficiency",
            notes="Proton-coupled ferrous iron uptake.",
        ))
        # Wave B2: expanded haem branch (was a single compressed stub)
        p.add_edge(ReactionEdge(
            from_node="dietary_heme", to_node="heme_enterocyte",
            mechanism_id="hcp1_heme_uptake",
            enzyme="HCP1 / PCFT-related haem uptake (teaching)",
            location="Apical membrane",
            notes="Apical haem uptake; higher fractional absorption than non-haem.",
        ))
        p.add_edge(ReactionEdge(
            from_node="heme_enterocyte", to_node="fe2_enterocyte",
            mechanism_id="heme_oxygenase_1",
            enzyme="Heme oxygenase-1 (HO-1)",
            location="Enterocyte",
            notes="Cleaves haem → Fe²⁺ + biliverdin + CO; joins labile iron pool.",
        ))
        p.add_edge(ReactionEdge(
            from_node="fe2_enterocyte", to_node="plasma_transferrin_fe",
            mechanism_id="ferroportin",
            enzyme="Ferroportin (SLC40A1) + hephaestin/ceruloplasmin oxidation",
            location="Basolateral membrane",
            regulation="Blocked when hepcidin high",
            notes="Export is the systemic control point for absorption (both branches).",
        ))
        p.add_edge(ReactionEdge(
            from_node="hepcidin", to_node="plasma_transferrin_fe",
            mechanism_id="hepcidin_ferroportin",
            effect="⊣",
            process="Hepcidin ⊣ ferroportin",
            location="Enterocyte basolateral / RES",
            regulation="Inflammation and iron repletion raise hepcidin",
            notes="Inhibitory teaching edge: high hepcidin lowers effective export.",
        ))

        p.references = [
            "Iron homeostasis / ferroportin regulation (lactoferrin model): PMID 39005063 "
            "(https://pubmed.ncbi.nlm.nih.gov/39005063/).",
            "DMT1 apical Fe²⁺ uptake — NCBI Gene SLC11A2: "
            "https://www.ncbi.nlm.nih.gov/gene/?term=SLC11A2",
            "Ferroportin basolateral iron export — NCBI Gene SLC40A1: "
            "https://www.ncbi.nlm.nih.gov/gene/?term=SLC40A1",
            "Hepcidin (HAMP) ⊣ ferroportin control point — NCBI Gene HAMP: "
            "https://www.ncbi.nlm.nih.gov/gene/?term=HAMP",
            "Magnitude bounds live in iron UNIT / laws (Biology as Code).",
        ]
        p.extra_summary = {
            "primary_system": "Assimilation",
            "systems": ["SYS_01", "SYS_02", "SYS_04"],
            "clinical_hooks": "iron deficiency anemia; anemia of inflammation",
            "control_point": "ferroportin / hepcidin",
            "queue_tier": "B",
        }
        self.register(p)

    # ------------------------------------------------------------------
    # 2. Cobalamin (B12) + intrinsic factor
    # ------------------------------------------------------------------
    def _build_cobalamin_absorption(self) -> None:
        p = MetabolicPathway(
            name="cobalamin_absorption",
            description=(
                "Vitamin B12 (cobalamin) absorption requires gastric intrinsic factor (IF). "
                "Dietary B12 is released in the stomach, binds IF, and the IF–B12 complex is "
                "absorbed in the terminal ileum via cubam receptor teaching path. "
                "Failure poles: IF deficiency (pernicious anemia), ileal disease."
            ),
        )
        for nid, name, nt, notes in [
            ("dietary_b12", "Dietary cobalamin (B12)", PathwayNodeType.LUMEN, "Protein-bound in food; acid/pepsin help release."),
            ("free_b12", "Free B12 (gastric/duodenal)", PathwayNodeType.LUMEN, "Transient; binds haptocorrin then IF."),
            ("intrinsic_factor", "Intrinsic factor (IF)", PathwayNodeType.SIGNAL, "Parietal-cell glycoprotein; acid-dependent production context."),
            ("if_b12_complex", "IF–B12 complex", PathwayNodeType.INTERMEDIATE, "Resistant complex for ileal uptake."),
            ("ileal_uptake", "Ileal enterocyte uptake", PathwayNodeType.ENTEROCYTE, "Cubam (cubilin/amnionless) teaching receptor."),
            ("plasma_b12", "Transcobalamin-bound B12 (plasma)", PathwayNodeType.CIRCULATION, "Delivery to tissues; methyl-B12 / Ado-B12 cofactor forms."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge(
            from_node="dietary_b12", to_node="free_b12",
            process="Gastric release (acid / pepsin context)",
            location="Stomach",
            notes="Hypochlorhydria can impair release from food matrix.",
        ))
        p.add_edge(ReactionEdge(
            from_node="free_b12", to_node="if_b12_complex",
            mechanism_id="intrinsic_factor",
            enzyme="Intrinsic factor binding",
            location="Duodenum / jejunum after haptocorrin handoff",
            notes="IF is obligatory for efficient ileal absorption.",
        ))
        p.add_edge(ReactionEdge(
            from_node="intrinsic_factor", to_node="if_b12_complex",
            mechanism_id="intrinsic_factor",
            process="IF co-occupation",
            location="Proximal small bowel",
            notes="Teaching edge: IF must be present with B12.",
        ))
        p.add_edge(ReactionEdge(
            from_node="if_b12_complex", to_node="ileal_uptake",
            enzyme="Cubam receptor-mediated endocytosis",
            location="Terminal ileum",
            notes="Receptor-mediated; ileal resection loses this step.",
        ))
        p.add_edge(ReactionEdge(
            from_node="ileal_uptake", to_node="plasma_b12",
            process="Export + transcobalamin binding",
            location="Enterocyte → portal/systemic",
            notes="Compressed multi-step exit to circulation.",
        ))

        p.references = [
            "Intrinsic factor required for B12 absorption in pernicious anemia: PMID 18112756 "
            "(https://pubmed.ncbi.nlm.nih.gov/18112756/).",
            "Intrinsic factor localization (gastric / duodenal extracts): PMID 15405205 "
            "(https://pubmed.ncbi.nlm.nih.gov/15405205/).",
            "Pernicious anemia = IF failure pole (B12 replacement): PMID 14935513 "
            "(https://pubmed.ncbi.nlm.nih.gov/14935513/).",
            "Ileal cubam receptor — NCBI Gene CUBN (cubilin) + AMN (amnionless): "
            "https://www.ncbi.nlm.nih.gov/gene/?term=CUBN",
        ]
        p.extra_summary = {
            "primary_system": "Assimilation",
            "systems": ["SYS_01", "SYS_02"],
            "clinical_hooks": "pernicious anemia; ileal disease",
            "obligatory_partner": "intrinsic_factor",
            "queue_tier": "B",
        }
        self.register(p)

    # ------------------------------------------------------------------
    # 3. Glucose epithelial transport
    # ------------------------------------------------------------------
    def _build_glucose_epithelial_transport(self) -> None:
        p = MetabolicPathway(
            name="glucose_epithelial_transport",
            description=(
                "Epithelial glucose handling after luminal liberation: SGLT1 (SLC5A1) "
                "Na⁺-coupled apical uptake in duodenum/jejunum; GLUT2 (SLC2A2) basolateral "
                "exit toward portal blood. GLUT5 fructose stub noted. Complements "
                "carb_digestion_absorption pack without duplicating amylase steps."
            ),
        )
        for nid, name, nt, notes in [
            ("glucose_lumen", "Glucose (lumen)", PathwayNodeType.LUMEN, "From starch/disaccharide digestion."),
            ("galactose_lumen", "Galactose (lumen)", PathwayNodeType.LUMEN, "Also SGLT1 cargo."),
            ("glucose_enterocyte", "Glucose (enterocyte)", PathwayNodeType.ENTEROCYTE, "Apical uptake product."),
            ("glucose_portal", "Glucose (portal blood)", PathwayNodeType.CIRCULATION, "To liver / systemic."),
            ("fructose_lumen", "Fructose (lumen)", PathwayNodeType.LUMEN, "GLUT5 path; not SGLT1."),
            ("fructose_enterocyte", "Fructose (enterocyte)", PathwayNodeType.ENTEROCYTE, "GLUT5 apical."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge(
            from_node="glucose_lumen", to_node="glucose_enterocyte",
            mechanism_id="sglt1",
            enzyme="SGLT1 (SLC5A1)",
            location="Apical membrane",
            notes="Na⁺-glucose cotransport; secondary active.",
        ))
        p.add_edge(ReactionEdge(
            from_node="galactose_lumen", to_node="glucose_enterocyte",
            mechanism_id="sglt1",
            enzyme="SGLT1 (SLC5A1)",
            location="Apical membrane",
            notes="Galactose shares SGLT1.",
        ))
        p.add_edge(ReactionEdge(
            from_node="glucose_enterocyte", to_node="glucose_portal",
            mechanism_id="glut2",
            enzyme="GLUT2 (SLC2A2)",
            location="Basolateral membrane",
            notes="Facilitated exit to interstitium / capillary.",
        ))
        p.add_edge(ReactionEdge(
            from_node="fructose_lumen", to_node="fructose_enterocyte",
            mechanism_id="glut5",
            enzyme="GLUT5 (SLC2A5)",
            location="Apical membrane",
            notes="Fructose-specific facilitated transporter.",
        ))
        p.add_edge(ReactionEdge(
            from_node="fructose_enterocyte", to_node="glucose_portal",
            mechanism_id="glut2",
            enzyme="GLUT2 (basolateral fructose/glucose)",
            location="Basolateral membrane",
            notes="Compressed: fructose can exit via GLUT2 toward portal blood.",
        ))

        p.references = [
            "SGLT1 Na⁺-glucose apical cotransport — NCBI Gene SLC5A1: "
            "https://www.ncbi.nlm.nih.gov/gene/?term=SLC5A1",
            "GLUT2 basolateral hexose exit — NCBI Gene SLC2A2: "
            "https://www.ncbi.nlm.nih.gov/gene/?term=SLC2A2",
            "GLUT5 apical fructose transport — NCBI Gene SLC2A5: "
            "https://www.ncbi.nlm.nih.gov/gene/?term=SLC2A5",
        ]
        p.extra_summary = {
            "primary_system": "Assimilation",
            "systems": ["SYS_01", "SYS_02", "SYS_06"],
            "apical": "SGLT1",
            "basolateral": "GLUT2",
            "queue_tier": "B",
        }
        self.register(p)

    # ------------------------------------------------------------------
    # 4. SCFA colonic production
    # ------------------------------------------------------------------
    def _build_scfa_colonic_production(self) -> None:
        p = MetabolicPathway(
            name="scfa_colonic_production",
            description=(
                "Colonic short-chain fatty acid production from fermentable fiber / RS. "
                "Microbiota ferment substrates to acetate, propionate, and butyrate; "
                "butyrate fuels colonocytes; acetate/propionate reach portal blood. "
                "Extends prebiotic_probiotic sketch with explicit SCFA products (FLOW)."
            ),
        )
        for nid, name, nt, notes in [
            ("fermentable_fiber", "Fermentable fiber / RS", PathwayNodeType.SUBSTRATE,
             "Escapes small-bowel absorption; substrate for microbiota."),
            ("microbiota", "Colonic microbiota", PathwayNodeType.INTERMEDIATE,
             "Taxa-dependent fermentation capacity."),
            ("acetate", "Acetate (C2)", PathwayNodeType.PRODUCT, "Often most abundant SCFA; portal delivery."),
            ("propionate", "Propionate (C3)", PathwayNodeType.PRODUCT, "Portal → liver gluconeogenesis teaching link."),
            ("butyrate", "Butyrate (C4)", PathwayNodeType.PRODUCT, "Preferred colonocyte fuel; barrier support teaching."),
            ("colonocyte_use", "Colonocyte oxidation", PathwayNodeType.PRODUCT, "Local host use of butyrate."),
            ("portal_scfa", "Portal SCFA delivery", PathwayNodeType.CIRCULATION, "Acetate/propionate systemic exposure."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge(
            from_node="fermentable_fiber", to_node="microbiota",
            process="Substrate delivery to colon",
            location="Lumen → colon",
            notes="Transit + matrix determine how much reaches the colon.",
        ))
        p.add_edge(ReactionEdge(
            from_node="microbiota", to_node="acetate",
            mechanism_id="colonic_fermentation",
            process="Fermentation → acetate",
            location="Colon lumen",
        ))
        p.add_edge(ReactionEdge(
            from_node="microbiota", to_node="propionate",
            mechanism_id="colonic_fermentation",
            process="Fermentation → propionate",
            location="Colon lumen",
        ))
        p.add_edge(ReactionEdge(
            from_node="microbiota", to_node="butyrate",
            mechanism_id="colonic_fermentation",
            process="Fermentation → butyrate",
            location="Colon lumen",
        ))
        p.add_edge(ReactionEdge(
            from_node="butyrate", to_node="colonocyte_use",
            process="Colonocyte β-oxidation / fuel use",
            location="Colonocyte",
            notes="Local consumption reduces systemic butyrate vs acetate.",
        ))
        p.add_edge(ReactionEdge(
            from_node="acetate", to_node="portal_scfa",
            process="Absorption → portal vein",
            location="Colon → portal",
        ))
        p.add_edge(ReactionEdge(
            from_node="propionate", to_node="portal_scfa",
            process="Absorption → portal vein",
            location="Colon → portal",
        ))

        p.references = [
            "Short-chain fatty acids — physiology and effects review: PMID 39845918 "
            "(https://pubmed.ncbi.nlm.nih.gov/39845918/).",
            "SCFA and intestinal mucosal immunity review: PMID 39286812 "
            "(https://pubmed.ncbi.nlm.nih.gov/39286812/).",
            "Colonic SCFA production (acetate / propionate / butyrate) — FLOW teaching; "
            "yields are taxa- and substrate-dependent.",
        ]
        p.extra_summary = {
            "primary_system": "Assimilation",
            "systems": ["SYS_01", "SYS_06"],
            "products": "acetate, propionate, butyrate",
            "queue_tier": "B",
        }
        self.register(p)


def get_meal_critical_pathways_registry() -> MealCriticalPathwaysRegistry:
    return MealCriticalPathwaysRegistry()


if __name__ == "__main__":
    reg = get_meal_critical_pathways_registry()
    for path in reg.list_all():
        print(path.name, path.summary())
