# Related projects — what this is, and what it is not

*Scope of this page: the projects `biology-as-code` sits next to, and a stated
position on each — consume, cite, watch, or leave alone. Written to answer
[issue #10](https://github.com/murffious/biology_as_code/issues/10) and to stop
this repository reinventing a layer that already exists.*

**As of 2026-08-29.** Every licence and activity claim below was checked against
the artefact itself on that date, not against a summary. Where a check failed to
find a licence, this page says `OPEN` and stops — the same rule
[FDP-1 §4](https://github.com/murffious/fdp-1) applies to nutrient values.
`OPEN` means *not known*; it does not mean *unlicensed*.

## How to read the verdicts

| Verdict | Meaning |
|---------|---------|
| **UPSTREAM** | We consume it, or should. Its identifiers or terms belong in our vocabulary; we do not rebuild them. |
| **ADJACENT** | Real overlap in subject, different altitude. Cite it, link to it, do not vendor it. |
| **PROCESS** | Read it for how they work, not for what they ship. |
| **WATCH** | No overlap today; a plausible path to overlap. Named tripwire below. |
| **UNRELATED** | Surfaced in the same searches, shares no layer. Listed so the question stops being asked. |

## The table

| Project | What it actually is | Licence (verified) | Verdict |
|---|---|---|---|
| [FoodOn](https://github.com/FoodOntology/foodon) | Food entity ontology, 40 MB release, active | CC BY 4.0 — agrees in repo, OBO Foundry, Bioregistry **and** `foodon.owl` header | **UPSTREAM** |
| [CDNO](https://github.com/CompositionalDietaryNutritionOntology/cdno) | Food-composition component vocabulary | **CC BY 3.0** in `cdno.owl`; repo `LICENSE` file is CC0-1.0 — see [Licence traps](#licence-traps) | **UPSTREAM** |
| [FOBI](https://github.com/pcastellanoescuder/FoodBiomarkerOntology) | Food ↔ biomarker ontology | **CC BY 4.0** in `fobi.owl` and repo; OBO Foundry and Bioregistry both still say 3.0 | **UPSTREAM** (dormant since 2022-05) |
| [CompTox / DSSTox](https://comptox.epa.gov/dashboard) | EPA chemical-exposure dashboard, >1M chemicals, DTXSID ids | US public domain; API key free but request-by-email | **UPSTREAM** |
| [Bioregistry](https://github.com/biopragmatics/bioregistry) | Metaregistry of 2,768 prefixes | MIT | **UPSTREAM** — and we owe it two prefixes |
| [joint-food-ontology-wg](https://github.com/FoodOntology/joint-food-ontology-wg) | Cross-ontology coordination venue | No `LICENSE` | **PROCESS** (files last pushed 2023-07-14) |
| [PTFI](https://foodperiodictable.org/) | Multi-omics characterisation of ~1,650 foods | `OPEN` — no licence stated on either public site | **WATCH** — namespace risk, not data risk |
| [VMH](https://www.vmh.life) | Recon3D / AGORA / whole-body GEM host | `OPEN` — see [the VMH position](#claim-b-the-vmh-position) | **ADJACENT**, and already a redistribution exposure |
| [COBRApy](https://github.com/opencobra/cobrapy) | Constraint-based metabolic modelling | **GPL-2.0** — matters, see below | **ADJACENT** |
| [Tellurium](https://github.com/sys-bio/tellurium) | SBML/Antimony modelling environment | Apache-2.0 | **ADJACENT** |
| [libSBML](https://github.com/sbmlteam/python-libsbml) | SBML reference implementation | LGPL-2.1 (majority) | **ADJACENT** |
| [PySB](https://github.com/pysb/pysb) | Rule-based systems-biology modelling | BSD-2-Clause | **ADJACENT** |
| [Open mHealth schemas](https://github.com/openmhealth/schemas) | JSON schemas for mobile health measures | Apache-2.0 | **ADJACENT** — but read the IEEE 1752.1 note |
| [awesome-nutrition-tracking](https://github.com/jrhizor/awesome-nutrition-tracking) | Curated list of consumer trackers and food APIs | CC0-1.0 | **ADJACENT** — it catalogues the problem |
| [anatomy](https://github.com/thebuggeddev/anatomy) | three.js 3D human anatomy explorer | **No `LICENSE`** — all rights reserved | **WATCH** |
| [gao-lab guideline](https://github.com/gao-lab/Guideline-for-Computational-Biology-and-Bioinformatics) | Lab training curriculum, largely in Mandarin | No `LICENSE` | **PROCESS** |
| [biocode](https://github.com/jorvis/biocode) | Genomics utility scripts (GFF, FASTA, BLAST) | MIT | **UNRELATED** |

---

## The ontology layer — the one that matters

The issue said these are *"higher leverage than any repo in the screenshot."*
That is correct, and the reason is narrow: [the claim schema](claim-schema.md)
already names FoodOn, CDNO, FOBI, ChEBI, MONDO, UBERON and NCBITaxon as the
normalisation targets for claim subjects and objects. They are not candidates.
They are the vocabulary this repository has already committed to.

The work left is not *choosing* them. It is resolving every accession before
shipping it — the rule [claim-schema.md](claim-schema.md) already states as
*never ship a guessed accession*.

### FoodOn

The clean case. `dcterms:license` in the release header, the repo `LICENSE.txt`,
the OBO Foundry registry and Bioregistry all say **CC BY 4.0**. Release
2025-12-30, repo active. Consume it, attribute it, do not fork it.

### CDNO

CDNO is the resolution target for FDP-1's `nutrient_ref` field, so its licence is
load-bearing for anything downstream of a nutrient value. It is **CC BY 3.0**,
not 4.0, and not CC0 — see [Licence traps](#licence-traps) for why three sources
disagree.

### FOBI

Food–biomarker links — the layer between "ate this" and "measured that", which is
the join our biomarker claims need. Two cautions: the repository has not been
pushed since **2022-05-03**, and the registries carry a stale licence for it.
Treat FOBI as a frozen but usable artefact, and read its licence off `fobi.owl`.

### CompTox / DSSTox

US public domain, no attribution obligation, no commercial restriction — the only
one of the four with no rights friction at all. DTXSID is the right identifier for
food-contact and additive substances, which is exactly what
[`FDA_ingredients/`](https://github.com/murffious/biology_as_code/tree/main/FDA_ingredients)
is full of. The API needs a free key obtained by emailing `ccte_api@epa.gov`, and
bulk data refreshes roughly every six months.

### joint-food-ontology-wg

A coordination venue, not an artefact. Repository files were last pushed
**2023-07-14**; issue traffic since is sparse. There is nothing here to vendor.
It is the right place to *ask* whether an alignment exists before building one —
which is precisely the question in the next section.

---

## Two load-bearing claims, tested

Both of these are assumptions this repository already relies on. If either is
wrong, something downstream is wrong. Both were attacked rather than confirmed.

### Claim A — "no official FoodOn → FDC mapping exists"

**CONFIRMED.** Reproduce it:

```bash
curl -sL https://raw.githubusercontent.com/FoodOntology/foodon/master/foodon.owl -o foodon.owl
grep -oE "<oboInOwl:hasDbXref[^>]*>[A-Za-z_]+:" foodon.owl \
  | grep -oE ">[A-Za-z_]+:" | sort | uniq -c | sort -rn | head -20
```

Across the full 40 MB release, the cross-reference namespaces FoodOn actually
carries are taxonomic and regulatory:

| Prefix | Count |
|---|---|
| `itis:` | 2,457 |
| `PLANTS:` | 834 |
| `Europe:` | 411 |
| `Codex:` | 399 |
| `MANSFELD:` | 324 |
| `langual:` | 49 |

There is **no FoodData Central namespace**. FDC appears exactly once in the whole
file, as a URL inside a prose definition
(`fdc.nal.usda.gov/fdc-app.html#/food-details/173711/nutrients`), plus four links
to the retired NDB interface. Fifty-three `langual:` references exist — LanguaL,
not FDC, is the alignment FoodOn actually ships.

**The trap worth naming:** FoodOn *does* carry USDA cross-references — 834 of them
— but they are `USDA PLANTS`, a plant-taxonomy database. A careless check greps
for "USDA", finds hundreds of hits, and reports a mapping that is not there. USDA
PLANTS is taxonomy; FoodData Central is composition. They are different databases.

The gap is real. Anything joining a FoodOn term to an FDC id is our own work and
must carry its own provenance.

### Claim B — the VMH position

**SUBSTANTIALLY CONFIRMED, one detail now stale.**

[`THIRD-PARTY-DATA.json`](https://github.com/murffious/biology_as_code/blob/main/THIRD-PARTY-DATA.json)
records the VMH licence as `OPEN` with `licence_confidence: OPEN`, on the grounds
that the NAR 2019 database paper names no licence and this project's own notes
record CC BY-NC 2.0 for Recon3D. That position stands, and is independently
corroborated: Bioregistry carries full entries for `vmh.metabolite`,
`vmh.reaction` and `vmh.gene` — resolving `https://www.vmh.life/#metabolite/$1` —
with the **`license` field null**. A metaregistry that resolves the identifier
still declines to assert the terms.

One detail has changed. The register's note says *"vmh.life returns 403 to
automated retrieval."* On 2026-08-29 the site returned **200**, with and without a
browser user-agent. It is reachable. What it does not have is a licence: there is
no `/terms`, `/license` or `/about` page (all 404), and the 27 KB front-page shell
contains no occurrence of *licence*, *license*, *Creative Commons*, *copyright*,
*terms* or *non-commercial*.

So the conclusion is unchanged and the reasoning is now stronger: VMH is silent,
not unreachable. The [licence enquiry](VMH-LICENCE-ENQUIRY.md) is still the only
way to close it, and `MASTER_CROSSWALK.tsv` stays non-commercial until it does.

---

## Licence traps

Three sources disagreed about two ontologies. The disagreements run in *opposite*
directions, which is why "check the registry" is not a method.

| Ontology | Repo `LICENSE` | OBO Foundry | Bioregistry | The artefact's own header | Authoritative |
|---|---|---|---|---|---|
| **CDNO** | CC0-1.0 | CC BY 3.0 | CC BY 3.0 | **CC BY 3.0** (`dcterms:license` in `cdno.owl`) | CC BY 3.0 |
| **FOBI** | CC BY 4.0 | CC BY 3.0 | CC BY 3.0 | **CC BY 4.0** (`fobi.owl`) | CC BY 4.0 |

For CDNO the repository is wrong; for FOBI the registries are. GitHub's licence
API reports CDNO as `CC0-1.0`, because it reads the `LICENSE` file and the
ontology's own declaration is somewhere else entirely. Bioregistry inherits OBO
Foundry's stale FOBI value, so the two "independent" registries are one source.

**The rule this produces:** *the licence of an artefact is what the artefact
declares.* A repository's `LICENSE` file governs the repository. A registry entry
is a summary and can be years old. A paper's CC BY covers the paper, not the
database it describes.

Verify with:

```bash
curl -sL http://purl.obolibrary.org/obo/cdno.owl | grep -m1 dcterms:license
curl -sL http://purl.obolibrary.org/obo/fobi.owl \
  | grep -m1 -oE "creativecommons.org/licenses/[a-z-]+/[0-9.]+"
```

This is the same failure mode
[`THIRD-PARTY-DATA.json`](https://github.com/murffious/biology_as_code/blob/main/THIRD-PARTY-DATA.json)
exists to catch, and the reason `check_third_party.py` runs in CI.

---

## The modelling layer — why we stay out of it

The [GEM primer](gem-primer.md) already argues the architectural case: a GEM
answers *which fluxes are feasible across the whole network*; this package models
*what happens to a meal* through named stages with provenance on every value.
That argument is unchanged.

There is a second reason, and it is not architectural.

**COBRApy is GPL-2.0.** This package is Apache-2.0 with a
[patent non-assertion covenant](https://github.com/murffious/biology_as_code/blob/main/PATENTS.md),
and advertises itself as zero-dependency. Taking COBRApy as a dependency would put
a copyleft obligation on top of a permissive licence that cannot carry it. The
decision not to become a GEM was made on modelling grounds; the licence makes it
structural. If a flux calculation is ever genuinely needed, it belongs behind a
process boundary — a separate tool, its own repository, its own licence — never as
an import.

The SBML stack is cleaner: Tellurium is Apache-2.0, PySB is BSD-2-Clause, libSBML
is LGPL-2.1. The issue's own condition is the right one — *only if a LAW-SPEC ever
needs a declared SBML hook*. Today none does. A LAW-SPEC declares a Gate, a Bound
and Conditions; it does not declare kinetics. When one does, `libsbml` at a module
boundary is the cheapest correct move, and LGPL-2.1 permits that use.

---

## The composition-data layer

### PTFI — a namespace question, not a data question

PTFI characterises foods at molecular scale: untargeted metabolomics, lipidomics,
ionomics, fatty acids, with glycomics and proteomics in development. They operate a
layer *below* this repository. A complete molecular inventory of a lentil does not
tell you that co-ingested ascorbate widens the non-haem iron bound — that is a
claim with conditions and a citation, which is what
[the 47 LAW-SPEC cards](constitution.md) and the claims register hold.

So "complementary upstream source" is the comfortable answer. The uncomfortable one
is about **identifiers**. An initiative that characterises foods at scale does not
only produce values; it produces the ids everyone downstream joins on. If PTFI
becomes the default food-composition namespace, the question is not whether it
competes with the laws — it does not — but whether our crosswalk gains a column or
gets routed around. The cheap hedge is to map to them early.

**Shipped versus claimed, as of 2026-08-29:**

- Data access requires account registration on the
  [PTFI Research Hub](https://ptfi.versobio.com/). There is no open bulk download.
- **No licence or terms-of-use statement appears on either public site.** Position:
  `OPEN`. Not asserted, not assumed permissive.
- No identifier namespace is publicly named. Whether PTFI mints its own food ids or
  reuses existing ones could not be determined from public pages.
- The flagship paper (*Nat Food*, 2024;
  [PMID 38459394](https://pubmed.ncbi.nlm.nih.gov/38459394/), with a correction at
  [PMID 38499749](https://pubmed.ncbi.nlm.nih.gov/38499749/)) is **not in PMC**, so
  the data-availability statement could not be read without a subscription.

An initiative whose stated mission is data *"shared openly and equitably as a
global resource"* currently publishes no licence and gates access behind
registration. That is not an accusation — young initiatives ship late — but it is
the reason PTFI is **WATCH** and not **UPSTREAM**. Nothing should be built against
it until the terms exist in writing.

### Bioregistry — and the two prefixes we owe it

Bioregistry (MIT, 2,768 prefixes, active daily) is a **metaregistry**: it registers
namespaces, not entities. `MASTER_CROSSWALK.tsv` maps entities. They do not
compete; the crosswalk should *declare* its prefixes in Bioregistry terms.

The nearer neighbours are in the same organisation, and they are the ones worth
watching: [Biomappings](https://github.com/biopragmatics/biomappings) (MIT) is
curated entity-level equivalences, and
[SeMRA](https://github.com/biopragmatics/semra) (MIT) assembles and reasons over
them. That is much closer to what the crosswalk does than Bioregistry itself is.
Before the crosswalk grows a new mapping lane, check whether Biomappings already
carries it.

Two findings that are directly actionable:

1. **USDA FoodData Central has no Bioregistry prefix.** Searching all 2,768 records
   for `fdc.nal`, `fooddata` or `FoodData Central` returns only false positives
   (`holofooddata.org`, an unrelated project) and one unrelated veterinary code,
   `usda.cvb.pcn`. The most-used nutrition identifier space in the world is not in
   the metaregistry.
2. **INFOODS has no prefix either.** FDP-1 accepts both `fdc` and `infoods` as
   alternate keys for `nutrient_ref`, so this repository already depends on two
   namespaces that nothing standardises.

Submitting those two prefix requests is a few hours of work, benefits everyone
downstream, and is the clearest available example of contributing upstream instead
of building a private table.

Note also that Bioregistry's `license` field is `null` for `vmh.metabolite`,
`comptox` and `langual` — even where the underlying data is unambiguously public
domain, as CompTox is. Bioregistry resolves identifiers; it does not assert rights.
That is exactly why
[`THIRD-PARTY-DATA.json`](https://github.com/murffious/biology_as_code/blob/main/THIRD-PARTY-DATA.json)
exists and cannot be replaced by pointing at a registry.

---

## The person layer

This repository models what a body does with a meal. It does not measure the body,
and it does not render it.

### Open mHealth schemas

Apache-2.0, active. JSON schemas for mobile-health measures, with a Java and Kotlin
SDK. The right answer if a downstream product ever needs to exchange measurement
data — do not invent a glucose or step schema.

Two things to know before adopting any of it:

- **Its sleep and physical-activity schemas are superseded by IEEE 1752.1.** The
  repository says so itself. Adopt the IEEE schemas for those measures, not the
  Open mHealth originals.
- It has **no food-composition schema**. The closest are `calories-burned` and
  `temporal-relationship-to-meal` — a meal is a *timestamp* in that model, not a
  composition. There is no overlap with a food packet, and nothing there to reuse
  for one.

### awesome-internet-of-the-body

The sibling list
([murffious/awesome-internet-of-the-body](https://github.com/murffious/awesome-internet-of-the-body),
CC0-1.0): the sensors and apps that measure the body, curated privacy-first. Kept
deliberately separate — that list is about *instruments*, this repository is about
*mechanism*. See [its page here](awesome-internet-of-the-body.md).

### awesome-nutrition-tracking

CC0-1.0, active, 146★. Worth reading precisely because it catalogues the problem
this repository was written against. Its **Food Databases** section — FDC,
Open Food Facts, Edamam, Spoonacular, Nutritionix, FatSecret and the rest — is a
list of places to get a number. Not one entry ships an evidence grade or a
provenance chain with that number. The list is an accurate census of a layer where
values circulate with their origins already stripped, which is the opening
paragraph of this repository's README restated as a directory.

There is no overlap. `biology-as-code` is not a tracker and should not appear on
that list until it has something a tracker could consume.

### anatomy

[thebuggeddev/anatomy](https://github.com/thebuggeddev/anatomy) — an interactive
three.js 3D human anatomy explorer, 2,870★, TypeScript.
[murffious/anatomy](https://github.com/murffious/anatomy) is a fork of it.

**It has no `LICENSE` file**, which means all rights reserved: it can be read and
forked on GitHub, but not vendored, redistributed or built on. Ask upstream before
any use beyond looking.

Why it is **WATCH** rather than **UNRELATED**: our LAW-SPEC cards carry an *Organ*
field and our claim schema resolves anatomical sites to UBERON. A renderer keyed on
UBERON identifiers would turn a law card into a picture. That is a real, attractive
convergence — and it is also the fastest way to acquire a 3D-rendering dependency
this project has no business maintaining. If it ever happens, it belongs in a
separate repository that consumes this one, and only after the licence question is
answered.

---

## Process, not product

### gao-lab guideline

The issue's note — *"read their checklist; don't vendor it"* — is right, with one
correction to what it is. This is not a reproducibility standard. It is the Peking
University Gao lab's **internal training curriculum** for new interns: Linux,
Python, R, writing, statistics, machine learning, with linked PDFs and courses,
written largely in Mandarin. Repository files were last pushed 2025-05-06 and it
carries no `LICENSE`.

Useful as a skills reading list. It defines no schema, ships no data, and overlaps
with nothing here.

### biocode

MIT, 573★, active. A curated grab-bag of genomics utility scripts — GFF, FASTA,
BLAST, Chado — explicitly framed by its author as *"a collection of bioinformatics
scripts many have found useful."*

There is no nutrition content and no shared layer. It appears on this page because
it surfaces in the same GitHub searches, and it is listed so the question does not
need asking twice. **UNRELATED.**

---

## What would change these verdicts

Tripwires. If one trips, this page is wrong and needs revisiting.

| Tripwire | Verdict it overturns |
|---|---|
| PTFI publishes a licence and an open bulk download | PTFI moves **WATCH → UPSTREAM**; map to their ids immediately |
| PTFI mints a food-identifier namespace that others adopt | The crosswalk needs a PTFI column, or gets routed around |
| VMH answers the [licence enquiry](VMH-LICENCE-ENQUIRY.md) | `MASTER_CROSSWALK.tsv` either clears for commercial use or migrates to Human-GEM |
| An official FoodOn → FDC alignment ships | Our own join becomes redundant; adopt theirs and delete ours |
| A LAW-SPEC needs declared kinetics | libSBML enters at a module boundary — never COBRApy |
| FOBI resumes releases | Re-check its licence header; the registries will still be stale |
| Biomappings covers a lane our crosswalk holds | Contribute the lane upstream instead of maintaining it here |

## Nothing here is vendored

To be explicit about the thing the issue was actually worried about: this
repository redistributes rows from exactly four sources — VMH/Recon3D, FDA
inventories, Open Food Facts and USDA FDC. All four are declared, with licence,
conflict and remedy, in
[`THIRD-PARTY-DATA.json`](https://github.com/murffious/biology_as_code/blob/main/THIRD-PARTY-DATA.json),
and `check_third_party.py` fails the build if that register drifts. No project on
this page is vendored, and none should be.
