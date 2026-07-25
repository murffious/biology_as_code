# Structured tests — `glycogen_metabolism`

**Module:** `biology_as_code.pathways.glycogen_metabolism`  
**Pack id:** `glycogen_metabolism`  
**Description:** Glycogen synthesis (glycogenesis) and breakdown (glycogenolysis). Reciprocally regulated so that both processes are not active at the same time.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 6 |
| Edges | 7 |
| `synthesis_key_enzyme` | Glycogen synthase |
| `breakdown_key_enzyme` | Glycogen phosphorylase |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 7

_No mechanism_id links (topology-only teaching graph)._

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
