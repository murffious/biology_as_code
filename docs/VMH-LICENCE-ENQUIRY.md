# Licence enquiry to VMH — draft, ready to send

**Status:** unsent as of 2026-08-29. Send to the VMH contact listed at
<https://www.vmh.life> (the site lists a contact/feedback address; the group is
Thiele/Fleming, University of Galway). Copy `vmh-support` if a support alias exists.
Do not guess an address — take it from the site.

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
> **2,797 rows**. Eight of its twelve columns are derived from a VMH Recon3D
> metabolite export: the VMH abbreviation, full name, charged formula, InChIKey,
> and the HMDB / KEGG / ChEBI / PubChem cross-references. The remaining four
> columns are our own.
>
> I want to make sure we are using and citing this correctly, and I could not find
> a definitive statement of the terms. The VMH database paper (Noronha et al., *NAR*
> 2019) says the data are "freely available" but does not name a licence. Separately
> I have seen ReconMap described as CC BY-NC-ND 4.0, and my own notes record
> Recon3D as CC BY-NC 2.0 — but I would rather ask than assume.
>
> **My question:** what licence governs reuse and redistribution of the VMH
> metabolite table (the `recon-store-metabolites` export) — in particular, may a
> derived identifier crosswalk like ours be redistributed, and under what
> conditions? If there is a non-commercial restriction, I would like to record it
> accurately rather than infer it.
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
