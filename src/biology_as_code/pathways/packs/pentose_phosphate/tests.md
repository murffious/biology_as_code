# Structured tests — `pentose_phosphate`

**Module:** `biology_as_code.pathways.pentose_phosphate`  
**Pack id:** `pentose_phosphate`  
**Description:** Pentose Phosphate Pathway. Oxidative phase generates NADPH and ribulose-5-P. Non-oxidative phase interconverts sugars and can feed back into glycolysis.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 10 |
| Edges | 9 |
| `nadph_per_g6p_oxidative` | 2 |
| `main_products` | NADPH + ribose-5-P (or glycolytic intermediates) |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 9

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
