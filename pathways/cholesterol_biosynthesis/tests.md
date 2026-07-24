# Structured tests — `cholesterol_biosynthesis`

**Module:** `biology_as_code.pathways.cholesterol_pathway`  
**Pack id:** `cholesterol_biosynthesis`  
**Description:** Cholesterol biosynthesis (mevalonate pathway). Starts from acetyl-CoA and produces cholesterol. HMG-CoA reductase is the rate-limiting step and primary statin target.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 11 |
| Edges | 10 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **1** / 10

```
  hmg_coa_reductase
```

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
