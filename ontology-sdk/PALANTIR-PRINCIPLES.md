# Palantir's ontology design guidance, applied here

They publish this openly and it is the most battle-tested public guidance on the
subject; there is no reason to re-derive it. Fetched 2026-08-29.

## Sources — the full set we are working from

| Doc | URL | What we took from it |
|---|---|---|
| Ontology overview | `palantir.com/docs/foundry/ontology/overview` | The fourfold (Data · Logic · Action · Security); the dataset→ontology mapping |
| Ontology design: best practices | `.../ontology/ontology-best-practices` | The four design principles; *separate identity from observation* |
| Ontology design: structural guidance | `.../ontology/ontology-structural-guidance` | The struct / main-field / interface / object-backed-link / derived-property decision table; naming conventions; the pragmatism clause |
| Ontology design: anti-patterns | `.../ontology/ontology-anti-patterns` | The eight anti-patterns audited below |
| Ontologies | `.../ontology/ontologies-overview` | Scoping — one ontology, many consumers |
| Object and link types | `.../object-link-types/type-reference` | Property types; link cardinality |
| Action types | `.../action-types` | Actions as the write path; Action Sprawl |
| Functions | `.../functions` | Logic as a first-class ontology citizen |
| Interfaces | `.../interfaces` | Multi-inheritance around capabilities — the highest-value idea here |
| Object backend | `.../object-backend/overview` | Why the ontology is not a graph database |
| Object views | `.../object-views/overview` | Views are presentation, **not** structure — see *Where we deliberately depart* |
| Ontology SDK | `.../ontology-sdk/overview` | Generated, typed, versioned clients — the thing we are building an analogue of |
| Ontology Manager (OMA) | `.../ontology-manager/overview` | Dependents · Usage · Branches · Observability — see `ONTOLOGY-MANAGER.md` |

Consolidated, with a stance and a machine check on each, in
[`principles.v1.json`](principles.v1.json) — 32 principles, 16 of them gated by
`check_principles.py`. This document is the reasoning; that register is the rule.

**The reason to take it seriously here is convergence.** Their guidance was written
for airlines, hospitals and manufacturers. It arrives, independently, at four rules
this project derived from nutrition evidence. Where two unrelated traditions reach
the same rule, the rule is probably load-bearing.

| Their rule | This project's version | Where ours came from |
|---|---|---|
| "Separate identity from observation (entity ≠ measurement)" | **Q1 does not determine Q2** — what is in it vs what happens when eaten | ch 9, the apple |
| Derived properties: values computed from links, never denormalized | **Weakest link, computed, never asserted** | FDP-1 §3.1 |
| Structs: group a value with its metadata, designate a main field | **`Declared[T]`** — value + unit + source + method + source_ref + retrieved, one property | FDP-1 §2 |
| Security boundaries align with domain boundaries | **The population fence** — scope travels with the estimate | MI-Nutrition |

Their closing line is the book's title, arrived at from the other direction:
*"The Ontology is the software that powers your organization."*

---

## The core model, verbatim

*Kept as published, so the mapping below can be checked against it.*

> Palantir models each operational decision as comprising four components:
>
> - **Data** — the information leveraged to make the decision.
> - **Logic** — the heuristics and computational processes that evaluate a decision.
> - **Action** — the orchestration and execution of the chosen decision.
> - **Security** — the assurance that the decision complies with operational policies.
>
> Foundry Ontology creates a complete picture of an organization's world by mapping
> datasets and models to object types, properties, link types, and action types.
>
> - An **object type** defines an entity or event in an organization.
> - A **property** defines the object type's characteristics.
> - A **link type** defines the relationship between two object types.
> - An **action type** defines how an object type can be modified.

| Datasets | Ontology |
|---|---|
| Dataset | Object type |
| Row | Object |
| Column | Property |
| Field | Property value |
| Join | Link type |
## The four principles, priority-ordered, with our instance

**1 · Domain-driven design — "model the real world, not the source data."**
Their warning is against 1:1 column-to-property mapping from whatever the upstream
table happened to look like. Ours is the same failure at a different scale: a
composition row is a *source system artifact*, not the object. The object is a food
in a matrix, eaten by a host, at a rate. Chapter 8 is that argument.

Their sub-rule **"separate identity from observation"** is worth lifting verbatim
into the manifest, because it settles a live question: `Food` and `FoodValue` are
different object types. The apple is the entity; 927 compounds from three labs are
observations *of* it. Collapsing them is how one database row came to stand for a
2,000-cell grid.

**2 · Don't repeat yourself — the rule of three.**
*"One instance is coincidence; two is a pattern; three triggers refactoring."*
A usable threshold for a project that currently has crosswalks, TTL shapes and
verdict vocabularies in more than one place each.

**3 · Open for extension, closed for modification.**
Lock the essential properties of core types; extend via linked types, new interface
implementations, or property namespaces — never by editing the core. This is the
governance model FDP-1 needs anyway: consumers pin a version, and a shared public
ontology cannot reshape a type underneath them.

**4 · Composition over deep hierarchies.**
Interfaces around *capabilities*, not taxonomy. Their examples are `Inspectable`,
`Schedulable`, `Billable`. Ours write themselves: **`Gradeable`** (carries a
weakest-link grade), **`Declarable`** (fields may be OPEN/NONE), **`Fenced`**
(carries a population boundary), **`Refusable`** (can return UNEVALUABLE).

A workflow written against `Gradeable` then runs over a food value, a score, a
study record and a claim without knowing which it has. That is the single highest-
value structural idea in their docs for this project.

---

## Anti-pattern audit — provisional

*Provisional because the verification workflow is still confirming the repo facts.
Marked ⚠ where I am confident, ? where the workflow will settle it.*

| Their anti-pattern | Here | Verdict |
|---|---|---|
| **System Silos** — same entity, separate types per source system | `aca.ttl` and `claim-shape.ttl` in two places (byte-identical mirrors, no owner declared) | ⚠ **Present, but narrower than first recorded.** The crosswalk pair is **not** a silo — it is an undeclared *pipeline* (extract → canonical), resolved 2026-08-29 and now gated. Worth keeping the correction visible: an undeclared derivation and a genuine silo look identical from the outside, and this project called one the other for a month |
| **The Misnomer** — vague or overloaded names | **"Layer" means two different things**: the OBO causal spine numbers L1–L5, the standardization stack numbers L0–L9. Also "unit" (STUDY_UNIT vs the UNITS claim tier), "grade" vs "tier" | ⚠ **Present, and the worst one.** Their stated harm — *"cross-team confusion from varied interpretations"* — is already happening inside one project |
| **The God Object** — one type covering distinct entities | Risk that `Food` absorbs raw ingredient, branded product, recipe and meal at once — the commercial-classification and kitchen-crucible axes point that way | ? **Risk, not yet realised.** Guard it in the manifest |
| **The Time Machine** — historical versions as separate objects | Registers version as `*.v1.json` with `as_of`; Zenodo uses concept + version DOIs | ? Probably **correctly avoided** — versioning is on the record, not modelled as separate objects. Confirm |
| **Department Silos** — separate versions of a shared entity per team | STUDY_UNIT vs MI-Nutrition *looks* like this | ✅ **Not the anti-pattern.** Field comparison showed two properties in common; they are orthogonal axes (licenses vs discloses), not rival copies. Worth recording, because the resemblance is misleading |
| **The Kitchen Sink** — ETL metadata as properties | FDP-1 values carry `retrieved`, `source_ref`, `method` | ✅ **Explicitly not.** Here provenance *is* business data — it is what licenses the claim. **A naive application of this anti-pattern would strip exactly the fields the book exists to argue for.** Note it in the manifest so nobody "cleans" them later |
| **Action Sprawl** — many single-property actions | Validators are cohesive (`validate_fdp`, `validate_mi_nutrition`) | ✅ Avoided |
| **The Golden Hammer** — one tool for every problem | Mixed: pipelines, validators, engines, registers | ? No evidence either way yet |

**Two of eight present, one at risk, three cleanly avoided, and one where their
advice must be deliberately refused.** That last row is the interesting one: an
anti-pattern that is correct for enterprise data and wrong for evidence.

---

## Structural decision rules, mapped

Their table, with our column filled in:

| Scenario | Their tool | Our case |
|---|---|---|
| Multi-field, semantically related value | **Struct** | An FDP-1 value: value + unit + source + method + source_ref + retrieved |
| Struct that should behave like a simple value | **Main field** | `Declared[T]` — `.value()` is the main field, provenance rides along |
| Common properties/actions across types | **Interface** | `Gradeable`, `Declarable`, `Fenced`, `Refusable` |
| Relationship carrying metadata | **Object-backed link** | SURFACE_CLAIM's *join* — claim→study, carrying verb class and verdict. The join **is** the object |
| Value computed from linked objects | **Derived property** | The weakest-link grade. Never stored — a stored grade is a grade that can drift from its inputs |
| Value from stable pipeline inputs | **Pipeline transform** | Register builds (`make registers`) |

**Naming conventions to adopt as-is:** singular concrete nouns for object types; no
type encoding in property names; links that read naturally in both directions; one
date convention; and *"ambiguous terms: qualify specifically"* — which is the fix
for the layer collision.

---

## Where we deliberately depart

**Object Views are separate from the ontology.** Their docs are explicit: views are
a presentation layer, not a structural component. So the evidence hub is **not** part
of this ontology and must not be modelled into it. That settles a question that would
otherwise have crept in — the hub renders registers; it does not define them.

**Security is not the fourth pillar; provenance is.** Their structural guidance
spends real effort on row/column/cell security because Foundry is multi-tenant.
Published evidence has no access-control problem. The substitution is argued in
`DESIGN.md` §1 and it is the one place the model diverges by design rather than by
scale.

**Their pragmatism clause applies, and should be quoted at ourselves:**
*"Build reasonably now with clear improvement paths rather than blocking on
perfection… Defend critical invariants: naming quality, semantic clarity, and
security design are difficult to fix retroactively."*

For us the invariants that are hard to fix later are **naming** (the layer
collision), **identity** (one canonical crosswalk), and **declaredness** (OPEN never
collapsing to null). Those three block the manifest. Everything else can improve
incrementally.


## The core model, verbatim

*Kept as published, so the mapping below can be checked against it.*

> Palantir models each operational decision as comprising four components:
>
> - **Data** — the information leveraged to make the decision.
> - **Logic** — the heuristics and computational processes that evaluate a decision.
> - **Action** — the orchestration and execution of the chosen decision.
> - **Security** — the assurance that the decision complies with operational policies.
>
> Foundry Ontology creates a complete picture of an organization's world by mapping
> datasets and models to object types, properties, link types, and action types.
>
> - An **object type** defines an entity or event in an organization.
> - A **property** defines the object type's characteristics.
> - A **link type** defines the relationship between two object types.
> - An **action type** defines how an object type can be modified.

| Datasets | Ontology |
|---|---|
| Dataset | Object type |
| Row | Object |
| Column | Property |
| Field | Property value |
| Join | Link type |Define Ontologies
Ontologies
Object and link types
Action types
Functions
Interfaces
Ontology design: Best practices
Ontology design: Structural guidance
Ontology design: Anti-patterns
Show less
Bash Write the manager-layer analysis and refresh the tracker
IN
make ontology-write 2>&1 | tail -3
cat > /Users/morf/Downloads/morf-engineering/mealcoachai/dev/NUTRI-COLLECTIVE_0/biology_as_code/ontology-sdk/ONTOLOGY-MANAGER.md <<'MD'
# The manager layer — what OMA is for, and what ours has to be

Palantir ships an **Ontology Manager** (OMA) alongside the ontology itself. Reading it
as an authoring UI misses the point: the object-type editor is the least interesting
part. The load-bearing panels are the ones that answer *what happens if I change
this* — **Branches**, **Dependents**, **Usage / Usage History**, **Observability**.

That is not UI polish. It is the admission that **an ontology has consumers, and a
type change breaks them.** A vocabulary with no consumers needs no manager. Ours has
consumers, so it needs the functions — not necessarily the application.

## The three questions a manager exists to answer

| OMA panel | The question | Our answer today |
|---|---|---|
| **Dependents** | Who reads this artifact? | **Now generated.** `ontology_inventory.py` scans the tree; `MASTER_CROSSWALK.tsv` has **29** readers, `aca.ttl` **14**, the vocabulary **7**. |
| **Observability / Usage** | How much moves if I change it? | **Partial, and hand-measured once.** 2026-08-24: adding two phrases to the `cardiovascular` group changed 4 of 123 association rows, added 5 studies (716→721), and moved a published pooled effect 0.78→0.75. Nothing recomputes that automatically. |
| **Branches** | Can I propose a change without breaking live readers? | **Ratchets, not branches.** `nutrition-vocab.baseline.json` and `quality_baseline.json` make a change *fail loudly*; they do not let you see the consequence before committing to it. |

Not having the first answer is what cost the crosswalk a month. The question *who
reads `MASTER_CROSSWALK.tsv`* had to be re-derived by hand on 2026-08-29, and the
answer — FDP-1 §2 cites it by URL, plus `README`, `CITATION.cff`, `PATENTS.md`,
`.zenodo.json` — is what settled which copy was canonical in about a minute. A
standing Dependents view would have made the decision available all along.

**So the v0 manager is not an application. It is those three answers, on the command
line, kept fresh by the same generators that already gate everything else.** One is
done. The second is the valuable one and is genuinely hard: it means being able to
say, before a vocabulary edit lands, *this moves N published effect sizes.* That is
the same capability the book demands of nutrition, turned on ourselves.

If a UI ever exists it is a tab in `evidence-hub-v2.html`, never a new page.

---

## The four components, and the one substitution

Palantir models every operational decision as **Data · Logic · Action · Security**.
Three map cleanly. The fourth does not, and the mismatch is informative.

| Component | Theirs | Ours |
|---|---|---|
| **Data** | datasets mapped to object types | registers, FDP-1 packets, the crosswalk, the corpus |
| **Logic** | functions evaluating a decision | 47 laws, 9 gates, 38 bounds — already frozen, already tested |
| **Action** | orchestrated writes back to the source | validators; `Declared[T]` refusals |
| **Security** | policy compliance on the decision | **Provenance.** |

Their fourth component asks *is this decision permitted?* Ours asks *is this decision
licensed by evidence?* Those are the same shape — a gate the decision must pass that
is not about the data's content — but a different authority. Access control says who
may see a number. Provenance says whether the number may be used at all, by anyone,
including its author. **A nutrition claim with perfect access control and no method is
still worthless**, which is why the substitution is not a rename.

## Dataset → ontology, and the cell that is missing

| Datasets | Ontology | Here |
|---|---|---|
| Dataset | Object type | `MASTER_CROSSWALK.tsv` → `Metabolite`; `nutrition-vocab.v1.json` → `Concept` |
| Row | Object | one metabolite; one SKOS concept |
| Column | Property | `chebi`, `hmdb`, `kegg`, `inchiKey`; `prefLabel`, `altLabel`, `hiddenLabel` |
| Field | Property value | `chebi:15637` |
| Join | Link type | the crosswalk **is** a link type, already — nutrient ↔ metabolite |

The mapping is exact until the fourth row, and then it stops. **"Field → Property
value" assumes a field has a value.** 20,983 of our 33,564 crosswalk cells do not —
they say `OPEN`, and 2,797 of them are the entire `inchiKey` column. In their table
those are nulls, and a null is not a property value; it is the absence of one.

That is where we extend rather than adopt, and it is the whole of `Declared[T]`: a
property whose value may be `a value`, `NONE` (checked, genuinely none exists), or
`OPEN` (nobody has looked). Three states, never `Optional[T]`. Their model has no
cell for the third, because in an operational system somebody always knows. In
nutrition nobody does, and pretending otherwise is the failure the book is about.

**Borrow the four nouns. Borrow the dataset mapping. Refuse the assumption that a
field has a value.**
MD
echo "written"

OUT
wrote inventory into ONTOLOGY-CONSOLIDATION.md
written
Bash Final verification across every gate
IN
cd /Users/morf/Downloads/morf-engineering/mealcoachai/dev/NUTRI-COLLECTIVE_0
echo "### crosswalk"; make crosswalk-check
echo "### vocabulary"; (cd nutri-collective/evidence-platform && make vocab-check)
echo "### platform suite"; (cd nutri-collective/evidence-platform && make test 2>&1 | tail -1)
echo "### ontology inventory"; (cd book && make ontology 2>&1 | tail -1)
echo "### claims"; (cd book/final-draft/claims && make test 2>&1 | grep -E "^(FAIL|closed|ok|FAILED)")

OUT
### crosswalk
OK    canonical == normalize(extract), byte for byte (2797 rows, 12 cols)
### vocabulary
OK    vocabulary round-trips to the source tables (118 concepts)
### platform suite
623 passed, 5 skipped in 8.85s
### ontology inventory

### claims
FAIL refuted CLM-Z1: prose not yet rewritten — a refuted claim is a rewrite, not an edit. Add rewrite.completed once it is done.
closed CLM-XW-1361-ROWS: refuted, prose rewritten 2026-08-29 (5 files)
closed CLM-VOCAB-FOUR-CONVENTIONS: refuted, prose rewritten 2026-08-29 (1 files)
FAILED
Both done, and the first one turned out to be a correction rather than a decision.

1. Canonical crosswalk — CROSSWALK-CANONICAL.md
The copies never disagreed. 24,893 cells differ; 0 values do. 12,581 populated cells on each side.

The "1,361 rows differ in value" was my bug: compare() flattened OPEN but knew nothing about CURIE prefixes, so kegg:C00234 vs C00234 counted as a conflict. They're a pipeline, not a fork:


VMH snapshot ──build──▶ extract (raw ids, blanks) ──normalize──▶ canonical (CURIEs, OPEN)
Two links were code. The middle one existed only as someone's memory of running it in July. A transform that isn't written down is indistinguishable from corruption — and it fails in the safe-looking direction: identical files get reported as contradictory and work stops on a blocker that was never there.

biology_as_code/ is canonical — FDP-1 §2 cites it by URL, it carries OPEN where the extract carries blanks, and every populated cell is a resolvable CURIE. Wrote normalize_crosswalk.py, fixed build_master_crosswalk.py (its paths were broken — neither copy was regenerable), and gated it: make crosswalk-check passes byte-for-byte. Regeneration doesn't touch the published file (md5 unchanged).

What it exposed is worse than what it replaced: inchiKey is 0% populated, 2,797/2,797 OPEN. It's the only structure-derived id in the table, so KEGG/ChEBI/PubChem agreement here is asserted and never verified.

2. Controlled vocabulary — 118 SKOS concepts
nutrition-vocab.v1.json + .ttl, via build_vocab.py / vocab.py. make vocab, make vocab-check.

Descriptive, never leading. Generated from lexicon.py and SEARCH_ONLY as they stand, and the gate is that those tables regenerate from it unchanged — the builder refuses to write otherwise. Full suite 623 passed, 5 skipped; nothing moved.

Your search/scoring rule is now structural, not remembered: lexicon_tables() returns prefLabel + altLabel and is unable to see a hiddenLabel.

Your earlier framing — "four times, four conventions" — was overstated, and I registered it REFUTED. Only two of the four own vocabulary; across ~1,490 strings just 14 appear in more than one. The real defect: every table maps string → string, never string → concept. Which is why nothing noticed that the typeahead files osteoporosis under bone while the screener files it under fracture, or that cognition and cognitive are two groups for one idea.

Debt declared and ratcheted, never auto-fixed — 12 ambiguous terms, 4 faked hierarchies, 3 cross-reader conflicts. Merging cognition into cognitive would rewrite screening for every cognition study in the ledger.

3. On Ontology Manager and the four components — ONTOLOGY-MANAGER.md
The load-bearing panels aren't the editor — they're Dependents, Usage, Branches: an ontology has consumers and a type change breaks them. Not having the first answer is exactly what cost the crosswalk a month; "who reads this?" settled it in a minute once asked. So I built it: the inventory now generates a Dependents table — MASTER_CROSSWALK.tsv 29 readers, aca.ttl 14, the vocabulary 7.

On Data·Logic·Action·Security: their dataset→ontology mapping is exact until row four. "Field → Property value" assumes a field has a value. 20,983 of ours don't. That's the one place we extend rather than adopt — and it's the whole of Declared[T].

Red, and staying red
make test in claims fails on CLM-Z1 — the MCS refutation whose Part IV prose rewrite is genuinely still pending. I added a close path for refuted claims (they previously could never be closed, so the gate would stay red forever), verified against the files, and it correctly refuses to close Z1.

Next cheapest move: skos:definition — no concept has one, and that's what turns the 12 ambiguous terms from visible into resolvable.

I pasted all teh key pricnicples we want to folow no