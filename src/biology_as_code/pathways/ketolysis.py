"""
ketolysis.py
=================================================================
Ketolysis (Ketone Body Oxidation) — the reverse of ketogenesis.

Extrahepatic tissues (brain, heart, skeletal muscle, renal cortex)
oxidize circulating ketone bodies back to acetyl-CoA for the TCA
cycle when glucose is scarce (fasting, low-carbohydrate, prolonged
exercise, the neonatal brain).

Key teaching point: the LIVER cannot use ketones — it lacks
SCOT (OXCT1). That absence is deliberate: it stops a futile cycle
where the liver would just re-burn the fuel it exports.

Net teaching yield: ~2 acetyl-CoA per ketone body; roughly
19–21.5 ATP-equivalents once those acetyl-CoA run through the TCA
cycle and ETC (FLOW teaching arithmetic, not a locked coefficient).
=================================================================
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional

try:
    from biology_as_code.pathways.metabolic_mechanisms import (
        MetabolicMechanism,
        get_metabolic_mechanism_registry,
    )
except ImportError:
    get_metabolic_mechanism_registry = None
    MetabolicMechanism = None


class PathwayNodeType(Enum):
    SUBSTRATE = "substrate"
    INTERMEDIATE = "intermediate"
    PRODUCT = "product"


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
    nadh_cost: int = 0
    regulation: str = ""
    notes: str = ""


class MetabolicPathway:
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.nodes: dict[str, MetaboliteNode] = {}
        self.edges: list[ReactionEdge] = []
        self.references: list[str] = []  # source citations (rendered into packs)

    def add_node(self, node: MetaboliteNode) -> None:
        self.nodes[node.id] = node

    def add_edge(self, edge: ReactionEdge) -> None:
        self.edges.append(edge)

    def get_mechanism(self, edge: ReactionEdge) -> Optional["MetabolicMechanism"]:
        if get_metabolic_mechanism_registry is None or not edge.mechanism_id:
            return None
        return get_metabolic_mechanism_registry().get(edge.mechanism_id)

    def summary(self) -> dict:
        return {
            "name": self.name,
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "main_substrate": "β-Hydroxybutyrate, Acetoacetate",
            "main_product": "Acetyl-CoA (to TCA cycle)",
            "location": "Extrahepatic mitochondria (NOT liver — lacks SCOT/OXCT1)",
            "acetyl_coa_per_ketone": 2,
        }


class KetolysisRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="ketolysis",
            description=(
                "Ketolysis. Extrahepatic tissues oxidize β-hydroxybutyrate and acetoacetate "
                "back to acetyl-CoA for the TCA cycle when glucose is scarce. The liver cannot "
                "run this pathway (no SCOT/OXCT1), which prevents a futile cycle with ketogenesis."
            ),
        )

        p.add_node(MetaboliteNode(
            "beta_hydroxybutyrate", "β-Hydroxybutyrate", PathwayNodeType.SUBSTRATE,
            "Most abundant circulating ketone body. Taken up by brain/heart/muscle via MCT transporters."))
        p.add_node(MetaboliteNode(
            "acetoacetate", "Acetoacetate", PathwayNodeType.INTERMEDIATE,
            "Also circulates directly. The actual substrate for SCOT."))
        p.add_node(MetaboliteNode(
            "acetoacetyl_coa", "Acetoacetyl-CoA", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode(
            "acetyl_coa", "Acetyl-CoA", PathwayNodeType.PRODUCT,
            "Two per ketone body. Enters the TCA cycle for oxidation to CO₂ + ATP."))

        p.add_edge(ReactionEdge(
            from_node="beta_hydroxybutyrate", to_node="acetoacetate",
            enzyme="β-Hydroxybutyrate dehydrogenase (BDH1)",
            regulation="Driven by the mitochondrial NAD⁺/NADH ratio",
            notes="Oxidation generates 1 NADH (the reverse of the ketogenesis reduction step).",
        ))
        p.add_edge(ReactionEdge(
            from_node="acetoacetate", to_node="acetoacetyl_coa",
            enzyme="Succinyl-CoA:3-oxoacid CoA transferase (SCOT / OXCT1)",
            regulation="Rate-limiting; absent in liver (prevents futile cycling)",
            notes="Transfers CoA from succinyl-CoA → succinate, 'spending' one TCA GTP-equivalent.",
        ))
        p.add_edge(ReactionEdge(
            from_node="acetoacetyl_coa", to_node="acetyl_coa",
            enzyme="Acetoacetyl-CoA thiolase (ACAT1)",
            notes="Thiolytic cleavage with CoA yields 2 acetyl-CoA. Largest flux control in ketone oxidation.",
        ))

        p.references = [
            "Ketone Bodies — Biology LibreTexts 17.3 (BDH1 / SCOT / thiolase steps): "
            "https://bio.libretexts.org/Bookshelves/Biochemistry",
            "OXCT1/SCOT as the rate-limiting ketolytic enzyme, absent in liver: "
            "PMC12838892 (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12838892/)",
            "Metabolic and Signaling Roles of Ketone Bodies: "
            "PMC8922216 (https://pmc.ncbi.nlm.nih.gov/articles/PMC8922216/)",
        ]
        self.register(p)


def get_ketolysis_registry() -> KetolysisRegistry:
    return KetolysisRegistry()


if __name__ == "__main__":
    reg = get_ketolysis_registry()
    path = reg.get("ketolysis")
    print("=" * 60)
    print("KETOLYSIS")
    print("=" * 60)
    print(path.description)
    print()
    print(path.summary())
    print()
    print("Liver makes ketones (ketogenesis) but cannot burn them (no SCOT) —")
    print("brain, heart, and muscle do the oxidation. ~2 acetyl-CoA per ketone body.")
