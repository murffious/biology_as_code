# Structured tests — `beta_oxidation`

**Module:** `biology_as_code.pathways.beta_oxidation`  
**Pack id:** `beta_oxidation`  
**Description:** β-Oxidation of fatty acids. Mitochondrial spiral that removes 2-carbon units as acetyl-CoA. Each cycle yields 1 NADH + 1 FADH₂ + 1 Acetyl-CoA.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 9 |
| Edges | 8 |
| `per_cycle` | 1 NADH + 1 FADH₂ + 1 Acetyl-CoA |
| `activation_cost` | 2 ATP equivalents |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 8

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
