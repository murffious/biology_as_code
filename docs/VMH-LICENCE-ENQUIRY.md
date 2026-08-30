# Licence enquiry to VMH — draft, ready to send
ines.thiele@universityofgalway.ie.
**Status:** unsent as of 2026-08-29. **Address resolved 2026-08-29** — see below.

## Where to send it

**Correction, 2026-08-29:** an earlier version of this file said `vmh.life` returns
**403** to automated retrieval. That was false. One fetching tool was blocked; plain
`curl` gets **HTTP 200** on the site, the FAQ and every `/_api/` endpoint. The error
mattered, because it is why nobody read VMH's terms — **which exist**, at
<https://delta.vmh.life/resources/faq/faq26.html>:

> VMH content is freely available for academic and research use; please cite the
> appropriate resources. Several data sources integrated into VMH carry their own
> licences, some of which restrict commercial use – please check the terms of the
> original source for such data. For commercial-licensing questions, please contact
> ines.thiele [at] universityofgalway [dot] ie

That answers most of the original letter, so the letter below is now **one question,
not four**. It also confirms the contact address independently — the FAQ's own
obfuscated address resolves to the same mailbox found from the NAR paper:

| | |
|---|---|
| **To** | Prof. Ines Thiele — `ines.thiele@universityofgalway.ie` |
| **Cc** | `ines.thiele@gmail.com` — the address printed in the NAR paper |
| **Cc** | Prof. Ronan M.T. Fleming — `ronan.mt.fleming@gmail.com` (NAR paper) |

Thiele has moved since the paper: she is now Personal Professor in the **School of
Biological and Chemical Sciences and the Ryan Institute, University of Galway**, and
directs the **Digital Metabolic Twin Centre** — which is what the copyright line at
the foot of the VMH site (`ThieleLab/FlemingLab @ DMTC`) refers to. The Luxembourg
address in the paper is stale; the Galway institutional address is the live one, so
it goes in the To line and the paper's gmail addresses are the fallback.

**Do not use LinkedIn.** A licence answer needs to be attributable and archivable —
a LinkedIn DM to a company page reaches whoever runs the account, is not on the
record, and cannot be cited in `THIRD-PARTY-DATA.json` as the basis for a licence
determination. Email from an institutional address can. Keep LinkedIn as the nudge
route only if there is no reply in three weeks.

**Why this letter matters:** the answer collapses three open items at once. If the
terms are permissive, the non-commercial constraint, the Human-GEM swap question,
and the Apache-2.0 conflict all disappear. If they are not, you have it in writing
and can act deliberately rather than conservatively.

**Keep it short.** Academics answer short, specific, easy-to-answer emails. One
question, clearly bounded, with the answer they can give in two sentences.

---

## Subject

`Licence terms for reuse of VMH metabolite identifiers in an open-source project`

## Body

> Dear VMH team,
>
> I maintain **biology-as-code**, a small open-source Python project for modelling
> meal digestion and metabolic pathways
> (<https://github.com/murffious/biology_as_code>, Apache-2.0). It is teaching and
> research software, not a clinical or commercial product.
>
> The project publishes a metabolite crosswalk table, `MASTER_CROSSWALK.tsv`, with
> **2,797 rows**. Nine of its twelve columns are derived from a VMH Recon3D
> metabolite export: the VMH abbreviation, full name, charged formula, the HMDB /
> KEGG / ChEBI / PubChem cross-references, the ModelSEED id (via your
> `SEED2VMH_translation.csv`), and an InChIKey column — which is empty in every row,
> as the export we took carried none. The remaining three columns are our own.
>
> I have read the terms on your FAQ: academic and research use is free with
> citation, several integrated sources carry their own restrictions, and commercial
> licensing goes through you. That is clear, and we are non-commercial research
> software, so I believe we are inside it.
>
> **My one question is about redistribution rather than use.** We do not only *use*
> the export — we publish a derived table containing those columns, in a public
> GitHub repository under Apache-2.0. Does the academic-and-research grant extend to
> redistributing a derived compilation that way, and if so is there wording you would
> like us to carry? I would rather ask than assume, because "freely available for
> academic and research use" is a grant to a *user*, and I cannot tell from it
> whether it also runs to that user's downstream readers.
>
> A smaller second question if it is easy: we may swap the metabolite backend to
> Human-GEM (CC BY 4.0). 819 of the rows we would take are marked `metFrom: Recon3D`.
> Would those remain under VMH's terms, or does Human-GEM's licence govern them?
>
> In the meantime we have taken the conservative reading. The table now ships with
> explicit VMH attribution (citing both Noronha et al. 2019 and Brunk et al. 2018),
> a notice stating that our Apache-2.0 licence does not extend to the VMH-derived
> columns, and a machine-readable third-party register. If any of that attribution
> is worded incorrectly, I would be glad to correct it.
>
> Thank you for building and maintaining VMH — the cross-reference mapping in
> particular has saved this project a great deal of work.
>
> With thanks,
>
> Paul Murff
> Morf Engineering Inc.
> <https://github.com/murffious/biology_as_code>

---

## Notes on the wording

- **Asks one question.** Everything else is context they can skim.
- **States what we already did.** This is the difference between an enquiry and a
  disclosure. We are not asking permission after the fact; we are asking them to
  confirm or correct a conservative reading we have already implemented.
- **Does not admit a violation, and does not need to.** We took the restrictive
  reading and attributed. That is the correct posture whether or not a restriction
  exists.
- **Does not ask for a licence grant.** Asking "may we have permission" invites a
  legal review and a slow no. Asking "what are the terms" invites a two-line answer.
- **Gives the exact numbers** — 2,797 rows, eight of twelve columns, named. A
  maintainer can judge substantiality immediately instead of asking follow-ups.
- **Thanks them for the mapping specifically.** It is the curatorial work that
  actually matters here, and saying so is both true and disarming.

## When the answer arrives

Whatever it says, it is a **primary source** and it changes several records:

| Update | File |
|---|---|
| `licence_confidence` OPEN → the confirmed value | `THIRD-PARTY-DATA.json` |
| The licence-status section | `MASTER_CROSSWALK.NOTICE.md` |
| The third-party paragraph | `NOTICE`, `.zenodo.json` |
| Evidence + `next_check` | claim `CLM-LICENCE-VMH` in `claims.v1.json` |
| The licence table | `nutri-collective/working_map_nutrition/VMH_REFERENCE.md` |

**Save the reply itself** — an email from the rights holder is the primary source
that upgrades this claim's tier from a self-survey to something citable. Keep it in
`docs/` alongside this file.

## If there is no reply

Silence is not permission and it is not refusal. After ~6 weeks with no answer,
record the attempt and its date in `THIRD-PARTY-DATA.json` and leave the status
`OPEN`. An unanswered good-faith enquiry, documented, is a materially better
position than never having asked — and it is exactly the "declared, not asserted"
discipline this project applies to everything else.


Virtual Metabolic Human
Browse
Toolbox
Models
Clinicians
API
Search for metabolites, reactions, diseases...

Background
Citations

Virtual Metabolic Human Website


Human Metabolism Resource


Microbial Metabolism Resource


Disease Resource


Thermodynamic Information


ReconMap


Leigh Map

Virtual Metabolic Human
Integrating human and gut-microbiome metabolism with nutrition and disease.

Follow us:
LinkedIn
YouTube
Browse
Human
Microbes
Microbiome
Disease
Nutrition
Maps
Toolbox
Overview
Persephone
Molecule editor
Metabolomics upload
Downloads
Resources
API
SPARQL
About
Statistics
Visitor map
How to cite
FAQ
Index
© 2026 by ThieleLab/FlemingLab @ DMTC
Disclaimer: For research purposes only
Feedback
/general/Citation