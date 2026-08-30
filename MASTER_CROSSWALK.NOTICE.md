# MASTER_CROSSWALK.tsv — attribution and licence

**This table is not entirely ours.** Eight of its twelve columns derive from a
Virtual Metabolic Human (VMH) / Recon3D metabolite export.

| From VMH / Recon3D | Not from VMH |
|---|---|
| `vmh` · `name` · `formula` · `inchiKey` · `hmdb` · `kegg` · `chebi` · `pubchem` | `seed` · `modeled_pathway` · `term_id` · `systems` |

## Cite VMH if you use this

> Noronha A, Modamio J, Jarosz Y, et al. **The Virtual Metabolic Human database:
> integrating human and gut microbiome metabolism with nutrition and disease.**
> *Nucleic Acids Research* 2019;47(D1):D614–D624. doi:10.1093/nar/gky992
>
> Brunk E, Sahoo S, Zielinski DC, et al. **Recon3D enables a three-dimensional view
> of gene variation in human metabolism.** *Nature Biotechnology* 2018;36:272–281.
> doi:10.1038/nbt.4072
>
> <https://www.vmh.life>

## Licence status: `OPEN`

Declared, not asserted — the same convention this table uses for its own cells.

- This project's own `working_map_nutrition/VMH_REFERENCE.md` records **CC BY-NC 2.0**
  for Recon3D and CC BY-NC-ND 4.0 for ReconMap.
- The VMH database paper (NAR 2019) names **no licence**; it says only that the data
  are "freely available".
- **VMH does publish terms, and they were found on 2026-08-29** at
  <https://delta.vmh.life/resources/faq/faq26.html>:

  > VMH content is freely available for academic and research use; please cite the
  > appropriate resources. Several data sources integrated into VMH carry their own
  > licences, some of which restrict commercial use – please check the terms of the
  > original source for such data. For commercial-licensing questions, please contact
  > ines.thiele [at] universityofgalway [dot] ie

  That is a statement of terms, not an SPDX licence, and it does **not** address
  redistributing a *derived compilation* in a public repository. So: academic and
  research use is granted with citation, commercial use is restricted, and our
  specific question remains open.
- A previous version of this file said `vmh.life` returns **HTTP 403 to automated
  retrieval**. That was wrong and it was load-bearing: it is why the terms above went
  unread for a month. The 403 came from one fetching tool being blocked, not from the
  site — plain `curl` gets HTTP 200 on the site, the FAQ and the `/_api/` endpoints.
  **A tool being blocked is not a source being silent**, and the two must never again
  be recorded as the same thing.
- **The redistribution question has not been confirmed with the rights holder.**

**Until they are: treat this file as non-commercial, and as carrying an attribution
requirement, regardless of the Apache-2.0 licence on the rest of this repository.**
Apache-2.0 governs the code here. It does not reach these rows, and this project has
no power to place them under it.

## What is actually exposed

The individual cells are largely facts. A chemical formula is not creative
expression; neither is `chebi:15637`. The exposure is the **compilation** — 2,797
curated rows lifted wholesale, and specifically the cross-reference mapping between
VMH, HMDB, KEGG, ChEBI and PubChem, which is the curatorial work that gives this
table its value. VMH is maintained in the EU, where the *sui generis* database right
restricts substantial extraction independently of copyright.

## Ways out, if commercial use is ever needed

1. **Confirm the terms with VMH.** The status above is `OPEN`; it may resolve to
   something permissive.
2. **Swap the backend to Human-GEM** (CC BY 4.0) and regenerate. This project's own
   `VMH_REFERENCE.md` identified this path for a commercial build in July.
3. **Reduce to identifiers only** — drop `name`, and rebuild the cross-references
   from each registry directly instead of from VMH's mapping. This removes the
   compilation exposure and discards the join that makes the table worth having.
4. **Licence it** from the rights holder.

## Not legal advice

Engineering hygiene, assembled from the sources' own statements and this project's
prior assessment. Confirm with counsel before commercial use or relicensing.

---

*A project whose thesis is that a value without its provenance is unusable cannot
ship a table without its own. This file is that provenance. See `NOTICE`,
`THIRD-PARTY-DATA.json`, and `../CROSSWALK-CANONICAL.md`.*
