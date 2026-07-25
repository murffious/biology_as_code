# Structured tests — `gluconeogenesis`

**Module:** `biology_as_code.pathways.gluconeogenesis`  
**Pack id:** `gluconeogenesis`  
**Description:** Gluconeogenesis – synthesis of glucose from non-carbohydrate precursors (lactate, glycerol, glucogenic amino acids). Bypasses the three irreversible steps of glycolysis. Costs 6 ATP equivalents per glucose.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 12 |
| Edges | 11 |
| `atp_equivalents_per_glucose` | 6 |
| `main_sites` | Liver and kidney cortex |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 11

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
