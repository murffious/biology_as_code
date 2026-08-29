# The seven systems — can we use them?

**Short answer: yes.** Use the seven category names as concepts and as code
identifiers. Do not reproduce IFM's diagram, do not call it "the Functional Medicine
Matrix", and cite the lineage anyway.

*Researched 2026-08-29. Engineering hygiene, not legal advice — confirm with counsel
before commercial release.*

---

## The seven, as they appear in `laws.py`

`kibo_system` on the 47 frozen laws: **Assimilation** (21) · **Biotransformation** (5)
· **Structure** (5) · **Communication** (5) · **Defense** (4) · **Energy** (4) ·
**Transport** (3).

These correspond to the functional-medicine "core clinical imbalances": Assimilation;
Defense & Repair; Energy; Biotransformation & Elimination; Transport; Communication;
Structural Integrity. Ours are the same seven, shortened.

## What is actually protected

| Thing | Status | Effect on us |
|---|---|---|
| **"FUNCTIONAL MEDICINE MATRIX MODEL"** as a federal trademark | **ABANDONED.** USPTO serial 77356883, filed 2007-12-20, final refusal 2008-10-03, abandoned 2009-05-07 for failure to respond. Class 41, education services. | **No live federal registration.** Common-law rights may still exist from use in commerce, so still do not adopt the name. |
| The **Matrix diagram / worksheet** | Copyrighted, © IFM. Their notice permits personal reproduction; commercial reproduction needs written consent. | Real, and we are not touching it. We ship no diagram and no IFM text. |
| The **seven category names** | Ordinary physiology words. "Assimilation" and "biotransformation" are standard terms with independent literatures. | Usable. |
| The **idea of grouping physiology into functional categories** | A system / method of organising. | Not copyrightable — 17 U.S.C. §102(b), *Baker v. Selden*. |

Two doctrines settle the category names. **17 U.S.C. §102(b)**: copyright never
extends to an idea, procedure, process, system or method of operation, regardless of
how it is described — a classification scheme is a system. **37 C.F.R. §202.1(a)**:
words and short phrases are not subject to copyright.

A thin *compilation* copyright can attach to an original selection and arrangement.
Against that here: the categories are functionally driven rather than expressive, the
individual terms are standard, and the grouping is reproduced widely by unrelated
clinics and schools. It is a weak claim, but it is not zero, which is why the
boundaries below are worth keeping.

## Rules

**May do**
- Use the seven as internal identifiers, enum values, class names, function names.
- Group laws, models and mechanisms by them.
- Describe the physiology in our own words.
- Say the grouping follows the functional-medicine tradition.

**Must not**
- Call it the **Functional Medicine Matrix**, the **Matrix Model**, or **the IFM
  Matrix**. Abandoned registration is not the same as abandoned rights.
- Reproduce IFM's diagram, worksheet, or descriptive text.
- Imply IFM endorsement, affiliation, or certification.
- Present the framework as IFM's inside a commercial product without consent.

## Lineage note — the wording to use

Not compelled by copyright. Included because it is true, and because a project whose
thesis is that claims must carry their provenance cannot take a vocabulary silently.
It is the same discipline applied to VMH and Open Food Facts this session.

> **Systems vocabulary.** The seven functional categories used here — Assimilation,
> Biotransformation, Structure, Communication, Defense, Energy, Transport — follow
> the "core clinical imbalances" grouping developed in functional medicine
> (Bland, Institute for Functional Medicine, 1991–). The category names are ordinary
> physiological terms and the grouping is a classification system, neither of which
> is subject to copyright; no IFM diagram, worksheet, or text is reproduced here, and
> no affiliation with or endorsement by IFM is claimed or implied.

Place in: `NOTICE` (lineage section), the systems module docstring, and the book
chapter that introduces the systems axis.

## Sources

- USPTO serial **77356883**, *FUNCTIONAL MEDICINE MATRIX MODEL* — abandoned 2009-05-07:
  <https://trademark.justia.com/773/56/functional-medicine-matrix-model-77356883.html>
- IFM copyright / trademark notices: <https://www.ifm.org/legal-privacy/copyright-trademark-ownership/>
  *(returns 403 to automated retrieval; read in a browser before relying on it)*
- IFM Matrix toolkit article: <https://www.ifm.org/articles/toolkit-functional-medicine-matrix> *(also 403)*
- 17 U.S.C. §102(b); 37 C.F.R. §202.1(a); *Baker v. Selden*, 101 U.S. 99 (1879)

**Open:** both IFM pages block automated retrieval, so their current notice text has
not been read directly. Read them in a browser and record any wording that changes
the position above.
