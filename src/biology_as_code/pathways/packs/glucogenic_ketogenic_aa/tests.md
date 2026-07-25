# Structured tests — `glucogenic_ketogenic_aa`

**Module:** `biology_as_code.pathways.amino_acid_catabolism`  
**Pack id:** `glucogenic_ketogenic_aa`  
**Description:** Carbon-skeleton fate map for amino acids (teaching classification). Glucogenic AA feed TCA intermediates or pyruvate (→ glucose via GNG). Ketogenic AA yield acetyl-CoA or acetoacetate (cannot make net glucose in humans). Several AA are mixed. Not a reaction sequence — a topology of destinations for exam / nutrition teaching.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 13 |
| Edges | 10 |
| `graph_kind` | classification_map |
| `purely_ketogenic` | Leu, Lys |
| `note` | Not a single enzyme cascade; destination topology. |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **0** / 10

_No mechanism_id links (topology-only teaching graph)._

## Sources

- Glucogenic vs ketogenic amino acids — standard medical biochemistry tables.

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
