# Structured tests — `fatty_acid_synthesis`

**Module:** `biology_as_code.pathways.fatty_acid_synthesis`  
**Pack id:** `fatty_acid_synthesis`  
**Description:** De novo fatty acid synthesis. Cytosolic pathway that builds palmitate from acetyl-CoA. Requires NADPH and is highly regulated at ACC.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 6 |
| Edges | 5 |
| `main_product` | Palmitate (C16:0) |
| `nadph_required` | 14 per palmitate |
| `atp_required` | 7 per palmitate |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 5

_No mechanism_id links (topology-only teaching graph)._

## Biochemical invariants (document here)

Hand-fill like root `glycolysis/tests.md` when auditing against textbook:

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
