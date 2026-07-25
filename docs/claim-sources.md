# Source registry — the authoritative slot map

Every source, the slot it owns, and the domain it is authoritative in. Companion to
the [claim schema](claim-schema.md).

> **The one rule.** A source is authoritative *only within its domain*. Route every
> claim slot to the source that is gold-standard **for that slot**. Rhea is definitive
> for "the canonical ID of a biochemical reaction" and useless — worse, discrediting —
> for a food's identity or a disease outcome. Matching source-to-slot is the whole
> discipline; getting it wrong is the amateur tell.
>
> **License matters for adoption.** An openly adoptable standard prefers open sources
> (OBO / CC0 / CC-BY) and references restricted ones (KEGG, SNOMED CT) by ID only,
> never redistributing them. The `License` column flags this.

## Identity layer — what the claim is about

| Slot | Source | Authoritative for | Prefix | License |
|---|---|---|---|---|
| Food / product | **FoodOn** | generic food identity, farm-to-fork | `FOODON:` | open (OBO) |
| ↳ common names | USDA **FDC**, **LanguaL** | crosswalk to nutrition data | `USDA_FDC:` | open |
| Source organism | **NCBITaxon** | species (e.g. *Arthrospira*) | `NCBITaxon:` | open (OBO) |
| Compound / nutrient | **ChEBI** | chemical identity | `CHEBI:` | open (OBO) |
| ↳ broader chemistry | **PubChem** | compounds beyond ChEBI | `CID:` | open |
| Anatomy / site | **UBERON** | organ, tissue, barrier (brain, BBB) | `UBERON:` | open (OBO) |

## Nutrition-content layer — what's *in* the food

| Slot | Source | Authoritative for | Notes |
|---|---|---|---|
| Polyphenols | **Phenol-Explorer** | polyphenol content, metabolism, processing effects | open; INRA |
| Food metabolome | **FooDB** | broad food-compound composition | open |
| Flavonoids / isoflavones / PACs | **USDA** special-interest DBs | ETL composition sources | open |
| Dietary components | **CDNO** | nutritional-component terms | open (OBO) |
| Supplement labels | **DSLD** (NIH) | what's on a supplement label | open |
| Ingredient identity | **UNII** (FDA) | unique ingredient IDs | open |

## Mechanism layer — *how* it's claimed to work

| Slot | Source | Authoritative for | License |
|---|---|---|---|
| Biochemical reaction | **Rhea** | the canonical reaction (participants are ChEBI) | open; SIB/EBI |
| Enzyme classification | **EC number** | enzyme class (e.g. NOS) | open |
| Enzyme / protein | **UniProt** | the protein itself | open |
| Process / function | **GO** (+ **GO-CAM**) | e.g. "NO biosynthetic process"; causal models | open (OBO) |
| Curated human pathway | **Reactome** | pathway context | open (CC-BY) |
| Community pathway | **WikiPathways** | open pathway context | open (CC0) |
| (Reference only) | **KEGG**, **MetaCyc** | pathways / reactions | ⚠ restricted — cite by ID |

## Statement structure — the triple

| Slot | Source | Authoritative for |
|---|---|---|
| subject–predicate–object | **Biolink Model** | the core triple + predicate set |
| relation semantics | **RO** | formal relation grounding under Biolink |

## Outcome layer — the claimed effect

| Slot | Source | Authoritative for | Notes |
|---|---|---|---|
| Disease / condition | **MONDO** | unified disease identity | open (OBO) |
| ↳ alternates | **DOID**, **MeSH**, **ICD-11**, **SNOMED CT** | DOID/MeSH open; ICD/SNOMED ⚠ licensed |
| Phenotype / symptom | **HPO** | human phenotype | open (OBO) |
| Trait / measurement | **EFO** | traits, measurements | open |
| Quality | **PATO** | e.g. "increased blood flow" | open (OBO) |
| Biological attribute | **OBA** | e.g. "blood pressure" | open (OBO) |
| Lab test / biomarker | **LOINC** | e.g. serum testosterone | open (reg.) |
| Food ↔ biomarker | **FOBI** | food-intake biomarkers | open (OBO) |

## Evidence layer — the stress-test's binding points

| Slot | Source | Authoritative for | Notes |
|---|---|---|---|
| Evidence type | **ECO** | type of each evidence line | open (CC0) |
| Study design | **OBI** | RCT, cohort, in-vitro | open (OBO) |
| Evidence organization | **SEPIO** pattern | evidence lines → a claim + confidence | open |
| Certainty grade | **GRADE** (coded) | High / Mod / Low / Very-low | open framework |
| Food–drug interaction | **FIDEO** | food-drug evidence | open (OBO) |
| Drug | **DrugBank** | drug identity / interactions | ⚠ academic license |

## Envelope — the object itself

| Slot | Source | Authoritative for |
|---|---|---|
| Claim object | **Nanopublication** | citable, immutable, versioned assertion + provenance + pub-info |
| Provenance / versioning | **PROV-O**, **PAV**, **Dublin Core** | who / when / how / version |
| Web-discoverable verdict | **schema.org ClaimReview** | fact-check markup for search |

## The one thing we author

| Slot | Source | Authoritative for |
|---|---|---|
| Verdict + attacks | **ACA** (Assay Claim Assessment) | Busted / Plausible / Confirmed; the 8 attack types; rubric version. ~20 terms, orthogonal to ECO/SEPIO. |

## Worked routing

| Item | Identity | Mechanism | Outcome | Read |
|---|---|---|---|---|
| Watermelon | `FOODON` → `CHEBI`(L-citrulline) | `Rhea`(citrulline→arginine; NOS: arginine→NO) + `GO`(NO biosynthesis) | erectile / vascular fn (`MONDO`/`HPO`) | **Plausible** — real pathway, small RCT, weaker than PDE5i |
| Beetroot | `FOODON` → `CHEBI`(nitrate) | nitrate→nitrite→NO | blood flow, BP (`PATO`/`OBA`) | real for BP; performance-specific is a further step |
| Oysters | `FOODON` → `CHEBI`(zinc) | zinc → testosterone | libido | mechanism node exists but chain breaks (deficiency-only) |

The mechanism column is exactly what lets the *mechanism-vs-outcome* attack separate
the first two rows from the third.

---

New sources get a slot, a domain-of-authority, and a license flag before they are
used — the same routing discipline the table above encodes.
