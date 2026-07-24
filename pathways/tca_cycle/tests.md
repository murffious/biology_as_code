# Structured tests — `tca_cycle`

**Module:** `biology_as_code.pathways.tca_cycle`  
**Pack id:** `tca_cycle`  
**Description:** TCA / Citric Acid Cycle (Krebs Cycle). Central amphibolic pathway that oxidizes acetyl-CoA to CO₂ while generating reducing equivalents (NADH, FADH₂) and one GTP. Edges are formally linked to MetabolicMechanism objects.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 9 |
| Edges | 8 |
| `nadh_per_acetyl_coa` | 3 |
| `fadh2_per_acetyl_coa` | 1 |
| `gtp_per_acetyl_coa` | 1 |
| `approx_atp_equivalents` | 10 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **8** / 8

```
  aconitase
  alpha_ketoglutarate_dehydrogenase
  citrate_synthase
  fumarase
  isocitrate_dehydrogenase
  malate_dehydrogenase
  succinate_dehydrogenase
  succinyl_coa_synthetase
```

## Biochemical invariants (document here)

Hand-fill like root `glycolysis/tests.md` when auditing against pathway mermaid packs:

| Invariant | Expected | Status |
|-----------|----------|--------|
| Energy / stoichiometry | _(TBD for this path)_ | Open |
| Irreversible / regulated steps | _(TBD)_ | Open |

## Automated tests

```bash
PYTHONPATH=src python3 tests/test_pathway_packs.py
# or: pytest tests/test_pathway_packs.py -q
```

Gold audit style: `glycolysis/tests.md`.
