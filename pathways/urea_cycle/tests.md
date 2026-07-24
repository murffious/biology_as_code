# Structured tests — `urea_cycle`

**Module:** `biology_as_code.pathways.urea_cycle`  
**Pack id:** `urea_cycle`  
**Description:** Urea Cycle (Ornithine Cycle). Converts toxic ammonia into urea for safe excretion. Occurs mainly in the liver. Costs ~4 ATP equivalents per urea.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 10 |
| Edges | 6 |
| `atp_per_urea` | 4 |
| `main_site` | Liver |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 6

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
