# STUDY.md — NUTR-PUBLIC-001

**This repository is the worked example.** It proves the spec is implementable. It is a machine, not a store — body records are passed to it at runtime, never committed to it.

```text
study_id:     NUTR-PUBLIC-001
schema_ref:
  food:       fdp-1@v0.1.0
  packet:     biology_as_code/schemas@v0.1.0
  study:      MI-Nutrition@v0.1
              https://nutri-collective.mealcoach.ai/mi-nutrition-v0.1.schema.json
rule:         a row OR a study record that does not validate is not study data
split:        food deposits are public; person-level rows stay in body;
              research export only via ResearchRelease + DUO
paper:        producer keeps first analysis
```

- `study_id` names the pin, so the adoption tracker has something to count.
- `schema_ref` names **three** contracts, because a study is three things: the number
  on a food, the packet that carries it, and the study record itself. The pin used to
  name the first two and behave as though that covered the third. **The same block is in
  `fdp-1/STUDY.md`.** If they diverge, the pin is broken.
  **Honest status of the third:** the MI-Nutrition *schema* is public at the URL above;
  its *validator* is not yet, so `study:` is today a contract you can read but not run.
  `food:` and `packet:` you can clone and watch refuse. That gap is the next thing to close.
- `rule` is refusal. Enforced today: the FDP-1 validator in `murffious/fdp-1`, pinned above.
- `split` is what stops a `human_id` landing in a public remote. Enforced today:
  `tools/check_no_human_rows.py`, which runs **first** in CI — every other failure here
  is recoverable, that one is not.
- `paper` is Fort Lauderdale 2003. Deposit the draft assay now, keep first publication
  on the analysis. It is the clause that makes this signable by a working lab.

Not in this file: nutrients, digestion machines, the ontology. `CONTRIBUTING.md`, the
specification and the book stay where they are.
