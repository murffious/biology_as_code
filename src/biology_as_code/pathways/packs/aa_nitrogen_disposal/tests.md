# Structured tests — `aa_nitrogen_disposal`

**Module:** `biology_as_code.pathways.amino_acid_catabolism`  
**Pack id:** `aa_nitrogen_disposal`  
**Description:** Amino-acid nitrogen disposal hub. Most amino acids transfer their α-amino group to α-ketoglutarate (aminotransferases → glutamate). Glutamate dehydrogenase releases free NH₄⁺; aspartate donates the second N into the urea cycle. Carbon skeletons exit as α-keto acids toward glucogenic or ketogenic fates. Links to existing urea_cycle graph.

## Graph size

| Metric | Value |
|--------|------:|
| Nodes | 8 |
| Edges | 8 |
| `links_to` | urea_cycle |
| `central_collector` | glutamate |
| `n_atoms_in_urea` | 2 |

## Structural checklist

- [ ] `nodes >= 1` and `edges >= 1`
- [ ] Every edge `from_node` / `to_node` exists in `nodes`
- [ ] No empty node ids
- [ ] Mermaid renders (`pathway.mermaid`)

## Mechanism links

Edges with `mechanism_id`: **4** / 8

```
  aminotransferase
  glutamate_dehydrogenase
```

## Sources

- Berg JM, Tymoczko JL, Stryer L. Biochemistry — Amino Acid Degradation and the Urea Cycle.
- Lehninger Principles of Biochemistry — Nitrogen excretion and the urea cycle.

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
