"""
amino_acid_catabolism.py
=================================================================
High-value amino-acid catabolism teaching graphs.

Textbook protein chapters usually cover nitrogen disposal + a few
clinically / nutritionally dense carbon-skeleton maps — not twenty
shallow one-AA files. This module scaffolds:

  1. aa_nitrogen_disposal          — hub: transamination → GDH → urea link
  2. bcaa_catabolism               — Leu / Ile / Val via BCKDH (MSUD teaching)
  3. phenylalanine_tyrosine_catabolism — Phe → Tyr → fumarate + acetoacetate (PKU)
  4. methionine_one_carbon         — Met → SAM → Hcy (remethylation + Cys)
  5. glucogenic_ketogenic_aa       — carbon-skeleton fate classification map

FLOW teaching graphs — not LAW-SPEC magnitudes. Connects to existing
``urea_cycle`` and ``cori_glucose_alanine`` packs; does not re-model them.
=================================================================
"""

from __future__ import annotations

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
    mechanism_id: str = ""
    enzyme: str = ""
    process: str = ""
    location: str = ""
    regulation: str = ""
    notes: str = ""


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

    def get_mechanism(self, edge: ReactionEdge) -> Optional["MetabolicMechanism"]:
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


class AminoAcidCatabolismRegistry:
    """Registry of amino-acid catabolism teaching graphs."""

    def __init__(self):
        self.pathways: dict[str, MetabolicPathway] = {}
        self._build_nitrogen_disposal()
        self._build_bcaa()
        self._build_phe_tyr()
        self._build_methionine_one_carbon()
        self._build_glucogenic_ketogenic_map()

    def register(self, pathway: MetabolicPathway) -> None:
        self.pathways[pathway.name.lower()] = pathway

    def get(self, name: str) -> MetabolicPathway | None:
        return self.pathways.get(name.lower())

    def list_all(self) -> list[MetabolicPathway]:
        return list(self.pathways.values())

    # ------------------------------------------------------------------
    # 1. Nitrogen disposal hub
    # ------------------------------------------------------------------
    def _build_nitrogen_disposal(self) -> None:
        p = MetabolicPathway(
            name="aa_nitrogen_disposal",
            description=(
                "Amino-acid nitrogen disposal hub. Most amino acids transfer their "
                "α-amino group to α-ketoglutarate (aminotransferases → glutamate). "
                "Glutamate dehydrogenase releases free NH₄⁺; aspartate donates the "
                "second N into the urea cycle. Carbon skeletons exit as α-keto acids "
                "toward glucogenic or ketogenic fates. Links to existing urea_cycle graph."
            ),
        )
        for nid, name, nt, notes in [
            ("amino_acid", "Amino acid (general)", PathwayNodeType.SUBSTRATE,
             "Dietary or endogenous protein-derived AA."),
            ("alpha_kg", "α-Ketoglutarate", PathwayNodeType.SUBSTRATE,
             "Universal amino-group acceptor for most transaminations."),
            ("glutamate", "Glutamate", PathwayNodeType.INTERMEDIATE,
             "Central nitrogen collector in liver (and muscle ALT branch)."),
            ("alpha_keto_acid", "α-Keto acid (carbon skeleton)", PathwayNodeType.PRODUCT,
             "Enters TCA / GNG / ketone paths depending on AA identity."),
            ("nh4", "Ammonia (NH₄⁺)", PathwayNodeType.PRODUCT,
             "Toxic; must be detoxified — mainly via urea cycle in liver."),
            ("aspartate", "Aspartate", PathwayNodeType.INTERMEDIATE,
             "Second nitrogen donor to urea (via argininosuccinate synthetase)."),
            ("urea_cycle_entry", "Urea cycle (see urea_cycle pack)", PathwayNodeType.PRODUCT,
             "Teaching link node — full cycle is modeled in urea_cycle.py."),
            ("glutamine", "Glutamine", PathwayNodeType.INTERMEDIATE,
             "Safe N transport form (muscle → gut/kidney/liver); GLS releases NH₄⁺."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge(
            from_node="amino_acid", to_node="alpha_keto_acid",
            mechanism_id="aminotransferase",
            enzyme="Aminotransferase (ALT/AST family, PLP)",
            location="Cytosol / mito (tissue-specific)",
            notes="Transfers α-amino N; leaves the carbon skeleton as an α-keto acid.",
        ))
        p.add_edge(ReactionEdge(
            from_node="alpha_kg", to_node="glutamate",
            mechanism_id="aminotransferase",
            enzyme="Aminotransferase (receives N on α-KG)",
            location="Cytosol / mito",
            notes="α-KG + amino-N → glutamate. Coupled to AA → α-keto acid.",
        ))
        p.add_edge(ReactionEdge(
            from_node="glutamate", to_node="nh4",
            mechanism_id="glutamate_dehydrogenase",
            enzyme="Glutamate dehydrogenase (GDH)",
            location="Mitochondrial matrix (liver)",
            regulation="Activated by ADP/leucine (isoform-dependent); high energy charge favors glutamate.",
            notes="Oxidative deamination regenerates α-KG and free NH₄⁺.",
        ))
        p.add_edge(ReactionEdge(
            from_node="glutamate", to_node="aspartate",
            mechanism_id="aminotransferase",
            enzyme="Aspartate aminotransferase (AST / GOT)",
            location="Mito / cytosol",
            notes="Glu + OAA ⇌ α-KG + Asp. Feeds the second N into urea.",
        ))
        p.add_edge(ReactionEdge(
            from_node="nh4", to_node="urea_cycle_entry",
            enzyme="CPS1 entry (see urea_cycle)",
            location="Liver mitochondria",
            notes="NH₄⁺ + CO₂ → carbamoyl phosphate. Full topology in urea_cycle pack.",
        ))
        p.add_edge(ReactionEdge(
            from_node="aspartate", to_node="urea_cycle_entry",
            enzyme="Argininosuccinate synthetase (see urea_cycle)",
            location="Liver cytosol",
            notes="Asp donates the second nitrogen atom of urea.",
        ))
        p.add_edge(ReactionEdge(
            from_node="glutamate", to_node="glutamine",
            enzyme="Glutamine synthetase",
            location="Muscle, brain, other tissues",
            notes="NH₄⁺ + Glu + ATP → Gln. Safe inter-organ nitrogen transport.",
        ))
        p.add_edge(ReactionEdge(
            from_node="glutamine", to_node="nh4",
            enzyme="Glutaminase (GLS)",
            location="Liver periportal, kidney, gut",
            notes="Releases NH₄⁺ for urea (liver) or ammonium excretion (kidney).",
        ))

        p.references = [
            "Berg JM, Tymoczko JL, Stryer L. Biochemistry — Amino Acid Degradation "
            "and the Urea Cycle.",
            "Lehninger Principles of Biochemistry — Nitrogen excretion and the urea cycle.",
        ]
        p.extra_summary = {
            "links_to": "urea_cycle",
            "central_collector": "glutamate",
            "n_atoms_in_urea": 2,
        }
        self.register(p)

    # ------------------------------------------------------------------
    # 2. BCAA catabolism
    # ------------------------------------------------------------------
    def _build_bcaa(self) -> None:
        p = MetabolicPathway(
            name="bcaa_catabolism",
            description=(
                "Branched-chain amino acid (BCAA) catabolism: leucine, isoleucine, "
                "and valine. Shared trunk: transamination → branched-chain keto acid "
                "dehydrogenase (BCKDH, MSUD enzyme). Then diverge: Leu → ketogenic "
                "(acetyl-CoA / acetoacetate); Val → glucogenic (succinyl-CoA); "
                "Ile → both."
            ),
        )
        for nid, name, nt, notes in [
            ("leucine", "Leucine", PathwayNodeType.SUBSTRATE, "Purely ketogenic essential AA."),
            ("isoleucine", "Isoleucine", PathwayNodeType.SUBSTRATE, "Mixed glucogenic + ketogenic."),
            ("valine", "Valine", PathwayNodeType.SUBSTRATE, "Purely glucogenic essential AA."),
            ("bcka", "Branched-chain α-keto acids", PathwayNodeType.INTERMEDIATE,
             "α-Ketoisocaproate (Leu), α-keto-β-methylvalerate (Ile), α-ketoisovalerate (Val)."),
            ("bcaa_coa", "Branched-chain acyl-CoA", PathwayNodeType.INTERMEDIATE,
             "Products of BCKDH oxidative decarboxylation."),
            ("acetyl_coa", "Acetyl-CoA", PathwayNodeType.PRODUCT, "Ketogenic end from Leu / Ile."),
            ("acetoacetate", "Acetoacetate", PathwayNodeType.PRODUCT, "Ketone body precursor from Leu."),
            ("succinyl_coa", "Succinyl-CoA", PathwayNodeType.PRODUCT,
             "Glucogenic end from Val / Ile (via propionyl-CoA → methylmalonyl-CoA)."),
            ("propionyl_coa", "Propionyl-CoA", PathwayNodeType.INTERMEDIATE,
             "3-carbon intermediate toward succinyl-CoA (B12-dependent mutase)."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        # Shared trunk
        for aa in ("leucine", "isoleucine", "valine"):
            p.add_edge(ReactionEdge(
                from_node=aa, to_node="bcka",
                mechanism_id="aminotransferase",
                enzyme="Branched-chain aminotransferase (BCAT)",
                location="Muscle (high), other tissues",
                notes=f"{aa.capitalize()} → corresponding BCKA + Glu (from α-KG).",
            ))
        p.add_edge(ReactionEdge(
            from_node="bcka", to_node="bcaa_coa",
            mechanism_id="bckdh",
            enzyme="Branched-chain α-keto acid dehydrogenase (BCKDH complex)",
            location="Mitochondria",
            regulation="Inactivated by BCKDK phosphorylation; activated by phosphatase (PPM1K).",
            notes="Irreversible committed step. Deficiency → maple syrup urine disease (MSUD).",
        ))
        # Divergent fates (teaching compression of multi-step tails)
        p.add_edge(ReactionEdge(
            from_node="bcaa_coa", to_node="acetyl_coa",
            enzyme="Leu / Ile ketogenic branch (multi-step)",
            location="Mitochondria",
            notes="Leucine and part of isoleucine yield acetyl-CoA.",
        ))
        p.add_edge(ReactionEdge(
            from_node="bcaa_coa", to_node="acetoacetate",
            enzyme="HMG-CoA path (leucine)",
            location="Mitochondria",
            notes="Leucine is purely ketogenic: acetoacetate + acetyl-CoA.",
        ))
        p.add_edge(ReactionEdge(
            from_node="bcaa_coa", to_node="propionyl_coa",
            enzyme="Val / Ile propionyl branch (multi-step)",
            location="Mitochondria",
            notes="Valine and part of isoleucine → propionyl-CoA.",
        ))
        p.add_edge(ReactionEdge(
            from_node="propionyl_coa", to_node="succinyl_coa",
            enzyme="Propionyl-CoA carboxylase → methylmalonyl-CoA mutase (B12)",
            location="Mitochondria",
            notes="Biotin + B12 dependent. Succinyl-CoA enters TCA / GNG.",
        ))

        p.references = [
            "Maple syrup urine disease / BCKDH: OMIM 248600; standard biochem texts.",
            "BCAA metabolism overview — Lehninger / Harper's Biochemistry.",
        ]
        p.extra_summary = {
            "committed_enzyme": "BCKDH",
            "clinical_hook": "MSUD",
            "leu_fate": "ketogenic",
            "val_fate": "glucogenic",
            "ile_fate": "mixed",
        }
        self.register(p)

    # ------------------------------------------------------------------
    # 3. Phe / Tyr
    # ------------------------------------------------------------------
    def _build_phe_tyr(self) -> None:
        p = MetabolicPathway(
            name="phenylalanine_tyrosine_catabolism",
            description=(
                "Phenylalanine and tyrosine catabolism. Phe is hydroxylated to Tyr "
                "by phenylalanine hydroxylase (PAH, BH₄ cofactor) — the PKU enzyme. "
                "Tyr proceeds via homogentisate to fumarate (glucogenic) + acetoacetate "
                "(ketogenic). Teaching compression of the full multi-enzyme cascade."
            ),
        )
        for nid, name, nt, notes in [
            ("phenylalanine", "Phenylalanine", PathwayNodeType.SUBSTRATE,
             "Essential AA. Excess must be cleared via Tyr path."),
            ("tyrosine", "Tyrosine", PathwayNodeType.INTERMEDIATE,
             "Also dietary/protein-derived; precursor of catecholamines, thyroid hormone, melanin."),
            ("hpp", "p-Hydroxyphenylpyruvate", PathwayNodeType.INTERMEDIATE, ""),
            ("homogentisate", "Homogentisate", PathwayNodeType.INTERMEDIATE,
             "Deficiency of homogentisate oxidase → alkaptonuria."),
            ("fumarylacetoacetate", "Fumarylacetoacetate", PathwayNodeType.INTERMEDIATE,
             "Cleaved to fumarate + acetoacetate. FAH deficiency → tyrosinemia type I."),
            ("fumarate", "Fumarate", PathwayNodeType.PRODUCT, "Glucogenic — enters TCA."),
            ("acetoacetate", "Acetoacetate", PathwayNodeType.PRODUCT, "Ketogenic product."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge(
            from_node="phenylalanine", to_node="tyrosine",
            mechanism_id="phenylalanine_hydroxylase",
            enzyme="Phenylalanine hydroxylase (PAH)",
            location="Liver cytosol",
            regulation="Requires tetrahydrobiopterin (BH₄) + O₂",
            notes="Irreversible. PAH deficiency → phenylketonuria (PKU).",
        ))
        p.add_edge(ReactionEdge(
            from_node="tyrosine", to_node="hpp",
            enzyme="Tyrosine aminotransferase (TAT)",
            location="Liver cytosol",
            notes="PLP-dependent transamination.",
        ))
        p.add_edge(ReactionEdge(
            from_node="hpp", to_node="homogentisate",
            enzyme="p-Hydroxyphenylpyruvate dioxygenase (HPD)",
            location="Liver cytosol",
            notes="Requires ascorbate as a supporting cofactor in classic teaching.",
        ))
        p.add_edge(ReactionEdge(
            from_node="homogentisate", to_node="fumarylacetoacetate",
            enzyme="Homogentisate 1,2-dioxygenase → maleylacetoacetate isomerase",
            location="Liver cytosol",
            notes="Compressed two steps for teaching graph clarity.",
        ))
        p.add_edge(ReactionEdge(
            from_node="fumarylacetoacetate", to_node="fumarate",
            enzyme="Fumarylacetoacetate hydrolase (FAH)",
            location="Liver cytosol",
            notes="Glucogenic half of the split.",
        ))
        p.add_edge(ReactionEdge(
            from_node="fumarylacetoacetate", to_node="acetoacetate",
            enzyme="Fumarylacetoacetate hydrolase (FAH)",
            location="Liver cytosol",
            notes="Ketogenic half of the split.",
        ))

        p.references = [
            "Phenylketonuria (PAH) — OMIM 261600; standard medical biochemistry.",
            "Tyrosine catabolism and alkaptonuria / tyrosinemia — Harper's / Lehninger.",
        ]
        p.extra_summary = {
            "clinical_hook": "PKU (PAH)",
            "fate": "mixed glucogenic + ketogenic",
            "products": "fumarate + acetoacetate",
        }
        self.register(p)

    # ------------------------------------------------------------------
    # 4. Methionine / one-carbon
    # ------------------------------------------------------------------
    def _build_methionine_one_carbon(self) -> None:
        p = MetabolicPathway(
            name="methionine_one_carbon",
            description=(
                "Methionine and one-carbon metabolism. Met is activated to S-adenosylmethionine "
                "(SAM), the universal methyl donor. After methyl transfer, SAH → homocysteine. "
                "Homocysteine is remethylated to Met (methionine synthase, B12 + 5-methyl-THF) "
                "or committed to cysteine via transsulfuration (CBS, B6)."
            ),
        )
        for nid, name, nt, notes in [
            ("methionine", "Methionine", PathwayNodeType.SUBSTRATE, "Essential AA; also recycled from Hcy."),
            ("sam", "S-Adenosylmethionine (SAM)", PathwayNodeType.INTERMEDIATE,
             "Universal methyl donor (DNA, proteins, lipids, neurotransmitters)."),
            ("sah", "S-Adenosylhomocysteine (SAH)", PathwayNodeType.INTERMEDIATE,
             "Product after methyl transfer; competitive inhibitor of many methyltransferases."),
            ("homocysteine", "Homocysteine", PathwayNodeType.INTERMEDIATE,
             "Branch point: remethylation vs transsulfuration. Elevated Hcy = vascular risk marker."),
            ("methyl_thf", "5-Methyl-THF", PathwayNodeType.SUBSTRATE,
             "Folate one-carbon form; methyl donor for Met synthase."),
            ("cysteine", "Cysteine", PathwayNodeType.PRODUCT,
             "Non-essential if Met + Ser sufficient; GSH precursor."),
            ("serine", "Serine", PathwayNodeType.SUBSTRATE,
             "Carbon/N donor into transsulfuration (with Hcy → cystathionine)."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge(
            from_node="methionine", to_node="sam",
            mechanism_id="methionine_adenosyltransferase",
            enzyme="Methionine adenosyltransferase (MAT / SAM synthase)",
            location="Cytosol (liver-enriched isoforms)",
            notes="Met + ATP → SAM + PPi + Pi. Commits Met to methyl metabolism.",
        ))
        p.add_edge(ReactionEdge(
            from_node="sam", to_node="sah",
            enzyme="Methyltransferases (many)",
            location="Cytosol / nucleus",
            notes="SAM donates methyl → SAH. Huge set of acceptor substrates.",
        ))
        p.add_edge(ReactionEdge(
            from_node="sah", to_node="homocysteine",
            enzyme="SAH hydrolase (AHCY)",
            location="Cytosol",
            notes="Reversible; high Hcy or adenosine can push back toward SAH.",
        ))
        p.add_edge(ReactionEdge(
            from_node="homocysteine", to_node="methionine",
            mechanism_id="methionine_synthase",
            enzyme="Methionine synthase (MTR) — B12",
            location="Cytosol",
            regulation="Requires methylcobalamin (B12) and 5-methyl-THF",
            notes="Remethylation cycle. Folate trap if B12 deficient.",
        ))
        p.add_edge(ReactionEdge(
            from_node="methyl_thf", to_node="methionine",
            mechanism_id="methionine_synthase",
            enzyme="Methionine synthase (methyl transfer)",
            location="Cytosol",
            notes="5-methyl-THF methyl group → Hcy → Met; THF released.",
        ))
        p.add_edge(ReactionEdge(
            from_node="homocysteine", to_node="cysteine",
            enzyme="Cystathionine β-synthase (CBS) → γ-cystathionase (CTH)",
            location="Cytosol (liver)",
            regulation="CBS needs PLP (B6); activated by SAM",
            notes="Irreversible transsulfuration. Compressed two steps. Serine co-substrate.",
        ))
        p.add_edge(ReactionEdge(
            from_node="serine", to_node="cysteine",
            enzyme="Transsulfuration (Ser carbon enters cystathionine)",
            location="Cytosol",
            notes="Serine provides the carbon skeleton half of cysteine.",
        ))

        p.references = [
            "One-carbon metabolism and methionine cycle — standard nutrition/biochem texts.",
            "Homocysteine, folate, B12 interactions — public health / vascular literature.",
        ]
        p.extra_summary = {
            "universal_methyl_donor": "SAM",
            "branch_point": "homocysteine",
            "cofactors": "B12, folate, B6",
        }
        self.register(p)

    # ------------------------------------------------------------------
    # 5. Glucogenic / ketogenic classification map
    # ------------------------------------------------------------------
    def _build_glucogenic_ketogenic_map(self) -> None:
        p = MetabolicPathway(
            name="glucogenic_ketogenic_aa",
            description=(
                "Carbon-skeleton fate map for amino acids (teaching classification). "
                "Glucogenic AA feed TCA intermediates or pyruvate (→ glucose via GNG). "
                "Ketogenic AA yield acetyl-CoA or acetoacetate (cannot make net glucose "
                "in humans). Several AA are mixed. Not a reaction sequence — a topology "
                "of destinations for exam / nutrition teaching."
            ),
        )
        # Destination hubs
        for nid, name, nt, notes in [
            ("pyruvate", "→ Pyruvate", PathwayNodeType.PRODUCT, "Glucogenic hub (Ala, Ser, Cys, Gly, Thr, Trp partial)."),
            ("oaa", "→ Oxaloacetate", PathwayNodeType.PRODUCT, "Asp, Asn."),
            ("alpha_kg_fate", "→ α-Ketoglutarate", PathwayNodeType.PRODUCT, "Glu, Gln, Pro, Arg, His."),
            ("succinyl_coa_fate", "→ Succinyl-CoA", PathwayNodeType.PRODUCT, "Met, Val, Ile (partial), Thr (partial)."),
            ("fumarate_fate", "→ Fumarate", PathwayNodeType.PRODUCT, "Phe, Tyr (partial), Asp (urea link)."),
            ("acetyl_coa_fate", "→ Acetyl-CoA / acetoacetyl-CoA", PathwayNodeType.PRODUCT, "Leu, Lys, Ile partial, Phe/Tyr partial, Trp partial."),
            # Representative AA substrates
            ("ala_ser", "Ala / Ser / Cys / Gly", PathwayNodeType.SUBSTRATE, "Classic glucogenic → pyruvate."),
            ("asp_asn", "Asp / Asn", PathwayNodeType.SUBSTRATE, "→ OAA."),
            ("glu_family", "Glu / Gln / Pro / Arg / His", PathwayNodeType.SUBSTRATE, "→ α-KG."),
            ("met_val_ile", "Met / Val / Ile", PathwayNodeType.SUBSTRATE, "→ succinyl-CoA (Ile also acetyl-CoA)."),
            ("phe_tyr", "Phe / Tyr", PathwayNodeType.SUBSTRATE, "→ fumarate + acetoacetate (mixed)."),
            ("leu_lys", "Leu / Lys", PathwayNodeType.SUBSTRATE, "Purely ketogenic essentials."),
            ("trp", "Tryptophan", PathwayNodeType.SUBSTRATE, "Mixed; also NAD⁺ precursor (kynurenine path)."),
        ]:
            p.add_node(MetaboliteNode(nid, name, nt, notes))

        p.add_edge(ReactionEdge("ala_ser", "pyruvate", process="Glucogenic", notes="ALT / serine dehydratase family routes."))
        p.add_edge(ReactionEdge("asp_asn", "oaa", process="Glucogenic", notes="AST / asparaginase."))
        p.add_edge(ReactionEdge("glu_family", "alpha_kg_fate", process="Glucogenic", notes="Transamination / deamination / Pro/Arg rings open to Glu."))
        p.add_edge(ReactionEdge("met_val_ile", "succinyl_coa_fate", process="Glucogenic (Ile mixed)", notes="Propionyl-CoA route; see also bcaa + met packs."))
        p.add_edge(ReactionEdge("met_val_ile", "acetyl_coa_fate", process="Ile ketogenic half", notes="Isoleucine is mixed."))
        p.add_edge(ReactionEdge("phe_tyr", "fumarate_fate", process="Glucogenic half", notes="See phenylalanine_tyrosine_catabolism."))
        p.add_edge(ReactionEdge("phe_tyr", "acetyl_coa_fate", process="Ketogenic half", notes="Acetoacetate / acetyl-CoA."))
        p.add_edge(ReactionEdge("leu_lys", "acetyl_coa_fate", process="Purely ketogenic", notes="No net glucose in humans."))
        p.add_edge(ReactionEdge("trp", "pyruvate", process="Glucogenic partial", notes="Alanine-like fragment in teaching maps."))
        p.add_edge(ReactionEdge("trp", "acetyl_coa_fate", process="Ketogenic partial", notes="Via kynurenine → acetyl-CoA branch."))

        p.references = [
            "Glucogenic vs ketogenic amino acids — standard medical biochemistry tables.",
        ]
        p.extra_summary = {
            "graph_kind": "classification_map",
            "purely_ketogenic": "Leu, Lys",
            "note": "Not a single enzyme cascade; destination topology.",
        }
        self.register(p)


def get_amino_acid_catabolism_registry() -> AminoAcidCatabolismRegistry:
    return AminoAcidCatabolismRegistry()


if __name__ == "__main__":
    reg = get_amino_acid_catabolism_registry()
    print("=" * 60)
    print("AMINO ACID CATABOLISM — TEACHING GRAPHS")
    print("=" * 60)
    for path in reg.list_all():
        print(f"\n{path.name}: {path.summary()}")
        print(f"  {path.description[:100]}...")
