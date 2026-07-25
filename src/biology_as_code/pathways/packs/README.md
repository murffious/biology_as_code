# Pathway packs — mermaid next to code

Lives under `src/biology_as_code/pathways/packs/` (same tree as Python modules).

**Important:** packs are in a `packs/` subfolder so directories do **not**
shadow modules like `beta_oxidation.py` (Python would prefer a package dir).

## Layout

```text
src/biology_as_code/pathways/
  beta_oxidation.py          # code
  metabolic_pathways.py      # code (glycolysis graph)
  packs/
    INDEX.md
    COVERAGE.md
    glycolysis/              # auto mermaid + tests.md
      pathway.mermaid
      glycolysis_extra/      # hand-authored gold mermaids
    beta_oxidation/
    ...
```

## Regenerate

```bash
cd biology_as_code
PYTHONPATH=src python3 scripts/export_pathway_packs.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```

See [INDEX.md](./INDEX.md) and [COVERAGE.md](./COVERAGE.md).
