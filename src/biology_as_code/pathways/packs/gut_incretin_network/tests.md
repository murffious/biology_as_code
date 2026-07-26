# Structured tests — `gut_incretin_network`

**Module:** `biology_as_code.pathways.nutrient_sensing`  
**Pack id:** `gut_incretin_network`  
**Description:** Meal-triggered gut hormone mini-graph: CCK (I cells, fat/protein), GLP-1 (L cells, carbs/mixed meal), GIP (K cells), and PYY. Teaching edges to satiety, gallbladder/bile release, and insulin (incretin effect). FLOW signaling topology — not a full enteroendocrine atlas.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 10 |
| Edges | 14 |
| `activating_edges` | 11 |
| `inhibiting_edges` | 3 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 14

_No mechanism_id links (topology-only teaching graph)._

## Sources

- Incretin hormones GLP-1 and GIP — standard endocrine/GI physiology.
- CCK and gallbladder / pancreatic secretion — GI teaching texts.
- PYY and ileal brake — satiety physiology reviews.

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
