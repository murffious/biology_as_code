# Contributing

Two kinds of contribution, one constitution.

## Data — strengthen the register

Evidence, packet fills, claims, and gate/bound rules go through a **fail-closed
gate**: an unsourced magnitude can never be promoted, so the crowd can only
strengthen the register. This is the highest-leverage way to help.

→ See [**docs/contributing-data.md**](docs/contributing-data.md). No code required;
you add one small JSON file and open a PR, or use the
[evidence issue form](../../issues/new?template=evidence.yml).

## Code

```bash
pip install -e ".[dev]"
ruff check src tests --exclude tests/_legacy_test_pathways_source.py
pytest -q
```

CI runs the full suite + ruff on 3.11 / 3.12 / 3.13 and builds the wheel. Keep it
green.

### Invariants that must not drift

These are the brand, enforced by tests — a PR that breaks one turns CI red:

- **Zero runtime dependencies.** `dependencies = []` stays empty. Anything heavier
  is a `dev` extra.
- **Empty beats fake.** Missing data is `UNEVALUABLE`/`OPEN`, never a default pass
  or a fabricated number. No citation is ever invented.
- **Gate ≠ Bound.** A `GateRule` may only cite laws whose card has
  `gate.present == True`; a `BoundRule` only laws where it is `False`.
- **No magnitude without primary evidence.** Directions are fine; numbers need a
  sourced, verifiable citation (see the [validation ledger](docs/VALIDATION_LEDGER.md)).

### The product boundary

The open package is the teaching/auditing engine. The patent-pending **Kibo meal
score and its variables are not part of this repo** — they live behind the gated
`product_score/` hook. Do not add scoring weights, Kibo-variable formulas, or a
meal-score implementation here; contributions that do will be declined.
