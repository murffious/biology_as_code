"""
pentose_phosphate.py
=================================================================
Pentose Phosphate Pathway (Hexose Monophosphate Shunt)

Two phases:
  1. Oxidative (irreversible) – produces NADPH + CO₂ + ribulose-5-P
  2. Non-oxidative (reversible) – interconverts sugars and links to glycolysis

Major roles: NADPH for biosynthesis/redox, ribose-5-P for nucleotides.
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
            "nadph_per_g6p_oxidative": 2,
            "main_products": "NADPH + ribose-5-P (or glycolytic intermediates)",
        }


class PentosePhosphateRegistry:
    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def _build(self) -> None:
        p = MetabolicPathway(
            name="pentose_phosphate",
            description=(
                "Pentose Phosphate Pathway. Oxidative phase generates NADPH and ribulose-5-P. "
                "Non-oxidative phase interconverts sugars and can feed back into glycolysis."
            )
        )

        # Nodes
        p.add_node(MetaboliteNode("g6p", "Glucose-6-phosphate", PathwayNodeType.SUBSTRATE,
            "Entry point from glycolysis / glycogenolysis."))
        p.add_node(MetaboliteNode("6pgl", "6-Phosphogluconolactone", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("6pg", "6-Phosphogluconate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("ru5p", "Ribulose-5-phosphate", PathwayNodeType.INTERMEDIATE,
            "Product of the oxidative phase."))
        p.add_node(MetaboliteNode("r5p", "Ribose-5-phosphate", PathwayNodeType.PRODUCT,
            "Used for nucleotide and nucleic acid synthesis."))
        p.add_node(MetaboliteNode("xu5p", "Xylulose-5-phosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("s7p", "Sedoheptulose-7-phosphate", PathwayNodeType.INTERMEDIATE))
        p.add_node(MetaboliteNode("gap", "Glyceraldehyde-3-phosphate", PathwayNodeType.INTERMEDIATE,
            "Can enter glycolysis."))
        p.add_node(MetaboliteNode("f6p", "Fructose-6-phosphate", PathwayNodeType.INTERMEDIATE,
            "Can enter glycolysis."))
        p.add_node(MetaboliteNode("e4p", "Erythrose-4-phosphate", PathwayNodeType.INTERMEDIATE))

        # Oxidative phase
        p.add_edge(ReactionEdge(
            from_node="g6p", to_node="6pgl",
            enzyme="Glucose-6-phosphate dehydrogenase (G6PD)",
            nadph_cost=-1,
            phase="oxidative",
            regulation="Major control point. Inhibited by high NADPH/NADP⁺ ratio.",
            notes="First and rate-limiting step of the oxidative phase. Most common human enzyme deficiency."
        ))
        p.add_edge(ReactionEdge(
            from_node="6pgl", to_node="6pg",
            enzyme="Lactonase",
            phase="oxidative",
            notes="Hydrolyzes the lactone."
        ))
        p.add_edge(ReactionEdge(
            from_node="6pg", to_node="ru5p",
            enzyme="6-Phosphogluconate dehydrogenase",
            nadph_cost=-1,
            co2_produced=1,
            phase="oxidative",
            notes="Produces the second NADPH and releases CO₂."
        ))

        # Non-oxidative phase
        p.add_edge(ReactionEdge(
            from_node="ru5p", to_node="r5p",
            enzyme="Ribulose-5-phosphate isomerase",
            phase="non-oxidative",
            notes="Produces ribose-5-P for nucleotides."
        ))
        p.add_edge(ReactionEdge(
            from_node="ru5p", to_node="xu5p",
            enzyme="Ribulose-5-phosphate epimerase",
            phase="non-oxidative",
            notes="Produces xylulose-5-P."
        ))
        p.add_edge(ReactionEdge(
            from_node="xu5p", to_node="gap",
            enzyme="Transketolase",
            phase="non-oxidative",
            notes="Transfers C2 unit. Requires thiamine pyrophosphate (TPP)."
        ))
        p.add_edge(ReactionEdge(
            from_node="r5p", to_node="s7p",
            enzyme="Transketolase",
            phase="non-oxidative",
            notes="Forms sedoheptulose-7-P + GAP."
        ))
        p.add_edge(ReactionEdge(
            from_node="s7p", to_node="f6p",
            enzyme="Transaldolase",
            phase="non-oxidative",
            notes="Forms fructose-6-P + erythrose-4-P."
        ))
        p.add_edge(ReactionEdge(
            from_node="xu5p", to_node="f6p",
            enzyme="Transketolase",
            phase="non-oxidative",
            notes="Can also produce F6P + GAP from xu5p + e4p."
        ))

        self.register(p)


def get_pentose_phosphate_registry() -> PentosePhosphateRegistry:
    return PentosePhosphateRegistry()


if __name__ == "__main__":
    reg = get_pentose_phosphate_registry()
    path = reg.get("pentose_phosphate")
    print("=" * 60)
    print("PENTOSE PHOSPHATE PATHWAY")
    print("=" * 60)
    print(path.description)
    print()
    print(path.summary())
    print()
    print("Oxidative phase:  G6P → → Ru5P + 2 NADPH + CO₂")
    print("Non-oxidative:    Sugar interconversions ↔ glycolysis intermediates")
    print("Key regulated enzyme: Glucose-6-phosphate dehydrogenase (G6PD)")
