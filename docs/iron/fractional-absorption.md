# Fractional iron absorption — weights for the `absorbed-iron:demo` scores

This document is the `weights_published` target for the two scores in
[`examples/iron-two-hosts.json`](../../examples/iron-two-hosts.json). Under FDP-1
§3, a score that does not publish its weights declares `weights_published: false`;
this demo publishes them here so the example is fully self-describing.

## What the demo computes

`absorbed_iron_mg = iron_mg × fractional_absorption`, where
`fractional_absorption` is set by host iron status:

| Host state | Serum ferritin | Hepcidin | `fractional_absorption` | absorbed (of 2.1 mg) |
|---|---|---|---|---|
| Iron-replete | 60 ng/mL | high | 0.02 | 0.042 mg |
| Iron-deficient | 8 ng/mL | low | 0.12 | 0.252 mg |

The ~6× spread between the two hosts is the point of the example: the same food
delivers very different absorbed iron depending on the eater.

## Where these numbers come from — and their limits

These two fractions are **illustrative teaching values**, chosen to sit within
the range and direction reported for non-haem iron absorption as a function of
iron status. They are directionally consistent with the Hallberg–Hulthén
prediction algorithm (Hallberg L, Hulthén L. *Am J Clin Nutr.* 2000;71(5):
1147–1160, PMID:10799377), which the score cites as `convergent` validation.
They are **not** a fitted or validated model, and no enhancer/inhibitor algebra
is applied here beyond the host-status switch.

## Why the score is still provenance-graded `—`

Absorption is modulated by ascorbate (enhancer) and by phytate and polyphenols
(inhibitors). The example declares iron, ascorbate, and phytate with provenance,
but **total polyphenols is `OPEN`** — not measured for this preparation. By the
weakest-link rule (FDP-1 §3.1) an `OPEN` input caps the whole score, so both
scores carry `provenance_grade: "—"` regardless of how confident the computed
number looks. That honest gap is the demonstration, not a defect to be patched.
