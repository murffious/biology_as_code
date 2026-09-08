"""
ketogenesis.py
=================================================================
Ketogenesis (Ketone Body Synthesis)

Occurs in liver mitochondria when acetyl-CoA from β-oxidation
exceeds the capacity of the TCA cycle (fasting, low carbohydrate,
prolonged exercise).

Major ketone bodies: Acetoacetate, β-Hydroxybutyrate, Acetone.
=================================================================
"""


try:
    from biology_as_code.pathways.metabolic_mechanisms import (
        MetabolicMechanism,
        get_metabolic_mechanism_registry,
    )
except ImportError:
    get_metabolic_mechanism_registry = None
    MetabolicMechanism = None


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
            "nodes": len(self.nodes),
            "edges": len(self.edges),
            "main_products": "Acetoacetate, β-Hydroxybutyrate, Acetone",
            "location": "Liver mitochondria",
        }


class KetogenesisRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="ketogenesis",
            description=(
                "Ketogenesis. Liver converts excess acetyl-CoA into ketone bodies "
                "that can be used by brain, heart, and muscle during fasting or low-carbohydrate states."
            )
        )

        p.add_node(MetaboliteNode("acetyl_coa", "Acetyl-CoA", PathwayNodeType.SUBSTRATE,
            "From β-oxidation. Accumulates when TCA capacity is limited (low OAA)."))
        p.add_node(MetaboliteNode("acetoacetyl_coa", "Acetoacetyl-CoA", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("hmg_coa", "HMG-CoA", PathwayNodeType.INTERMEDIATE,
            "Same intermediate as in cholesterol synthesis, but mitochondrial isoform."))
        p.add_node(MetaboliteNode("acetoacetate", "Acetoacetate", PathwayNodeType.PRODUCT,
            "Primary ketone body. Can be reduced to β-hydroxybutyrate or spontaneously decarboxylated."))
        p.add_node(MetaboliteNode("beta_hydroxybutyrate", "β-Hydroxybutyrate", PathwayNodeType.PRODUCT,
            "Most abundant circulating ketone body. Preferred fuel for many tissues."))
        p.add_node(MetaboliteNode("acetone", "Acetone", PathwayNodeType.PRODUCT,
            "Volatile. Formed by spontaneous decarboxylation of acetoacetate. Exhaled."))

        p.add_edge(ReactionEdge(
            from_node="acetyl_coa", to_node="acetoacetyl_coa",
            enzyme="Thiolase (Acetyl-CoA acetyltransferase)",
            notes="Condensation of two acetyl-CoA. Reversible."
        ))
        p.add_edge(ReactionEdge(
            from_node="acetoacetyl_coa", to_node="hmg_coa",
            enzyme="HMG-CoA synthase (mitochondrial)",
            notes="Adds a third acetyl-CoA. Rate-influencing step under ketogenic conditions."
        ))
        p.add_edge(ReactionEdge(
            from_node="hmg_coa", to_node="acetoacetate",
            enzyme="HMG-CoA lyase",
            notes="Cleaves HMG-CoA to acetoacetate + acetyl-CoA. Key ketogenic enzyme."
        ))
        p.add_edge(ReactionEdge(
            from_node="acetoacetate", to_node="beta_hydroxybutyrate",
            enzyme="β-Hydroxybutyrate dehydrogenase",
            nadh_cost=1,  # consumes NADH
            notes="Reversible. Ratio of β-HB / AcAc reflects mitochondrial NADH/NAD⁺ ratio."
        ))
        p.add_edge(ReactionEdge(
            from_node="acetoacetate", to_node="acetone",
            enzyme="Spontaneous decarboxylation",
            notes="Non-enzymatic. Acetone is exhaled and accounts for the fruity odor in ketoacidosis."
        ))

        self.register(p)


def get_ketogenesis_registry() -> KetogenesisRegistry:
    return KetogenesisRegistry()


if __name__ == "__main__":
    reg = get_ketogenesis_registry()
    path = reg.get("ketogenesis")
    print("=" * 60)
    print("KETOGENESIS")
    print("=" * 60)
    print(path.description)
    print()
    print(path.summary())
    print()
    print("Triggered when acetyl-CoA production (β-oxidation) exceeds TCA capacity.")
    print("Ketone bodies are water-soluble fuels usable by brain, heart, and skeletal muscle.")
