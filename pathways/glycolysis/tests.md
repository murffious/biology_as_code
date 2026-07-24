# Structured tests — `glycolysis`

**Module:** `biology_as_code.pathways.metabolic_pathways`  
**Pack id:** `glycolysis`  
**Description:** Glycolysis – the central pathway that converts glucose into pyruvate (or lactate under anaerobic conditions). Modeled from the book pathway chart.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 12 |
| Edges | 12 |
| `net_atp` | 2 |
| `net_nadh` | 2 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **4** / 12

```
  hexokinase
  lactate_dehydrogenase
  pfk1
  pyruvate_kinase
```

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
