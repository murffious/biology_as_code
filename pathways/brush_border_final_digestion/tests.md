# Structured tests — `brush_border_final_digestion`

**Module:** `biology_as_code.pathways.digestion_absorption_pathways`  
**Pack id:** `brush_border_final_digestion`  
**Description:** Brush-border disaccharidases and peptidases completing lumen → absorbable monomers.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 4 |
| Edges | 2 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 2

_No mechanism_id links (topology-only teaching graph)._

## Biochemical invariants (document here)

Hand-fill like root `glycolysis/tests.md` when auditing against textbook:

| Invariant | Expected | Status |
|-----------|----------|--------|
| Energy / stoichiometry | _(TBD for this path)_ | Open |
| Irreversible / regulated steps | _(TBD)_ | Open |

## Automated tests

```bash
PYTHONPATH=src python3 tests/test_pathway_packs.py
# or: pytest tests/test_pathway_packs.py -q
```

Gold audit style: `glycolysis/tests.md`.
