# ontology.json — what the manifest is, and is not

`ontology.json` is the one-file declaration DESIGN.md §1 asks for: object types,
interfaces, predicates, entity kinds, spine stages, actions and response types in a
shape a generator can read. It is exploratory, like everything in this folder
(README.md): nothing in it is normative, and where it disagrees with FDP-1, FDP-1 wins.

Current version: **1.1.0**, as of 2026-09-03. Checked by `check_manifest.py`
(`python3 ontology-sdk/check_manifest.py --strict`), which the test suite runs through
`tests/test_ontology_manifest.py`.

## Where each block comes from

| Block | Derived from | Kept honest by |
|---|---|---|
| `spine_stages` | the six stages `migrate_spine_naming.py` declares (blockers 1 and 2) | every `spine_stage` must be one of them or `null`, and a `null` must say why |
| `entity_kinds` | `mechanism_schema.EntityKind` | each kind names the object type that realises it, or `null` |
| `predicates` | `mechanism_schema.COMPAT`, copied by hand | re-derived from the executed matrix whenever a nutri-collective checkout sits beside this repo |
| `object_types` | the object table in GROUNDED-OBJECT-MODEL.md §3 | properties are the fields each register carries, with the register named |
| `interfaces` | FDP-1 §2 `VALUE_FIELDS` and `SOURCE_TO_GRADE`; `declared.py` | an `implements` claim fails unless the required properties are present |
| `actions` | DESIGN.md's kinetic verbs | each carries `implemented: false`; none has code behind it |
| `types` | `declared.py` (`Declared`), DESIGN.md (`ActionResponse`, `Refusal`) | `Declared` is the one implementer of `Gradeable` |
| `object_types` (governance, §3a) | the standards catalog, the adoption tracker's adopters and history, the decision ledger, and the standardization ledger's subjects, events and predictions | each names its register; `Prediction` implements `Falsifiable` |
| `relation-crosswalk.v1.json` (beside the manifest) | six relation vocabularies, read from their source files | every member has a row, shared names map identically, counts are recomputed, sources are re-read when reachable |

## What 1.1.0 corrected in 1.0.0

- `Value` claimed `Gradeable` and `Citable` without carrying `grade`, `evidence_span` or
  `method_ref`. `evidence_span` exists nowhere in the SDK. `Citable` now requires what
  FDP-1 enforces (`source_ref`, `method`, with `method_ref` recorded as `Declared`'s alias),
  and `Gradeable` is implemented by `Declared`, because an FDP-1 value derives its grade
  from `source` rather than storing one.
- `spine:catalogue`, `controlled_vocabulary`, `mechanism_chain` and `not_on_spine` were
  invented stage values. Off-spine types now carry `null` plus a note; `Principle` carries
  `spine_span` because it is a chain.
- Predicates were typed over kinds (`biomarker`, `process`, `disease`, …) that no block
  declared. `entity_kinds` now declares them and says which have an object type.
- The `types` block existed but the MCP surface could not reach it.

## What it settles, and what it does not

- **Blocker 4 is cleared.** The base is `mechanism_schema.py`'s eleven relations. Every other
  vocabulary — the law model (9), the graph (10), the claim-language lexicon (15),
  nutrient-edge.v2 (16), the id-crosswalk kinds (5), the taxonomy joins (8) — is mapped onto it
  verb by verb in `relation-crosswalk.v1.json`, with a rule for what counts as a mapping and a
  `gaps` block listing what the base cannot carry. nutrient-edge.v2's sixteen come out as six
  direct, eight by expansion over a reified node, two not expressible. Nothing is retired.
- **Blockers 5 and 6 are visible, not solved.** `Claim.verdict` and `Claim.grade` are two
  fields by design; `method` / `method_ref` is one recorded alias. Namespacing the other
  collisions is still the manifest's job.
- **Actions are declared, not implemented.** A tool that serves this file must never offer
  `declare_value`, `assert_claim` or `record_layer_pass` as callable.

## How it is served

nutri-collective's MCP server serves the file through its existing `get_standard` tool
(`name="ontology-manifest"` or `"ontology.json"`, `section=<block>`), with a reporting rule
that says the manifest is a sketch of the object model and not the project's standard. It is
not a tool of its own: sixteen is that server's declared ceiling, and the decision ledger
row that set it says future asks fold into existing tools.

## Next

The generator that reads this file and emits typed dataclasses around the `Declared[T]`
primitive has not been started. The blockers above gate what it may generate.
