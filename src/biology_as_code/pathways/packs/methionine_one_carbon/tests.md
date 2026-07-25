# Structured tests — `methionine_one_carbon`

**Module:** `biology_as_code.pathways.amino_acid_catabolism`  
**Pack id:** `methionine_one_carbon`  
**Description:** Methionine and one-carbon metabolism. Met is activated to S-adenosylmethionine (SAM), the universal methyl donor. After methyl transfer, SAH → homocysteine. Homocysteine is remethylated to Met (methionine synthase, B12 + 5-methyl-THF) or committed to cysteine via transsulfuration (CBS, B6).

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 7 |
| Edges | 7 |
| `universal_methyl_donor` | SAM |
| `branch_point` | homocysteine |
| `cofactors` | B12, folate, B6 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **1** / 7

```
  methionine_adenosyltransferase
```

## Sources

- One-carbon metabolism and methionine cycle — standard nutrition/biochem texts.
- Homocysteine, folate, B12 interactions — public health / vascular literature.

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
