# Notational conventions

How a law is written down so that two people reading it compute the same thing.

The registry's prose statements are readable and imprecise. "Ascorbate in the
same meal increases non-haem iron absorption and can overcome inhibitors such
as tea tannin" is a true sentence and an under-specified instruction: it does
not say in what order the effects apply, what happens when ascorbate is present
and its amount is unknown, or what "can overcome" means when both modifiers
fire. Three implementers will produce three answers.

This document fixes the notation that closes those gaps. It is a specification
convention, not a programming language — everything here is expressible in the
existing JSON-Schema layer and the existing Python types.

`LAW-004` is written out in full AO form as the worked example; see
[the AO form of LAW-004](#annex-a-law-004-in-ao-form) below and
`src/biology_as_code/engine/laws/ao/law_004.py`.

---

## 1. Abstract Physiological Operations

An **Abstract Physiological Operation** (AO) is a named, numbered step in a
law's execution. A law in AO form is an ordered list of them.

Numbering is the point. A law with numbered steps can be cited by step — a test
can say it is exercising **AO-004.3**, a report can say the walk blocked at
**AO-004.2**, and a reviewer can disagree with one step rather than with a
paragraph. Ordering is normative: **AO-004.2** happens before **AO-004.3**, and
an implementation that applies them in the other order is non-conforming even
if the arithmetic commutes.

The form:

```
AO-<law>.<n>  <Name>
    Reads:      what the step consumes
    Writes:     what the step changes
    Precondition: what must hold, or the step does not run
    Effect:     what it does
    Uncertainty: what happens when an input is unknown
```

Steps are numbered from 1 within a law. Numbers are **stable**: inserting a step
between 2 and 3 makes it 2a, never renumbers 3 to 4. Published step numbers are
cited in tests and reports, and renumbering silently invalidates every citation.

A step that turns out to be wrong is marked withdrawn and kept:

```
AO-004.4  [WITHDRAWN 2027-06] Ferritin ceiling
```

---

## 2. Uncertainty completion

Every AO must say what it does when an input is missing. The convention is a
record, not a magic value:

```json
{
  "state": "normal | out_of_kingdom | contested",
  "value": 2.0,
  "bounds": [1.5, 10.0]
}
```

| `state` | Meaning |
|---|---|
| `normal` | The input was present and in range. `value` is what was supplied. |
| `out_of_kingdom` | The input falls outside the modelled domain — a food, dose or host the law was never characterised for. Not an error: the law simply does not speak to this case. |
| `contested` | The input is present but the literature disagrees about its effect. `bounds` carry the disagreement. |

`bounds` are always present when `value` is. A completion with a point value and
no bounds is malformed — the whole purpose is to stop a number travelling
without its uncertainty.

### The two operators

**`?` — propagate and widen.** Applied to a quantity, `?x` means: use `x` if
known, and if not, continue with the bounds widened to the law's stated range
rather than stopping.

```
yield ← yield × ?ascorbate_fold
```

If `ascorbate_fold` is known, multiply by it and carry its bounds. If it is not,
multiply by the interval `[1.5, 10.0]` from the law's `bound` text and mark the
result `contested`. The computation continues; the widened interval is the
honest output.

Widening is monotone: `?` may only make bounds wider, never narrower. An
implementation whose `?` narrows an interval is non-conforming.

Monotonicity is checked against the interval you *had*, which is usually none.
`?` applies to an unknown, so there is normally no prior interval to contain and
the law's range is simply established. Do not widen from a no-effect placeholder:
the degenerate interval `[1, 1]` is a claim that the modifier does nothing, and
the law's `[1.5, 10.0]` correctly does not contain it, because ascorbate being
present excludes "no effect". Going from one to the other is a different claim,
not a widening, and the check will say so.

**`!` — assert verified.** Applied to a quantity, `!x` means: `x` must be
present with `evidence_state` of `verified` or `supported`, or the step fails.

```
require !same_meal_concurrency
```

`!` is how a law says a precondition is load-bearing. It never silently
substitutes a default. Use it where proceeding on an assumption would produce a
confidently wrong answer rather than a wide one.

The two are complementary, and choosing between them is the substance of writing
a law: `?` for things that widen the answer, `!` for things that invalidate it.

---

## 3. Host-defined parameters

Some quantities are supplied by the host implementation rather than fixed by the
specification. A **host-defined parameter** has:

- a **fixed algorithm** — the specification says exactly how the value is used,
  and that is not negotiable;
- **host-supplied values** — the number itself comes from the implementation;
- **normative bounds** — the specification states the range a conforming value
  must lie in.

Written `⟨name⟩` in AO text, with the bounds beside it:

```
⟨gastric_emptying_rate⟩   host-defined, normative bounds [0.5, 4.0] g/min
```

A host supplying 2.1 g/min is conforming. A host supplying 12 g/min is not, and
a validator can say so without knowing anything about that host's model. This is
how the specification stays implementable by people with better data than it has,
without becoming unfalsifiable.

Host-defined is **not** the same as unknown. An unknown value takes the `?`
route; a host-defined value is known, by someone else, within a stated range.

---

## 4. Internal slots

`[[x]]` denotes an **internal slot**: a value an AO computes and uses, which is
not part of the law's observable interface.

```
AO-004.2  [[free_fe2]] ← lumen_fe × ?reduction_fraction
```

Slots exist so that intermediate quantities can be named and referred to across
steps without becoming part of the contract. A conforming implementation must
produce the law's declared outputs; it is free to compute `[[free_fe2]]` however
it likes, or not at all if it reaches the same outputs another way.

The practical consequence: a test may assert on a law's outputs and on its
step numbers. A test asserting on the value of `[[free_fe2]]` is testing an
implementation, not the specification, and will break for no good reason.

---

## 5. Intrinsics

An **intrinsic** is a specification-defined symbol resolving to a catalog entry.
Written `%NAME%`.

| Form | Resolves to | Registry |
|---|---|---|
| `%GLP1%`, `%CCK%`, `%GHRELIN%` | a signal | `engine/signals.py` |
| `%Stomach%`, `%SmallIntestine%` | a compartment | `engine/compartments.py`, from `ORGAN_BOUNDS` |
| `%GlycemicResponse%` | a response protocol | `responses/` |

Intrinsics are resolved at validation time, not at run time: an unresolvable
intrinsic is a defect in the law, caught before anything executes. This is the
same discipline as `x-binding_site` — a law that cites `%GLP1%` is making a
checkable claim, whereas a law that mentions "GLP-1" in prose is making none.

The registries are the ones that already exist. Adding an intrinsic means adding
a catalog entry, not editing this table. CamelCase resolves onto the snake_case
id, so `%SmallIntestine%` finds `compartments.small_intestine`.

`resolve_intrinsic()` in `engine/parameters.py` is the implementation, and it is
already earning its keep: **`%Duodenum%` does not resolve.** The duodenum is
where LAW-004 acts, and `ORGAN_BOUNDS` models the small intestine as a single
compartment, so there is no entry to point at. That is a real limitation of the
compartment model rather than a naming problem, and the resolver surfacing it is
better than prose quietly implying a duodenum the engine does not have. The AO
text below writes `%Duodenum%` deliberately, and `tests/test_ao_law_004.py`
records that it does not yet resolve.

---

## 6. Annex B — Atwater general factors

The Atwater general factors (4 / 4 / 9 kcal per gram for carbohydrate, protein
and fat; 2 for fibre) are **specified for legacy compatibility and marked
not-for-new-work.**

They are in the specification because published data uses them and a conforming
implementation must be able to read that data. They are not in it because they
are correct. An Atwater factor prices a gram of a food's analyte panel without
asking whether the gram is reachable, which is precisely the assumption this
specification exists to break: whole almonds and almond flour have the same
panel and differ by about 32% in delivered energy
(`tests/conformance/`, test 2).

Rules:

1. A conforming implementation **must** be able to compute Atwater general
   values, for reading legacy data.
2. It **must not** report an Atwater value as metabolizable energy without
   marking it Annex-B.
3. New laws **must not** derive from Atwater factors. A law needing an energy
   figure takes it from delivered substrate, not from the panel.

Annex-B status is machine-readable: `ATWATER_GENERAL` in
`tests/conformance/harness.py` carries the marking, and a test fails if the
marking is removed.

---

## Annex A — LAW-004 in AO form

The flagship `EXPANDS_BOUND` law, written out. Executable form in
`src/biology_as_code/engine/laws/ao/law_004.py`; the tests in
`tests/test_ao_law_004.py` cite these step numbers.

> **LAW-004** — Co-ingested ascorbic acid increases non-haem Fe absorption and
> can overcome inhibitors such as tea tannin.
> System: Assimilation · Organ: `%Duodenum%` · Relation: `EXPANDS_BOUND`
> Evidence: supported · Bound: tea 3.8% → 2.1%; ascorbate ~10× and cancels tea
> inhibition (Derman 1977); orange juice ~2× (Rossander 1979)

**AO-004.1 — Admit non-haem iron**

```
Reads:        packet.cargo[nonhaem_Fe], packet.identity
Writes:       [[lumen_fe]]
Precondition: require !nonhaem_species
Effect:       [[lumen_fe]] ← packet.cargo[nonhaem_Fe]
Uncertainty:  haem iron ⇒ out_of_kingdom; the law does not speak to it
```

`!` and not `?`, because the haem/non-haem distinction is the law's domain
boundary. Proceeding on an assumption here would apply an ascorbate fold to
haem iron, which is not a wide answer but a wrong one.

**AO-004.2 — Establish same-meal concurrency**

```
Reads:        context_stream.ascorbate_same_meal, context_stream.co_ingested
Writes:       [[concurrent]]
Precondition: none
Effect:       [[concurrent]] ← ascorbate present in the SAME eating occasion
Uncertainty:  unknown timing ⇒ contested, [[concurrent]] = false
```

Ordered before the fold deliberately. Ascorbate taken two hours later is not a
smaller effect, it is no effect, and a step order that applied the fold first
and discounted it afterwards would get the wrong shape.

**AO-004.3 — Apply the ascorbate fold**

```
Reads:        [[concurrent]], ⟨ascorbate_dose_mg⟩
Writes:       [[yield]]
Precondition: [[concurrent]] is true, else step does not run
Effect:       [[yield]] ← [[yield]] × ?ascorbate_fold
Uncertainty:  dose unknown ⇒ ?ascorbate_fold = contested over [1.5, 10.0]
Bounds:       ⟨ascorbate_dose_mg⟩ host-defined, normative [0, 2000] mg
```

The interval is the literature's own spread: ~2× for orange-juice doses
(Rossander), up to ~10× in the tea-rescue conditions (Derman). A single point
value would be picking one paper's condition and presenting it as the law.

**AO-004.4 — Resolve against tannin inhibition (LAW-006)**

```
Reads:        [[yield]], context_stream.tannin_same_meal
Writes:       [[yield]]
Precondition: none
Effect:       both modifiers apply multiplicatively, in registry order
Uncertainty:  neither modifier is skipped when the other fires
```

"Can overcome" is a statement about the *product* of the two folds, not a
precedence rule. Under Derman's conditions ascorbate's ~10× against tannin's
~0.55× nets above the tea-free baseline, and the law is satisfied by the
arithmetic rather than by ascorbate winning a fight. Encoding it as precedence
would give the wrong answer at every dose where it does not.

**AO-004.5 — Emit**

```
Reads:        [[yield]]
Writes:       packet.cargo[nonhaem_Fe], fluxes
Precondition: none
Effect:       Flux(nonhaem_Fe, %Duodenum% → portal) at the resolved yield
Uncertainty:  a contested [[yield]] emits a contested flux; the state is carried,
              never dropped at the boundary
```

## Two system lenses, one renaming rule

Every law answers through two classifications at once, and they are different
axes on purpose: **functional** (the seven systems — Assimilation,
Biotransformation, Structure, Communication, Defense, Energy, Transport:
*what the body is doing*) and **anatomical** (`organ` on a law card;
`BodySystem` instances in the ontology: *where it happens*). Food interacts
across anatomy — a single meal spans mouth to colon — so process and place
must not be collapsed into one field.

The naming convention: **raw data keeps the short key `system`; every serving
boundary renames to the explicit lens name.** The law registry emits
`functional_system` (see `engine/laws/registry.py` — "data key unchanged");
claim-card servers emit `body_system` for the anatomical lens. A new payload
that carries both lenses must use the explicit names — a bare `system` field
in a cross-lens payload is a bug, not a style choice.
