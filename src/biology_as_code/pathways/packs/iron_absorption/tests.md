# Structured tests — `iron_absorption`

**Module:** `biology_as_code.pathways.meal_critical_pathways`  
**Pack id:** `iron_absorption`  
**Description:** Iron absorption teaching path with parallel non-haem and haem branches. Non-haem: Fe³⁺ reduction → DMT1 apical uptake → ferroportin export (hepcidin block). Haem: HCP1-like apical uptake → HO-1 releases Fe²⁺ into the enterocyte pool → same ferroportin exit. Ascorbate co-occupation favors the ferrous lumen pool. FLOW topology — magnitude bounds live in iron UNIT / laws.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 8 |
| Edges | 7 |
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

Edges with `mechanism_id`: **6** / 7

```
  dmt1
  duodenal_cytochrome_b
  ferroportin
  hcp1_heme_uptake
  heme_oxygenase_1
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
