# Structured tests — `scfa_colonic_production`

**Module:** `biology_as_code.pathways.meal_critical_pathways`  
**Pack id:** `scfa_colonic_production`  
**Description:** Colonic short-chain fatty acid production from fermentable fiber / RS. Microbiota ferment substrates to acetate, propionate, and butyrate; butyrate fuels colonocytes; acetate/propionate reach portal blood. Extends prebiotic_probiotic sketch with explicit SCFA products (FLOW).

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 7 |
| Edges | 7 |
| `primary_system` | Assimilation |
| `systems` | ['SYS_01', 'SYS_06'] |
| `products` | acetate, propionate, butyrate |
| `queue_tier` | B |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **3** / 7

```
  colonic_fermentation
```

## Sources

- Short-chain fatty acids — physiology and effects review: PMID 39845918 (https://pubmed.ncbi.nlm.nih.gov/39845918/).
- SCFA and intestinal mucosal immunity review: PMID 39286812 (https://pubmed.ncbi.nlm.nih.gov/39286812/).
- Colonic SCFA production (acetate / propionate / butyrate) — FLOW teaching; yields are taxa- and substrate-dependent.

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
