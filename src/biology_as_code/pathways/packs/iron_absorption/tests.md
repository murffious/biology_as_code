# Structured tests — `iron_absorption`

**Module:** `biology_as_code.pathways.meal_critical_pathways`  
**Pack id:** `iron_absorption`  
**Description:** Non-haem iron absorption teaching path. Dietary Fe³⁺ is reduced at the brush border; DMT1 takes up Fe²⁺ into the enterocyte; ferroportin exports iron basolaterally (blocked by hepcidin under iron repletion / inflammation). Ascorbate favors the Fe²⁺ pool (same-meal co-occupation). Heme path is a parallel stub. FLOW topology — magnitude bounds live in iron UNIT / laws.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 7 |
| Edges | 6 |
| `primary_system` | Assimilation |
| `systems` | ['SYS_01', 'SYS_02', 'SYS_04'] |
| `clinical_hooks` | iron deficiency anemia; anemia of inflammation |
| `control_point` | ferroportin / hepcidin |
| `queue_tier` | B |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **4** / 6

```
  dmt1
  duodenal_cytochrome_b
  ferroportin
  hepcidin_ferroportin
```

## Sources

- Iron homeostasis / ferroportin regulation (lactoferrin model): PMID 39005063 (https://pubmed.ncbi.nlm.nih.gov/39005063/).
- DMT1 apical Fe²⁺ uptake — NCBI Gene SLC11A2: https://www.ncbi.nlm.nih.gov/gene/?term=SLC11A2
- Ferroportin basolateral iron export — NCBI Gene SLC40A1: https://www.ncbi.nlm.nih.gov/gene/?term=SLC40A1
- Hepcidin (HAMP) ⊣ ferroportin control point — NCBI Gene HAMP: https://www.ncbi.nlm.nih.gov/gene/?term=HAMP
- Magnitude bounds live in iron UNIT / laws (Biology as Code).

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
