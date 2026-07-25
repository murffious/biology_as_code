# Structured tests — `mtorc1_network`

**Module:** `biology_as_code.pathways.nutrient_sensing`  
**Pack id:** `mtorc1_network`  
**Description:** mTORC1 growth network. Amino acids (leucine via the Rag GTPases) and insulin/IGF (PI3K→Akt→TSC2→Rheb) converge to activate mTORC1, which drives protein synthesis (S6K1, 4E-BP1) and lipogenesis (SREBP) while shutting down autophagy (ULK1). AMPK opposes it (double-negative feedback).

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 13 |
| Edges | 13 |
| `activating_edges` | 7 |
| `inhibiting_edges` | 6 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 13

_No mechanism_id links (topology-only teaching graph)._

## Sources

- New developments in AMPK and mTORC1 cross-talk — Essays in Biochemistry 2024: PMC12055038 (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12055038/)
- AMPK-ULK1-mTORC1 regulatory triangle / autophagy oscillation: PMC7576158 (https://www.ncbi.nlm.nih.gov/pmc/articles/PMC7576158/)
- mTORC1, the maestro of cell metabolism and growth — Genes & Development 2025: https://genesdev.cshlp.org/content/39/1-2/109.full

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
