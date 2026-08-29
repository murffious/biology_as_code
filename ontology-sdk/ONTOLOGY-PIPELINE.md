# The ontology pipeline — and the stage we skipped

Source: Jessica Talisman's *ontology pipeline*, a staged framework for building
semantic expressiveness. It reframes the plan in `DESIGN.md` and
`WHERE-THIS-FITS.md`, so it is recorded here rather than folded in quietly.

```
controlled vocabulary → metadata schemas → taxonomy → ontology → RDF knowledge graph
```

Two properties of the framework matter more than the stages themselves:

1. **Each stage builds the next.** You cannot model what you have not defined.
2. **Each stage is independently usable.** *"For many organizations, you may have a
   controlled vocabulary, arrive at metadata schemas, and that's all you're going to
   work with for right now. It's just enough context for many."* You do not have to
   reach the knowledge graph to get value.

Palantir's docs assume you already have your terms. This framework says the terms
**are stage one**, and that skipping it is the common failure.

---

## Where this project actually is

**We jumped to stage four.** The OBO causal spine — L1 Food → L2 Compound →
L3 Mechanism → L4 Physiology → L5 Outcome, keyed to FOODON/ChEBI/Reactome/GO/MONDO
with RO for relations — is a stage-four artifact. It declares typed relations
between concepts. It is good work.

**Stage one was never built** — v0 now exists; see *What was actually wrong*, below.
There was no controlled vocabulary for the nutrition domain: no single place where a
term had one preferred label, its alternates, its hidden labels, and a source.

Synonym control — Talisman's stage-one core function, alongside disambiguation and
validation — is handled in four places:

| File | Mechanism | Owns its terms? |
|---|---|---|
| `lexicon.py` | `FACTOR_PHRASES` / `OUTCOME_PHRASES` — whole-phrase aliases; drives corpus screening and gold-card binding | **yes** (74 + 41 groups) |
| `build_search_index.py` | `SEARCH_ONLY` — variants that must reach search but must **not** reach scoring | **yes** (10 keys) |
| `ingredient_mine.py` | `ingredient_terms()` reads `aka` / `search` / `search_exclude` | no — reads the register |
| `ingredient_fda.py` | `synonyms()` parses FDA's `&diams;`-separated cells | no — reads FDA source rows |

### The first framing was wrong, and the correction is the finding

This was recorded as *"implemented four times, with four conventions"* — the rule of
three breached. Measured, that overstates it. Only two of the four own any
vocabulary; the other two read terms from a register and from FDA's own data. And
the four barely overlap: across **~1,490 distinct strings, exactly 14 appear in more
than one of them.**

So the defect is not duplication. It is that **every one of these tables maps string
→ string. Not one maps string → concept.** Nothing has an identifier, so nothing can
notice that:

- `cognition` and `cognitive` are two outcome groups for one idea, and the term
  `cognitive` sits in both;
- `sweetener` and `artificial sweetener` express a hierarchy by repeating
  `aspartame` and `sucralose` in both, rather than by a broader/narrower link;
- `fluid intake` is filed under both `oxalate` and `water intake`;
- the typeahead files `osteoporosis` and `bone density` under a search key `bone`
  while the screener files them under `fracture` — **the same word resolves to
  different concepts depending on which reader you are**;
- the ingredient register's `Sodium glutamate` and the lexicon's factor `msg` can
  never be known to be the same substance.

Twelve ambiguous terms, four faked hierarchies, three cross-reader conflicts. Each is
small. Collectively they are precisely what a concept layer exists to prevent, and
none of them was visible before the terms had ids.

The split between search and scoring is a deliberate, documented rule — a search
synonym is *not* a lexicon edit, because `lexicon.py` moves published effect
estimates. That rule is correct, must survive, and is now enforced rather than
remembered: `vocab.lexicon_tables()` returns `prefLabel + altLabel` and is
structurally unable to return a `hiddenLabel`.

**SKOS was present and unused.** `biology_as_code/schemas/aca.ttl` imports the SKOS
namespace and then uses it for exactly one `skos:note`. The pattern was known here
and had never been applied to the food and nutrient vocabulary. It now is:
`evidence-platform/site/nutrition-vocab.v1.json` and its `.ttl` projection, 118
concepts, generated from the tables above and gated to reproduce them exactly.

---

## Why this explains L3 = 45

The nine-layer stack's failing layer is named, in its own words,
**"Vocabulary & reference data."** It scores **45** against a floor of 60, while
Identity above it scores 70.

Read through the pipeline, that is not a mysterious institutional failure. It is a
**stage-one gap being measured at stage four**. The field has identifiers — that is
L2 Identity at 70, and it is why L2 passes. What it lacks is the controlled
vocabulary that makes those identifiers resolve, disambiguate, and carry their
alternates. Physics steps 90 → 92 across the same boundary because SI units and
CODATA reference values *are* the same artifact as the naming.

**So the highest-value next move is not the manifest. It is a controlled
vocabulary** — and, usefully, that is the one stage that pays off on its own.

---

## What that changes about the plan

**Previous order:** resolve the crosswalk → write `ontology.json` → generate the SDK.
**Revised order:**

1. ~~**Canonical `MASTER_CROSSWALK`.**~~ **Done 2026-08-29.** `biology_as_code/` is
   canonical, derived from the extract by a written transform, gated byte-for-byte.
   The copies had never disagreed — 0 value differences. See `CROSSWALK-CANONICAL.md`.
2. **A controlled vocabulary, SKOS-encoded.** **v0 done 2026-08-29.** 118 concepts
   (74 factor, 41 outcome, 3 retrieval-only), 372 `altLabel`, 26 `hiddenLabel`.
   `make vocab` builds it; `make vocab-check` gates it.
   - Built by *describing* the existing mechanisms, not by consolidating them. The
     gate is that `lexicon.py` and `build_search_index.py` regenerate from the
     register **unchanged** — because a vocabulary that led the tables it describes
     would move published effect sizes with nothing in the diff to show it. A layer
     under a live corpus can only be introduced this way.
   - The search/scoring split is preserved and now enforced by which predicate each
     reader may read: `hiddenLabel` for retrieval, `altLabel` for anything that can
     bind a study. SKOS had the distinction built in — a structural defect fixed by
     adopting an existing noun rather than inventing one.
   - Its defects are **declared, not fixed**: 12 ambiguous terms, 4 candidate
     broader/narrower, 3 cross-reader conflicts, 4 redundant retrieval labels,
     ratcheted in `nutrition-vocab.baseline.json`. Merging `cognition` into
     `cognitive` would rewrite screening for every cognition study in the ledger, so
     each fix is made deliberately and its corpus effect measured.
   - **Still missing:** definitions and notations. Every concept has labels and a
     source; none has a `skos:definition`. That is the next stage-one task, and it
     is the one that makes disambiguation possible rather than merely visible.
3. **Metadata schemas.** Largely done — FDP-1, EDP-1, MI-Nutrition, HostState.
   The gap is that they do not yet share a vocabulary layer beneath them.
4. **Taxonomy.** Partly present, scattered across `book/*-taxonomy/`.
5. **Ontology + manifest + SDK.** Where `DESIGN.md` starts. It should start here.

**Conform to a real standard while doing it.** ANSI/NISO Z39.19 governs the
construction, format and management of monolingual controlled vocabularies; SKOS is
the W3C encoding. That pairing matters beyond tidiness: it makes the vocabulary a
**claimable tier** — the free-artifact adoption route from ch 27, and exactly what
ch 58 argues is available to a project with no gatekeeper. A vocabulary that
declares Z39.19 conformance can be *failed*, which is the whole definition of a
standard this book uses.

---

## Three further points worth keeping

**Taxonomy is where inference starts.** Parent-child relations let a system infer:
if B is part of A and C is part of B, then C relates to A. That is the mechanism
behind the claim engine's reasoning, and it means the taxonomy layer is not
bookkeeping — it is the first place the structure does work on its own.

**This is not a job to automate.** *"Many ask, is this something an AI system can
generate? Not very well… this is something that needs human touch."* That is the
same conclusion the case ledger reached from the other direction — a single-pass
judgment needs a second scorer. Both say the curation is the product.

**The IKEA effect is an argument for building it.** Talisman's point is that people
invest in infrastructure they helped make. It is also the honest answer to *"why not
just adopt someone else's vocabulary wholesale"*: imported terms stay imported —
FOODON, ChEBI, CDNO and VMH are referenced under their own licences and are not ours
to relicense. **What is ours is the curation layer over them**: which term is
preferred, which are alternates, which are hidden, what each means in this domain,
and what may be inferred. That layer is authored, publishable, and the thing worth
owning.

---

## Open question for the manifest

RDF knowledge graph or labelled property graph? Talisman is explicit that the two
are siblings and that the pipeline targets RDF. This project has one foot on each:
`aca.ttl` and `claim-shape.ttl` are RDF/SHACL, while the registers, crosswalks and
schemas are JSON with typed links — property-graph shaped.

Not resolved here. But the SDK's generated types are property-graph shaped by
nature, and a controlled vocabulary is SKOS/RDF by convention. **The likely answer
is both, with the vocabulary authored in SKOS and projected into the manifest** —
which is a decision to make deliberately rather than to discover later.
