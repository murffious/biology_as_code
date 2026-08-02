# Structured tests — `tryptophan_niacin`

**Module:** `biology_as_code.pathways.micronutrient_cofactor_pathways`  
**Pack id:** `tryptophan_niacin`  
**Description:** Tryptophan catabolism through the kynurenine route to niacin, with the serotonin/melatonin branch. The source of the niacin equivalent, and PLP-dependent at two steps.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 19 |
| Edges | 18 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 18

_No mechanism_id links (topology-only teaching graph)._

## Sources

- Berdanier CD. Advanced Nutrition: Macronutrients, 2nd ed. CRC Press, 2000. Appendix 2, Metabolic Maps, pp. 471-492. Map 6, p. 475.
- Institute of Medicine. Dietary Reference Intakes for Thiamin, Riboflavin, Niacin, Vitamin B6, Folate, Vitamin B12, Pantothenic Acid, Biotin, and Choline. National Academies Press, 1998. DOI 10.17226/6015 [accession UNVERIFIED — resolve before it is quoted as the anchor]

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
