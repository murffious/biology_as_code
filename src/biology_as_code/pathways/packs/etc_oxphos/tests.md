# Structured tests — `etc_oxphos`

**Module:** `biology_as_code.pathways.etc_oxphos`  
**Pack id:** `etc_oxphos`  
**Description:** Electron Transport Chain + Oxidative Phosphorylation. Electrons from NADH and FADH₂ flow through Complexes I–IV, creating a proton gradient that drives ATP synthesis via ATP synthase.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 13 |
| Edges | 10 |
| `atp_per_nadh` | 2.5 |
| `atp_per_fadh2` | 1.5 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 10

_No mechanism_id links (topology-only teaching graph)._

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
