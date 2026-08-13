# Divergences from the work order

Where the work order and repo reality disagreed, repo reality won and the
divergence was logged here rather than silently adapted to.

---

## D-001 — `design/hoststate_v0.yaml` and its README were never delivered

**Work order says:** "New reference design files will be dropped into `design/`
before you start: `hoststate_v0.yaml` + its README (five-strata host packet,
four mandatory facets) and this work order."

**Repo reality:** `design/` did not exist at baseline commit `21f73ac`. Neither
`hoststate_v0.yaml`, its README, nor the work order itself were present anywhere
in the tree (checked `design/`, `docs/`, `schemas/`, and the git history).

**Consequence for Phase 3.** The five strata and four mandatory facets are fully
specified *in the work order prose itself*, so Phase 3 was implemented from that
text rather than blocked:

- strata: `constants` / `slow_state` / `fast_state` / `context_stream` /
  `response_history`
- facets: `x-binding_site`, `x-clock`, `x-tier` (T0–T4), `x-evidence_state`
  (`verified` / `supported` / `contested` / `candidate`)

Two items were named in the work order but had **no source to copy from**:

1. *"seed registry rows are in the hoststate_v0 README"* — the genome
   `ModifierBinding` seed rows, written to `design/genome_modifier_seed.json`.
   Six candidates were authored from the repo's own law and pathway content
   (MTHFR/one-carbon, HFE/iron, LCT/lactase, FTO/appetite, CYP1A2/caffeine,
   APOE/lipoprotein). **Only three survived**: `tools/resolve_bindings.py`
   rejected MTHFR outright (it pointed at a parameter that does not exist), and
   review of the rest found CYP1A2 and APOE bound to parameters that *resolve*
   and are wrong — elapsed time since eating is not caffeine clearance, and
   APOE acts post-absorptively rather than on fat absorption. All three are
   recorded in an `unmodellable` section naming the parameter that would have
   to exist first. They are **candidate seed rows, not the approved v0
   registry** — reconcile against `hoststate_v0.yaml` when it lands.
2. The exact v0 field-to-stratum mapping. Every existing flat `HostState`
   property was mapped into a stratum by this work; the mapping is recorded in
   `HostState.v2.schema.json` and is likewise subject to reconciliation.

**Action on delivery of `hoststate_v0.yaml`:** diff it against
`machines/data/schemas/HostState.v2.schema.json` and against
`design/genome_modifier_seed.json`, and treat the yaml as authoritative.

---

## D-002 — no unmerged LAW-048–053 drafts exist in this repo

**Work order anticipates:** possible conflict with "unmerged LAW-048–053 drafts".

**Repo reality:** the law registry tops out at LAW-047 and no 048+ identifiers
appear anywhere in the tree or in any branch visible to this session
(`main` and `claude/biology-code-audit-typing-tests-rrj43z` only). Nothing was
adapted around them. If those drafts exist privately, the Phase 2 additions to
the law model (`review_by`, `evidence_state`) and the `RelationType` extension
(`CONSERVES`, `IDENTITY`) are the surfaces they will touch.

---

## D-003 — `product_score` generalised rather than removed (option (a))

The work order offered two dispositions and asked for (a) if the interface was
already generic. It is: `interface.py` defines a `Protocol` with plain
request/result dataclasses, and `loader.py` resolves a plugin by environment
variable or import path with a fail-closed unavailable stub. Nothing in the
contract is specific to any product.

So the package became `scoring/` with a documented external-scorer plugin
interface. Two product-shaped details in the *contract* had to change, and these
are breaking for any out-of-tree caller:

| Before | After |
|---|---|
| env var `KIBO_PRODUCT_SCORE_MODULE` | `BAC_SCORER_MODULE` |
| result field `kibo_vars_score` | `vendor_scores` |
| result `schema: "kibo.ProductScoreAnalysis/v1"` | `"bac.ExternalScoreAnalysis/v1"` |
| candidate import `kibo_product_score` | none — the env var is the only entry point |

The old `biology_as_code.product_score` import path is **not** kept as a shim:
keeping it would re-introduce a product identifier into `src/`, which the
no-product gate forbids. The rename is called out in `CHANGELOG.md`.

---

## D-004 — withdrawn; the work order was right about `Modifier`

An earlier draft of this file claimed the `Modifier` dataclass did not exist and
that Phase 2 had introduced it. That was wrong, and it is recorded here rather
than deleted because a divergence log that quietly drops its own errors is worth
less than one that keeps them.

`engine/laws/models.py` has carried `@dataclass(frozen=True) class Modifier`
with exactly the fields the work order named — `id`, `nutrient`, `relation`,
`law_id` — plus `magnitude`, `conditions`, `prior`, `requires_context` and
`note`, since before this work started. No divergence.

What Phase 2 actually did is additive and is not a divergence either: the
pathway-graph `Modifier` is enough to walk a graph and not enough to bind host
state, so `engine/modifiers.py` adds `ModifierBinding` alongside it with the
four fields the work order asked for (`effect_direction`, `effect_magnitude`,
`evidence_state`, `binding_site`). The original `Modifier` is untouched.

---

## D-005 — clock typing added as a new enum, `sim/state.py` left structurally intact

`sim/state.py` is a small dataclass holding simulation counters; it has no field
that a clock type would attach to without changing its shape and breaking the
phase engine. The `Clock` enum was therefore added in `engine/clocks.py` and
applied where the work order actually needs it — as the `x-clock` facet on every
`HostState` v2 field. `sim/state.py` gained a `clock` attribute defaulting to
`Clock.MEAL`, which is additive and does not disturb existing consumers.
