# The manager layer — what OMA is for, and what ours has to be

Palantir ships an **Ontology Manager** (OMA) alongside the ontology itself. Reading it
as an authoring UI misses the point: the object-type editor is the least interesting
part. The load-bearing panels are the ones that answer *what happens if I change
this* — **Branches**, **Dependents**, **Usage / Usage History**, **Observability**.

That is not UI polish. It is the admission that **an ontology has consumers, and a
type change breaks them.** A vocabulary with no consumers needs no manager. Ours has
consumers, so it needs the functions — not necessarily the application.

## The three questions a manager exists to answer

| OMA panel | The question | Our answer today |
|---|---|---|
| **Dependents** | Who reads this artifact? | **Now generated.** `ontology_inventory.py` scans the tree; `MASTER_CROSSWALK.tsv` has **29** readers, `aca.ttl` **14**, the vocabulary **7**. |
| **Observability / Usage** | How much moves if I change it? | **Partial, and hand-measured once.** 2026-08-24: adding two phrases to the `cardiovascular` group changed 4 of 123 association rows, added 5 studies (716→721), and moved a published pooled effect 0.78→0.75. Nothing recomputes that automatically. |
| **Branches** | Can I propose a change without breaking live readers? | **Ratchets, not branches.** `nutrition-vocab.baseline.json` and `quality_baseline.json` make a change *fail loudly*; they do not let you see the consequence before committing to it. |

Not having the first answer is what cost the crosswalk a month. The question *who
reads `MASTER_CROSSWALK.tsv`* had to be re-derived by hand on 2026-08-29, and the
answer — FDP-1 §2 cites it by URL, plus `README`, `CITATION.cff`, `PATENTS.md`,
`.zenodo.json` — is what settled which copy was canonical in about a minute. A
standing Dependents view would have made the decision available all along.

**So the v0 manager is not an application. It is those three answers, on the command
line, kept fresh by the same generators that already gate everything else.** One is
done. The second is the valuable one and is genuinely hard: it means being able to
say, before a vocabulary edit lands, *this moves N published effect sizes.* That is
the same capability the book demands of nutrition, turned on ourselves.

If a UI ever exists it is a tab in `evidence-hub-v2.html`, never a new page.

---

## The four components, and the one substitution

Palantir models every operational decision as **Data · Logic · Action · Security**.
Three map cleanly. The fourth does not, and the mismatch is informative.

| Component | Theirs | Ours |
|---|---|---|
| **Data** | datasets mapped to object types | registers, FDP-1 packets, the crosswalk, the corpus |
| **Logic** | functions evaluating a decision | 47 laws, 9 gates, 38 bounds — already frozen, already tested |
| **Action** | orchestrated writes back to the source | validators; `Declared[T]` refusals |
| **Security** | policy compliance on the decision | **Provenance.** |

Their fourth component asks *is this decision permitted?* Ours asks *is this decision
licensed by evidence?* Those are the same shape — a gate the decision must pass that
is not about the data's content — but a different authority. Access control says who
may see a number. Provenance says whether the number may be used at all, by anyone,
including its author. **A nutrition claim with perfect access control and no method is
still worthless**, which is why the substitution is not a rename.

## Dataset → ontology, and the cell that is missing

| Datasets | Ontology | Here |
|---|---|---|
| Dataset | Object type | `MASTER_CROSSWALK.tsv` → `Metabolite`; `nutrition-vocab.v1.json` → `Concept` |
| Row | Object | one metabolite; one SKOS concept |
| Column | Property | `chebi`, `hmdb`, `kegg`, `inchiKey`; `prefLabel`, `altLabel`, `hiddenLabel` |
| Field | Property value | `chebi:15637` |
| Join | Link type | the crosswalk **is** a link type, already — nutrient ↔ metabolite |

The mapping is exact until the fourth row, and then it stops. **"Field → Property
value" assumes a field has a value.** 20,983 of our 33,564 crosswalk cells do not —
they say `OPEN`, and 2,797 of them are the entire `inchiKey` column. In their table
those are nulls, and a null is not a property value; it is the absence of one.

That is where we extend rather than adopt, and it is the whole of `Declared[T]`: a
property whose value may be `a value`, `NONE` (checked, genuinely none exists), or
`OPEN` (nobody has looked). Three states, never `Optional[T]`. Their model has no
cell for the third, because in an operational system somebody always knows. In
nutrition nobody does, and pretending otherwise is the failure the book is about.

**Borrow the four nouns. Borrow the dataset mapping. Refuse the assumption that a
field has a value.**
