# Pathway packs — mermaid + structured tests

**Gold template:** [`../glycolysis/`](../glycolysis/)

Auto packs for every teaching pathway graph in `biology_as_code.pathways`.

## Layout

```text
pathways/<pathway_id>/
  README.md
  pathway.mermaid
  tests.md
glycolysis/                 # hand-authored gold pack (repo root)
scripts/export_pathway_packs.py
tests/test_pathway_packs.py
```

## Regenerate

```bash
cd biology_as_code
PYTHONPATH=src python3 scripts/export_pathway_packs.py
PYTHONPATH=src python3 tests/test_pathway_packs.py
```

See [INDEX.md](./INDEX.md).
