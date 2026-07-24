# Structured tests — `lipoprotein_transport`

**Module:** `biology_as_code.pathways.cholesterol_pathway`  
**Pack id:** `lipoprotein_transport`  
**Description:** Lipoprotein-mediated transport of cholesterol and triglycerides. VLDL carries cholesterol out of the liver; LDL delivers it to tissues; HDL performs reverse cholesterol transport back to the liver.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 7 |
| Edges | 6 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 6

_No mechanism_id links (topology-only teaching graph)._

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
