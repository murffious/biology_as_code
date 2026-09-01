# ontology-sdk — exploration, not the pin

**Status: exploratory. Nothing here is normative, and nothing here is a product.**

This folder is a second lens on the same problem the specification solves: what a
nutrition ontology looks like if you model it the way an object-oriented data platform
would — object types, link types, shared properties, roles, views, and *need as a
function over an interface* rather than a stored table.

It was written to be argued with. It is deliberately a different perspective from
FDP-1, and where the two disagree, **FDP-1 wins** — that is the specification, this is
a sketch beside it.

## What this is not

- **Not the study pin.** `NUTR-PUBLIC-001` is `../STUDY.md`. Nothing in this folder is
  pinned, validated, or checked by the conformance suite.
- **Not the product.** `body_system_protocol.py` carries a `WEIGHTS` dict that is an
  **illustrative placeholder**, marked as such at the point of use. A second draft of
  the same sketch uses different numbers entirely, which is the clearest evidence they
  mean nothing: a fitted weight does not change because someone rewrote the paragraph
  around it. Per `PROPRIETARY_IP.md`, teaching meters belong here only when labelled
  as not the product meal score. They are.
- **Not a public API.** No stability promise. Do not import from it.

## Why it is in the public repository at all

The argument this project makes is that the *shape* is the contribution and the
*person* is what stays private. A sketch of the shape is exactly the sort of thing that
should be readable. What must never appear here is a real weighting, a tier cutoff, a
product identifier, or a human row — and as of 2026-08-30 the separation gate and the
no-human-rows guard both cover this folder, which they did not before.

## Files

| File | What |
|---|---|
| `GROUNDED-OBJECT-MODEL.md` | The object model, grounded against what the repo actually ships |
| `DESIGN.md` · `ONTOLOGY-PIPELINE.md` · `ONTOLOGY-MANAGER.md` | How the model would be built and maintained |
| `PALANTIR-PRINCIPLES.md` · `foundry_ont.md` · `COMPARABLES.md` | The borrowed vocabulary, attributed, and how it maps |
| `docs/nutrition_ontology_spec.md` · `shared_properties.md` · `roles_and_object_views.md` | Object types, the shared-property catalogue, and the roles matrix |
| `body_system_mapping.md` · `body_system_protocol.py` | The interface sketch — read the docstring first |
| `principles.v1.json` · `check_principles.py` · `declared.py` | The principles register and its checker |
| `WHERE-THIS-FITS.md` | How this sits next to the specification |
