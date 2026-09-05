# STUDY.md — NUTR-PUBLIC-001

**This repository is the worked example.** It proves the spec is implementable. It is a machine, not a store — body records are passed to it at runtime, never committed to it.

```text
study_id:     NUTR-PUBLIC-001
schema_ref:
  food:       fdp-1@v0.1.0
  packet:     biology_as_code/schemas@v0.1.0
  study:      MI-Nutrition@v0.1
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
  **Honest status of the third, updated 2026-09-05:** `food:` and `packet:` resolve to
  public repositories you can clone and watch refuse a bad row. `study:` now resolves the
  same way for the schema — MI-Nutrition has a neutral public home
  (`github.com/murffious/mi-nutrition`, CC BY 4.0), and the file there is the real
  annotated schema (`$defs`, `x-crosswalk` to EN 16104/EuroFIR and STROBE), not the stub
  that used to sit behind that name. What is still missing is a validator: the repo ships
  a JSON Schema 2020-12 document, not a reference implementation that runs it, so a
  stranger can fetch the contract but not yet run it without writing their own validation
  call — the FDP-1 validator pinned above only checks `food:` and `packet:`. **The pin
  therefore names a contract a stranger can fetch but not yet run.** That is stated
  rather than papered over, and shipping a `study:` validator is the next task.
- `rule` is refusal. Enforced today: the FDP-1 validator in `murffious/fdp-1`, pinned above.
- `split` is what stops a `human_id` landing in a public remote. Enforced today:
  `tools/check_no_human_rows.py`, which runs **first** in CI — every other failure here
  is recoverable, that one is not.
- `paper` is Fort Lauderdale 2003. Deposit the draft assay now, keep first publication
  on the analysis. It is the clause that makes this signable by a working lab.

Not in this file: nutrients, digestion machines, the ontology. `CONTRIBUTING.md`, the
specification and the book stay where they are.
