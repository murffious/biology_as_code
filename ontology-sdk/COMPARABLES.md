# Comparables — Theraos, and what our version of that page would say

**Theraos** ("Agentic OS for Therapeutics") is the same play in a neighbouring
domain: a curated ontology as knowledge graph, sold as grounding for an agent.
Its pitch is three lines — *curated therapeutic ontology (reduce hallucinations),
frontier AI agent, domain-specific applications* — and its proof is a count board:

> Therapeutics ~30,000 · Clinical trials ~300,000 · Biopharma ~3,000 · Biotech funds ~300

Useful as evidence that the shape works commercially. More useful as a contrast.

## The legibility move worth stealing

They make an ontology legible by **leading with object-type counts**, not with a
philosophy of knowledge representation. A node-link diagram plus four numbers, and a
reader knows what is in the box.

Ours, counted from the registers on 2026-08-29:

| Object type | Count | Source |
|---|---:|---|
| PubMed corpus records | **2,020,000+** | the corpus |
| Crosswalk rows (identity map) | **2,797** | `MASTER_CROSSWALK.tsv` |
| Search index entries | 604 | `search-index.v1.json` |
| Ingredient lists | 249 | `ingredient-lists.v1.json` |
| Nutrients | 169 | `nutrient-register.v1.json` |
| Brands | 86 | `brands.v1.json` |
| UPF tracker rows | 75 | `upf-tracker.v1.json` |
| **Laws** | **47** — 9 gates, 38 bounds | `laws.py`, CI-asserted |
| Curated OBO terms | 51 across 6 layers | `bfo_stack_ontology.json` |
| Nobel prizes | 38 | `nobel-nutrition.v1.json` |
| Standards catalogued | 19 | `standards-catalog.v1.json` |
| Digestion state machines | 9 | `machines/data/stage/` |
| Processing definitions | 7 | `processing-definitions.v1.json` |

## The honest diff, which is the whole point

**Their big numbers are inherited; ours are curated.** ClinicalTrials.gov hands you
300,000 trials for free. Nutrition has no equivalent registry, which is why the one
number of ours that is comparable in scale — 2.02M corpus records — is also the one
we did not have to build. Everything curated is three orders of magnitude smaller.

That ratio is not a gap in our execution. **It is the field's condition, and it is
what the book is about.** The apple chapter says it precisely: a ≥2,000-cell grid
with fewer than ten cells ever measured in a human.

So a count board built like theirs would misrepresent us in both directions — it
would look thin next to 300,000 trials, and it would imply the thinness is ours
rather than the field's.

## What our page should do instead, and it is a genuine differentiator

Print the **declared-unknown count next to every object count.**

> Of the 33,564 cells in the identity map, **20,983 are `OPEN`** — 63% of the
> crosswalk is explicitly declared unknown rather than left blank.

Theraos would never print that number, and no ontology-as-product would, because it
reads as incompleteness. Here it is the deliverable: it is the difference between a
map with holes and a map that *knows where its holes are*, and it is only printable
at all because `OPEN` ≠ blank. Appendix D already commits to this posture — *the
page of OPENs is the measurement*.

That is the count board to build: **every object type, with its OPEN column.** It is
honest, it is unusual, and it is the visible form of the one primitive we own.

## Two structural differences to hold onto

**They sell a private instance** — *"Build your private Theraos"* — which is the
Foundry model: the ontology is the customer's asset. Ours is one public ontology,
many consumers, which is the inversion that makes a shared standard possible and a
product harder.

**They lead with the agent; the ontology is grounding for it.** We lead with the
record; the agent is the Epilogue's acceptance test. Same two components, opposite
emphasis — and the emphasis is the argument, since a coach built on the record layer
alone is a citation engine with nothing to say about dinner.
