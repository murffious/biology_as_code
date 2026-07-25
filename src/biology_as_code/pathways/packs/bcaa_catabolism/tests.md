# Structured tests — `bcaa_catabolism`

**Module:** `biology_as_code.pathways.amino_acid_catabolism`  
**Pack id:** `bcaa_catabolism`  
**Description:** Branched-chain amino acid (BCAA) catabolism: leucine, isoleucine, and valine. Shared trunk: transamination → branched-chain keto acid dehydrogenase (BCKDH, MSUD enzyme). Then diverge: Leu → ketogenic (acetyl-CoA / acetoacetate); Val → glucogenic (succinyl-CoA); Ile → both.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 9 |
| Edges | 8 |
| `committed_enzyme` | BCKDH |
| `clinical_hook` | MSUD |
| `leu_fate` | ketogenic |
| `val_fate` | glucogenic |
| `ile_fate` | mixed |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **4** / 8

```
  aminotransferase
  bckdh
```

## Sources

- Maple syrup urine disease / BCKDH: OMIM 248600; standard biochem texts.
- BCAA metabolism overview — Lehninger / Harper's Biochemistry.

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
