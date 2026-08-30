# STUDY.md — NUTR-PUBLIC-001

**This repository is THE WORKED EXAMPLE.** Its job is to prove the spec is implementable: digestion machines, pathway graphs, fail-closed `UNEVALUABLE`, and the `scoring/interface.py` + `loader.py` split that keeps product algorithms out of a public Apache-2.0 history. It is a machine, not a store — body records are passed to it at runtime and never committed to it.

## The rule

**If you generate data in this study, you emit it in the pinned schema, or it does not
count as study data.** Analysis papers can wait. The deposit cannot.

This is not a law and not a norm. It is a participation condition, the way the Bermuda
Principles became a grant condition in 1996: the rules bound because Wellcome and the
NIH wrote them into grants, and a centre that would not release did not get the money.
A rule that cannot refuse a row is a harmonisation paper.

## The pin

```text
study_id:     NUTR-PUBLIC-001
schema_ref:   fdp-1@v0.1.0 + biology_as_code/schemas@v0.1.0
rule:         a row that does not validate is not study data
split:        food public; person in body; export only with DUO
paper:        producer keeps first analysis
```

The `schema_ref` string is identical in `fdp-1/STUDY.md` and
`biology_as_code/STUDY.md`. If they ever differ, the pin is broken and nothing
downstream means anything.

## What refuses a row today

| Rule | Check | Where |
|---|---|---|
| **B** — shared properties, never a welded column | `nutrient_ref` + `value` + `unit` required; `protein_mg` rejected | `fdp-1` `validator/validate_fdp.py`, asserted by `tests/test_rejections.py` |
| **B** — unknowns are the literal `OPEN` | `null` / `""` / omitted all rejected | same |
| **B** — nutrient identity resolves | bare `"iron"` rejected; must be a CURIE with an accepted prefix | same |
| **E** — no person in a public repository | forbidden field names in key position | `tools/check_no_human_rows.py`, asserted by `tests/test_no_human_rows.py` |

Rule E runs **first** in CI. Every other failure here is recoverable — a wrong id gets
corrected, a licence renegotiated, a score re-run. A person's identifier in a public git
history is not: it survives deletion, force-push, every clone and every fork.

Rule E is a **study rule, not FDP-1 conformance**. FDP-1 §6 asks *is this value properly
provenanced*; Rule E asks *does this repository contain a human being*. Adding the second
to §6 would change conformance for every third party implementing FDP-1, which is not
ours to change.

## Duties (Fort Lauderdale 2003)

| Party | Duty |
|---|---|
| Funder | If you pay for a community resource, public release is a grant condition |
| Producer | Deposit early; you keep first-publication rights on the **analysis**, not the data |
| User | Credit the producer; do not scoop their first paper; do not re-identify anyone |

That middle row is what makes the rule survivable. It removes the honest objection — *I
will be scooped* — without removing the obligation.

## Claim the term

Before inventing a nutrient, analyte or object type, find the **CDNO, FoodOn, FDC or
ChEBI** term and claim that. Only if none exists do you propose a local id, recording the
search that failed. Two labs must not fork iron.

## What is not here

No `human_id`, no genetic profile, no meal log, no lab result, no computed need for a
named person. Those live in a private store that has no public clone, and they reach
this code at runtime — passed in, never committed.

Research exports leave that store only through an explicit action, tagged with GA4GH
DUO. Food data carries `DUO:0000004` (no restriction) or no tag at all: a composition
table has no human subject, and stamping a consent code on one is how a `human_id`
eventually leaks into a public catalogue by inheritance.
