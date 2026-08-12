# Changelog

All notable changes to the **biology-as-code** Python package are documented here.

## [Unreleased]

### Nutrient nodes, absorption bounds & the nutrient-requirement edge

Four loose drafts sat in the repo root describing work the package could not
execute: two `*.node.yaml` files declaring a schema that did not exist, an
absorption seed nothing read, and two standalone Python modules. Harvested into
the package; originals moved to `../archive/biology_as_code-harvest-2026-08-01/`
with a per-file note recording what was taken and what was deliberately not.

#### Added — nutrient nodes (`nodes/`, tier EVIDENCE)

- **`schemas/nutrient-node.schema.json`** — the contract `zinc.node.yaml` and
  `glucose.node.yaml` already claimed to satisfy. Written inside the repo's
  zero-dependency validator subset (no `$ref`), so `packets/validate.py` checks it.
- **`nodes/`** — loader, `NutrientNode`, and the `rejected < candidate < prior <
  gate < bound` certification lattice with `at_least()`. Both reference nodes now
  load and validate; **52 claims, none at `bound`**, which is the correct answer
  for two nodes built entirely from secondary sources.
- `validate_node()` runs three passes: document spine, the claim-provenance
  vocabulary lifted from `$defs`, then cross-references. The third pass carries
  the real rule — a `source_ref` must always resolve, while a `parent_ref` may
  dangle *only* when the claim declares `existence_verdict: NOT_FOUND`. The zinc
  node legitimately has fourteen such unresolved parents.
- `nodes/data/{zinc,glucose}.node.yaml` now ship as package data (`zinc.node.yaml`
  moved from the repo root). Parsing needs PyYAML, added to the `dev` extra —
  core stays zero-dependency and the loaders raise a directed `ImportError`.

#### Added — fractional-absorption bounds (`nodes/bounds.py`)

- Parses the absorption seed **without flattening it**: `FractionSpec` keeps
  `">0.90"` as a lower bound rather than inventing a midpoint, and keeps calcium's
  cohort split and copper's dose-response curve intact.
- `reconcile_with_registry()` compares the sourced priors against the unsourced
  `typical_bioavailability` floats in `dig/mineral_interactions.py`. **Five
  minerals conflict** (zinc, selenium, manganese, molybdenum, fluoride), pinned by
  tests so neither side moves silently.
- **The registry floats were not overwritten.** Most conflicts are scope, not
  error — zinc absorbs at 0.70 from a 3 mg dose and 0.30 across a mixed diet, and
  both are true. Choosing which condition a default models is a modelling decision
  for a reviewed diff. The seed's own calcium `REANCHOR` flag turned out to agree
  with the code already in place.
- `absorption_prior()` and `unsourced_minerals()` on the mineral module. Iron is
  on the unsourced list, and the interaction rules lean on iron hardest.

#### Added — `requires_nutrient` edges (→ 40 graphs)

- `ReactionEdge.requires_nutrient` in `pathways/_types.py`: the micronutrient a
  step cannot run without. Every other field on the edge tracks carbon or energy;
  this is the one that tracks nutrition. Read through `edge_nutrients()`, so the
  sixteen legacy per-module edge classes are unaffected.
- `MetabolicPathway.nutrient_dependencies()` — which steps stop if a nutrient is
  short. A rendered diagram cannot answer this.
- **`pathways/micronutrient_cofactor_pathways.py`** with two graphs, the first
  module built on the shared `_types` contract:
  - `tryptophan_niacin` (Berdanier Map 6) — four PLP-dependent steps, so low B6
    lowers effective niacin. A nutrient-nutrient edge with a direction.
  - `carnitine_synthesis` (Map 25) — five micronutrient families on one linear
    chain, the cleanest argument against independent per-nutrient scoring.
- Berdanier volume question **resolved**: the running head on p. 204 confirms
  Appendix 2 belongs to the 2000 2nd edition, not Berdanier/Zempleni 2009.
- The 60:1 niacin-equivalent ratio is **not** attributed to Map 6 — it is a DRI
  convention, carried with its accession explicitly marked UNVERIFIED.

#### Added — energy as a balance (`simulation/energy_accounting.py`)

- `SCORING_GUARD`: energy has no reference intake and cannot have one, so a score
  may act on macronutrient distribution and substrate storage cost and **must not
  act on an absolute kcal target**. Plus `amdr_verdict()`, `EnergyCascade`, the
  species-specific postabsorptive clock, and the storage-cost asymmetry.
- Deliberately excludes BMR (already in `body_composition_energy.py`, with better
  equations) and RQ (already in `respiratory_quotient.py`).

#### Fixed

- `respiratory_quotient.py` compared RQ against `1.0` and `0.7` with `==`. Real
  divisions essentially never land there, so both branches were unreachable and
  ordinary fat-predominant values (0.75) fell through to "protein or mixed with
  ketogenesis". Now banded, with `substrate_mix()` that refuses to extrapolate
  outside 0.70–1.00 rather than returning a fraction outside 0–1.
- `interpretation()` read `self.rq` before computing it, so calling it directly
  interpreted the `0.0` default as a measurement.

#### Documented

- `docs/VALIDATION_LEDGER.md` — **five arithmetic errors in Berdanier Ch. 1**,
  two of which propagate into every efficiency figure in the chapter. ERR-GLU-01
  (glucose heat of combustion low by 2.27×) was caught by cross-reading two
  textbooks; neither alone would have surfaced it.
- One claim from the extraction **did not survive review**: it asserted the
  corrected model agrees with McGuire & Beerman on both storage routes. It agrees
  on de novo lipogenesis (80.5% vs 75–80%) and not on preformed fat (99.0% vs
  ~95%), because the two measure different scopes. Now stated in both the
  function and the ledger.

### Pathway graphs, mermaid packs & sources (teaching FLOW)

Numbers below are **registry pathway graphs** (each with a co-located
`pathways/packs/<id>/pathway.mermaid` after export). Mermaid is **auto-generated**
from live code — do not hand-edit topology; re-run
`scripts/export_pathway_packs.py` and `scripts/check_pathway_integration.py`.

| Milestone | Registry graphs | Mermaid packs (`pathway.mermaid`) | Mechanisms (approx.) |
|-----------|----------------:|----------------------------------:|---------------------:|
| Earlier co-located baseline | 28 | 28 | ~21 core dig/TCA set |
| + amino-acid catabolism pack | **33** | **33** | +5 AA mechanisms (~26) |
| + meal-critical Wave B1 | **37** | **37** | +9 (~35) |
| + Wave B2 (gut + haem + wire-ups) | **38** | **38** | +5 (~**40**) |

**Pack layout (source of truth for diagrams)**

- Packs live under `src/biology_as_code/pathways/packs/<pathway_id>/` next to
  Python modules (not a root `pathways/` tree). Each pack includes:
  - `pathway.mermaid` — auto flowchart from nodes/edges
  - `tests.md` — structural checklist + mechanism links
  - `README.md` — module pointer
- Index / honesty map: `packs/INDEX.md`, `packs/COVERAGE.md` (must list every
  registry graph or integration check fails).
- Gold hand extras remain only under `packs/glycolysis/glycolysis_extra/`.
- Shadow-safe: never create `pathways/<same_name_as_module>/` next to a `.py` file.

**Contributor / gate tooling**

- `docs/python/ADD_PATHWAY.md` + templates (checklist, module stub).
- `scripts/check_pathway_integration.py` — discovery ↔ packs ↔ COVERAGE ↔
  mermaid non-empty ↔ mechanism_id resolve.
- `tests/test_pathway_packs.py` — structural pack suite (graph count tracks
  registry; now **38**).
- Monorepo root (outside package install): `MAP_COG_QUEUE.md` / `.json` for
  tiered “map cogs not encyclopedia” queue; evidence leads stay OPEN (not laws).

#### Added — amino-acid catabolism (→ 33 graphs)

- Module `pathways/amino_acid_catabolism.py` with five graphs:
  - `aa_nitrogen_disposal`, `bcaa_catabolism`,
    `phenylalanine_tyrosine_catabolism`, `methionine_one_carbon`,
    `glucogenic_ketogenic_aa`
- Mechanisms: `aminotransferase`, `glutamate_dehydrogenase`, `bckdh`,
  `phenylalanine_hydroxylase`, `methionine_adenosyltransferase`
- Mermaid packs exported for all five; COVERAGE table updated.
- Tests: `tests/test_amino_acid_catabolism.py`

#### Added — meal-critical Wave B1 (→ 37 graphs)

- Module `pathways/meal_critical_pathways.py`:
  - `iron_absorption` (non-haem + hepcidin control point)
  - `cobalamin_absorption` (B12 + intrinsic factor)
  - `glucose_epithelial_transport` (SGLT1 / GLUT2 / GLUT5)
  - `scfa_colonic_production` (acetate / propionate / butyrate)
- Mechanisms: `dmt1`, `ferroportin`, `hepcidin_ferroportin`,
  `duodenal_cytochrome_b`, `intrinsic_factor`, `glut2`, `glut5`, `pept1`,
  `colonic_fermentation`
- Regulation keys in `pathway_regulation.pathway_activity_snapshot`:
  `iron_absorption`, `glucose_epithelial_transport`, `scfa_colonic_production`
- **Sources on iron path** (and related teaching refs): PMID/NCBI Gene style
  references on pathway objects (e.g. ferroportin / DMT1 / HAMP) — these show up
  as `%% Source:` lines in exported mermaid and in pack `tests.md` when present.
  Source *counts* on a graph can change when references are added or compressed;
  they are teaching provenance, not LAW-SPEC magnitudes.
- Mermaid packs for all four new ids; COVERAGE textbook table rows for iron /
  B12 / epithelial glucose / SCFA.
- Tests: `tests/test_meal_critical_pathways.py`

#### Added / changed — Wave B2 (→ 38 graphs; mechanism wire-ups)

- **New graph:** `gut_incretin_network` in `nutrient_sensing.py` (CCK, GLP-1, GIP,
  PYY → bile release, enzymes, insulin, satiety, gastric emptying). Pack:
  `packs/gut_incretin_network/pathway.mermaid`.
- **PepT1:** `protein_digestion_absorption` apical edge now
  `mechanism_id="pept1"` (re-export updates that pack’s mermaid edge labels).
- **Bile / micelle:** `lipid_digestion_absorption` edges tagged
  `bile_salt_emulsification` and `bile_salt_micelle` (mermaid edge labels change
  from free-text process-only to mechanism ids where set).
- **Methionine synthase:** `methionine_one_carbon` remethylation edges use
  `mechanism_id="methionine_synthase"` (pack mermaid + tests.md mechanism list
  grow).
- **Haem iron branch expanded** on `iron_absorption` (was one compressed stub):
  - New nodes: `heme_enterocyte` (8 nodes total on this graph)
  - New edges: dietary haem → HCP1 → HO-1 → shared Fe²⁺ pool → ferroportin
  - Mechanisms: `hcp1_heme_uptake`, `heme_oxygenase_1`
  - Pack remirror: `packs/iron_absorption/` node/edge counts **n=8 e=7** (was n=7
    e=6 before haem expansion).
- Mechanisms added this wave: `bile_salt_emulsification`, `bile_salt_micelle`,
  `methionine_synthase`, `hcp1_heme_uptake`, `heme_oxygenase_1` (**~40** total).
- Regulation: `gut_incretin_network` activity in snapshot (↑ fed vs fast).
- Tests: `tests/test_wave_b2_cogs.py` (+ existing meal-critical + pack suites).

#### Mermaid / source number changes operators should expect

When re-exporting after graph edits:

1. **`packs/INDEX.md`** total graph count ticks up with registry (now **38**).
2. **Per-pack `pathway.mermaid`**: node/edge lines and `|"mechanism_id"|` labels
   change when edges gain `mechanism_id` or topology grows (iron, protein, lipid,
   methionine packs especially).
3. **`%% Source:`** comment lines appear/change only when
   `pathway.references` is edited (iron absorption is the densest example).
4. **`packs/*/tests.md`**: “Edges with `mechanism_id`” counts rise when mechanisms
   are wired (e.g. methionine remethylation 0 → 2 linked edges).
5. **`COVERAGE.md`**: row count and textbook-gap table must stay 1:1 with
   registry or `check_pathway_integration.py` fails.

Evidence / monorepo term index work (ranked PubMed leads, `MASTER_TERMS_INDEX`,
etc.) lives at the **NUTRI-COLLECTIVE_0** root and does **not** change installed
package pathway mermaids unless a graph is promoted into `biology_as_code`.

### Evidence-layer sources — **why numbers / source fields change**

These artifacts sit at the **monorepo root** (NUTRI-COLLECTIVE_0), not inside the
installed PyPI wheel unless later vendored:

| Artifact | Role |
|----------|------|
| `MASTER_TERMS_INDEX.json` | De-duped vocabulary + optional system seats |
| `TERM_EVIDENCE_INDEX.json` | Per-term match metadata + ranked `evidence[]` leads |
| `TERM_EVIDENCE_BY_ID.json` | Compact `{ term_id → evidence[] }` |
| `TERM_EVIDENCE_LEADS_BY_ID.json` | Same, **candidate leads only** (demoted roles excluded) |
| `TERM_EVIDENCE_INDEX.md` | Human rollup of the latest rebuild |

They are **ranked leads** (`promotion.status: OPEN`), not a finished evidence
register and not LAW-SPEC citations. Counts and “sources” shift for deliberate
pipeline reasons:

#### 1. Master vocabulary rebuild (`tools/build_master_terms_index.py`)

| What you see change | Why |
|---------------------|-----|
| `stats.term_count` (e.g. 2152 → 2106; `terms_dropped_junk = 46`) | Junk filter drops markdown / capture-note debris (`**`, “re-shoot”, gap bullets). |
| `stats.terms_dropped_junk` | Explicit counter of rejected labels. |
| `sources[]` / `domain_packages[]` on a term | Merge order: encyclopedia + topics_ontology + digestive/nutrient/food catalogs + systems examples. Re-merge after any of those inputs change. |
| `system_ids` / unassigned count | Heuristic or hand seats; empty beats fake. |

#### 2. Local evidence rebuild (`tools/build_term_evidence.py`)

| What you see change | Why |
|---------------------|-----|
| `stats.terms_with_evidence` / coverage % | Match strictness: `--min-score` (default **8**), no pure weak `title_tokens`, generic-label guards, MeSH exact/prefix vs loose partial. **Stricter = lower %** on purpose (honesty). |
| `stats.local_articles` | Size of SQLite nutrition slice (`pubmed_slice.db`) loaded for ranking PMIDs. |
| `stats.mesh_topic_rows` / `approx_corpus_studies` | Docker/Postgres `mesh_topics` (or SQLite topics table) — **corpus-scale MeSH study counts**, not full PubMed world. Rebuild after `pubmed topics` or corpus ingest. |
| `evidence[].pmid` set / scores / order | Rescore after algorithm or slice changes; same term can keep fewer higher-quality leads. |
| `evidence[].term_context` | Title/abstract **window** from the local article record (how the term appears). Changes if abstracts are longer/shorter in the slice or matching phrase shifts. |
| `evidence[].match_via` | Which signals fired (`mesh_exact`, `title_phrase`, `abstract`, …). |
| `lead_role` / `demoted_lead` / LEADS file size | Study-design, model-organism, generic, method-noise labels demoted; excluded from `TERM_EVIDENCE_LEADS_BY_ID.json` so UI “strongest evidence” is not rats/RCT-method noise. |
| `corpus.note` string | Documents which SQLite path + whether Postgres/docker mesh_topics joined. |

**Why this is not “sources getting worse”:** coverage dropping after a quality pass
means fewer weak co-occurrence hits, not fewer real papers in the world.

#### 3. Live PubMed counts (`tools/enrich_term_live_counts.py`)

| What you see change | Why |
|---------------------|-----|
| `match.n_live_pubmed` | NCBI E-utilities `esearch` count for `"term"[Title/Abstract] OR "term"[MeSH Terms]` — **breadth signal only**. |
| `match.live_query` | Exact query string used (reproducibility). |
| `match.live_error` | Throttle / network / bad query; leave null, fail-closed. |
| `stats.terms_with_live_count` / `live_ncbi_calls` | How many thin terms were enriched this run (`--thin-only`, `--max N`). Partial batches → count rises over multiple runs. |
| Live count `0` vs missing | `0` = query returned zero hits; missing/`null` = not queried yet. |

Live counts **do not** replace local `evidence[]` PMIDs and **do not** prove a claim.
They only answer: “how large is the PubMed hit list for this label today?”

#### 4. What must *not* change without intent

| Field | Meaning |
|-------|---------|
| `promotion.status: "OPEN"` | Still fail-closed until human / law pipeline promotes. |
| Empty `evidence[]` | OPEN — never invent PMIDs to fill a hole. |
| Pathway mermaid packs | Independent of evidence rebuilds unless a term is promoted into a Python graph. |

#### 5. Rebuild commands (when numbers should move)

```bash
# vocabulary
python3 tools/build_master_terms_index.py

# local ranked leads + demotion
python3 tools/build_term_evidence.py --min-score 8

# optional live breadth for thin terms
export NCBI_EMAIL=… NCBI_API_KEY=…
python3 tools/enrich_term_live_counts.py --thin-only --max 500

python3 tools/verify_term_evidence.py
```

Document operator-facing honesty also in `TERM_EVIDENCE_INDEX.md` (regenerated)
and `PLAN_TERM_MAPPING.md` § evidence prebuild.

### Contribution & review pipeline — cog/step targets + peer sign-off tiers

The crowd-contribution gate (`biology_as_code.contrib.validate_contribution`) now
reviews **code cogs**, not just the register — folding human review and community
collaboration into one fail-closed pipeline: `submit → validate → peer sign-off →
board`.

- **New target kinds** in `schemas/contribution.schema.json`: `mechanism`
  (`ref` = a mechanism id, e.g. `dmt1`) and `pathway_step`
  (`ref` = `"<pathway>::<from>-><to>"`). Both resolve against the live registries;
  a ref that is not a real mechanism or edge is `REFUSE`d, so a step review cannot
  drift from the graph.
- **Peer sign-offs → tiers.** An optional `signoffs` array raises the ledger's 0–5
  strength: sourced-only → 3, one reviewer → 4, **≥2 independent reviewers → 5**
  (the only tier that may lock a magnitude). `disputed` sign-offs and duplicate
  reviewers never promote — the two-independent-verifier bar a journal uses.
  Sign-offs are assigned by review; the submitter cannot set them.
- **Operate in the tier they are.** Nothing is blocked and nothing over-claims; a
  cog keeps working at whatever tier it has earned. This mirrors the auditor
  lattice, where `Confirmed` is already unreachable from a mechanism walk.
- **Review board (monorepo root, outside the wheel):** `tools/check_cog_evidence.py`
  reads the contribution ledger back through the same gate and renders every
  mechanism, pathway step and law at its current tier — alongside term-evidence
  leads and which laws are wired into the executable auditor (**7 of 47**). It
  replaces the throwaway `COG_REVIEW_LEDGER.json`; the contribution ledger is the
  single source of review state.
- Example: `examples/contributions/contrib.review-dmt1-iron-step.json` — a
  pathway-step review promoted to tier 5 by two independent sign-offs.
- Docs: `docs/contributing-data.md` gains a "Reviewing cogs and steps" section.
- Tests: six new cases in `tests/test_contribution.py` (mechanism/step targets,
  bad-step `REFUSE`, tier promotion 0/1/2, duplicate-reviewer and `disputed` do not
  promote). Existing verdicts and `all_sources` shape are unchanged.

> Coupling note: resolving the new target kinds makes `contrib.validator` import
> the `pathways` registry, so the contribution gate now depends on the pathways
> layer. Fine inside the package; it travels with `contrib` if that ever splits out.

### Added

- **Fail-closed claim auditor** (`biology_as_code.audit`): `audit_claim(claim, packet)`
  walks the L1→L5 delivery ladder and returns a `ClaimAudit` conforming to
  `schemas/claim_audit.schema.json`. Verdict lattice is `REFUSE` / `UNEVALUABLE` /
  `Busted` / `Plausible`. `Confirmed` is deliberately unreachable from a mechanism
  walk — confirmation is an evidence-tier judgement — and a test asserts it can
  never be emitted. `Claim`, `ClaimAudit`, and `audit_claim` are on the top-level API.
- **Declared gate/bound rule table** (`biology_as_code.audit.gates`): `GateRule` for
  categorical requirements, `BoundRule` for signed magnitude modifiers, kept as
  separate types so Gate ≠ Bound is enforced by the type system rather than a flag.
  Every rule carries `law_refs` into the LAW-SPEC register, and CI asserts the
  structural invariant that a `GateRule` may only cite laws with `gate.present == True`
  and a `BoundRule` only laws where it is `False`. No rule may cite a nonexistent law.
- **Typed food packet loader** (`biology_as_code.packets`): `get_packet`, `list_packets`,
  `iter_packets`, `validate_packet`, and a `FoodPacket` view over `examples/foods/`.
  `FoodPacket.declares()` separates "field not declared" from "declared false" —
  the distinction the auditor rests on, since silence is not a zero.
- **Zero-dependency JSON Schema validator** (`biology_as_code.packets.validate`)
  covering the keyword subset the repo's schemas actually use, preserving the
  package's no-dependency guarantee. `unsupported_keywords()` reports its own blind
  spot, and a test fails if a schema ever uses a keyword it cannot check.
- Tests: `tests/test_claim_audit.py` and `tests/test_packets.py` (38 new tests for the
  auditor; **291 in the suite today**). Includes derivation of both hand-written fixtures in `examples/claims/`,
  and coverage of all three teaching pairs (iron/ascorbate vs tannin, fat-vehicle
  gate, almond matrix).
- Docs: `docs/claim-auditor.md`.
- **MkDocs Material documentation site** (`mkdocs.yml`) with a four-lab **cookbook**
  under `docs/cookbook/`: Gate vs Bound (iron/ascorbate vs tannin), the fat-vehicle
  gate (carotenoids), the matrix effect (whole almond vs flour), and auditing a real
  marketing claim. Each lab runs against shipped packets and laws.
- `scripts/build_notebooks.py` generates Colab-ready `notebooks/*.ipynb` from the
  cookbook markdown, so the site and the classroom cannot disagree. `--check` mode
  fails CI when a notebook is stale.
- `tests/test_cookbook.py` executes every `python` block in the cookbook (one shared
  namespace per page), so a public-API rename breaks the build instead of silently
  leaving a broken lab published.
- `.github/workflows/docs.yml` builds the site with `mkdocs build --strict` on pushes
  and PRs, and deploys only from `main`.
- `docs` optional-dependency extra (`pip install -e ".[docs]"`). Runtime stays
  zero-dependency.
- **JOSS paper draft** under `paper/` (`paper.md`, `paper.bib`) plus
  `paper/SUBMISSION.md`, which lists the blocking items — ORCID, two unverified
  bibliographic records, and one load-bearing statistic deliberately left uncited
  rather than sourced from memory.
- **`docs/VALIDATION.md`**: a tiered validation report separating what is
  structurally tested from what is `FLOW` teaching scaffolding, with an explicit
  "not verified" table and a ranked list of what would raise each tier.
- **`tests/test_version_manifest.py`**: integrity harness over
  `VERSION_MANIFEST.json` — version agreement across pyproject / manifest /
  `CITATION.cff` / runtime, every component module and data artifact path resolving,
  tier values drawn from a known vocabulary, and skeleton artifacts required to
  declare `magnitude_locked`.
- `.zenodo.json` for machine-readable deposit metadata on tagged releases.
- CI, docs, Python and license badges in the README, plus links to the site,
  cookbook and validation report.
- **`docs/naming.md`**: canonical disambiguation from *Code Biology* (Barbieri), the
  established descriptive program on organic codes in living systems. Shortened
  versions land in the README, the package docstring, the Zenodo description and
  `paper/paper.md`, each at a length suited to its register.
  `tests/test_naming_note.py` guards them against drift: every surface must name the
  prior art and state the methodological claim, and the package-facing copy must not
  import the book's disciplinary thesis — the package is a 0.1.0 alpha and asserting
  what a whole field *should* do overclaims from a README.
- **Gate rules accept alternative satisfying fields.** `GateRule.requires` is now a
  tuple of `(field, predicate)` alternatives: the gate opens if any declared
  alternative passes, stays unknown if none are declared, and fails if every declared
  one fails. This lets `lipid_phase_present: true` open the fat-vehicle gate without
  writing a `dietary_lipid_g` value, so a packet can be filled in without inventing a
  magnitude.
- **`scripts/fill_packets.py`**: declarative, idempotent structural fill. Declares
  only facts that follow from a food's identity — lipid phase, matrix integrity,
  tannins, undisputed cargo presence — each carrying `derivation: "structural"` and a
  `rationale`. Took filled packets from 6 to 32; every carotenoid-, lipid- and
  iron-bearing packet now resolves. 12 packets are deliberately skipped with recorded
  reasons.
- **`tests/test_packet_fills.py`**: no structural declaration may carry a magnitude,
  structural cargo must keep `label_amount: "open"`, every declaration needs a
  rationale, the fill must be idempotent, and skipped packets must stay stubs.
- **`tests/test_law026_policy.py`**: makes `LAW026_PROMOTION_DECISION.md` executable.
  Locking the colonic fermentation energy band, collapsing it toward a point,
  hardening `bound_kind`, dropping the anti-overlock evidence (EV-041 / PMID
  33995299) or un-marking PMID 40403748 as pending all fail CI.
- `ClaimAudit.constitution_state`, mapping schema verdicts onto the four states in
  `docs/constitution.md`. Read-only view; absent from `to_dict()`, so schema
  conformance is unchanged.
- **`references` on `MetabolicMechanism`.** Enzyme cogs now carry authoritative
  provenance — stable **gene + EC** identifiers (NCBI Gene / ExPASy), never
  fabricated PMIDs — via a `_MECHANISM_REFERENCES` table applied at registry build.
  21 enzyme mechanisms sourced; the three with a nutrition-vocabulary term
  (`lipase`, `α-amylase`, `phosphofructokinase`) link it so they join the evidence
  spine. Surfaced by the root review board.

### Changed

- CI now runs the **whole** `tests/` suite. It previously ran four hand-picked
  files; the remaining nine were green but unguarded, so regressions in them could
  land unnoticed.
- CI gained a coverage job with a 90% floor on `audit` and `packets` (currently 92%),
  so an unexercised branch in the fail-closed core cannot silently become a pass.
- Documentation moved from Jekyll (`remote_theme: pages-themes/minimal`) to MkDocs
  Material. `docs/_config.yml` and the hand-written `docs/index.html` landing page
  are removed, and `.github/workflows/pages.yml` is replaced by `docs.yml`.

### Fixed

- Schema validator treated Python `bool` as satisfying `type: number`, because
  `bool` subclasses `int`. JSON separates the two; `True` is no longer a valid number.
- Keyword-coverage walker descended into `properties` and reported every property
  *name* as an unsupported keyword.
- `docs/index.md` linked `../schemas/` and `../examples/foods/`, which resolved only
  because Jekyll served `docs/` as raw files. Now absolute repository URLs.
- `docs/VALIDATION.md` recommended promoting the colonic fermentation energy band
  from `UNITS_skeleton` to `UNITS`. That contradicted `LAW026_PROMOTION_DECISION.md`,
  which had already decided the band must stay unlocked until primary human
  metabolizable-energy evidence exists. Recommendation retracted; the real open item
  is a full-text read of PMID 40403748.
- `LAW026_PROMOTION_DECISION.md`'s implementation checklist listed three items as
  outstanding that were already satisfied in the skeleton artifact, which made the
  work look undone. Reconciled.
- `VERSION_MANIFEST.json` advertised `compatibility.python: ">=3.10"` while
  `pyproject.toml` required `>=3.11`, so the manifest claimed support for a Python
  the package rejects at install.
- The `evidence_pubmed` manifest component pointed at `evidence_pubmed.py`, which no
  longer exists; the module is `evidence.py`.
- The `path_colon_scfa_atomic` artifact is tier `UNITS_skeleton` and carries 24
  numeric coefficients but did not declare `magnitude_locked`. Now declared `false`,
  matching the other skeleton artifacts.

## [0.1.0] — 2026-07-24

### Added

- First public PyPI-oriented release of the open dig + teaching pathway package.
- Open declarative **digestion machines** (`biology_as_code.machines`): versioned,
  inspectable JSON state graphs for the GI arc (oral -> stomach -> duodenum ->
  jejunum -> colon) plus a `full-digest` process, with `list_machines`/`get_machine`
  on the top-level API and a zero-dependency loader + validator (`validate_all`).
  Open FLOW tier only - the validator fails if any product-score/penalty hook leaks in.
- `simulate_meal()` high-level API wrapping the meal compile pipeline.
- Pathway graph discovery (`list_pathways`, `get_pathway`) over existing modules.
- Physiological scenarios: fed / overnight fast / prolonged fast / exercise.
- Meal fixtures (no product meal score / flow_score fields), vitamins registry, personas.
- Law / iron / colon data via `engine`.
- **Ketolysis** teaching pathway (`get_pathway("ketolysis")`) — ketone-body oxidation
  (BDH1 -> SCOT/OXCT1 -> ACAT1 -> 2 acetyl-CoA), including the liver's lack of SCOT.
  Closes TODO 6b; complements the existing ketogenesis graph.
- Multi-node **nutrient-sensing** regulatory graphs (`ampk_network`, `mtorc1_network`,
  `srebp_network`) with signed activates/inhibits edges and explicit AMPK/mTORC1/SREBP
  cross-talk. Now **executable from state**: `evaluate_network` propagates a signed graph,
  and `nutrient_sensing_snapshot(state)` chains AMPK→mTORC1→SREBP — surfaced under
  `report["nutrient_sensing"]` (the flat `pathway_regulation` floats are unchanged).
  Sources are rendered into the mermaid packs.
- `β-hydroxybutyrate` signaling pathway (HCAR2/GPR109A, class-I HDAC inhibition, NLRP3,
  GPR41) in the signaling registry — ketones as signals, not just fuel.
- Public LAW-SPEC **law cards** (`get_law`, `list_laws`, `law_card`) over the 47-law
  engine register (System / Organ / Gate / Bound / Conditions / relation).
- Open **evidence/provenance** surface (`all_sources`, `pubmed_url`, `law_evidence`):
  aggregates declared sources, loads bundled LAW-026 PubMed candidates, and offers a
  **fail-closed** (offline, no fabricated citations) PubMed lookup.
- Pack exporter renders a pathway's `references` as `%% Source:` lines + a `## Sources`
  section, so citations survive regeneration.
- Optional product-score **hook only** (engine not shipped; patent pending).
- Quiet default logging (`BIOLOGY_AS_CODE_LOG=DEBUG` for dig traces).
- CI workflow + **Trusted Publisher** OIDC publish workflow.
- MIT `LICENSE` for the installable package.

### Changed

- Removed bulk snapshot fixtures from the wheel (`off_products_snapshot`, `packets-for-sim`,
  `payloads-for-sim`, `FOOD_SUBSET_CLASSIFICATION`, `beverage_library`) to keep the package lean.
- Ruff lint gate focused on real issues (`F` / imports) for legacy teaching modules.
- **M4:** topics ontology build scripts moved to `tools/topics_build/` (not in wheel).
- **L3:** register `EXTRA_MOLECULAR` dig structures; drop dead bare `Structure(...)` block.
- **L4:** single `get_digestive_mechanism_registry()` factory (no triple rebind).
- **L5:** vitamin adequacy keeps `coenzyme_factor` in sync so meal modifiers affect energy/path signals.

### Notes

- FLOW teaching software — not clinical decision support.
- Product meal score and vendor-variable product scorer are **not** included.
- Book manuscript is **in progress / not yet released**, and is separately licensed (not part of this package).
