# Baseline — separation audit / typing / conformance work order

Recorded at Phase 0, before any change in this series.

## Snapshot

| Item | Value |
|---|---|
| Baseline commit | `21f73acc725f12e2fa501af20982659e7e6698e1` |
| Branch | `claude/biology-code-audit-typing-tests-rrj43z` |
| Python | 3.11.15 (repo requires >=3.11) |
| Runtime dependencies | none (zero-dependency; `pyyaml` is dev-only) |
| Test result | **408 passed**, 0 failed, 0 skipped, ~22 s |
| Command | `python -m pytest` (testpaths `tests/`, pythonpath `src/`) |
| Ruff | 0.15.8, `ruff check src tests --exclude tests/_legacy_test_pathways_source.py` clean |

## Separation-audit starting position

`grep -riE "kibo|mealcoach|morf" src/ tests/` at baseline:

| Measure | Count |
|---|---|
| Matching files (incl. `__pycache__`) | 269 |
| Matching files (source only, `__pycache__` excluded) | **216** |
| Matching files outside `data/fixtures/meals/` | 147 |

Distinct matched tokens (case-folded, top of the distribution):

| Token | Occurrences |
|---|---|
| `mealcoach` | 400 |
| `kibo` | 306 |
| `kibo_core` | 89 |
| `kibo_system` | 58 |
| `kibo_score` | 29 |
| `kibo_engine` | 18 |
| `morf` | 16 |

No false positives were found — every match is a genuine product identifier
(there is no `morphology`-style collision in `src/` or `tests/`).

The bulk is structural, as the work order anticipated: the `kibo_core` package
directory, the meal-fixture corpus under `data/fixtures/meals/`, and the
`machines/data/schemas/` `$id`/description strings.

## Gate

Phase 0 gate: **met.** Suite green at 408 tests; baseline recorded here.
