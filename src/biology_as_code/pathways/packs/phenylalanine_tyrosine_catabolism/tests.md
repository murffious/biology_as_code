# Structured tests — `phenylalanine_tyrosine_catabolism`

**Module:** `biology_as_code.pathways.amino_acid_catabolism`  
**Pack id:** `phenylalanine_tyrosine_catabolism`  
**Description:** Phenylalanine and tyrosine catabolism. Phe is hydroxylated to Tyr by phenylalanine hydroxylase (PAH, BH₄ cofactor) — the PKU enzyme. Tyr proceeds via homogentisate to fumarate (glucogenic) + acetoacetate (ketogenic). Teaching compression of the full multi-enzyme cascade.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 7 |
| Edges | 6 |
| `clinical_hook` | PKU (PAH) |
| `fate` | mixed glucogenic + ketogenic |
| `products` | fumarate + acetoacetate |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **1** / 6

```
  phenylalanine_hydroxylase
```

## Sources

- Phenylketonuria (PAH) — OMIM 261600; standard medical biochemistry.
- Tyrosine catabolism and alkaptonuria / tyrosinemia — Harper's / Lehninger.

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
