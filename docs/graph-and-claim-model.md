# The graph and the claim model

Two additions that fit together: a property graph over the constitution, and a
model that predicts claims against it.

```
biology_as_code/
├── graph/          schema.sql · store.py · build.py · export.py
└── claim_model/    rosetta.py · court.py · model.py · __main__.py
```

Quick start:

```bash
python -m biology_as_code.claim_model "Vitamin C increases non-heme iron absorption"
python -m biology_as_code.claim_model --metrics
```

---

## 1. The graph

Built from the repository's own registers — nothing is invented, and where a
register leaves a magnitude open the graph leaves it open too.

| Source | Contributes |
|---|---|
| `engine.laws.registry` | 47 laws, 7 systems, 44 organs, 9 gates, 47 bounds |
| `examples/contributions/*.json` | 4 contributions, 2 sources |
| `examples/claims/claim_*.json` | 2 hand-adjudicated gold fixtures |
| `examples/claims/food_health_claims_500.json` | 500 foods, 1,228 claims, 88 compounds, 27 outcomes |

**2,005 nodes, 5,440 edges.**

### Why SQLite

The store is SQLite, not Neo4j. Traversal depth here is small — a claim resolves
in a handful of hops — so the engine is not the interesting part. What matters is
that the graph builds identically in CI with no install, and that the closed
ENUMs can be enforced as constraints rather than conventions. Export to Cypher,
Turtle or GraphML when a real graph engine is wanted:

```python
from biology_as_code.graph import build
from biology_as_code.graph.export import to_cypher, to_turtle, to_graphml
```

The Turtle export emits `prov:wasDerivedFrom` wherever an edge names its
evidence, which is the join point with the repo's existing `aca.ttl` and
`claim-shape.ttl`.

### Three rules enforced by the database

These are structural, so they survive direct SQL and cannot be forgotten by a
caller:

1. **Node labels and relations are closed sets.** A relation outside the
   RelationType ENUM is rejected.
2. **A Gate may not carry a magnitude.** Gate/bound collapse is a trigger
   violation, not a code review comment.
3. **An edge asserting a magnitude with no evidence is refused.** Empty beats
   fake, at the storage layer.

```python
g.add_edge("LAW-004", "EXPANDS_BOUND", "bound:LAW-004", asserts_magnitude=True)
# GraphError: fail-closed: edge asserts a magnitude with no evidence node
```

### What the graph says about the register

`GraphStore.integrity_report()` on the current register:

| Measure | Value |
|---|---|
| Laws | 47 |
| Laws with no evidence attached | 44 |
| Laws asserting a bound with no source | 44 |
| Laws with no categorical gate | 38 |

The register that exists to enforce *gate ≠ bound* is **81% bound-only**, and
94% of its laws carry no evidence contribution. That is not a defect in the
graph; it is the graph reporting the register's actual state, which is the same
finding the manuscript audit reached independently.

---

## 2. The claim model

Three stages. Only the middle one is learned, and that split is the design.

```
surface text ──▶ Rosetta ──▶ Court ◀── graph
                 (rules)     (rules)
                                ▲
                                │
                     EvidenceGradeModel (learned)
```

### Rosetta — surface language to typed relation

Deterministic and lexical. It decides what *kind* of assertion a claim is, and
returns the token that produced the decision, because this is the stage most
likely to be wrong and so must be the easiest to inspect.

```python
>>> parse("Iron supports energy").verb_class
'soft'
>>> parse("Vitamin C increases iron absorption").relation
'EXPANDS_BOUND'
```

Hedging is treated as a modifier rather than a class: *"may increase"* is still a
bound claim, asserted tentatively, and the Court caps it at Plausible.

### EvidenceGradeModel — the learned component

Multinomial logistic regression over hashed word, bigram and 4-character
features, in pure Python. No third-party dependency, deterministic given a seed,
trains in under two seconds on the 1,228 labelled claims.

It predicts **one thing**: the evidence grade (A/B/C/D) a claim would receive.

| Metric | Value |
|---|---|
| Held-out accuracy | **0.943** |
| Majority baseline | 0.703 |
| A (n=173) | P 0.96 · R 0.99 · F1 0.98 |
| B (n=40) | P 0.87 · R 0.98 · F1 0.92 |
| C (n=33) | P 1.00 · R 0.64 · F1 0.78 |

**Two limitations worth stating plainly.** Grade D — "contested,
marketing-driven, or contradicted by better-designed studies" — has **zero
examples** in the corpus, so the model cannot predict it at all; the class exists
in the taxonomy and not in the data. And class C recall is 0.64, with seven of
eleven misses landing in A: the model is optimistic exactly where the corpus is
thinnest. Both argue for labelling more C and D claims before this is trusted on
weak evidence.

### The Court — verdicts are computed, never predicted

The precedence rules are fixed and ordered; the first to fire wins.

| Rule | Condition | Verdict |
|---|---|---|
| 1 | soft or marketing verb | REFUSE |
| 1b | no recognised claim verb | UNEVALUABLE |
| 2 | gate closed in the graph | Busted |
| 3 | malformed mechanism, or endpoint with no path | REFUSE |
| 4 | nothing in the register grounds it | UNEVALUABLE |
| 5/6 | typed, grounded, graded | Confirmed / Plausible |

**Rule 4 is the reason the model sits underneath the Court rather than replacing
it.** A classifier asked to choose among four verdicts will always choose one.
This returns *"I cannot evaluate that"*.

The structural guarantee: the learned component's output space is evidence
grades only. It has no path to "Confirmed". A mis-prediction can weaken a verdict
but can never manufacture one — and that is asserted by a test.

### Grounding

A claim grounds to a law two ways: by naming a Compound or Nutrient the graph
knows, or by sharing distinctive vocabulary with the law's statement, gate,
bound, conditions or subsystem. Terms are weighted by rarity — a term appearing
in one law counts for more than one appearing in twenty — and a law needs two
distinct term hits plus enough combined rarity to count. A single shared word
cannot pull in an unrelated law.

### Worked examples

```
Vitamin C increases non-heme iron absorption
  → Confirmed (rule 5) · EXPANDS_BOUND · 5 laws · grade A

Fat-free spinach delivers carotenoids to prevent deficiency disease
  → Busted (rule 2) · gate fail · LAW-020 gated on fat co-presence

This superfood boosts immunity and detoxifies the liver
  → REFUSE (rule 1) · marketing verb, weakest of 2 assertions

Eating oats prevents heart disease
  → REFUSE (rule 3) · endpoint with no mechanism named

Fibre may be associated with improved bowel regularity
  → UNEVALUABLE (rule 4) · well-formed but ungrounded
```

The second is the interesting one: the claim is Busted rather than refused
because *"fat-free"* states the absence of the very condition LAW-020's gate
requires. The Court reads gate conditions from the whole claim even when
adjudicating one atom of it, because splitting the sentence would separate the
condition from the assertion.

---

## 3. CLI

```bash
# rule on claims; exit code 1 if anything is refused, so it can gate a build
python -m biology_as_code.claim_model "claim one" "claim two"

# emit claim_audit.schema.json fixtures
python -m biology_as_code.claim_model --json "Iron supports energy"

# constitution only, no learned component
python -m biology_as_code.claim_model --no-model "..."

# graph counts, register integrity, model metrics
python -m biology_as_code.claim_model --metrics
```

---

## 4. Known limits

- **Grade D is unlearnable** from the current corpus (zero examples).
- **Rosetta is English and lexical.** It types on surface verbs, so a claim
  phrased around an unusual verb falls through to UNEVALUABLE rather than being
  mistyped — the safe direction, but it will under-resolve.
- **Grounding is literal by design.** A fuzzy matcher would let the Court ground
  a claim on a resemblance, which the register forbids; the cost is that
  paraphrases fail to ground and return UNEVALUABLE.
- **The gold set is two fixtures.** Both pass, but two is not an evaluation. The
  1,228 food claims carry evidence grades, not verdicts, so they train the model
  without validating the Court. Adjudicating a few dozen claims by hand is the
  single highest-value thing that could be added.
- **The register is 94% unsourced,** so "Confirmed" currently rests on grounding
  plus a predicted grade, not on attached primary evidence. As contributions
  land, the Court should require evidence strength for Confirmed — the field is
  already carried on the edge and is not yet used in the rules.
