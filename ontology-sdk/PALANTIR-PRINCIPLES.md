# Palantir's ontology design guidance, applied here

Source: `palantir.com/docs/foundry/ontology/` — `ontology-best-practices`,
`ontology-structural-guidance`, `ontology-anti-patterns`. Fetched 2026-08-29.
They publish this openly and it is the most battle-tested public guidance on the
subject; there is no reason to re-derive it.

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
| **System Silos** — same entity, separate types per source system | `MASTER_CROSSWALK.tsv` in two places (`biology_as_code/`, `working_map_nutrition/`); `aca.ttl` and `claim-shape.ttl` in two places | ⚠ **Present.** Textbook case, and the crosswalk copies have diverged |
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
