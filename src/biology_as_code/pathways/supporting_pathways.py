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

from biology_as_code.pathways._types import (
    MetabolicPathway as _BasePathway,
)
from biology_as_code.pathways._types import (
    MetaboliteNode,
    PathwayNodeType,
    ReactionEdge,
)


class MetabolicPathway(_BasePathway):
    """Shared graph type; only this module's own summary differs."""

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
            p.add_node(MetaboliteNode(id=nid, name=name, node_type=nt))
        p.add_edge(ReactionEdge(from_node="muscle_glycogen", to_node="pyruvate_muscle", process="Glycolysis", location="Muscle"))
        p.add_edge(ReactionEdge(from_node="pyruvate_muscle", to_node="lactate", process="LDH", location="Muscle", notes="Anaerobic / Cori branch."))
        p.add_edge(ReactionEdge(from_node="pyruvate_muscle", to_node="alanine", process="ALT transamination", location="Muscle", notes="Glucose-alanine cycle."))
        p.add_edge(ReactionEdge(from_node="lactate", to_node="liver_pyruvate", process="LDH", location="Liver"))
        p.add_edge(ReactionEdge(from_node="alanine", to_node="liver_pyruvate", process="ALT", location="Liver", notes="N → urea path side branch."))
        p.add_edge(ReactionEdge(from_node="liver_pyruvate", to_node="liver_glucose", process="Gluconeogenesis", location="Liver"))
        p.add_edge(ReactionEdge(from_node="liver_glucose", to_node="muscle_glycogen", process="Blood glucose → muscle uptake", location="Systemic"))
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
            p.add_node(MetaboliteNode(id=nid, name=name, node_type=PathwayNodeType.INTERMEDIATE))
        p.add_edge(ReactionEdge(from_node="nadh_cyto", to_node="malate", process="MDH cytosolic", location="Cytosol", notes="Malate-aspartate shuttle start."))
        p.add_edge(ReactionEdge(from_node="malate", to_node="oaa_mito", process="Malate/αKG antiport + MDH mito", location="Mito"))
        p.add_edge(ReactionEdge(from_node="oaa_mito", to_node="nadh_mito", process="MDH mito regenerates NADH", location="Mito", notes="~2.5 ATP/NADH via ETC."))
        p.add_edge(ReactionEdge(from_node="nadh_cyto", to_node="g3p", process="cG3PDH", location="Cytosol", notes="G3P shuttle."))
        p.add_edge(ReactionEdge(from_node="g3p", to_node="dhap", process="mG3PDH", location="IMS/mito", notes="Yields FADH₂-eq (~1.5 ATP)."))
        p.add_edge(ReactionEdge(from_node="dhap", to_node="g3p", process="cG3PDH reverse pool", location="Cytosol"))
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
            p.add_node(MetaboliteNode(id=nid, name=name, node_type=nt))
        p.add_edge(ReactionEdge(from_node="fructose", to_node="f1p", process="Ketohexokinase (KHK)", location="Liver", notes="Bypasses PFK-1 regulation."))
        p.add_edge(ReactionEdge(from_node="f1p", to_node="dhap_gap", process="Aldolase B", location="Liver"))
        p.add_edge(ReactionEdge(from_node="dhap_gap", to_node="glycolysis", process="Triose kinase / TPI", location="Liver"))
        p.add_edge(ReactionEdge(from_node="galactose", to_node="gal1p", process="Galactokinase", location="Liver"))
        p.add_edge(ReactionEdge(from_node="gal1p", to_node="udp_gal", process="GALT", location="Liver", notes="Classic galactosemia enzyme."))
        p.add_edge(ReactionEdge(from_node="udp_gal", to_node="g1p", process="GALE + UDP-glucose cycle", location="Liver"))
        p.add_edge(ReactionEdge(from_node="g1p", to_node="glycolysis", process="PGM / G6Pase context", location="Liver"))
        self.register(p)

    def _build_secondary_bile(self) -> None:
        p = MetabolicPathway(
            name="secondary_bile_acids",
            description="Microbial 7α-dehydroxylation and related transforms of primary → secondary bile acids.",
        )
        p.add_node(MetaboliteNode(id="primary_ba", name="Primary bile acids (CA, CDCA)", node_type=PathwayNodeType.SUBSTRATE))
        p.add_node(MetaboliteNode(id="deconj", name="Deconjugated bile acids", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode(id="secondary_ba", name="Secondary bile acids (DCA, LCA)", node_type=PathwayNodeType.PRODUCT))
        p.add_node(MetaboliteNode(id="fxr_tgr5", name="FXR / TGR5 signaling", node_type=PathwayNodeType.SIGNAL))
        p.add_edge(ReactionEdge(from_node="primary_ba", to_node="deconj", process="Bile salt hydrolases", location="Colon microbiota"))
        p.add_edge(ReactionEdge(from_node="deconj", to_node="secondary_ba", process="7α-dehydroxylation", location="Colon microbiota"))
        p.add_edge(ReactionEdge(from_node="secondary_ba", to_node="fxr_tgr5", process="Host nuclear / GPCR sensing", location="Ileum / systemic", notes="Metabolic regulation; dose/context sensitive."))
        self.register(p)

    def _build_prebiotic_probiotic(self) -> None:
        p = MetabolicPathway(
            name="prebiotic_probiotic",
            description="Teaching sketch: prebiotic substrate → selective growth → SCFA/signals; probiotic as introduced taxa.",
        )
        p.add_node(MetaboliteNode(id="prebiotic_fiber", name="Prebiotic fiber / oligos", node_type=PathwayNodeType.SUBSTRATE))
        p.add_node(MetaboliteNode(id="selective_taxa", name="Selective taxa expansion", node_type=PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode(id="scfa_signals", name="SCFA + microbial signals", node_type=PathwayNodeType.PRODUCT))
        p.add_node(MetaboliteNode(id="probiotic_input", name="Probiotic organisms (input)", node_type=PathwayNodeType.SUBSTRATE))
        p.add_node(MetaboliteNode(id="host_effects", name="Host barrier / immune effects", node_type=PathwayNodeType.PRODUCT))
        p.add_edge(ReactionEdge(from_node="prebiotic_fiber", to_node="selective_taxa", process="Selective fermentation", location="Colon"))
        p.add_edge(ReactionEdge(from_node="selective_taxa", to_node="scfa_signals", process="Fermentation / exchange", location="Colon", notes="Links to colonic medium + SCFA FLOW."))
        p.add_edge(ReactionEdge(from_node="probiotic_input", to_node="selective_taxa", process="Transient colonization", location="Gut", notes="Strain- and dose-dependent; often transient."))
        p.add_edge(ReactionEdge(from_node="scfa_signals", to_node="host_effects", process="Host sensing", location="Colonocyte / systemic"))
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
            p.add_node(MetaboliteNode(id=nid, name=name, node_type=nt))
        p.add_edge(ReactionEdge(from_node="fed_insulin", to_node="glucose_use", process="Insulin-dominant state", notes="Suppresses net lipolysis / fat oxidation."))
        p.add_edge(ReactionEdge(from_node="fasted_glucagon", to_node="fat_use", process="Mobilization-dominant state"))
        p.add_edge(ReactionEdge(from_node="prolonged_fast", to_node="ketone_use", process="Hepatic ketogenesis + peripheral use"))
        p.add_edge(ReactionEdge(from_node="fed_insulin", to_node="fat_use", process="Conflict if concurrent high fat+carb", notes="Teaching concurrency foil; not every mixed meal."))
        self.register(p)


def get_supporting_pathways_registry() -> SupportingPathwaysRegistry:
    return SupportingPathwaysRegistry()


if __name__ == "__main__":
    reg = get_supporting_pathways_registry()
    for p in reg.list_all():
        print(p.name, p.summary())
