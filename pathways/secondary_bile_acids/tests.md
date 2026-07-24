# Structured tests — `secondary_bile_acids`

**Module:** `biology_as_code.pathways.supporting_pathways`  
**Pack id:** `secondary_bile_acids`  
**Description:** Microbial 7α-dehydroxylation and related transforms of primary → secondary bile acids.

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
