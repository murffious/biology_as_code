# Structured tests — `ketogenesis`

**Module:** `biology_as_code.pathways.ketogenesis`  
**Pack id:** `ketogenesis`  
**Description:** Ketogenesis. Liver converts excess acetyl-CoA into ketone bodies that can be used by brain, heart, and muscle during fasting or low-carbohydrate states.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 6 |
| Edges | 5 |
| `main_products` | Acetoacetate, β-Hydroxybutyrate, Acetone |
| `location` | Liver mitochondria |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 5

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
