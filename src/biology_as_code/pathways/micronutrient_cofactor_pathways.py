"""
micronutrient_cofactor_pathways.py
=================================================================
Two pathways whose point is the *cofactor*, not the carbon.

Most teaching graphs in this package trace where carbon and energy go. These two
trace where a vitamin or mineral shortfall stops the line, using the
``requires_nutrient`` edge field. They were chosen because each makes an argument
that a per-nutrient score cannot make on its own:

**Tryptophan → niacin.** The origin of the niacin equivalent. It is also a
nutrient-nutrient interaction with a direction: kynureninase is PLP-dependent, so
in vitamin B6 deficiency the pathway backs up and niacin synthesis from
tryptophan fails. A model that scores B6 and niacin as independent axes cannot
express "low B6 lowers effective niacin".

**Carnitine synthesis.** Five distinct micronutrient dependencies on one linear
chain — SAM (methionine, and behind it folate/B12), iron, vitamin C, B6 and NAD
(niacin). A shortfall at any single step blocks endogenous synthesis, which is
why carnitine is conditionally essential rather than simply non-essential.

Both are FLOW-level teaching topology. Berdanier's own framing of the appendix
(p. 471) is that the maps are a guide to intermediary metabolism and lack the
detail of a full wall chart — so treat them as topology, not as stoichiometry.

Source
------
Berdanier, C. D. *Advanced Nutrition: Macronutrients*, 2nd ed. CRC Press, 2000.
Appendix 2, "Metabolic Maps": Map 6 (p. 475) and Map 25 (p. 489).

The volume was ambiguous for a while — an Appendix 2 starting at p. 471 does not
match the 2009 Berdanier/Zempleni edition, which ends at Ch. 12 (p. 499) with no
appendices. It is settled now: the running head on p. 204, captured while
extracting ``nodes/data/glucose.node.yaml``, reads "Advanced Nutrition:
Macronutrients, Second Edition". This is that volume.
=================================================================
"""

from __future__ import annotations

from biology_as_code.pathways._types import (
    MetabolicPathway,
    MetaboliteNode,
    PathwayNodeType,
    ReactionEdge,
)

BERDANIER_2000 = (
    "Berdanier CD. Advanced Nutrition: Macronutrients, 2nd ed. CRC Press, 2000. "
    "Appendix 2, Metabolic Maps, pp. 471-492."
)

#: The 60:1 conversion is NOT printed on Map 6. It is the DRI convention and must
#: be cited to the DRI report, not to the textbook page the topology came from.
IOM_1998_B_VITAMINS = (
    "Institute of Medicine. Dietary Reference Intakes for Thiamin, Riboflavin, "
    "Niacin, Vitamin B6, Folate, Vitamin B12, Pantothenic Acid, Biotin, and "
    "Choline. National Academies Press, 1998. DOI 10.17226/6015 "
    "[accession UNVERIFIED — resolve before it is quoted as the anchor]"
)


def _build_tryptophan_niacin() -> MetabolicPathway:
    pathway = MetabolicPathway(
        name="tryptophan_niacin",
        description=(
            "Tryptophan catabolism through the kynurenine route to niacin, with the "
            "serotonin/melatonin branch. The source of the niacin equivalent, and "
            "PLP-dependent at two steps."
        ),
    )
    pathway.references = [
        f"{BERDANIER_2000} Map 6, p. 475.",
        IOM_1998_B_VITAMINS,
    ]

    for node_id, name, kind, notes in [
        ("TRP", "Tryptophan", PathwayNodeType.SUBSTRATE, "Indispensable amino acid; dietary entry point"),
        ("NFK", "N-formylkynurenine", PathwayNodeType.INTERMEDIATE, ""),
        ("KYN", "Kynurenine", PathwayNodeType.INTERMEDIATE, "Branch point: three competing fates"),
        ("KYNA", "Kynurenate", PathwayNodeType.PRODUCT, "Excreted; diverts from niacin"),
        ("ANTH", "Anthranilate", PathwayNodeType.PRODUCT, "Diverts from niacin"),
        ("OHKYN", "3-hydroxykynurenine", PathwayNodeType.INTERMEDIATE, ""),
        ("XANTH", "Xanthurenate", PathwayNodeType.PRODUCT,
         "Accumulates and spills into urine when PLP is short — the classic B6 status marker"),
        ("OHANTH", "3-hydroxyanthranilate", PathwayNodeType.INTERMEDIATE, ""),
        ("ACMS", "2-amino-3-carboxymuconate semialdehyde", PathwayNodeType.INTERMEDIATE,
         "The commitment point: cyclise to quinolinate or divert to picolinate"),
        ("QUIN", "Quinolinate", PathwayNodeType.INTERMEDIATE, ""),
        ("NIACIN", "Niacin (nicotinic acid)", PathwayNodeType.PRODUCT,
         "Endogenous synthesis; low yield"),
        ("PIC", "Picolinate", PathwayNodeType.PRODUCT,
         "Competing branch; implicated in trace-mineral conservation"),
        ("AMS", "2-aminomuconate semialdehyde", PathwayNodeType.INTERMEDIATE, ""),
        ("AM", "Aminomuconate", PathwayNodeType.INTERMEDIATE, ""),
        ("GLU", "Glutamate", PathwayNodeType.PRODUCT, "Full oxidation route; no niacin made"),
        ("SERO", "Serotonin (5-HT)", PathwayNodeType.PRODUCT, "Neurotransmitter branch"),
        ("MEL", "Melatonin", PathwayNodeType.PRODUCT, ""),
        ("FORM", "Formate", PathwayNodeType.PRODUCT, "Co-product"),
        ("ALA", "Alanine", PathwayNodeType.PRODUCT, "Co-product of both kynureninase steps"),
    ]:
        pathway.add_node(MetaboliteNode(id=node_id, name=name, node_type=kind, notes=notes))

    for edge in [
        ReactionEdge(from_node="TRP", to_node="NFK", enzyme="tryptophan 2,3-dioxygenase",
                     notes="O2-dependent ring opening; rate-limiting and cortisol-inducible"),
        ReactionEdge(from_node="TRP", to_node="SERO", enzyme="tryptophan hydroxylase",
                     notes="Competing branch — the same dietary tryptophan cannot do both"),
        ReactionEdge(from_node="SERO", to_node="MEL", process="N-acetylation + O-methylation"),
        ReactionEdge(from_node="NFK", to_node="KYN", enzyme="formamidase"),
        ReactionEdge(from_node="NFK", to_node="FORM", process="co-product release"),
        ReactionEdge(from_node="KYN", to_node="KYNA", enzyme="kynurenine aminotransferase",
                     requires_nutrient=["vitamin B6 (PLP)"],
                     notes="Transaminase, so also PLP-dependent; drains the pool away from niacin"),
        ReactionEdge(from_node="KYN", to_node="ANTH", enzyme="kynureninase",
                     requires_nutrient=["vitamin B6 (PLP)"]),
        ReactionEdge(from_node="KYN", to_node="OHKYN", enzyme="kynurenine 3-monooxygenase",
                     nadph_cost=1, notes="O2 + NADPH consumed"),
        ReactionEdge(from_node="OHKYN", to_node="XANTH", enzyme="kynurenine aminotransferase",
                     requires_nutrient=["vitamin B6 (PLP)"],
                     notes="THE B6 SPILLWAY. When kynureninase stalls for want of PLP, "
                           "3-hydroxykynurenine backs up and exits here instead of "
                           "continuing to niacin"),
        ReactionEdge(from_node="OHKYN", to_node="OHANTH", enzyme="kynureninase",
                     requires_nutrient=["vitamin B6 (PLP)"],
                     notes="THE BOTTLENECK. The only route from tryptophan to niacin runs "
                           "through this PLP-dependent step"),
        ReactionEdge(from_node="OHKYN", to_node="ALA", process="co-product release"),
        ReactionEdge(from_node="OHANTH", to_node="ACMS",
                     enzyme="3-hydroxyanthranilate 3,4-dioxygenase",
                     requires_nutrient=["iron"],
                     notes="Non-heme iron dioxygenase"),
        ReactionEdge(from_node="ACMS", to_node="QUIN", process="non-enzymatic cyclisation",
                     notes="Spontaneous, so it only wins when ACMS decarboxylase is saturated"),
        ReactionEdge(from_node="ACMS", to_node="PIC", enzyme="ACMS decarboxylase",
                     notes="Competing branch; its capacity sets how much reaches niacin"),
        ReactionEdge(from_node="ACMS", to_node="AMS", enzyme="ACMS decarboxylase",
                     co2_produced=1),
        ReactionEdge(from_node="QUIN", to_node="NIACIN",
                     enzyme="quinolinate phosphoribosyltransferase", co2_produced=1,
                     notes="LOW YIELD — Berdanier: 'this conversion is not very efficient'"),
        ReactionEdge(from_node="AMS", to_node="AM", enzyme="aminomuconate semialdehyde dehydrogenase",
                     nadh_cost=-1),
        ReactionEdge(from_node="AM", to_node="GLU",
                     notes="Complete oxidation route; tryptophan spent without making niacin"),
    ]:
        pathway.add_edge(edge)

    return pathway


def _build_carnitine_synthesis() -> MetabolicPathway:
    pathway = MetabolicPathway(
        name="carnitine_synthesis",
        description=(
            "Endogenous carnitine from lysine and methionine. Five micronutrient "
            "dependencies on one linear chain — the cleanest argument against "
            "scoring nutrients independently."
        ),
    )
    pathway.references = [f"{BERDANIER_2000} Map 25, p. 489."]

    for node_id, name, kind, notes in [
        ("LYS", "Lysine (protein-bound)", PathwayNodeType.SUBSTRATE,
         "Carbon skeleton; must already be incorporated into protein to be methylated"),
        ("SAM", "S-adenosylmethionine", PathwayNodeType.SUBSTRATE,
         "Methyl donor; its supply is downstream of methionine, folate and B12"),
        ("TML", "ε-N-trimethyl-L-lysine", PathwayNodeType.INTERMEDIATE, ""),
        ("HTML", "β-hydroxy-ε-N-trimethyl-L-lysine", PathwayNodeType.INTERMEDIATE, ""),
        ("BBALD", "γ-butyrobetaine aldehyde", PathwayNodeType.INTERMEDIATE, ""),
        ("BB", "γ-butyrobetaine", PathwayNodeType.INTERMEDIATE,
         "Hydroxylated in liver and kidney; most tissues cannot finish the job"),
        ("CARN", "L-carnitine", PathwayNodeType.PRODUCT,
         "Required to carry long-chain fatty acyl groups into mitochondria"),
        ("GLY", "Glycine", PathwayNodeType.PRODUCT, "Co-product"),
    ]:
        pathway.add_node(MetaboliteNode(id=node_id, name=name, node_type=kind, notes=notes))

    for edge in [
        ReactionEdge(from_node="LYS", to_node="TML", enzyme="protein-lysine methyltransferase",
                     requires_nutrient=["methionine (SAM)", "folate", "vitamin B12"],
                     notes="Three methyl transfers. Folate and B12 enter indirectly by "
                           "regenerating methionine for SAM"),
        ReactionEdge(from_node="SAM", to_node="TML", process="methyl donation",
                     notes="Co-substrate edge; SAM is consumed, not transformed into TML"),
        ReactionEdge(from_node="TML", to_node="HTML", enzyme="TML dioxygenase (TMLD)",
                     requires_nutrient=["iron", "vitamin C"], co2_produced=1,
                     location="mitochondria",
                     notes="Fe(II)/2-oxoglutarate dioxygenase; ascorbate keeps the iron reduced"),
        ReactionEdge(from_node="HTML", to_node="BBALD", enzyme="HTML aldolase",
                     requires_nutrient=["vitamin B6 (PLP)"], location="cytosol"),
        ReactionEdge(from_node="HTML", to_node="GLY", process="co-product release"),
        ReactionEdge(from_node="BBALD", to_node="BB",
                     enzyme="γ-butyrobetaine aldehyde dehydrogenase",
                     requires_nutrient=["niacin (NAD)"], nadh_cost=-1),
        ReactionEdge(from_node="BB", to_node="CARN", enzyme="γ-butyrobetaine dioxygenase (BBD)",
                     requires_nutrient=["iron", "vitamin C"], co2_produced=1,
                     location="liver/kidney cytosol",
                     notes="Second ascorbate-dependent dioxygenase. Tissue-restricted, so "
                           "muscle depends on hepatic supply"),
    ]:
        pathway.add_edge(edge)

    return pathway


class MicronutrientCofactorRegistry:
    """Teaching graphs where the micronutrient dependency is the subject."""

    def __init__(self) -> None:
        self.pathways: dict[str, MetabolicPathway] = {}
        for pathway in (_build_tryptophan_niacin(), _build_carnitine_synthesis()):
            self.register(pathway)

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    def nutrient_index(self) -> dict[str, list[str]]:
        """Micronutrient -> ``pathway::step`` for every step that needs it.

        The cross-pathway version of :meth:`MetabolicPathway.nutrient_dependencies`.
        Vitamin B6 lands in both pathways, which is the useful part: a single
        shortfall shows up in niacin synthesis and carnitine synthesis at once.
        """
        index: dict[str, list[str]] = {}
        for pathway in self.list_all():
            for nutrient, steps in pathway.nutrient_dependencies().items():
                index.setdefault(nutrient, []).extend(
                    f"{pathway.name}::{step}" for step in steps
                )
        return {k: sorted(v) for k, v in sorted(index.items())}


_REGISTRY: MicronutrientCofactorRegistry | None = None


def get_micronutrient_cofactor_registry() -> MicronutrientCofactorRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = MicronutrientCofactorRegistry()
    return _REGISTRY


if __name__ == "__main__":
    registry = get_micronutrient_cofactor_registry()
    for pathway in registry.list_all():
        print("=" * 68)
        print(f"{pathway.name} — {len(pathway.nodes)} nodes, {len(pathway.edges)} edges")
        print("=" * 68)
        for nutrient, steps in sorted(pathway.nutrient_dependencies().items()):
            print(f"  {nutrient:28} {len(steps)} step(s)")
        orphans = pathway.orphan_nodes()
        if orphans:
            print(f"  ORPHAN NODES (declared, never used): {orphans}")

    print("\n" + "=" * 68)
    print("CROSS-PATHWAY NUTRIENT INDEX")
    print("=" * 68)
    for nutrient, steps in registry.nutrient_index().items():
        print(f"  {nutrient}")
        for step in steps:
            print(f"      {step}")
