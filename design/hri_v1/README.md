# `hri_v1/` — Host Response Index, editor's draft

Dropped in as authored. **These three files are verbatim** — spec, record
schema, and the juice-versus-orange instance. Nothing in them was edited to fit
the repo; where they and the engine disagree, the disagreement is recorded below
rather than smoothed over.

| File | What it is |
|---|---|
| `HRI-1.0-spec.md` | Editor's Draft 0.1.0 — the 7×3 matrix, Liebig floor rule, coverage tiers, anti-capture invariants |
| `HRIRecord.schema.json` | The record shape (JSON Schema 2020-12) |
| `example_juice_vs_orange.hri.json` | Teaching case 1 — the RDA-adequate glass |

Status: **pre-Stage-2 proposal.** No engine code implements HRI yet. The spec is
the target; `responses/` is where it will be built.

## What is checked

`tests/test_hri_artifacts.py` runs in CI. It pins the claims these documents make
*about this repository*, so they cannot rot silently — which is not a
hypothetical concern here: this branch shipped a bug where a relation type was
added to one vocabulary and three others were missed, and every test stayed
green. See `tests/test_graph_relation_vocabulary.py`.

Currently pinned:

1. **The `SevenSystem` claim holds, verbatim.** The spec says the matrix reuses
   the engine's existing enum. It does — the schema's system list and
   `engine.laws.models.SevenSystem` are exactly equal, in both directions. If
   either moves, the test fails.
2. **The example obeys its own floor rule.** `floor_cell` is the argmin over
   covered critical cells (`Energy.acute`, subscore 18, below
   `Communication.acute` at 22) — not an assertion pasted in by hand.
3. **The coverage-tier caps hold.** Tier 0 may not exceed `provisional`; the top
   band requires Tier ≥ 2 on both critical acute cells.
4. **`review_by` is present.** The anti-1941 field.

## Divergences to reconcile

**D-HRI-1 — the clock axis is a fourth vocabulary, and it overlaps the engine's
by zero values.**

| | Values |
|---|---|
| HRI matrix clocks | `acute`, `adaptive`, `parameter` |
| `engine.clocks.Clock` | `fixed`, `adaptation`, `diurnal`, `meal`, `bite`, `event` |

They are measuring different things, and that is defensible: `Clock` types *how
fast a state variable changes* (it is the `x-clock` facet on every HostState v2
field), whereas the HRI clocks type *the horizon over which a response
manifests*. A meal-clock variable can produce an acute response and contribute
to parameter drift.

What makes it worth flagging rather than ignoring is `adaptive` / `adaptation` —
two near-identical names on two different axes, which is precisely the shape of
the LAW-039 bug. The test asserts the two sets are **disjoint**, so if someone
later decides they should be unified, that is a deliberate edit to a failing
test rather than an assumption that quietly half-holds.

Not resolved here. Resolving it means deciding whether HRI's horizons are a
derived view over `Clock` or an independent axis, and that is a spec decision.

**D-HRI-2 — schema `$id` host.** `HRIRecord.schema.json` uses
`https://biology-as-code.org/schemas/…`; every other schema in the repo uses
`https://github.com/murffious/biology_as_code/schemas/…`. Left as authored —
picking a canonical host is a project decision, not a cleanup.

**D-HRI-3 — the repo's zero-dependency validator cannot check this schema.**
`packets/validate.py` implements a deliberate subset of JSON Schema and does not
support `$ref`, which `HRIRecord.schema.json` uses for `CellRef` and
`CellResult`. The tests therefore check the example structurally rather than by
schema validation. Either the validator grows `$ref` support or the schema is
rewritten `$ref`-free, as `nutrient-node.schema.json` already was.

## Dependencies before HRI can produce a real record

- `responses/` has **one** executable protocol (`GlycemicResponse/1.0`).
  `SatietyResponse` and `LipemicResponse` raise. So `Communication.acute` — a
  universally critical cell — cannot be `measured` or `modeled` from a versioned
  protocol yet; the example correctly marks it `modeled` against a
  `SatietyResponse/1.0` ref that does not exist as executable code.
- The Tier-1 licence clause ("a VHM version may produce Tier-1 records only while
  green on the ward-literature suite") already has its mechanism: the five
  conformance tests in `tests/conformance/` are strict-xfail, so a model cannot
  claim the suite silently. The example's `conformance_ref: PENDING` is accurate.
