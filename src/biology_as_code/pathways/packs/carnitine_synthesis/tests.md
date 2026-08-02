# Structured tests — `carnitine_synthesis`

**Module:** `biology_as_code.pathways.micronutrient_cofactor_pathways`  
**Pack id:** `carnitine_synthesis`  
**Description:** Endogenous carnitine from lysine and methionine. Five micronutrient dependencies on one linear chain — the cleanest argument against scoring nutrients independently.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 8 |
| Edges | 7 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 7

_No mechanism_id links (topology-only teaching graph)._

## Sources

- Berdanier CD. Advanced Nutrition: Macronutrients, 2nd ed. CRC Press, 2000. Appendix 2, Metabolic Maps, pp. 471-492. Map 25, p. 489.

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
