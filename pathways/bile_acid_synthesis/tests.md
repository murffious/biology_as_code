# Structured tests — `bile_acid_synthesis`

**Module:** `biology_as_code.pathways.digestion_absorption_pathways`  
**Pack id:** `bile_acid_synthesis`  
**Description:** Classic pathway: cholesterol → primary bile acids (cholic / chenodeoxycholic) in hepatocytes.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 4 |
| Edges | 3 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 3

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
