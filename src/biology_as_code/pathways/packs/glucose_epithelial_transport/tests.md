# Structured tests — `glucose_epithelial_transport`

**Module:** `biology_as_code.pathways.meal_critical_pathways`  
**Pack id:** `glucose_epithelial_transport`  
**Description:** Epithelial glucose handling after luminal liberation: SGLT1 (SLC5A1) Na⁺-coupled apical uptake in duodenum/jejunum; GLUT2 (SLC2A2) basolateral exit toward portal blood. GLUT5 fructose stub noted. Complements carb_digestion_absorption pack without duplicating amylase steps.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 6 |
| Edges | 5 |
| `primary_system` | Assimilation |
| `systems` | ['SYS_01', 'SYS_02', 'SYS_06'] |
| `apical` | SGLT1 |
| `basolateral` | GLUT2 |
| `queue_tier` | B |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **5** / 5

```
  glut2
  glut5
  sglt1
```

## Sources

- SGLT1 Na⁺-glucose apical cotransport — NCBI Gene SLC5A1: https://www.ncbi.nlm.nih.gov/gene/?term=SLC5A1
- GLUT2 basolateral hexose exit — NCBI Gene SLC2A2: https://www.ncbi.nlm.nih.gov/gene/?term=SLC2A2
- GLUT5 apical fructose transport — NCBI Gene SLC2A5: https://www.ncbi.nlm.nih.gov/gene/?term=SLC2A5

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
