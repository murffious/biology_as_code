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

**Stage one was never built.** There is no controlled vocabulary for the nutrition
domain: no single place where a term has one preferred label, its alternates, its
hidden labels, a definition, and a notation.

The evidence is synonym control — Talisman's stage-one core function, alongside
disambiguation and validation. It is implemented **four times, in four files, with
four conventions**:

| File | Mechanism | Hits |
|---|---|---:|
| `build_search_index.py` | `SEARCH_ONLY` dict (line 109) — variants that must reach search but must **not** reach scoring | 16 |
| `ingredient_fda.py` | `synonyms()` parsing FDA's `&diams;`-separated cells | 9 |
| `ingredient_mine.py` | hand-listed aliases (`MSG`, `BHA` …) | 7 |
| `lexicon.py` | phrase aliases, whole-phrase only to avoid loose-token matches | 1 |

Each is defensible in isolation and the split between search and scoring is a
deliberate, documented rule — a search synonym is *not* a lexicon edit, because
`lexicon.py` moves published effect estimates. That rule is correct and must
survive. But four mechanisms is Palantir's **rule of three**, breached, at the
vocabulary layer.

**SKOS is present and unused.** `biology_as_code/schemas/aca.ttl` imports the SKOS
namespace and then uses it for exactly one `skos:note`. The pattern is known here.
It has never been applied to the food and nutrient vocabulary.

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

1. **Canonical `MASTER_CROSSWALK`.** Unchanged, still first — identity is the
   foundation and two copies currently disagree.
2. **A controlled vocabulary, SKOS-encoded.** One concept per term: `prefLabel`,
   `altLabel`, `hiddenLabel`, definition, notation, and a source. Built by
   *consolidating the four existing mechanisms*, not by starting over — they are the
   raw material and they already encode real curatorial decisions.
   **Preserve the search/scoring split explicitly**: search-only variants are
   `hiddenLabel`, scoring-bearing variants are `altLabel`. SKOS has the distinction
   built in, which is a second structural defect fixed by adopting an existing noun.
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
