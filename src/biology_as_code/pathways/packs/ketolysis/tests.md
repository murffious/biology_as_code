# Structured tests — `ketolysis`

**Module:** `biology_as_code.pathways.ketolysis`  
**Pack id:** `ketolysis`  
**Description:** Ketolysis. Extrahepatic tissues oxidize β-hydroxybutyrate and acetoacetate back to acetyl-CoA for the TCA cycle when glucose is scarce. The liver cannot run this pathway (no SCOT/OXCT1), which prevents a futile cycle with ketogenesis.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 4 |
| Edges | 3 |
| `main_substrate` | β-Hydroxybutyrate, Acetoacetate |
| `main_product` | Acetyl-CoA (to TCA cycle) |
| `location` | Extrahepatic mitochondria (NOT liver — lacks SCOT/OXCT1) |
| `acetyl_coa_per_ketone` | 2 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 3

_No mechanism_id links (topology-only teaching graph)._

## Sources

- Ketone Bodies — Biology LibreTexts 17.3 (BDH1 / SCOT / thiolase steps): https://bio.libretexts.org/Bookshelves/Biochemistry
- OXCT1/SCOT as the rate-limiting ketolytic enzyme, absent in liver: PMC12838892 (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12838892/)
- Metabolic and Signaling Roles of Ketone Bodies: PMC8922216 (https://pmc.ncbi.nlm.nih.gov/articles/PMC8922216/)

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
