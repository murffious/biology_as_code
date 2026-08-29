# A nutrition Ontology SDK — design

**Home: `biology_as_code`.** Not a standalone project and not `nutri-collective`.
Three reasons: this package is already pip-installable, Apache-2.0, and
zero-runtime-dependency — an SDK has to be installable, and this one already is. It
owns the Logic layer the SDK wraps (digestion engine, laws, auditor), and the design
rule is *wrap, never reimplement*. And `nutri-collective` is a platform, not a
library; shipping an SDK from it would tie the library's release cadence to the
hub's.

**The split, then:** `nutri-collective/evidence-platform` **produces** registers and
runs the corpus; `biology_as_code` **consumes** them and exposes the typed surface.
That is the same arrangement already settled for the claims agent — consumption, not
merger.

*Placement note: `declared.py` and its fixtures belong in
`src/biology_as_code/ontology/` and `tests/` once the generator exists. They are held
here while this is a seed, so the package layout is not disturbed before there is
something to disturb it for.*

**Goal.** `pip install nutrition-sdk` (and later npm) gives a developer typed,
autocompleting access to food, nutrient, study, claim, host and law objects, with
the grading and refusal semantics enforced by the types rather than by discipline.

**Model: SuperRepo, not Foundry-backed.** Palantir's OSDK treats Foundry as the
backend — Developer Console, scoped tokens, read-time access control, writeback.
None of that applies here and trying to reproduce it would sink the project. The
variant that fits is the one their docs call a **SuperRepo**: ontology-as-code in
the same repository as the functions, SDK generated locally and regenerated
whenever the definitions change, versioned and released as a single artifact.

**The consequence is a feature, not a compromise.** With no backend, the SDK ships
its own data and works offline. Registers travel in the wheel; the PubMed corpus is
an optional HTTP lane. Nothing about the core requires a server, an account, or a
token — which is the only version of this that a researcher can actually adopt.

---

## Why this is not a knockoff

Every generated SDK types an absent value as `Optional[T]` — `float | None`. That
collapses two facts this project spent a book separating:

| State | Meaning | `Optional[T]` says |
|---|---|---|
| a value | measured, with a method | `float` |
| `OPEN` | **not known** — exists, could be supplied | `None` |
| `NONE` | **not applicable** — known absent | `None` |

`fdp-1/validator/validate_fdp.py` already enforces the distinction: *"unknowns
SHALL be the literal `OPEN`, never null/empty/omitted"* (§4), with `GRADE_RANK`
putting `OPEN` at the bottom and `weakest_link()` propagating it.

So the SDK's core primitive is **`Declared[T]`**, a three-state value, and grading
is a property of the type system rather than a convention a caller may forget.
Ontology SDKs generate accessors; this one generates accessors **that can refuse**.
That is the differentiator, it is already specified, and it is why the thing is
worth building rather than wrapping.

*(Live evidence it matters: `MASTER_CROSSWALK.tsv` exists as an extract with 20,983
blank cells and a canonical copy where the same 20,983 say `OPEN`. The blanks are a
faithful dump — the source genuinely had nothing — but a consumer reading the extract
cannot tell that from "nobody filled it in". A round-trip through a type system
without three states is how a table loses that distinction, permanently and
silently.)*

---

## The object model already exists — it is just not declared in one place

| OSDK concept | This project's equivalent | Lives in |
|---|---|---|
| Object type | `Food` (FDP-1 packet) · `Nutrient` (CDNO/ChEBI) · `Study` (MI-Nutrition) · `Claim` (SURFACE_CLAIM) · `StudyUnit` · `Host` (HostState) · `Law` · `Exposure` (EDP-1) | `fdp-1/`, `edp-1/`, `evidence-platform/site/`, `biology_as_code/` |
| Link type | food→value→nutrient · value→method · claim→study join · nutrient↔metabolite · law→gate/bound | `MASTER_CROSSWALK.tsv`, `id-crosswalk.v1.json` |
| Action type (validated mutation) | `declare_value`, `assert_claim`, `record_layer_pass` — each **fails closed** | `validate_fdp.py`, `validate_mi_nutrition.py` |
| Query / function | `digest(food, host, conditions)` · `audit(claim)` · `weakest_link(values)` · `layer_pass(object)` | `biology_as_code` engine, auditor, case ledger |
| Interface | conformance tier; `Gradeable`, `Refusable` | FDP-1 §3, MI-Nutrition `conformance` |
| Ontology version | register `as_of` + `schema_version` | `site/*.v1.json` |

**Nothing here needs inventing.** What is missing is one machine-readable manifest
declaring these together, and a generator that reads it.

---

## What to build, in order

**1 · `ontology.json` — the manifest.** One file declaring object types, their
properties and declaredness, links, actions, queries, and the ontology version.
Bootstrapped *from* the existing JSON Schemas, then becomes canonical so the
schemas are generated from it rather than the reverse.

**2 · The generator.** Manifest → typed Python. Dataclasses with `Declared[T]`
fields, link accessors, action functions that call the existing validators, query
functions that call the existing engines. **Wrap, never reimplement** — the
validators and the digestion engine are tested code and the SDK is a typed surface
over them.

**3 · Packaging.** `nutrition-sdk` on PyPI, version pinned to the ontology version
the way OSDK pins to an Ontology version. `biology-as-code` is already
pip-installable, Apache-2.0, zero runtime dependencies — the SDK depends on it.

**4 · TypeScript**, generated from the same manifest, once Python is stable.

---

## What blocks it today, honestly

1. ~~**The identity spine disagrees with itself.**~~ **Cleared 2026-08-29.** It did
   not: 0 cells differed in value; the "1,361 rows" was a comparison bug of mine
   (notation counted as fact). `biology_as_code/MASTER_CROSSWALK.tsv` is canonical,
   derived from the extract by `tools/normalize_crosswalk.py`, gated byte-for-byte
   by `make crosswalk-check`. See `CROSSWALK-CANONICAL.md`.
   *Replaced by a smaller but real one:* `inchiKey` is 0% populated (2,797/2,797
   `OPEN`), so agreement between KEGG, ChEBI and PubChem ids in this table is
   asserted, never structurally verified. That is a data gap, not a blocker — the
   SDK can ship an identity layer that declares it.
2. **MI-Nutrition is fluid.** Codegen against a moving schema produces types that
   churn. Either pin a version for v0 or leave `Study` out of the first release.
3. **EDP-1 has no DOI and is undeposited.** `Exposure` cannot be a public object
   type until it is.
4. **Imported vocabularies are not yours to relicense.** FoodOn, ChEBI, CDNO, VMH
   have their own terms. Reference and attribute; do not vendor wholesale. Only ACA
   is authored, per the claims-agent standard — the SDK must make that split visible.
5. **Naming.** "OSDK" is Palantir's. Call it something else.

## Deliberately out of scope

Access control, writeback, a Developer Console, hosting, WebSocket subscriptions.
Those exist because Foundry is a multi-tenant platform. This is a library with data
in it.

---

## Status

`declared.py` in this folder is the core primitive, with tests. Everything else
above is design.

**The object model above is superseded by
[`GROUNDED-OBJECT-MODEL.md`](GROUNDED-OBJECT-MODEL.md)**, which was produced by a
22-agent verification pass against the repo (264 findings survived, 154 refuted).
It found that this document never mentions the OBO causal spine at all, and that
the one artifact declaring a food→disease ladder — `bfo_stack_ontology.json` — is
absent from the object-type table, the link-type row and the blocker list. Read
that file first; this one is the argument, not the inventory.

**Order of work, corrected.** Identity (the crosswalk) and stage one (the
controlled vocabulary) are done and gated. The manifest is now blocked on the
**layer naming collision**, not on identity — see
`GROUNDED-OBJECT-MODEL.md` §2 for the resolution (`spine:` named stages; the
format stack keeps `L0–L9`) and §8 for the ordered blockers.

*Correction:* an earlier version of this line gated all work on blocker 1 while §6
of this same file declared blocker 1 cleared. Both statements were in the file at
once for several hours.

---

# Reading the full Palantir architecture — what to take, what to refuse

Foundry's architecture is the right answer to *its* problem: a multi-tenant
enterprise operating system where tens of thousands of humans and agents read and
write to operational systems under granular access control. Almost none of that
problem exists here, and copying the answer to a problem you do not have is the
main way projects like this die.

## 1. The fourfold, with one substitution

Palantir models decisions through **Data · Logic · Action · Security**. Security is
load-bearing there because Foundry is multi-tenant: row and column controls, marking
based access, scopes inherited by agents from users.

**Published evidence has no row-level access control problem.** A citation is not
sensitive; the entire point is that anyone can check it. Dropping to a threefold
would be a mistake though — there *is* a fourth dimension here, and it is the one
this project has spent its whole life on:

> **Data · Logic · Action · Provenance**

| | Foundry asks | This ontology asks |
|---|---|---|
| The fourth pillar | *may this user see this value?* | *where did this value come from, and what may it license?* |
| Enforced by | ACLs, markings, scoped tokens | `method_ref`, `source_ref`, grade, weakest link, the population fence |
| Failure mode | data leak | **a number used outside what produced it** |

That substitution is the architectural version of `Declared[T]`. It is why this is
a different system rather than a smaller one.

## 2. Language, Engine, Toolchain — build two, refuse one

| Layer | Foundry | Here |
|---|---|---|
| **Language** — objects, links, properties, actions, logic | dozens of components | **Build it.** This is the `ontology.json` manifest. It is the whole deliverable. |
| **Engine** — high-scale SQL, real-time subscription, atomic transactional writes, CDC, batch mutation | very large | **Refuse.** Nothing in this domain needs it (see §3). |
| **Toolchain** — SDK generation, DevOps, governance | OSDK + Developer Console | **Build a thin slice:** the generator and the wheel. No console, no hosting, no marketplace. |

Their own text says the Ontology "is not a 'semantic layer'" and cannot be done
thinly. That is true when Action means writing back to an ERP in real time under
audit. Here, Action means *appending a validated declaration to a register*. The
same word, two orders of magnitude apart.

## 3. MMDP — refuse it, and say why in one number

"Any data, any compute, any model, anywhere" answers enterprise heterogeneity:
Iceberg catalogs, Spark, Flink, DataFusion, Polars, DuckDB, BYO containers,
pushdown to Databricks and Snowflake.

**This ontology fits in a wheel.** The registers are static JSON. The mechanism
model is pure standard library with zero runtime dependencies and 408 passing
tests. The crosswalk is 2,797 rows. There is exactly **one** genuinely large
dataset — the ~2M-record PubMed corpus — and the correct architecture for it is not
a data plane. It is a service behind an **optional HTTP lane** that the SDK works
without.

Offline-first is not a limitation to apologise for. It is the only version a
researcher, a student, or a journal reviewer can actually run, and it is the reason
this can be a standard rather than a product.

## 4. The inversion worth naming

Foundry's ontology is **private per customer**: your OSDK is generated from *your*
Ontology, and the ontology models one enterprise's world.

A nutrition ontology is the opposite — **one shared ontology, many consumers**. That
single difference rewrites three things:

- **Versioning** becomes semver with a deprecation policy, not per-tenant
  regeneration. Consumers pin; you cannot silently reshape a type under them.
- **Governance** becomes public change history, not access control. The `as_of`
  discipline already in every register is the right primitive.
- **Authorship must be explicit.** Only ACA is authored; FoodOn, ChEBI, CDNO and VMH
  terms are imported under their own terms. A shared ontology that blurs this is
  claiming other people's work.

Palantir cannot ship a public ontology because their customers' ontologies are the
proprietary asset. That gap is the opening.

## 5. The nine capability sets, triaged

| Capability set | Verdict |
|---|---|
| Ontology **Language** | **Build** — the manifest |
| Ontology **Toolchain** | **Build thin** — generator + wheel |
| Ontology **Engine** | Refuse |
| **Data Services** | Refuse — registers are files |
| **Logic Services** | **Have already** — digestion engine, auditor, validators, case ledger |
| **Workflow Services** | Refuse |
| Analytics & Applications | Out of scope — the hub already does this |
| Automations | Refuse |
| Product Delivery toolchain | Refuse |
| *(mesh: Storage, Compute, Networking, Security, Governance, Workspace)* | Refuse all six — none has an analogue at this scale |

**Two of nine.** That is the honest scope, and it is achievable. The Logic layer is
the one usually missing from a project like this, and here it already exists and is
tested — which is why the SDK is a packaging problem rather than a research problem.

## 6. The blocker is cleared

`MASTER_CROSSWALK.tsv` has one canonical copy — `biology_as_code/` — and the extract
it derives from is now joined to it by a written, tested, byte-exact transform rather
than by an assumption. The identity spine is reproducible from a VMH snapshot in two
commands. Work above this line can start.

What the decision surfaced in its place is smaller and sharper: the `inchiKey`
column is entirely `OPEN`, so the table's cross-registry identity claims rest on the
registries agreeing with each other, which nothing here checks. The SDK should
therefore expose identity as `Declared[T]` from day one — not as a courtesy, but
because the honest value for "is `kegg:C00001` the same substance as `chebi:15377`?"
is currently `OPEN`.
