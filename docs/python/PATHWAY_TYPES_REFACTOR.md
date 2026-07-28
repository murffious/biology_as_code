# Pathway types — de-duplication plan

**Status:** Phases 0–2 **done**. Phase 3 ready. Phase 4 signed off, not started.
**Scope:** the 16 modules in `src/biology_as_code/pathways/` that each declare their own
`PathwayNodeType`, `MetaboliteNode`, `ReactionEdge`, `MetabolicPathway`.

> **Phase 4 vocabulary decision (agreed):** one multi-scale controlled catalog,
> Recon3D-first. Subcellular `m` / `c` / `e` (later `n` / `x` / `g` / `l` / `r`);
> absorptive-teaching scale `lumen` / `enterocyte` / `circulation`. Node identity is
> chemical species **+** compartment, so two pools are two node ids (`orn_m` /
> `orn_c`). `node_type` stays pure role. `edge.location` stays free text for process
> context ("Apical membrane") — membranes are interfaces between compartments, not
> bulk pools. Do **not** admit `LUMEN` / `ENTEROCYTE` / `CIRCULATION` into the shared
> `PathwayNodeType`; that would re-encode the bug into the contract.

---

## Why this is worth doing

Not because duplication is untidy. Because there is **no shared contract**, so the one
cross-cutting consumer — `scripts/export_pathway_packs.py` — has to guess with
`getattr` fallback chains, and it guesses wrong. Verified data loss in shipped packs:

| Pack | What is lost | Cause |
|---|---|---|
| `etc_oxphos` | **Every** edge label is the literal `"step"`. Complex I–IV names gone, `protons_pumped` never exported. | edge field is `enzyme_or_complex`; exporter reads `enzyme` / `process` |
| `cholesterol_biosynthesis` | Most edge labels are `"step"`. | edge field is `enzyme_or_process` |
| `tca_cycle` | Only `NADH-1` survives. No FADH₂, no GTP, no CO₂. | exporter reads `atp_cost` / `nadh_cost` only |
| `pentose_phosphate` | NADPH — the point of the pathway — absent. | field is `nadph_cost` |

`tests/test_pathway_packs.py` passes throughout, because it asserts the generator's
output matches itself ("packs in sync with generator") and that mermaid is non-empty.
Nothing asserts the export *preserved* what the registry held. The TCA invariants test
checks 3 NADH + 1 FADH₂ + 1 GTP against the **registry object**, which is correct — the
pack written from it is not.

So: the duplication is the cause, the lossy packs are the damage, and the packs are what
feeds the book.

---

## What actually diverges

Measured by AST, ignoring comments and whitespace.

**`MetaboliteNode` — 14 of 16 are structurally identical.** Outliers:
`cholesterol_pathway`, `metabolic_pathways`. Effectively already unified.

**`MetabolicPathway` — 16 "distinct" definitions, but all have the same 5 methods**
(`__init__`, `add_node`, `add_edge`, `get_mechanism`, `summary`). Three lack
`get_mechanism` (`cholesterol_pathway`, `metabolic_pathways`, `supporting_pathways`);
`metabolic_pathways` adds `get_net_energy`; `urea_cycle` adds `atp_cost_total` and
`orphan_nodes`. **The only genuine variation is what `summary()` returns.** This is a
textbook template-method split, not 16 different classes.

**`PathwayNodeType` — 8 variants**, all `{SUBSTRATE, INTERMEDIATE, PRODUCT}` plus domain
extras (`SIGNAL`, `REGULATORY`, `LIPOPROTEIN`, `COMPLEX`, `CARRIER`, `POLYMER`) —
**except** `digestion_absorption_pathways`, which is `{LUMEN, ENTEROCYTE, CIRCULATION,
INTERMEDIATE}`. That one is not a role vocabulary at all; it is **anatomical
compartment** wearing the node-type slot. See Phase 4.

**`ReactionEdge` — 15 variants**, decomposing cleanly into three groups:

- **core** (everywhere): `from_node`, `to_node`, `mechanism_id`, `notes`
- **yields**: `atp_cost`, `nadh_cost`, `fadh2_cost`, `gtp_cost`, `nadph_cost`,
  `co2_produced`, `protons_pumped`
- **descriptors**: `location`, `regulation`, `process`, `phase`, `direction`,
  `is_bypass`, `effect`
- **one concept, three names**: `enzyme` / `enzyme_or_process` / `enzyme_or_complex`

---

## Plan

Five phases. Each is independently shippable, and each ends green. Phase 2 delivers the
user-visible fix; phases 3–5 are cleanup that Phase 2 makes safe.

### Cofactor signs — a trap found while doing Phase 2

`atp_cost` / `gtp_cost` and the redox fields use **opposite** sign conventions, and
two modules documented the contradiction in their own docstrings:

| Field | Convention | Why |
|---|---|---|
| `atp_cost`, `gtp_cost` | negative = consumed | tracks the carrier itself |
| `nadh_cost`, `fadh2_cost`, `nadph_cost` | **negative = produced** | tracks the *oxidised* partner (NAD⁺ / FAD / NADP⁺) |

`nadh_cost` and `fadh2_cost` were consistent across all 14 edges. **`nadph_cost` was
not:** the pentose phosphate pathway stored `-1` for NADPH *produced*, while
cholesterol synthesis and FAS stored `-2` for NADPH *consumed*. Corrected in Phase 2
by realigning the 3 outliers (positive = consumed) rather than the 14.

`edge_yields()` normalises all of it to **positive = produced**. The lossless test
asserts *signed* tokens (`NADPH+1` for G6PD, `NADPH-2` for HMG-CoA reductase);
asserting only that the species name appears is what let the inversion through the
first time.

### Phase 0 — safety net (no behaviour change)

1. Standardise the interpreter. There are two venvs: root `.venv` has cobra/scipy but
   **no pytest**; `biology_as_code/.venv` has pytest 9.1.1 and is the complete one.
   Use the inner venv for this package, and note it in `CONTRIBUTING.md` so the next
   person doesn't conclude the suite is unrunnable.
   Baseline today: **291 passed** under `./.venv/bin/python -m pytest tests/ -q`.
2. Add a **golden-snapshot test**: hash every file under `pathways/packs/` and pin the
   digests. Any later phase then has to prove it changed only what it meant to.
3. Add a **lossiness test that fails today**: for every registry edge carrying any
   enzyme-ish or yield field, assert the exported mermaid does not render it as bare
   `"step"` and does not drop the yield. This encodes the bug before fixing it.

Commit with the failing test marked `xfail`, so the suite stays green and the bug is on
the record.

### Phase 1 — the contract module (additive, touches none of the 16)

New `src/biology_as_code/pathways/_types.py`:

- `PathwayNodeType` — core three plus the union of the domain extras.
- `MetaboliteNode` — the 14-way-identical shape.
- `ReactionEdge` — core + all seven yield fields defaulting to `0`/`None` + the
  descriptors, with **`enzyme` as the single name** for the enzyme/complex/process slot.
  Add `label()` and `yields()` accessors so consumers stop introspecting fields.
- `MetabolicPathway` — the five common methods, plus a `summary()` returning the common
  keys (`name`, `nodes`, `edges`) for subclasses to extend.

Nothing imports it yet. Ship it on its own so review is about the shape, not the churn.

**Decision needed:** one wide `ReactionEdge` with optional fields, or per-domain
subclasses? *Recommendation: one wide dataclass.* Subclasses would push the
introspection problem straight back into the exporter, which is the thing being fixed.
Dataclass defaults make the unused fields free.

### Phase 2 — fix the export loss (the actual win)

Teach `export_pathway_packs.py` to call `edge.label()` / `edge.yields()`, keeping the
`getattr` chain **only** as a fallback for not-yet-migrated modules — and extend that
fallback to cover `enzyme_or_complex`, `enzyme_or_process`, and all seven yield fields.

Re-export, diff the packs, un-`xfail` the Phase 0 test. ETC, cholesterol, TCA and PPP
regain their labels and yields here — **before** a single pathway file is touched.

### Phase 3 — migrate the 16, one commit each

Per file: delete the local class declarations, import from `_types`, rename
`enzyme_or_process` / `enzyme_or_complex` → `enzyme`, keep the module's own `summary()`
as an override. The golden test must show zero pack diff beyond Phase 2's intended gains.

Order, easiest first:

1. **The clean seven** (identical `MetaboliteNode` + identical `PathwayNodeType`):
   `beta_oxidation`, `fatty_acid_synthesis`, `gluconeogenesis`, `ketogenesis`,
   `ketolysis`, `pentose_phosphate`, `urea_cycle`.
2. **Shared-variant pairs**: `amino_acid_catabolism` + `supporting_pathways` (`SIGNAL`),
   `metabolic_pathways` + `tca_cycle` (`REGULATORY`).
3. **Single-variant**: `glycogen_metabolism` (`POLYMER`), `cholesterol_pathway`
   (`LIPOPROTEIN`, and drops `enzyme_or_process`), `etc_oxphos` (`COMPLEX`/`CARRIER`,
   drops `enzyme_or_complex`, gains `protons_pumped` export).
4. **Last, because Phase 4 decides them**: `digestion_absorption_pathways`,
   `meal_critical_pathways`.

### Phase 4 — compartment is not a node type

`digestion_absorption_pathways` uses `LUMEN` / `ENTEROCYTE` / `CIRCULATION` as node
types, and `meal_critical_pathways` mixes both vocabularies in one enum. These are
compartments, not metabolic roles.

Add a `compartment` field to `MetaboliteNode` and keep `node_type` for role. Then those
two modules describe both axes honestly instead of overloading one.

This is the same question the urea cycle raised: `location` currently lives on the edge
as free text, so `orn[m]` and `orn[c]` cannot be distinct nodes, which is why transport
reactions are inexpressible. Deciding it once here fixes both.

### Phase 5 — the urea cycle structural work

With compartment-on-node in place, the deferred items become ordinary edits rather than
special cases: `CITRtm` / `ORNt3m` / `UREAt` as real transport reactions, and the
aspartate–malate arm (`FUM`, `MALtm`, `MDHm`, `ASPTAm`, `ASPGLUm`).

Target shape is already generated and sourced:
[`docs/figures/urea-cycle.md`](../figures/urea-cycle.md). SLC25A15 / HHH syndrome and
SLC25A13 / citrin deficiency become representable — today they are not.

---

## Effort and risk

| Phase | Files touched | Risk |
|---|---|---|
| 0 | 2 new tests, `CONTRIBUTING.md` | none |
| 1 | 1 new file | none — nothing imports it |
| 2 | 1 (`export_pathway_packs.py`) | low; golden test bounds it |
| 3 | 16, one commit each | low per commit, mechanical |
| 4 | 2–3 + `_types.py` | **design decision**, needs sign-off |
| 5 | 1 (`urea_cycle.py`) | low once Phase 4 lands |

Phases 0–2 are worth doing on their own even if 3–5 never happen: they fix real data loss
in shipped artifacts. Phases 3–5 stop it recurring and unblock the transport modelling.
