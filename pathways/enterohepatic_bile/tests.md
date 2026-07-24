# Structured tests — `enterohepatic_bile`

**Module:** `biology_as_code.pathways.digestion_absorption_pathways`  
**Pack id:** `enterohepatic_bile`  
**Description:** Enterohepatic circulation of bile acids: liver → bile → ileum reuptake → portal return.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 5 |
| Edges | 5 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 5

_No mechanism_id links (topology-only teaching graph)._

## Biochemical invariants (document here)

Hand-fill like root `glycolysis/tests.md` when auditing against pathway mermaid packs:

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
