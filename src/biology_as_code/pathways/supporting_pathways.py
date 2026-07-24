"""
supporting_pathways.py
=================================================================
Minimal graph models for remaining textbook TODO items:
  - Cori cycle + glucose-alanine cycle
  - Malate-aspartate & G3P shuttles
  - Fructose & galactose entry
  - Secondary bile acid metabolism (microbial)
  - Prebiotic / probiotic mechanism sketch
  - Fuel selection hierarchy (teaching)

FLOW-level teaching graphs — not LAW-SPEC magnitudes.
=================================================================
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class PathwayNodeType(Enum):
    SUBSTRATE = "substrate"
    INTERMEDIATE = "intermediate"
    PRODUCT = "product"
    SIGNAL = "signal"


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
    process: str = ""
    location: str = ""
    notes: str = ""
    mechanism_id: str = ""


class MetabolicPathway:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, MetaboliteNode] = {}
        self.edges: list[ReactionEdge] = []

    def add_node(self, node: MetaboliteNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ReactionEdge) -> None:
        self.edges.append(edge)

    def summary(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
        }


class SupportingPathwaysRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_cori_glucose_alanine()
        self._build_shuttles()
        self._build_fructose_galactose()
        self._build_secondary_bile()
        self._build_prebiotic_probiotic()
        self._build_fuel_selection()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    def _build_cori_glucose_alanine(self) -> None:
        p = MetabolicPathway(
            name="cori_glucose_alanine",
            description=(
                "Cori cycle (lactate ↔ glucose) and glucose-alanine cycle "
                "(muscle alanine → liver glucose)."
            ),
        )
        for nid, name, nt in [
            ("muscle_glycogen", "Muscle glycogen / glucose", PathwayNodeType.SUBSTRATE),
            ("pyruvate_muscle", "Pyruvate (muscle)", PathwayNodeType.INTERMEDIATE),
            ("lactate", "Lactate", PathwayNodeType.INTERMEDIATE),
            ("alanine", "Alanine", PathwayNodeType.INTERMEDIATE),
            ("liver_pyruvate", "Pyruvate (liver)", PathwayNodeType.INTERMEDIATE),
            ("liver_glucose", "Glucose (liver → blood)", PathwayNodeType.PRODUCT),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt))
        p.add_edge(ReactionEdge("muscle_glycogen", "pyruvate_muscle", process="Glycolysis", location="Muscle"))
        p.add_edge(ReactionEdge("pyruvate_muscle", "lactate", process="LDH", location="Muscle", notes="Anaerobic / Cori branch."))
        p.add_edge(ReactionEdge("pyruvate_muscle", "alanine", process="ALT transamination", location="Muscle", notes="Glucose-alanine cycle."))
        p.add_edge(ReactionEdge("lactate", "liver_pyruvate", process="LDH", location="Liver"))
        p.add_edge(ReactionEdge("alanine", "liver_pyruvate", process="ALT", location="Liver", notes="N → urea path side branch."))
        p.add_edge(ReactionEdge("liver_pyruvate", "liver_glucose", process="Gluconeogenesis", location="Liver"))
        p.add_edge(ReactionEdge("liver_glucose", "muscle_glycogen", process="Blood glucose → muscle uptake", location="Systemic"))
        self.register(p)

    def _build_shuttles(self) -> None:
        p = MetabolicPathway(
            name="redox_shuttles",
            description="Malate-aspartate and glycerol-3-phosphate shuttles transfer cytosolic NADH reducing power into mitochondria.",
        )
        for nid, name in [
            ("nadh_cyto", "NADH (cytosol)"),
            ("malate", "Malate"),
            ("oaa_mito", "OAA (mito)"),
            ("nadh_mito", "NADH (mito)"),
            ("g3p", "Glycerol-3-phosphate"),
            ("dhap", "DHAP"),
            ("fadh2_eq", "FADH₂-equivalent (G3P DH)"),
        ]:
            p.add_node(MetaboliteNode(nid, name, PathwayNodeType.INTERMEDIATE))
        p.add_edge(ReactionEdge("nadh_cyto", "malate", process="MDH cytosolic", location="Cytosol", notes="Malate-aspartate shuttle start."))
        p.add_edge(ReactionEdge("malate", "oaa_mito", process="Malate/αKG antiport + MDH mito", location="Mito"))
        p.add_edge(ReactionEdge("oaa_mito", "nadh_mito", process="MDH mito regenerates NADH", location="Mito", notes="~2.5 ATP/NADH via ETC."))
        p.add_edge(ReactionEdge("nadh_cyto", "g3p", process="cG3PDH", location="Cytosol", notes="G3P shuttle."))
        p.add_edge(ReactionEdge("g3p", "dhap", process="mG3PDH", location="IMS/mito", notes="Yields FADH₂-eq (~1.5 ATP)."))
        p.add_edge(ReactionEdge("dhap", "g3p", process="cG3PDH reverse pool", location="Cytosol"))
        self.register(p)

    def _build_fructose_galactose(self) -> None:
        p = MetabolicPathway(
            name="fructose_galactose",
            description="Hepatic fructose (KHK → aldolase B) and Leloir galactose pathway entry into glycolytic intermediates.",
        )
        for nid, name, nt in [
            ("fructose", "Fructose", PathwayNodeType.SUBSTRATE),
            ("f1p", "Fructose-1-P", PathwayNodeType.INTERMEDIATE),
            ("dhap_gap", "DHAP + Glyceraldehyde → GAP", PathwayNodeType.INTERMEDIATE),
            ("galactose", "Galactose", PathwayNodeType.SUBSTRATE),
            ("gal1p", "Galactose-1-P", PathwayNodeType.INTERMEDIATE),
            ("udp_gal", "UDP-galactose", PathwayNodeType.INTERMEDIATE),
            ("g1p", "Glucose-1-P / G6P pool", PathwayNodeType.PRODUCT),
            ("glycolysis", "Glycolytic intermediates", PathwayNodeType.PRODUCT),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt))
        p.add_edge(ReactionEdge("fructose", "f1p", process="Ketohexokinase (KHK)", location="Liver", notes="Bypasses PFK-1 regulation."))
        p.add_edge(ReactionEdge("f1p", "dhap_gap", process="Aldolase B", location="Liver"))
        p.add_edge(ReactionEdge("dhap_gap", "glycolysis", process="Triose kinase / TPI", location="Liver"))
        p.add_edge(ReactionEdge("galactose", "gal1p", process="Galactokinase", location="Liver"))
        p.add_edge(ReactionEdge("gal1p", "udp_gal", process="GALT", location="Liver", notes="Classic galactosemia enzyme."))
        p.add_edge(ReactionEdge("udp_gal", "g1p", process="GALE + UDP-glucose cycle", location="Liver"))
        p.add_edge(ReactionEdge("g1p", "glycolysis", process="PGM / G6Pase context", location="Liver"))
        self.register(p)

    def _build_secondary_bile(self) -> None:
        p = MetabolicPathway(
            name="secondary_bile_acids",
            description="Microbial 7α-dehydroxylation and related transforms of primary → secondary bile acids.",
        )
        p.add_node(MetaboliteNode("primary_ba", "Primary bile acids (CA, CDCA)", PathwayNodeType.SUBSTRATE))
        p.add_node(MetaboliteNode("deconj", "Deconjugated bile acids", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("secondary_ba", "Secondary bile acids (DCA, LCA)", PathwayNodeType.PRODUCT))
        p.add_node(MetaboliteNode("fxr_tgr5", "FXR / TGR5 signaling", PathwayNodeType.SIGNAL))
        p.add_edge(ReactionEdge("primary_ba", "deconj", process="Bile salt hydrolases", location="Colon microbiota"))
        p.add_edge(ReactionEdge("deconj", "secondary_ba", process="7α-dehydroxylation", location="Colon microbiota"))
        p.add_edge(ReactionEdge("secondary_ba", "fxr_tgr5", process="Host nuclear / GPCR sensing", location="Ileum / systemic", notes="Metabolic regulation; dose/context sensitive."))
        self.register(p)

    def _build_prebiotic_probiotic(self) -> None:
        p = MetabolicPathway(
            name="prebiotic_probiotic",
            description="Teaching sketch: prebiotic substrate → selective growth → SCFA/signals; probiotic as introduced taxa.",
        )
        p.add_node(MetaboliteNode("prebiotic_fiber", "Prebiotic fiber / oligos", PathwayNodeType.SUBSTRATE))
        p.add_node(MetaboliteNode("selective_taxa", "Selective taxa expansion", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("scfa_signals", "SCFA + microbial signals", PathwayNodeType.PRODUCT))
        p.add_node(MetaboliteNode("probiotic_input", "Probiotic organisms (input)", PathwayNodeType.SUBSTRATE))
        p.add_node(MetaboliteNode("host_effects", "Host barrier / immune effects", PathwayNodeType.PRODUCT))
        p.add_edge(ReactionEdge("prebiotic_fiber", "selective_taxa", process="Selective fermentation", location="Colon"))
        p.add_edge(ReactionEdge("selective_taxa", "scfa_signals", process="Fermentation / exchange", location="Colon", notes="Links to colonic medium + SCFA FLOW."))
        p.add_edge(ReactionEdge("probiotic_input", "selective_taxa", process="Transient colonization", location="Gut", notes="Strain- and dose-dependent; often transient."))
        p.add_edge(ReactionEdge("scfa_signals", "host_effects", process="Host sensing", location="Colonocyte / systemic"))
        self.register(p)

    def _build_fuel_selection(self) -> None:
        p = MetabolicPathway(
            name="fuel_selection_hierarchy",
            description=(
                "Teaching hierarchy of fuel use under hormonal state: "
                "glucose/glycogen priority under insulin; fat under low insulin; ketones in prolonged fast."
            ),
        )
        for nid, name, nt in [
            ("fed_insulin", "Fed / high insulin", PathwayNodeType.SIGNAL),
            ("glucose_use", "Glucose oxidation + storage", PathwayNodeType.PRODUCT),
            ("fasted_glucagon", "Fasted / low insulin", PathwayNodeType.SIGNAL),
            ("fat_use", "Fatty acid oxidation", PathwayNodeType.PRODUCT),
            ("prolonged_fast", "Prolonged fast / low carb", PathwayNodeType.SIGNAL),
            ("ketone_use", "Ketone production / use", PathwayNodeType.PRODUCT),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt))
        p.add_edge(ReactionEdge("fed_insulin", "glucose_use", process="Insulin-dominant state", notes="Suppresses net lipolysis / fat oxidation."))
        p.add_edge(ReactionEdge("fasted_glucagon", "fat_use", process="Mobilization-dominant state"))
        p.add_edge(ReactionEdge("prolonged_fast", "ketone_use", process="Hepatic ketogenesis + peripheral use"))
        p.add_edge(ReactionEdge("fed_insulin", "fat_use", process="Conflict if concurrent high fat+carb", notes="Teaching concurrency foil; not every mixed meal."))
        self.register(p)


def get_supporting_pathways_registry() -> SupportingPathwaysRegistry:
    return SupportingPathwaysRegistry()


if __name__ == "__main__":
    reg = get_supporting_pathways_registry()
    for p in reg.list_all():
        print(p.name, p.summary())
