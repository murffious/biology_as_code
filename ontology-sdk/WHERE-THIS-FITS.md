# Where this fits, and what we own

Two questions, answered from the registers rather than from enthusiasm:
**which layer of our own audit does an ontology actually move**, and
**what do we borrow from Palantir versus build ourselves**.

---

## Part 1 — It is an L2/L3/L9 intervention, and the numbers say so

The nine-layer stack already scores the thing an ontology would fix.
From `standardization-chart.v1.json` (as_of 2026-08-31), threshold = 60:

| Layer | Nutrition | Physics | vs threshold |
|---|---:|---:|---:|
| L2 Identity | **33** | 90 | **−27** |
| L3 Vocabulary & reference data | **45** | 92 | **−15** |
| L9 Traceability | **30** | 88 | **−30** |

> **Corrected 2026-08-31, and it inverts what this file used to say.** L2 Identity
> read **70** through working paper v1.3 and was corrected to **33** in v1.4. This
> section previously ran: *"Nutrition L2 → L3: 70 → 45. A 25-point fall. Physics L2 →
> L3: 90 → 92. Level."* At the corrected score nutrition goes **33 → 45**, which is a
> 12-point **rise**, and the cliff this file was built around does not exist.

Now the step between the first two:

> **Nutrition L2 → L3: 33 → 45.** Identity is *worse* than vocabulary.
> **Physics L2 → L3: 90 → 92. Level.**

**The finding survives the correction and gets stronger, which is why the argument is
restated rather than withdrawn.** The old reading had to explain why L2 passed while
L3 failed — a field with good identifiers and bad vocabulary. The correction removes
that puzzle. The reason v1.4 gave for dropping L2 is that identifiers exist for
branded, packaged, barcoded goods and **nothing plays that role for a generic
unbranded food**. That is not an identity failure that happens to sit next to a
vocabulary failure. It is a stage-one gap surfacing at the identity layer: *you
cannot mint a stable identifier for a concept nobody has defined.*

Talisman's first property — each stage builds the next — predicts exactly this. If
stage one was never built, stage three cannot be sound, and the corrected scores show
the damage is **lowest in the stack**, not at L3. The pipeline reading now explains
both numbers instead of one.

The distinction the field keeps blurring — taxonomy versus ontology — still maps onto
those two layers:

| Concept | What it is | Our layer | Score |
|---|---|---|---|
| **Taxonomy** | hierarchy, classification, identifiers | **L2 Identity** | 33 — failing |
| **Ontology** | *typed relations between the identified things* | **L3 Vocabulary & reference data** | 45 — failing |
| **Knowledge graph** | the populated instances | the registers + the corpus | — |
| **Semantics** | data plus the understanding to act on it | what the SDK exposes | — |

**Nutrition has taxonomies and lacks ontologies, and the 25-point cliff between
L2 and L3 is that sentence, measured.** The field solved naming — FoodOn, GTIN,
FDC, INFOODS tagnames all exist and work, which is why L2 is the only layer above
the floor. What it never built is the layer that makes those names *resolve to each
other* with typed, traversable relations. In physics the two layers are level
because SI units and CODATA reference values are the same artifact as the naming.

So the ontology work has a measurable target rather than a vibe: **move L3 from 45
toward 60**, with L2 already in hand as the foundation. It is the cheapest
remaining move on the board — every other sub-floor layer needs either new
instruments (L1), new institutions (L8), or a discipline no schema can supply (L7,
at 20). L3 needs a graph, and the pieces are already on disk.

**And L9 is the sleeper.** Traceability sits at 30 — thirty points below the floor,
against physics at 88. Traceability is the one capability an ontology delivers that
a relational store plus a language model structurally cannot: the chain from an
answer back through every link to the source datum. Ours already has the vocabulary
for it (`method_ref`, `source_ref`, weakest link, the population fence). It has
never been assembled into a traversable chain. **One artifact, three layers.**

*(Honest note: these are calibrated ordinal expert judgments, not measurements, and
the framework is not externally validated. A 25-point step is a large ordinal step,
not a quantity. The direction is the claim; the arithmetic is not.)*

---

## Part 2 — Borrow the language, own the model, refuse the platform

The instruction is right: use it, do not reinvent it, and still own something.
Here is the line, drawn explicitly so it can be checked later.

### Borrow — the design language, verbatim

These are public, documented, and mostly not Palantir's invention anyway (their own
docs cite domain-driven design, the rule of three, open-closed, and Java's
covariance rules). Reinventing the vocabulary would cost months and produce
something worse that nobody else can read.

| Borrowed | Used as-is |
|---|---|
| **Object type / link type / action type** | the manifest's three top-level kinds |
| **Interface** — abstract, multiple inheritance, no backing data | `Gradeable`, `Declarable`, `Fenced`, `Refusable` |
| **Shared property** — one definition, reused across object types | **`nutrient_ref` + `method_ref` as a shared property pair** |
| **Struct + main field** | an FDP-1 value: six fields, one of them primary |
| **Value type** — a semantic wrapper on a field type | `Declared[T]` |
| **Derived property** — computed from links, never stored | the weakest-link grade |
| **Object-backed link** — a relationship that carries metadata | the claim→study *join* |
| **Function** — server-side logic over the ontology | `digest()`, `audit()`, `layer_pass()` |
| The 4 design principles · the 8 anti-patterns | the review checklist in `PALANTIR-PRINCIPLES.md` |

**The single best thing borrowed is `shared properties`**, and it is not obvious.
Our standing hazard is that `nutrient_ref` must travel with `method_ref` or the
FIBTG-vs-FIBC distinction silently dies — today that is a rule enforced by prose and
a validator. As a shared property pair defined once and reused by FDP-1 values,
EDP-1 exposures and MI-Nutrition composition, **it stops being a convention and
becomes structural.** That is a real defect fixed by adopting someone else's noun.

### Own — the domain, and the primitives the domain forced

Nothing below is derivable from their docs. This is the part that is ours, and it is
the part worth publishing.

1. **The OBO causal spine.** L1 Food → L2 Compound → L3 Mechanism → L4 Physiology →
   L5 Outcome, keyed to FOODON / ChEBI / Reactome+Rhea / GO+PATO / MONDO+HPO, with
   RO for relations. Deliberately small and hand-curated — *~50–200 curated terms
   beat a 40k GO dump*. Nobody else has this shape for food.
2. **`Declared[T]` — three states, not two.** `OPEN` ≠ `NONE` ≠ a value. Every
   generated SDK in existence collapses the first two into null. Ours cannot,
   because the type will not let it. Tested, in `declared.py`.
3. **Weakest-link grading as a derived property.** Their derived properties keep a
   value in sync; ours refuses to let a score outrank its worst input. Averaging is
   banned by construction.
4. **Refusal semantics — five states.** HOLDS / UNEVALUABLE / REFUSE / OPEN /
   REFUTED, with `Confirmed` structurally unreachable from a mechanism walk and a
   test that proves it. No evaluation vocabulary in nutrition makes the last
   distinction.
5. **The population fence as a first-class property.** Not access control — *scope*.
   It travels with the estimate and marks where it stops applying.
6. **Provenance as the fourth pillar, replacing security.** Argued in `DESIGN.md` §1.
7. **The Nine-Layer Case Ledger** — the instrument that scores any object against
   the stack, with `score_artifact` and `score_construct` as separate columns.

### Refuse — the platform

| Refused | Why |
|---|---|
| Object backend (Phonograph, Object Storage v2, Object Data Funnel, Object Set Service) | Built for tens of billions of objects per type. Our crosswalk is 2,797 rows |
| MMDP — Iceberg, Spark, Flink, DuckDB, BYO compute | The whole ontology fits in a wheel |
| Security model — row/column/cell, markings, scoped tokens | Published evidence has no access-control problem |
| **Object Views** | Their docs are explicit that views are *"separate from"* the ontology — a presentation layer. **The evidence hub is therefore not part of this ontology and must not be modelled into it** |
| Developer Console, Marketplace, hosting, WebSocket subscriptions | Platform features for a multi-tenant product |
| Ontology-as-container scoped 1:1 to a space, private or shared per organization | **No analogue.** Theirs is private per customer; ours is one public ontology, many consumers |

That last row is the inversion the whole project turns on. Foundry's ontology is the
customer's proprietary asset, which is precisely why Palantir cannot ship a public
one. **A shared, public, versioned nutrition ontology is the thing their architecture
is structurally unable to produce** — and it is available to us for the cost of
adopting their vocabulary and refusing their platform.

Their governance is organization membership. Ours has to be semver, a deprecation
policy, public change history, and the `as_of` discipline already in every register.

---

## What this changes about the plan

Cleared: `MASTER_CROSSWALK` has a canonical copy (`biology_as_code/`), a written
transform from its extract, and a byte-exact gate. Identity is L2, our only passing
layer, and it is now reproducible rather than inherited — the L2→L3 bridge has a
foundation that can be rebuilt from a snapshot.

The correction is worth carrying into the manifest: the copies were never in
conflict (0 value differences across 24,893 differing cells). What we had was a
derivation nobody had written down, which for a month was indistinguishable from
corruption. **A published ontology must declare its derivations, not just its
types** — otherwise every downstream consumer has to re-derive the question of
whether two artifacts agree, and most will guess.

Added by this pass:
- Adopt **shared properties** for the `nutrient_ref`/`method_ref` pair — the highest
  structural return of anything in their docs.
- Resolve the **"layer" misnomer** before the manifest exists. Two numbering systems
  named L cannot both survive; per their own naming rule, *qualify ambiguous terms
  specifically*.
- Record L3=45 and L9=30 as the **stated targets** for the ontology work, so the
  claim "this helps" is falsifiable against a register we already publish.
