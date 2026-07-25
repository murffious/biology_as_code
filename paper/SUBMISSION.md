# JOSS submission checklist

Draft only. Do not submit until the items below are resolved.

## Blocking

- [ ] **ORCID.** `paper.md` has a placeholder. JOSS requires a real ORCID for the
      corresponding author.
- [ ] **Author list on `dooley2018`.** Reconstructed from the paper's author block;
      confirm order and initials against the publisher record before submission.
- [ ] **`griffiths2024` volume/issue/pages.** The DOI resolves; the bibliographic
      detail beyond year is incomplete.
- [ ] **`wilkinson2016` author list** uses `and others`. Expand or confirm the
      truncation is acceptable to the JOSS proof.

## Claims in the paper that need a citation before submission

Two quantitative claims currently appear **without** a reference, because the source
was not verified to this repository's standard. Either verify and cite, or soften the
sentence. Do not paper over it with an approximate citation.

1. **"discordant classifications for between 5% and 37% of the same 15,342 foods,
   and ... most published models had never been validated."** This is the load-bearing
   number in the Statement of Need. The source is a nutrient-profiling model validation
   study in the *British Journal of Nutrition* (PubMed 30015603) comparing FSANZ,
   Nutri-Score, HCST, EURO and PAHO against the Ofcom reference. **Author list, year,
   volume and DOI are unverified here.** Resolve via PubMed 30015603.

2. Any statement about ultra-processed food intake or Hall's controlled-feeding trial
   was deliberately left out of this draft rather than cited from memory. If you want
   the UPF framing in the Statement of Need, pull the citations from the verified
   reference list already produced for *Biology as Code* (the book) rather than
   re-deriving them.

## Non-blocking, worth doing

- [ ] JOSS expects a statement of the software's research application. Consider naming
      one concrete downstream use (a course, a review, an audit) once one exists.
- [ ] Confirm the Zenodo DOI in the Acknowledgements matches the release being
      submitted; JOSS archives a specific version.
- [ ] Word count is within JOSS's 250–1000 word guidance for the body; re-check after
      edits.

## Rendering the paper locally

JOSS builds with Pandoc via their Docker image:

```bash
docker run --rm -v "$PWD/paper":/data -w /data openjournals/inara -o pdf paper.md
```

## Why the paper leads with the auditor

The auditor is the strongest claim in the package: a rule table that cannot drift
from its cited law without failing CI, and a verdict lattice whose top value is
unreachable by construction. Digestion machines and pathway graphs are good teaching
infrastructure but are not novel. Lead with the part reviewers cannot get elsewhere.
