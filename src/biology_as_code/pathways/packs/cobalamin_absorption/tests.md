# Structured tests — `cobalamin_absorption`

**Module:** `biology_as_code.pathways.meal_critical_pathways`  
**Pack id:** `cobalamin_absorption`  
**Description:** Vitamin B12 (cobalamin) absorption requires gastric intrinsic factor (IF). Dietary B12 is released in the stomach, binds IF, and the IF–B12 complex is absorbed in the terminal ileum via cubam receptor teaching path. Failure poles: IF deficiency (pernicious anemia), ileal disease.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 6 |
| Edges | 5 |
| `primary_system` | Assimilation |
| `systems` | ['SYS_01', 'SYS_02'] |
| `clinical_hooks` | pernicious anemia; ileal disease |
| `obligatory_partner` | intrinsic_factor |
| `queue_tier` | B |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **2** / 5

```
  intrinsic_factor
```

## Sources

- Intrinsic factor required for B12 absorption in pernicious anemia: PMID 18112756 (https://pubmed.ncbi.nlm.nih.gov/18112756/).
- Intrinsic factor localization (gastric / duodenal extracts): PMID 15405205 (https://pubmed.ncbi.nlm.nih.gov/15405205/).
- Pernicious anemia = IF failure pole (B12 replacement): PMID 14935513 (https://pubmed.ncbi.nlm.nih.gov/14935513/).
- Ileal cubam receptor — NCBI Gene CUBN (cubilin) + AMN (amnionless): https://www.ncbi.nlm.nih.gov/gene/?term=CUBN

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
