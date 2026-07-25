# Structured tests — `lipid_digestion_absorption`

**Module:** `biology_as_code.pathways.digestion_absorption_pathways`  
**Pack id:** `lipid_digestion_absorption`  
**Description:** Lipid digestion from emulsion to chylomicron export into lymph.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 6 |
| Edges | 5 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **1** / 5

```
  pancreatic_lipase
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
