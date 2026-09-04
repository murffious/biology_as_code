# Grounded object model for the nutrition Ontology SDK

*Produced 2026-08-29 by a 22-agent verification workflow (`wf_10a52272-879`):
7 mapping dimensions, each adversarially challenged, then synthesized.
**264 findings survived, 154 were refuted.** 0 agent errors, ~3.1M subagent tokens.*

*Every row cites a path opened during the review. Where the evidence does not
settle a question, the row says "uncertain" — those are not to be quietly
resolved by whoever reads this next.*

*Supersedes the object-model section of `DESIGN.md`, which was written before
`bfo_stack_ontology.json` was known to exist.*

---


*Scope: `biology_as_code/ontology-sdk/`. Every row cites a path opened during this review. Where the evidence does not settle a question, the row says "uncertain".*

---

## 1. What DESIGN.md got wrong or missed

`DESIGN.md` never mentions the OBO causal spine. A grep for `obo`, `bfo`, `FOODON`, `MONDO` across the file returns nothing; the spine appears only in its siblings — `ONTOLOGY-PIPELINE.md:26-28` and `WHERE-THIS-FITS.md:97-100`. The object-model table at `DESIGN.md:69-80` names `Food` / `Nutrient` / `Study` / `Claim` / `StudyUnit` / `Host` / `Law` / `Exposure` and sources them to `fdp-1/`, `edp-1/`, `evidence-platform/site/`, `biology_as_code/`. The one artifact that actually declares a food→disease causal ladder — `nutri-collective/backend/bfo_stack_ontology.json` — is not in that table, not in the link-type row, and not in the blocker list.

Specific errors and omissions, each checkable:

**"The object model already exists — it is just not declared in one place" is half true and dangerously so.** The *terms* exist. The *relations* do not. `bfo_stack_ontology.json` has top-level keys exactly `[reviewed, method, layers, terms, expert_recommendations]` — no node collection, no edge collection. `nutri-collective/backend/mechanism_ontology.db`'s only join table is `principle_mechanism(principle_id, curie)` with **no predicate column**, so a principle links to `CHEBI:18248` (iron atom) and `UBERON:0002107` (liver) through an identical untyped edge. The only materialised RO-typed causal edges in the entire tree are **10 hardcoded `StackEdge` records** in `nutri-collective/src/components/analysis/OboStackDesign.tsx`, whose own header says *"Demo fixtures only — not a live OBO import."* DESIGN.md's link-type row therefore has no data behind it for the spine.

**The spine is not five layers.** `layers` is a **six**-key map: `L1 L2 L3 L4 L5 RO` — RO is a peer key, not a sub-facet. And three terms (`uberon-liver`, `uberon-small-intestine`, `uberon-mito`) carry `obo_layer: "ANATOMY"`, a value with **no entry in the `layers` map at all**. Verified histogram over the 51 terms: `L3:11, L5:10, RO:8, L2:7, L4:7, L1:5, ANATOMY:3`. A naive `Layer = L1..L5` enum rejects 11 of 51 shipped terms.

**RO is scoped as a vocabulary but wired as data of the wrong kind.** The 8 relation terms sit in `terms[]` with the *identical record shape* as `FOODON:03312087 salmon`. In the DB, `mechanism_term` holds 8 rows with `source='ro'` and `principle_mechanism` has **zero** rows referencing an RO curie. Predicates and classes are the same type in this model. The SDK must lift RO out; DESIGN.md does not know it needs to.

**Grade is per (edge, outcome), not per edge.** `OboStackDesign.tsx` types `EdgeStrength {outcomeId, grade, direction, note}` and every one of the 10 edges carries a dense array of 3 (out-cvd, out-hypertg, out-depression). `bfo_stack_ontology.json expert_recommendations[5]` states the rule explicitly: *store RO edge strength per outcome as edge attributes, never one global grade on the relation type.* DESIGN.md's `weakest_link(values)` query models a single scalar chain and would encode exactly the defect the spine's own design rejects.

**`source` is not derivable from the CURIE, and `iri` casing is not derivable either.** 13 `source` values; `go_mf`/`go_bp`/`go_cc` all carry `GO:` curies; `uberon-mito` has `curie: GO:0005739` with `source: go_cc` under a UBERON-style local id. And FDP-1 mandates lowercase prefixes (`chebi:`, `cdno:`) while `bfo_stack_ontology.json` is uppercase throughout (`CHEBI:`, `GO:`). Two identifier serialisations for one spine.

**The spine is unpopulated exactly where DESIGN.md promises traversal.** Across the 94 ontology terms embedded on the 26 principles in `nutri-collective/backend/principles.json`, the layer histogram is `L2:30 L3:29 L4:28 ANATOMY:4 L5:2 L1:1`. **One** food term (`FOODON:03312087`) and **two** outcome terms (`MONDO:0005044`, `MONDO:0004995`) in the entire register. A `Food → … → Outcome` accessor has one food and two outcomes to walk.

**Production outcomes and foods are not ontology-keyed at all.** All 123 rows in `nutri-collective/backend/claims.json` carry an inline `outcome {id, label, query}` with slug ids and zero MONDO/DOID/HP occurrences. `nutri-collective/evidence-platform/site/id-crosswalk.v1.json` states it as data: `gaps.outcomes_with_mondo_ids: 0`, `gaps.ingredients_with_foodon_ids: 0`. The L1 and L5 ends of the spine do not connect to anything the product ships.

**There are two disjoint spines, not one.** The BFO stack (109 distinct curies across the catalog and principles) and the crosswalk (1,285 nodes / 873 edges over CDNO, INFOODS, FDC-nutrient, CAS, and local product ids). No join exists between them, and only one is covered by any licence manifest.

**Two more items DESIGN.md gets wrong about itself.** Its Status section says *"the manifest and generator … should not start until blocker 1 is resolved"* — while §6 of the same file declares blocker 1 cleared, and `ONTOLOGY-PIPELINE.md:2` re-ordered the plan away from the manifest toward a controlled vocabulary that now exists (`nutri-collective/evidence-platform/site/nutrition-vocab.v1.json`, 118 concepts, 372 altLabel, 26 hiddenLabel). And its own seed file breaks its own "wrap, never reimplement" rule: `GRADE_RANK` + `weakest_link()` are re-derived in `biology_as_code/ontology-sdk/declared.py` alongside identical copies in `fdp-1/validator/validate_fdp.py` and `edp-1/validator/validate_edp.py`.

**One thing DESIGN.md gets right and should be preserved verbatim:** `Declared[T]` is the correct core primitive, and the `inchiKey` finding (2,797/2,797 `OPEN` in `biology_as_code/MASTER_CROSSWALK.tsv`) is the sharpest identity fact in the tree.

---

## 2. The two layer systems

| | Causal spine | Format stack |
|---|---|---|
| Declared in | `nutri-collective/backend/bfo_stack_ontology.json` (`layers`) | `nutri-collective/evidence-platform/site/standardization-chart.v1.json` (`layers[]`) |
| Members | L1 Food · L2 Nutrient compound · L3 Biochemical mechanism · L4 Physiological effect · L5 Health outcome · **RO** (+ undeclared ANATOMY) | L0 Measurand · L1 Instrument/method · L2 Identity · L3 Vocabulary & reference data · L4 Study record/provenance · L5 Reporting · L6 Synthesis/grading · L7 Translation/scope · L8 Governance/incentives · L9 Traceability |
| What it numbers | positions on a food→disease causal ladder | positions in a measurement-to-governance format stack |

**The collision, plainly:** `L3` means both *"biochemical mechanism"* and *"vocabulary & reference data"*. `L5` means both *"health outcome"* and *"reporting"*. `L1` means both *"food"* and *"instrument/method"*. `L2` means both *"nutrient compound"* and *"identity"*. Bare L-tokens are already used in prose on both sides — `bfo_stack_ontology.json expert_recommendations[0].title` ("Keep L5 on MONDO primary…") and `standardization-chart.v1.json layers[7].nutrition_why` ("an L7 failure that caps L6"). `biology_as_code/ontology-sdk/PALANTIR-PRINCIPLES.md:87` already rates this the project's worst structural problem and nothing in code enforces the distinction. Three further consumers declare the causal enum independently: `nutri-collective/benchmark/evidence.py:44-46` (`LAYERS` tuple), `biology_as_code/schemas/claim_audit.schema.json:21-34` (`l1_to_l5`, `closed_through`), and `nutri-collective/fim-evidence-tool/src/lib/ontology.ts`.

### The one renaming

**The format stack keeps `L0–L9`. The causal spine loses its numbers entirely and becomes named stages under a `spine:` prefix.**

```
spine:food  spine:compound  spine:mechanism  spine:physiology  spine:outcome  spine:anatomy
```

RO leaves the layer axis altogether and becomes a predicate registry, not a layer value.

**Why the causal side is the one that moves, not the format side:**

- The format stack is referenced from six registers in three serialisations already — bare integers (`adoption-trends.v1.json`, `state-of-nutrition.v1.json`), slug ids (`emerging-tech.v1.json`, `nobel-nutrition.v1.json`), and embedded copies of the whole table (`adoption-tracker.v1.json`, `standardization-sources.v1.json`). It also carries a `superseded` block whose note says plotting old numbering against new *"is a category error"* — it has already been renumbered once and the register knows it. Renumbering it again is the expensive, destructive option.
- The causal spine's numbers exist in exactly four places (`bfo_stack_ontology.json`, its SQLite copy, one TypeScript fork, and prose) and its own file already breaks the numbering twice — with the `RO` pseudo-layer and the undeclared `ANATOMY`. It is not really a number line; naming it admits that.
- Named stages resolve `ANATOMY` for free: it becomes `spine:anatomy`, a declared peer, instead of an orphan value with no `title`, `bfo`, or `ontologies`.
- `S-` is not available as a replacement prefix: `S-0…S-8` already names the digestion stages (`biology_as_code/src/biology_as_code/machines/data/schemas/score-axes.catalog.json`, `nutri-collective/src/lib/giJourneyModel.ts`), and `L-1`/`C-6`/`L-FAT-1`/`HP-1` already name law hints (*(private) playground law hints*, `biology_as_code/src/biology_as_code/bridge/bridge_engine.py:171-183`). Numbered prefixes are exhausted.

**Files that must change to land it:** `nutri-collective/backend/bfo_stack_ontology.json` (the `layers` keys and all 51 `terms[].obo_layer`), `nutri-collective/backend/principles.json` (94 embedded terms), `nutri-collective/scripts/seed_mechanism_ontology_db.py` (writes the DB column), `nutri-collective/backend/principles.py:131` (`by_layer` histogram), `nutri-collective/benchmark/evidence.py:44-46`, `biology_as_code/schemas/claim_audit.schema.json:21-34`, `nutri-collective/fim-evidence-tool/src/lib/ontology.ts`, `nutri-collective/src/components/analysis/OboStackDesign.tsx`.

---

## 3. Object types

Only types with real instance backing. `spine:` values use the §2 renaming.

| Type | Identifier namespace | Authoritative source file | Key properties | Spine position |
|---|---|---|---|---|
| `OntologyTerm` | CURIE (uppercase in this file; FDP-1 uses lowercase) | `nutri-collective/backend/bfo_stack_ontology.json` | `curie, label, source, obo_layer, iri` (+ opt. `stack_node, in_demo_stack, notes, priority`) — 51 records | the spine catalogue itself |
| `Concept` (controlled vocab) | `factor-*` / `outcome-*` | `nutri-collective/evidence-platform/site/nutrition-vocab.v1.json` | `pref_label, alt_labels[], hidden_labels[], broader, source, scheme` — 118 concepts | not on the spine — the layer beneath it |
| `Food` (organism) | `node_id` + `FOODON:` + `NCBITaxon:` | `book/food-taxonomy/out/atlas_all_named.jsonl` (schema `book/food-taxonomy/food_node.schema.json`) | `commonName, taxonomy{kingdom…species}, map_status, fdc_id, foodon_id, ncbi_taxid, composition` — 8,133 records, 5,351 with FOODON | `spine:food` (partial) |
| `Nutrient` (group / species / aggregate) | `nutrient:<slug>` + `ontology.primary` CHEBI | `book/nutrient-taxonomy/v2/nutrient-node.v2.json`; instance `book/nutrient-taxonomy/v2/folate.group.json` | `node_kind, invariants{carries_lawhood, carries_relationships}, dri_key, ontology.primary, essentiality[]` | `spine:compound` — **instance count uncertain**; only the folate group node was opened |
| `Metabolite` | VMH abbreviation | `biology_as_code/MASTER_CROSSWALK.tsv` (canonical per `CROSSWALK-CANONICAL.md`) | `vmh, name, formula, hmdb, kegg, chebi, pubchem, seed, term_id` — 2,797 rows; `inchiKey` **0/2,797** | `spine:compound` |
| `NutrientRegisterItem` | bare slug (`ala`, `calcium`) | `nutri-collective/evidence-platform/site/nutrient-register.v1.json` | `i, n, k, t, f, s, d, rn, rv, ru, rt` — 169 items, **zero external ids**, in no crosswalk namespace | not on the spine |
| `DigestiveNode` | `comp.*/enz.*/trans.*/horm.*` + `ontology.primary` | `book/digestive-taxonomy/out/digestive_atlas.jsonl` | `ontology.primary, within, parent_id, cargo[]` — 147 nodes, 147 with a primary curie (UBERON 62, GO 24, HGNC 19, CL 15, UniProtKB 13, CHEBI 12, local 2) | `spine:anatomy` |
| `Principle` | slug | `nutri-collective/backend/principles.json` | `pathway, statement, systems[], nutrient_ids[], law_ids[], pillars[], kind, ontology{mapped, method, terms[]}` — 26, all 10 fields present | spans `spine:compound → mechanism → physiology` |
| `Claim` (product) | slug | `nutri-collective/backend/claims.json` | `factor, outcome{id,label,query}, direction, grade, verdict, system, pillars` — 123, 37 distinct outcome ids, **zero OBO curies** | not on the spine |
| `Value` (FDP-1) | composite `(nutrient_ref, source_ref)` | `fdp-1/validator/validate_fdp.py` (`VALUE_FIELDS`) + `fdp-1/FDP-1-food-data-provenance.md` §2 | `nutrient_ref, value, unit, source, source_ref, method, retrieved` — all seven enforced as a unit | `spine:compound` |
| `Exposure` (EDP-1) | composite `(exposure_ref, instrument_ref)`, document-scoped | `edp-1/validator/validate_edp.py` (`EXPOSURE_FIELDS`) | `exposure_ref, instrument, instrument_ref, attenuation, composition_ref, ascertainment, ascertained` | `spine:food` / `spine:compound` (`foodon` prefix accepted) |
| `EdpClaim` | `source#locus` | `edp-1/validator/validate_edp.py` (`CLAIM_FIELDS`) | `claim_id, outcome_ref, effect, exposures[], model_published, specification, evidence_grade` (computed) | `spine:outcome` by intent; unpopulated in practice |
| `Law` | `LAW-001…LAW-047` | `biology_as_code/src/biology_as_code/engine/data/all_laws_system_bound.json` (47) + `textbook_to_code_laws.json` (42) | `system, law, gate, bound, relation, related` — two registers, one id space, different field vocabularies | not on the spine |
| `Machine` | `stage.*` / `lens.*` / `process.*` | `biology_as_code/src/biology_as_code/machines/data/_schema/machine.schema.json` + `.../data/registry.json` | `kind, id, version, revision, title, status, updated, startAt, states{}` | not on the spine |
| `HostState` | **none — no id property** | `biology_as_code/src/biology_as_code/machines/data/schemas/HostState.schema.json` | 24 properties, `additionalProperties: false`, `required: ["ready"]`, four `["number","null"]` fields | not on the spine — value object, not an entity |
| `PathwayGraph` | pack directory id | `biology_as_code/src/biology_as_code/pathways/packs/*/graph.json` (40 packs, 322 nodes, 292 edges) | nodes `{id, kind, label, compartment}`; edges `{from, to, enzyme, cofactors, yields, mechanism_id}` — **no CURIEs anywhere** | `spine:mechanism`, unkeyed |
| `Contribution` | `contrib.*` | `biology_as_code/schemas/contribution.schema.json` | `id, type, target{kind, ref}, payload`; `strength` 0–5 and `signoffs` review-assigned | not on the spine — write path |
| `CrosswalkNode` | `namespace.local` + `curie` side field | `nutri-collective/evidence-platform/site/id-crosswalk.v1.json` | `id, namespace, curie` \| `cas_number` — 1,285 nodes over 9 namespaces; 364 carry a curie, all `cdno:` | `spine:compound` for cdno/fdc/infoods only |
| `SurfaceClaim` / `StudyUnit` | `SC-*` / `SU-*` | `nutri-collective/agents/claims_agent/study-claim-pipeline/schemas/surface_claim.schema.json`, `study_unit.schema.json` | SC: `atoms[], verb_class, join, court`; SU: `kingdom, role_vs_law, carries_lawhood: const false` — 14 + 12 gold instances | not on the spine |
| `Study` (MI-Nutrition) | `^(pmid\|doi\|preprint\|nct\|isrctn):` | `nutri-collective/evidence-platform/site/mi-nutrition-v0.1.schema.json` | 8 required members over an 18-field `x-mi-field` checklist | **zero conforming instances** — schema + template only. Exclude from v0 |

Deliberately excluded for lack of backing: `Outcome` as an ontology-keyed type (0 MONDO ids in production), `Ingredient` as a substance type (`id-crosswalk` shows 10 CAS numbers each carrying two ingredient slugs, including typo pairs `ethoxyquin`/`ethyoxyquin`), `Protein`/`Enzyme` as entities (0 `PR:` and 0 `NCIT:` curies anywhere in the tree).

---

### 3a. Governance objects (added 2026-09-03)

The spine types above are what the biology is *about*. These are the objects the project uses to govern its own claims about standardization: what is adopted, by whom, what was captured, what was predicted, what was decided. Each is grounded the same way — the properties are the fields the register carries — and none is on the spine.

| Object type | Identity | Register | Properties on disk | Note |
|---|---|---|---|---|
| `Standard` | catalog slug | `nutri-collective/evidence-platform/site/standards-catalog.v1.json` `entries[]` | `id, name, kind, origin, status, what_it_covers, id_format, license, access, crosswalks, how_to_adopt` | four rows are this project's own proposals, flagged by `origin` |
| `Organization` | the adopter name, verbatim | `adoption-tracker.v1.json` `rows[].adopter` | `name, type, is_target` | observed only through the rows that name it; there is no organization table and the manifest does not invent one |
| `AdoptionEvent` | (row, date) | `adoption-tracker.v1.json` `rows[].history[]` | `stage, date, note` | one dated stage change; the tracker's rule is that every change is appended when it happens — three rows (R03–R05) predate that rule and have none |
| `TrackedSubject` | `kind.key` slug | `nutri-collective/predictor_ledger/standardization-ledger.v1.json` `tracked[]` | `id, kind, ref, label, why` | a ref that must resolve to a register row on disk — 72 subjects on 2026-09-03 |
| `CapturedEvent` | `ev-<date>-<slug>` | same file, `events[]` | `id, on, captured_on, captured_by, kind, organization, subjects, what, evidence, effect, resolves_predictions` | dated twice, evidenced, append-only; an effect on a tracker row must match a `history[]` entry there |
| `Prediction` | `P-<date>-<slug>` | same file, `predictions[]` | `id, subject, type, status, made_on, proposed_by, signed_on, claim, metric, baseline, expected, resolves_by / resolves_when, falsifies_if, probability, condition, derived_from, public_record, resolved` | implements `Falsifiable`; never a person, a prize or a judgment score; an open row past its date fails the build |
| `Decision` | `<lane>-<slug>` | `nutri-collective/decisions/decision-ledger.v1.json` `decisions[]` | `id, lane, date, status, knob, knob_kind, held_fixed, observation, predicted, measured, assessment, verdict, checks` | one knob per row; the memory of a control loop run by hand |

`Falsifiable` is the one new interface: `claim`, `falsifies_if`, `resolves_by`, `made_on`. `Decision.predicted` is prose and does not implement it; that is a fact about the decision ledger, not a defect to fix here.

## 4. Link types

| From | To | Via (file) | Object-backed? | Why |
|---|---|---|---|---|
| `Principle` | `OntologyTerm` | `nutri-collective/backend/principles.json` `ontology.terms[]`; `backend/mechanism_ontology.db` `principle_mechanism(principle_id, curie)` | **must become yes** | Today it is an untyped bag of mixed-spine curies — 94 links with no predicate column. A predicate must live on the link |
| `Principle` | `Law` | `nutri-collective/backend/principles.json` `law_ids[]` → `backend/claims.json` ids | no | Plain reference; 7 of 26 populated, all resolve. n:1, so the reverse accessor returns a list (`backend/principles.py for_law`) |
| `OntologyTerm` | `StackNode` | `bfo_stack_ontology.json` `terms[].stack_node` → `NODES` in `nutri-collective/src/components/analysis/OboStackDesign.tsx` | **yes** | Many-to-one (3 L3 terms → `go-mf-resolvin`), and the node carries its own presentation label that differs from the term's (`FOODON:03312087` is "salmon (raw)" in the catalog, "Atlantic salmon (cooked)" in the node). Also: the target exists only in TypeScript |
| `StackNode` | `StackNode` (causal) | `OboStackDesign.tsx` `EDGES` (10) | **yes** | `{relation: RoRelation{curie, label, family}, strengths: EdgeStrength[]}`. Strength is per (edge, outcome), never a scalar. `family` exists in no JSON. `RO:0002327` is bound to two named relations (`enables`, `catalyzes`), so relation identity is the local key, not the curie |
| `Nutrient` | `Nutrient` \| `Outcome` \| `Protein` | `book/nutrient-taxonomy/v2/nutrient-edge.v2.json` (5 instances) | **yes** | 16 predicates with `allOf`/`if-then` conditional payloads — `CONVERTS_TO` requires `conversion`, `INHIBITS` requires `interaction`, `DEFICIENCY_CAUSES` requires `clinical`. The payload cannot exist off the link |
| `Nutrient` | `Mechanism` (chain) | `book/nutrient-taxonomy/chain_relations.json` (6) | **yes** | n-ary and role-bearing: `partners[]` each with their own `ro_role`, plus `acts_on`, `chain_span`, `magnitude`, `endpoint`, `durability`, `verdict`, `source`. The reference shape for a real relation in this repo |
| `Nutrient` | anything | `book/nutrient-taxonomy/out/chain_edges.jsonl` (58) | **no — do not model** | The `ro` field is stamped at build time from the layer pair (`build_nutrient_atlas.py:169-178`, guard `if e.get("ro"): continue` never fires). 40 rows assert `RO:0002411 causally_upstream_of` that nobody curated |
| `Id` | `Id` (identity) | `nutri-collective/evidence-platform/site/id-crosswalk.v1.json` (873 edges) | **yes** | `{from, to, kind, strength, via}` + optional `ambiguous` on 125 edges. Ambiguity resolution and provenance have nowhere else to live. Kinds are local slugs (`same_nutrient` 642, `same_substance` 137, `same_disease` 51, `aligns_with` 43) — **not** `owl:sameAs`; mapping all four onto sameAs asserts 43 identities the data denies |
| `Nutrient` | `Metabolite` | `biology_as_code/MASTER_CROSSWALK.tsv` | no | But **no loader exists** — the only readers are its generator and `tools/see.py`. And there is no `cdno→chebi` table anywhere, so from a conforming FDP-1 `cdno:` ref this join is unreachable; only the non-preferred `chebi:` fallback path reaches it, and `chebi:26195` from FDP-1's own worked example has no row |
| `Score` | `Value` | `fdp-1/validator/validate_fdp.py` `check_score()` — `inputs[]` resolved by `(nutrient_ref, source_ref)` | no | Generic resolved-reference. Within-document only; neither validator resolves across files |
| `EdpClaim` | `Exposure` | `edp-1/validator/validate_edp.py` `check_claim()` — `exposures[]` by `(exposure_ref, instrument_ref)` | no | Same shape as the row above; one base type covers both specs |
| `Exposure` | FDP-1 declaration | `edp-1` `exposure.fdp1 {declaration, grade, note}` | **yes** | The cross-spec seam. The validator reads only `fdp1.grade` and never dereferences `fdp1.declaration` — so the object carries a denormalised grade plus prose about why |
| `Atom` | `StudyUnit` | `surface_claim.schema.json` `atoms[].linked_study_unit_ids` + claim-level `join {join_type, fair_restatement, note}` | **yes, and currently mis-attached** | The join is one per claim but the edges are per atom, which forces `join_type: "mixed"` on 2 of 14 gold claims. `validate.py` only resolves `cited_study_unit_ids`, never `atoms[].linked_study_unit_ids` — two parallel edge sets, one validated |
| `Law` \| `Claim` | `Source` | `biology_as_code/src/biology_as_code/graph/schema.sql` (`EVIDENCED_BY`, `CITES`) + `graph/build.py` | **yes — already is** | `Contribution` is a first-class node label carrying `type, contributor, submitted, strength, signoffs, asserts_magnitude`. Reference implementation. Two defects: `build.py:184-192` duplicates `strength`/`asserts_magnitude` onto the edge, and only `target.kind == "law"` materialises an edge — the other five kinds get `target_kind`/`target_ref` as node props instead |
| `Ingredient` | `RestrictionList` | `nutri-collective/evidence-platform/site/ingredient-lists.v1.json` — `sets[]` + `as_listed{}` + `scope_note{}` keyed by set id | **yes** | The verbatim listed name and the scope note are per-edge facts, currently held in three parallel structures kept in sync by convention |
| `Disease` | `Cause` | `nutri-collective/evidence-platform/site/disease-causes.v1.json` — nested `causes[]` | **yes** | 65 cause rows over 40 distinct ids; 12 recur across diseases. It is a graph stored as a forest — normalise or duplicate `adiposity` per disease |
| `DigestiveNode` | cargo | `book/digestive-taxonomy/out/digestive_atlas.jsonl` `cargo[]` | **no — model as unresolved labels** | 73 distinct values, **zero** resolve to a node id; free text (`Fe2+`, `CCK`, `ApoB-48`). The schema hedges: *"labels or CHEBI"* |
| `Food` | `Nutrient` (composition) | `book/food-taxonomy/out/atlas_whole_foods.jsonl` `composition{}` | no | Keyed by USDA nutrient **display names** ("Cryptoxanthin, beta"). Label join, not identifier join. Must route through `id-crosswalk` or be typed as label-keyed and said so |
| `ScoreAxes` | `Machine` stage | `biology_as_code/.../schemas/ScoreAxes.schema.json` `process_hooks[].stage_id`, `digest_run_fields[]` | no | Three link mechanisms in one family — inline `$ref`, id reference, and stringly-typed dotted `MachineContext` paths. Only the first two are checkable |

---

## 5. The four design principles applied

**Domain-driven design — instance found.** `fdp-1/FDP-1-food-data-provenance.md` §2: *"`method` is not optional decoration"* — AOAC 985.29 / 991.43 / 2011.25 yield systematically different fibre values, so *"a fibre value without a method is not comparable to another fibre value."* That domain fact is encoded as a type: `VALUE_FIELDS` in `fdp-1/validator/validate_fdp.py` enforces all seven fields as a unit, so the number is never legal on its own. The ubiquitous language became a struct. The counter-example in the same project shows what its absence costs: `nutri-collective/evidence-platform/site/nutrient-register.v1.json` puts reference intake in three sibling keys `rv/ru/rt` on 44 items and free-text `rn` prose on 123 others, mixing genuine NONE ("caffeine": "Not a nutrient") with genuine OPEN ("boron": "No RDA/AI/UL established…") in one string field.

**Don't repeat yourself — violated, with a named instance, including by the SDK's own seed.** `GRADE_RANK = {"A":4,"B":3,"C":2,"D":1,"—":0}` plus `weakest_link()` exists byte-identically three times: `fdp-1/validator/validate_fdp.py`, `edp-1/validator/validate_edp.py`, and `biology_as_code/ontology-sdk/declared.py`. DESIGN.md's own rule is *"wrap, never reimplement"*; `declared.py` breaks it. A positive instance exists too and is the pattern to copy: `nutri-collective/benchmark/nutrition_mcp_server.py` states *"3 reference validators imported, never reimplemented"* and `nutri-collective/benchmark/vendored/cdno-xref.pinned.tsv` is a pinned copy carrying a five-line provenance header naming its source path, CDNO release (2026-06-10), vendoring date and cell semantics — a copy managed as a copy rather than forked.

**Open–closed — instance found, failing by fork.** `nutri-collective/fim-evidence-tool/src/lib/ontology.ts` is a hand-copy of the 51-term catalog that adds an **eighth layer** `R05` "Undefined register", ontologies `[FDA, USDA, DGA]`, bfo "Operative federal term — not an OBO class". A downstream consumer needed to extend the layer set, could not, and forked the whole vocabulary — also renaming `obo_layer`→`layer`, `in_demo_stack`→`demo`, dropping `iri`, and shortening every layer title. No build step generates it. The positive instance is `book/nutrient-taxonomy/v2/nutrient-edge.v2.json`: eight `allOf`/`if-then` blocks mean a new predicate arrives with its own required payload without touching any existing predicate's rules — open for extension, closed for modification.

**Producer extends / consumer supers — both directions found.** Producer-extends works in `nutri-collective/evidence-platform/site/id-crosswalk.v1.json`: 748 of 873 edges are the base five-key shape and 125 carry an added sixth `ambiguous` field, so consumers that ignore it still function. It fails on the consumer side in three places. `surface_claim.schema.json` `court.verdict` is `[Busted, Plausible, Confirmed]` — a **narrowing** of `biology_as_code/schemas/claim_audit.schema.json`'s five, so `UNEVALUABLE` and `REFUSE` (the auditor's dominant outputs; its docstring says 41 of 47 packets must land on `UNEVALUABLE`) have no representable value downstream. The same file narrows `integrity` from four values to three by dropping `unknown`. And the `honesty` enum is forked five ways inside one directory: `HostState` `{FLOW, UNITS, OPEN}`, `IngestionEvent.derived` `{FLOW, OPEN}`, `ScoreAxes` `{FLOW, OPEN}` while its own `AxisResult` is `{FLOW, OPEN, UNITS}` — consumers narrowing the producer's set, with different defaults.

---

## 6. Which Foundry features earn a place

**Structs — yes, load-bearing.** This is the feature the repo cannot do without. `Value` is 7 fields enforced as a unit (`validate_fdp.py VALUE_FIELDS`). `attenuation` is `{coefficient, statistic, reference, population, citation}` with its own conformance rule — a coefficient without a citation is non-conforming (`validate_edp.py check_attenuation`). `paf` is `{value, lo, hi, cite}` (`disease-causes.v1.json`). `status_date` is `{value, precision, text}` and `presence` is `{value, basis, share, denominator, measured_on, method}` (`adoption-tracker.v1.json`). `verified {source, first_author, year, title, journal}` beside `citation_as_given` and `citation_corrected` (`evidence-platform/src/verify_citations.py:186-196`). A generated accessor returning bare `float` for `.iron` is non-conforming to the spec this project wrote.

**Struct main fields — yes, but opt-in per struct and explicitly refusable.** Earns its place on `attenuation`: `validate_edp.py` requires a `coefficient` (or `OPEN`), so the struct sorts and renders by it. Must be **refused** on the FDP-1 value struct, because FDP-1 §2 says a value without its method is not comparable — a blanket main-field affordance reintroduces exactly the bug the spec exists to prevent. So: a per-struct declaration, never a default, with "refused" as a legal setting.

**Derived properties — yes, but they must return a trace, not a value.** Three live cases. FDP-1's `provenance_grade` is specified *"Computed, not asserted"* and `check_score()` recomputes it and fails on disagreement. EDP-1 goes further: `grade_document()` writes `evidence_grade` **and** `grade_layers` in place *"so a producer never has to reimplement the weakest-link computation"*. MI-Nutrition declares its own derived block in-schema: `conformance` is *"Emitted by the validator, not by the author"* with `required_fields_present` 0–14, `level` none|core|full, `missing[]`. And `edp-1/examples/fibre-two-instruments.json` already ships `grade_trace {instrument, composition_fdp1, specification, weakest, why}` — a derived property that carries its inputs and a reason. That is stronger than Foundry's version and it is the shape the SDK should adopt. Caveat: `grade_trace` (example) and `grade_layers` (harness output) are two incompatible shapes for one concept, neither validated.

**Object-backed link types — yes, and one already exists.** `Contribution` in `biology_as_code/src/biology_as_code/graph/schema.sql` is the reference case: a node label sitting between a Law and a Source, carrying type, contributor, submitted, strength, signoffs. Three more links need it and do not have it: `EdgeStrength[]` (per-outcome grade on a causal edge), `exposure.fdp1` (the FDP-1↔EDP-1 seam), and `surface_claim.join` (currently on the claim, needs to be on the atom→study-unit edge, where "the join IS the object" per `study-claim-pipeline/README.md:12`).

**Interfaces — yes, but declared in the manifest, never discovered structurally.** Two implicit interfaces exist. `Validatable`: `nutri-collective/benchmark/nc_standards.py validate_study_record()` branches on four strings and loads each validator by filesystem path via `NC_FDP1_DIR`/`NC_EDP1_DIR`. `Citable`: five registers carry `landmark[]`, and `nutri-collective/evidence-platform/Makefile:66-72` enumerates seven `(register, items-key)` pairs by hand because nothing declares the interface. Structural sniffing is unsafe here: `disease-causes.v1.json` uses `landmark` as a **boolean**, so iterating it as a citation array raises. `evidence-platform/tests/test_register_conformance.py` is already a structural stand-in — its docstring says *"it contains no register names"* on purpose — and it documents the cost: two schema generations coexist (`schema_version`/`as_of` vs `version`/`generated`) because nothing declares which shape a register implements.

**Reducers — no, not as a general facility.** Three places in the repo explicitly forbid reducing a specific multi-valued property: FDP-1 §3.1 bans averaging provenance; `processing-definitions.v1.json` `meta.framing` says *"Lanes are never pooled across instruments"*; `id-crosswalk.v1.json` emits all ambiguous candidates with `ambiguous: true` and states *"consumers must never silently pick one"*. A default `first`/`any` reducer produces exactly those three failures. Ship instead **two named, opted-in reduced properties** and nothing generic: `weakest_link` (which collapses three duplicate implementations) and `Law.best_strength` (already `COALESCE(MAX(e.strength), 0)` in `graph/schema.sql`'s `v_law_evidence` view). One further candidate is genuinely waiting: `adoption-tracker.v1.json`'s top-level `stage` equals the latest `history[]` entry on all 21 rows, maintained by hand with no test — but it needs a declared tiebreak (latest date, or max `stages[].rank`) before it becomes a reducer rather than a guess.

**Also refuse** (already triaged at `DESIGN.md:220-236`, and nothing found here changes it): the Ontology Engine, Data Services, Workflow Services, Automations, writeback, access control, and object views. `WHERE-THIS-FITS.md:124` is right that the evidence hub is a presentation layer and must not be modelled into the ontology.

---

## 7. Taxonomy vs ontology, honestly

**Artifacts wearing the word "ontology" that contain no typed relations:**

| Artifact | What it actually is |
|---|---|
| `book/laws_nutrution_ontology/` | 6 PDF book exports + a `package-lock.json` + 60 MB of `node_modules` + 13 empty directories. The project's own inventory bills it as its largest ontology area with **0** ontology files (`book/ONTOLOGY-CONSOLIDATION.md`, generated by `book/ontology_inventory.py`) |
| `nutri-collective/backend/bfo_stack_ontology.json` | 51 flat term records. Zero edge-shaped keys (`subject`/`object`/`predicate`/`from`/`to`/`domain`/`range` all absent). A layered term catalogue — a faceted taxonomy |
| `nutri-collective/backend/mechanism_ontology.db` | Three tables. The join is `(principle_id, curie)` with no predicate column; 8 RO rows sit in `mechanism_term` and 0 rows in `principle_mechanism` reference one. A tag cloud |
| `nutri-collective/fim-evidence-tool/src/lib/ontology.ts` | A hand-copy of the term list with renamed fields, a dropped `iri`, and a forked eighth layer. No edge array |
| `book/terminology-mapping/biomarker_ontology.jsonl` | 30 flat rows, **no curies of any kind**. Its two relation-shaped fields (`synergies`, `inhibitors`) hold 130 targets of which **0** resolve to a `bm.*` id |
| *(private) book taxonomy joins* | Prose suggestions keyed `[concept, book_pages, why_it_matters, suggested_use]` |

**Honestly-named taxonomies** (these are fine, and two are the best-populated data in the tree): `book/food-taxonomy/` (8,133 Linnaean records with a first-class `map_status` enum and the rule *"Never invent family for leftovers — keep UNMAPPED"*), `book/digestive-taxonomy/` containment (147/147 nodes with a primary curie, 26 of 27 `within`/`parent_id` refs resolving), `nutrient-taxonomy` v1 `class`/`family` facets, and `book/digestive-taxonomy/taxonomy2.{5,6,7,8}.json` — which is not a digestive taxonomy at all but a 638-string topics glossary, where 2.5 and 2.8 are byte-identical (md5 `a3cdf8f5b5dc8c3adfbf5414c41d9ead`) and the file named 2.5 declares `"version": "2.8"` inside.

**Where typed relations genuinely exist:**

| Artifact | Shape | Instances |
|---|---|---|
| `biology_as_code/schemas/aca.ttl` | The only OWL in the tree: 8 `owl:ObjectProperty` with `rdfs:domain`/`rdfs:range`, an attack subclass hierarchy, `owl:NamedIndividual` value sets | **0** — T-box with no A-box. Nothing in the repo emits `aca:` triples into a data file. Worse, the JSON-LD emitter (`agents/assay/schema.py:239,263`) writes `aca:verdict`, which `aca.ttl` does not declare (it declares `aca:hasVerdict`) |
| `nutri-collective/evidence-platform/src/mechanism_schema.py` | **The strongest relation model in the repo.** 9 `EntityKind` × 11 `Relation` with a `COMPAT` domain/range matrix that is *executed* (the M1 gate FAILs on an illegal subject-kind→object-kind), plus `EVIDENCE_WEIGHT`, `RELATION_SIGN` for chain arithmetic, and `CAUSAL_RELATIONS` | 26 shipped (`site/data/core.json`) — **and all 26 fail the gate in the same repo.** `build_platform_data.py:280-297` hardcodes `relation="MEDIATES"`, `evidence_class="CITED"`, `status="SUPPORTED"` for all 26 principles; `COMPAT[MEDIATES] = ({BIOMARKER, PROCESS} → {DISEASE})`, and the object is a free-text pathway label |
| `book/nutrient-taxonomy/v2/nutrient-edge.v2.json` | 16 predicates with mandatory conditional payloads. Its own text: *"The predicate carries the epistemic class — it is NOT a sub-field"*, naming v1's failure (`outcomes_mondo: ["MONDO:0004641"]` could not say whether B12 causes, diagnoses or treats) | 5 |
| `book/claim-language/claim_verbs.json` | 88 surface verbs → 9 classes → 15 `RelationType`s, each class mapped to an `ro_primary` and a default evidence tier. Mandatory per `book/taxonomies/README.md` rule 4 | 0 — vocabulary only |
| `book/nutrient-taxonomy/chain_relations.json` | n-ary, role-bearing, dual-grounded (local type + RO), with `partners[]` each carrying their own `ro_role` | 6 |
| `nutri-collective/evidence-platform/site/id-crosswalk.v1.json` | `{from, to, kind, strength, via}` + optional `ambiguous`; the only place in the tree where link provenance is a first-class field | **873** — but all four kinds are *identity*, never biology |
| `nutri-collective/src/components/analysis/OboStackDesign.tsx` | RO-typed causal edges with per-outcome `EdgeStrength[]` | 10, fixtures, no fetch/api call in 1,272 lines |
| *(private) graph schema* | 8 node labels × 10 `EdgeTypeSpec` where `from`/`to` **are** domain and range, plus openCypher DDL with edge properties | schema; a private anabolic graph carries 14 typed instances, a private digestion map 8 |
| `biology_as_code/src/biology_as_code/pathways/packs/*/graph.json` | 40 packs, 322 nodes, **292 edges** — the largest biological edge set in the tree | 292, but the predicate is *implicit* (substrate→product catalysed by a free-text `enzyme` name) and there are zero CURIEs |

**Semantics / reasoning: none.** The whole tree contains exactly four `.ttl`/`.owl`/`.obo` files (`aca.ttl`, `claim-shape.ttl`, and identical copies of both under `nutri-collective/agents/claims_agent/claims-agent/`), and no `rdflib`, `pyshacl`, `owlready` or `owlrl` anywhere outside prose. `claim-shape.ttl` calls for itself to be run *"in the pipeline BEFORE publish"*; no runner exists, and if it were run it would fail on the emitter's own output.

**The honest population count for typed relation instances is roughly 900 identity edges plus under 400 biological ones, spread across at least seven predicate vocabularies that share no members.** That is what the SDK inherits: a rich, well-populated taxonomy sitting on top of a nearly empty and badly forked relation store.

---

## 8. Blockers, ordered

> **Status 2026-08-29: blockers 1 and 2 are LANDED.** The spine is named
> (`spine:food … spine:outcome`, plus off-ladder `spine:anatomy`), the field is
> `spine_stage`, and `nutri-collective/scripts/migrate_spine_naming.py --check`
> gates it. 51 spine terms, 94 embedded principle terms, 160 SQLite rows, both
> TypeScript apps typechecking clean, both Python suites green.
> **Blocker 3 is half done** — RO now carries `role: "predicate"` and
> `spine_stage: "NONE"`, and the file declares a `relations` block; the DB
> predicate column is still missing.
> **One exception is declared, not fixed:** the claim auditor's `l1_to_l5` still
> uses causal L-numbers across 6 files. Renaming it reaches the audit engine, its
> tests and notebooks, and terminology already printed in the book draft — that is
> an editorial call, so it is ratcheted at 6 files rather than done silently.
> **Status 2026-09-03: blocker 4 is LANDED.** The base is `mechanism_schema.py`'s 11 relations, and
> `ontology-sdk/relation-crosswalk.v1.json` maps all six other vocabularies onto it, verb by verb.


Each names the file that has to change. Blockers 1–4 must clear before a manifest can be *generated*; 5–8 before it can be *published*.

**1 · ~~The layer naming collision.~~ LANDED 2026-08-29.** Nothing can be typed while `L3` means two things. → `nutri-collective/backend/bfo_stack_ontology.json` (adopt §2's `spine:` names in `layers` and all 51 `terms[].obo_layer`). Cascades that must land in the same change: `nutri-collective/backend/principles.json` (94 embedded terms), `nutri-collective/scripts/seed_mechanism_ontology_db.py`, `nutri-collective/benchmark/evidence.py:44-46`, `biology_as_code/schemas/claim_audit.schema.json:21-34`, `nutri-collective/fim-evidence-tool/src/lib/ontology.ts`.

**2 · ~~`ANATOMY` is an undeclared layer value.~~ LANDED — it is now `spine:anatomy`, a declared peer with a title, ontologies and a note.** Three of 51 terms carry it; the `layers` map has no key for it, so the file cannot validate against itself. → `nutri-collective/backend/bfo_stack_ontology.json` (add the entry, or retire the value onto the three UBERON/GO:CC terms as a separate `context` property — the `fim-evidence-tool` fork already promoted it to a real layer, so downstream has already voted).

**3 · RO is stored as terms, not as predicates.** *(Half done: `role`/`spine_stage:NONE` and a `relations` block landed; the DB predicate column has not.)* Until the 8 relation rows leave `terms[]`, "predicate" and "class" are one type and no link accessor can be generated. → `nutri-collective/backend/bfo_stack_ontology.json` (lift the 8 RO rows into a sibling `relations` block with domain/range), and `nutri-collective/scripts/seed_mechanism_ontology_db.py` + the `principle_mechanism` DDL (add a predicate column).

**4 · ~~Pick one predicate vocabulary.~~ LANDED 2026-09-03.** Five candidates, none a subset of another: `book/claim-language/claim_verbs.json` (15 RelationTypes with RO mappings), `book/nutrient-taxonomy/v2/nutrient-edge.v2.json` (16 with conditional payloads), `nutri-collective/evidence-platform/src/mechanism_schema.py` (11 with an **executed** domain/range matrix), `id-crosswalk` kinds (4, identity only), `biology_as_code/schemas/relation_enums.subset.json` (8, self-declared as a public subset). Plus two undeclared sets in `book/taxonomies/joins/*` that already drifted between sibling files. → The decision belongs in `biology_as_code/schemas/relation_enums.subset.json`'s upstream (the full list its header points to). Recommendation: `mechanism_schema.py` is the only one with an enforced domain/range and should be the base; `claim_verbs.json` maps onto it as the claim-language projection. **Uncertain** whether `nutrient-edge.v2`'s 16 can be expressed in 11 — that needs a mapping pass, not an assertion.

> *Landed 2026-09-03:* the base is `mechanism_schema.py`'s 11, declared in `ontology-sdk/ontology.json`. The mapping pass is `ontology-sdk/relation-crosswalk.v1.json`: 63 rows over six vocabularies (the sixth, `engine.laws.models.RelationType`, this list had not named — it has 9 members, and the published subset's header pointed at `claim_verbs.json`, whose 15 do not contain CONSERVES or IDENTITY). The uncertain question is answered: nutrient-edge.v2's 16 are 6 direct, 8 by expansion over a reified node, 2 not expressible (VITAMER_OF, PARTICIPATES_IN). What the base cannot carry is now a list in the register's `gaps` block, and `check_manifest.py` re-reads every source vocabulary that is beside this repo. Nothing is retired: each vocabulary keeps its job.

**5 · The name collisions that would land two things under one key.** `verdict` is three enums (`biology_as_code/docs/constitution.md`, `biology_as_code/schemas/claim_audit.schema.json`, `nutri-collective/agents/claims_agent/assay/schema.py`) and `Verdict` is three Python bindings. `kingdom` is four disjoint enums (`claim_audit.schema.json`, `study_unit.schema.json`, `surface_claim.schema.json`, `biology_as_code/src/biology_as_code/bridge/bridge_engine.py`'s `K1…K_end`). `integrity` is three (`food_packet.schema.json`, `claim_audit.schema.json`, `surface_claim.schema.json`). `unit` is four. `evidence_tier` carries two disjoint value sets in one product (`nutri-collective/backend/analytics.py:43-50` study-design labels vs `platform-data.json`'s HIGH/MODERATE/null). `G2` means two different guardrails in `docs/BUILD_PLAN.md:90` and `docs/BIZ_REFINEMENT.md:310`. → No single file; the manifest must namespace each and the SDK must never round-trip between them.

**6 · Grade is six or more scales under four words** (`grade`, `tier`, `strength`, `level`), and the `A|B|C|D` letters are used for two opposite axes: source provenance in `fdp-1/validator/validate_fdp.py:39-50`, and evidence strength on 2,798 claims in `nutri-collective/agents/claims_agent/food_health_claims_500.json`. A `Gradeable` interface is underdetermined until each gets its own type. → Same manifest change as 5.

**7 · Outcome has no ontology key, and the fix is a link, not a lookup.** `nutri-collective/backend/claims.json` carries 37 inline outcome slugs and zero MONDO; `id-crosswalk.v1.json` records `gaps.outcomes_with_mondo_ids: 0`. But `nutri-collective/working_map_nutrition/MASTER_TERMS_INDEX.json` already holds 26 MONDO ids, **4 of which label-match a spine outcome exactly** (cardiovascular-disease, iron-deficiency-anemia, vitamin-b12-deficiency, vitamin-d-deficiency). → `nutri-collective/evidence-platform/src/build_id_crosswalk.py` (its "Sources read" block does not read `MASTER_TERMS_INDEX.json` at all, which also hides GO, UBERON, HGNC, CL and UniProtKB from the only queryable resolver).

**8 · `fdc.nutrient` vs `fdc-nutrient` is a one-entry alias, and it currently breaks the round trip.** `fdp-1/validator/validate_fdp.py:28` fixes the prefix as `fdc.nutrient`; `build_id_crosswalk.py:142` mints node ids as `fdc-nutrient.{v}` because its declared scheme replaces CURIE colons with dots. `nc_standards.resolve_ontology_id("fdc.nutrient:1089")` returns `found: false`; bare `1089` and `fdc-nutrient:1089` both resolve. → `nutri-collective/benchmark/nc_standards.py` (a one-entry alias table), not a spec change.

**9 · Licensing, before anything is published.** `biology_as_code/NOTICE` has no third-party section, while `biology_as_code/MASTER_CROSSWALK.tsv` vendors VMH expression (its `fullName` labels and `chargedFormula`) that three files in this tree assess as CC BY-NC 2.0 — including `biology_as_code/docs/figures/urea-cycle.md:108-110` (*"Recon3D and the VMH data tables are CC BY-NC 2.0"*). `PATENTS.md:10` and `CITATION.cff:13` claim the crosswalk as first-party work. Three source manifests disagree with each other (`nutri-collective/data/SOURCES.md`, `evidence-platform/site/standards-catalog.v1.json`, `biology_as_code/docs/claim-sources.md` — LanguaL is "NOT an open license" in one and "open" in another). `id-crosswalk.v1.json` has no licence key. `nutri-collective` has no LICENSE file at all. → `biology_as_code/NOTICE` first, then one machine-readable manifest replacing the three.

**10 · `weakest_link` triplication.** → `biology_as_code/ontology-sdk/declared.py` is the copy to fix first, because it is the SDK's own seed breaking the SDK's own stated rule.

**11 · Two object types have no data (still live from DESIGN.md).** MI-Nutrition has zero conforming instances — running `evidence-platform/src/validate_mi_nutrition.py` on its own template yields `conformance: none (required 12/14)`, exit 1, and `grep mi_nutrition_version` hits only the schema and the template. ~~EDP-1 is undeposited with no DOI.~~ *(Deposited 2026-08-30, concept `10.5281/zenodo.22168822`; the MI-Nutrition half still holds.)* → Leave `Study` and `Exposure` out of v0; the files to change are the deposit metadata, not the schemas.

**12 · Divergent copies that will drift under a generator.** `nutri-collective/machines/registry.json` vs `biology_as_code/src/biology_as_code/machines/data/registry.json` — 3 `lens.*` ids exist only in the former, all 10 shared ids differ in hash and in status (draft vs published), and version numbers move in **opposite** directions (`stage.oral` 1.1.0/nc vs 1.0.0/bac; `process.full-digest` 1.0.0/nc vs 1.1.0/bac). `HostState.schema.json` is byte-identical in three places (md5 `2e483947b3567f80853a60231041d65f`) with no generator. → `biology_as_code/.../machines/data/registry.json` must be declared canonical the way `CROSSWALK-CANONICAL.md` did for the crosswalk.

**13 · DESIGN.md's own Status line is stale and should be corrected in the same pass.** It gates all work on a blocker that §6 of the same file already declares cleared, and `ONTOLOGY-PIPELINE.md` has since re-ordered the plan so that the controlled vocabulary — now shipped as `nutri-collective/evidence-platform/site/nutrition-vocab.v1.json` — precedes the manifest. → `biology_as_code/ontology-sdk/DESIGN.md`.