---
title: "biology-as-code: a fail-closed toolkit for auditing nutrition claims against declared law"
tags:
  - Python
  - nutrition
  - digestion
  - metabolism
  - provenance
  - reproducibility
authors:
  - name: Paul Murff
    orcid: 0000-0000-0000-0000 # TODO: required by JOSS — see paper/SUBMISSION.md
    affiliation: 1
affiliations:
  - name: Morf Engineering, Salt Lake City, Utah, United States
    index: 1
date: 2026-07-25
bibliography: paper.bib
---

# Summary

`biology-as-code` models what happens to a meal — digestion, absorption, and the
metabolic pathways it drives — as inspectable code rather than a numeric verdict.
It provides a meal-simulation pipeline, the gastrointestinal tract as versioned
declarative state machines, 28 teaching metabolic-pathway graphs, 47 machine-readable
"LAW-SPEC" law cards expressing rules as queryable data, and a claim auditor that
walks a nutrition claim through a five-tier delivery ladder and returns a verdict
with citations to the laws it rests on.

The package's organising commitment is that it fails closed. Where a required fact
is not declared, the auditor returns `UNEVALUABLE` rather than a default pass, a
zero, or an interpolated estimate. Of the 46 example food packets shipped with the
repository, a carotenoid-absorption claim returns `UNEVALUABLE` for 44 — and the
software reports that number rather than concealing it. The runtime has no
dependencies and makes no network calls by default, so an audit is reproducible
from the repository alone.

# Statement of need

Software that scores food is abundant; software that can be interrogated about
*why* it scored something is rare. Nutrient profiling models are widely deployed in
regulation and consumer applications, yet a validation study of five regional models
against a reference model found discordant classifications for between 5% and 37% of
the same 15,342 foods, and reported that most published models had never been
validated at all. Divergence of that magnitude on identical inputs indicates absent
specification rather than genuine scientific disagreement, and it is not diagnosable
from the outputs alone.

Considerable effort has gone into standardising the *identity* of food — FoodOn and
its partner ontologies in the OBO Foundry provide a harmonised farm-to-fork
vocabulary [@dooley2018; @griffiths2024] — and into making research data reusable
in general [@wilkinson2016]. Food composition is likewise well served by established
reference databases. What remains unstandardised is *judgement*: the rule that turns
a composition record into a claim about a person, together with the provenance of
that rule and the conditions under which it does not apply.

`biology-as-code` addresses a tractable part of that gap. Two mechanisms that are
routinely conflated are separated at the type level: a **gate** is categorical (a
required co-factor is absent, so the transport path does not run), while a **bound**
is a signed magnitude modifier (the path runs; a ceiling moves). Fat-soluble cargo
without a lipid phase is a closed gate — the claim is false, not small. Ascorbate and
tea tannins acting on non-haem iron are bounds in opposite directions with the gate
open throughout. Every rule carries references into the law register, and continuous
integration asserts that a gate rule may only cite laws whose card declares a gate
and a bound rule only those that do not, so the rule table cannot drift from the
stated law without failing the build.

Two design decisions follow from the fail-closed commitment and are unusual enough
to state explicitly. First, the auditor distinguishes an undeclared field from a
field declared zero: silence is not a zero, and treating it as one would manufacture
confident negative results from missing data. Second, the strongest verdict a
mechanism walk can return is `Plausible`; the schema's `Confirmed` value is
unreachable by construction and a test asserts it can never be emitted, because
confirmation is a judgement about magnitude and endpoint that no mechanism trace can
establish. A mechanically sound meal still returns `UNEVALUABLE` for a
disease-prevention claim.

The intended users are educators who need a transparent alternative to opaque
nutrition applications, researchers and reviewers who need to record why a claim
does or does not hold, and developers building tools that must decline to answer
rather than guess. The package is deliberately scoped to the open teaching and
audit layer; a separate proprietary scoring engine is not included, and the public
interface returns a documented unavailability signal in its absence.

# Naming note

The established field of *code biology* studies naturally occurring organic codes
[@barbieri2015]. This package makes an unrelated engineering claim — that nutrition
rules should be written, versioned, and tested like software — and is closer in
spirit to "infrastructure as code." The similarity of names is coincidental.

# Acknowledgements

Archived releases are deposited on Zenodo (DOI 10.5281/zenodo.21536449).

# References
