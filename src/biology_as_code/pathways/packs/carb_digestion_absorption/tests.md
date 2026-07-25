# Structured tests — `carb_digestion_absorption`

**Module:** `biology_as_code.pathways.digestion_absorption_pathways`  
**Pack id:** `carb_digestion_absorption`  
**Description:** Carbohydrate digestion and absorption from starch/sugars to portal blood glucose.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 5 |
| Edges | 4 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **2** / 4

```
  salivary_amylase
  sglt1
```

## Biochemical invariants (document here)

Hand-fill like `packs/glycolysis/tests.md` / gold extras when auditing diagrams:

| Invariant | Expected | Status |
|-----------|----------|--------|
| Energy / stoichiometry | _(TBD for this path)_ | Open |
| Irreversible / regulated steps | _(TBD)_ | Open |

## Automated tests

```bash
PYTHONPATH=src python3 tests/test_pathway_packs.py
# or: pytest tests/test_pathway_packs.py -q
```

Gold audit style: `packs/glycolysis/tests.md` + `glycolysis_extra/`.
