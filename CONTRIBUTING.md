# Contributing

Two kinds of contribution, one constitution. A third path is **teaching pathways**
(graphs + mermaid packs) with a fixed integration template.

## Data — strengthen the register

Evidence, packet fills, claims, and gate/bound rules go through a **fail-closed
gate**: an unsourced magnitude can never be promoted, so the crowd can only
strengthen the register. This is the highest-leverage way to help.

→ See [**docs/contributing-data.md**](docs/contributing-data.md). No code required;
you add one small JSON file and open a PR, or use the
[evidence issue form](../../issues/new?template=evidence.yml).

## Pathways — teaching graphs + mermaid

Adding or extending a metabolic / digestion / sensing **pathway graph** is a
structured workflow: code first, export mermaid, tests, coverage, integration gate.

| Resource | Purpose |
|----------|---------|
| [**docs/python/ADD_PATHWAY.md**](docs/python/ADD_PATHWAY.md) | Full template guide (order of work, anti-patterns) |
| [**docs/python/templates/NEW_PATHWAY_CHECKLIST.md**](docs/python/templates/NEW_PATHWAY_CHECKLIST.md) | Paste into PR body |
| [**docs/python/templates/pathway_module_stub.py**](docs/python/templates/pathway_module_stub.py) | Copy to `src/.../pathways/` |
| `scripts/export_pathway_packs.py` | Regenerate `packs/<id>/pathway.mermaid` |
| `scripts/check_pathway_integration.py` | **Must exit 0** before merge |
| `packs/COVERAGE.md` | Graphs ↔ modules honesty map |

```bash
pip install -e ".[dev]"
# after editing a graph:
PYTHONPATH=src python3 scripts/export_pathway_packs.py
PYTHONPATH=src python3 scripts/check_pathway_integration.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```

**Single wire point:** register loaders only in
`src/biology_as_code/pathways/registry.py` (`pathway_loaders`). Export uses that
list — do not duplicate module lists in the export script.

Gold example of a complete small addition: `ketolysis.py` + `tests/test_ketolysis.py`.

## Code (general)

```bash
pip install -e ".[dev]"
ruff check src tests --exclude tests/_legacy_test_pathways_source.py
pytest -q
PYTHONPATH=src python3 scripts/check_pathway_integration.py
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
- **Pathway packs match the registry.** Every graph has a mermaid pack; no orphan
  packs (`check_pathway_integration.py`).

### The product boundary

The open package is the teaching/auditing engine. The patent-pending **Kibo meal
score and its variables are not part of this repo** — they live behind the gated
`product_score/` hook. Do not add scoring weights, Kibo-variable formulas, or a
meal-score implementation here; contributions that do will be declined.
