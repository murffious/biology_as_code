# The Rhea bridge

**Rhea is the only place in this project where a chemical is allowed to become a
gene function — and even then the function is an enzyme activity, never a health
outcome.** This file says what we store, what we refuse to store, and what is
still empty.

It is the concrete form of one row in
[`relation-crosswalk.v1.json`](relation-crosswalk.v1.json): `participates_in`
(`RO:0000056`), whose range is *process or reaction*. That row explains why the
join exists. This file explains what it looks like when populated.

## Numbers, checked

Read off Rhea itself on 2026-09-07, not quoted from a summary:

| | |
|---|---|
| Release | **142**, dated 2026-09-02 |
| Unique reactions | **18,611** — and Rhea's own statistics page says this counts *quartets*, not rows |
| Unique participants | **15,203** |
| `rhea2go` mappings | **7,745** |
| Balanced at | pH 7.3, participants as ChEBI major microspecies — not the neutral textbook formula |

The quartet is real and it is the thing most likely to be flattened by accident.
One transformation carries four ids: an undefined master, left-to-right,
right-to-left, and bidirectional. Merging them destroys direction.

**Where the annotations actually land** — counted from the mapping files, because
the rule is usually stated more absolutely than it holds:

| File | undefined | left→right | right→left |
|---|---|---|---|
| `rhea2go` | 7,738 | 5 | 2 |
| `rhea2uniprot` | 334,813 | 56,098 | 9,732 |

So: GO overwhelmingly hangs on the undefined member — but **seven mappings do
not**, and a schema that forbids a directional GO xref would be wrong seven times.
Store the direction; do not assume it.

## Our row

`BiochemicalMechanism` (`models/biochemical_mechanisms.py`) already carries
`node_id`, `label`, `go`, `other_ontologies`, `reactome`, `participants`, `source`.
The Rhea-shaped version splits three of those and adds direction:

| Field | Ours today | Change | Why |
|---|---|---|---|
| `rhea` | inside `other_ontologies` | **promote** to its own field, holding the **master (undefined)** id | it is the join, not a cross-reference like the others |
| `rhea_direction` | — | **new**: `undefined` · `left_to_right` · `right_to_left` · `bidirectional` | the quartet is four ids; seven `rhea2go` rows are directional |
| `participants` | one list of pseudo-ids | **split** into `substrates` / `products`, each a resolvable ChEBI accession with stoichiometry, and `(in)`/`(out)` for transport | a reaction has sides; a flat list cannot say which |
| `go` | one field | **split** into `go_mf` and `go_bp` | see below — this is the expensive one |
| `ec` | — | **new**, optional | Rhea returns it; it is a class, never a direction |
| `uniprot` | — | **deliberately absent** | we have no protein layer. An empty field we cannot fill is the "empty beats fake" rule pointed at ourselves |
| `match` | — | **new**: `exact` · `narrower` · `broader` · `related` | reuse the relation-crosswalk vocabulary verbatim; do not invent `narrow`/`broad` |

**Why `go` must split.** `rhea2go` maps molecular function only. A biological
process is reached *through* the function, by `involved_in` (`RO:0002331`), and
never from the chemical directly. One `go` field invites exactly the error already
in the tree: `GO:0008270` — zinc ion binding — sits on the row labelled *Vitamin D
receptor ligand binding*. A single field cannot tell you whether the value was
supposed to be an activity or a process, so nothing catches the swap.

Identifier dialect is the repository's, not Rhea's: lowercase CURIEs
(`chebi:15377`), because that is what `normalize_crosswalk.py` emits and what
FDP-1 §2 accepts.

## Our chain

Same shape as the general one, with our spine stages named — that is the part a
generic diagram cannot give you:

```
spine:food        FOODON food term
      │ has_component        RO:0002180   ← the only rung that is a base edge (CONTAINS)
spine:compound    ChEBI accession, pH 7.3 microspecies if it appears in a Rhea
      │ participates_in      RO:0000056   ← ONLY if a named enzyme reaction exists
                  RHEA master id + direction
      │ xref                              ← rhea2go, molecular function only
spine:mechanism   GO molecular function
      │ involved_in          RO:0002331   ← process reached through the function
spine:physiology  GO biological process
      │ occurs_in            BFO:0000066
spine:anatomy     UBERON or CL
```

**No Rhea, stop at the compound.** That is not a gap to be filled with a plausible
id; it is the honest end of the chain. An organ endpoint — flow-mediated dilation
after cocoa — is a measured outcome at `spine:outcome`, not a reaction. There is no
`RHEA:vasodilation` and inventing one is the failure this whole file exists to
prevent.

## What we refuse

Already recorded as `forbidden` in the relation crosswalk and executed by
`tests/test_ontology_join_contract.py`. The Rhea-specific additions:

- **Never collapse the quartet.** Four ids, one chemistry, different arrows.
- **Never treat a Rhea id and a KEGG reaction id as identity.** Different
  protonation policy and, at times, a different stereocentre.
- **Never attach a biological process to a chemical** because a review used the
  same English word.
- **Searching Rhea by a ChEBI class walks `is_a` and `has_role`.** Querying a
  parent term pulls every child's reactions. Useful for discovery, wrong as a
  stored join — pick exact matching when writing a row.

## State today

Honest, and short:

- **One** Rhea id ships in the whole repository, and it is wrong. `RHEA:16501` sits
  on the ascorbate / 2-oxoglutarate-dioxygenase mechanism and is
  `sn-glycero-3-phospho-1D-myo-inositol + H2O = myo-inositol + sn-glycerol
  3-phosphate + H(+)` (EC 3.1.4.44). Unrelated chemistry. It survived because
  nothing resolved Rhea ids until 2026-09-07; `tools/check_curies.py` now does.
- **Twenty** `participants` entries are placeholders of the form `chebi:` plus an
  English word rather than an accession. They are reported as `MALFORMED` and
  carried in `tools/curie_baseline.json`. Until they are accessions, the
  `participates_in` join this file describes does not actually resolve to a
  molecule.
- **No** protein layer, so `enables` (`RO:0002327`) has no subject and `uniprot`
  stays absent rather than empty.

Nothing above is scheduled here. This file records the shape; the debt is tracked
in the baseline, which may only go down.
