# Note on the title

*This page is the canonical text. The README, the package docstring, the Zenodo
description and `paper/paper.md` each carry a shortened version of it;
`tests/test_naming_note.py` asserts they stay consistent.*

## The note (book front matter)

**Note on the title.** *Code Biology* is an established research program (Barbieri
and others) that treats living systems as containing organic codes — the genetic
code being only the most familiar of many. *Biology as Code* is a different claim.
It is not a theory about the nature of biological information. It is a
methodological stance: nutrition science and meal–pathway modeling should be
written the way engineers write infrastructure — versioned, tested,
provenance-tracked, and fail-closed. Where the existing literature is descriptive,
this work is prescriptive. The name collision is therefore useful: it forces the
distinction between studying codes *in* biology and treating nutrition models *as*
code.

## The distinction

| | Code Biology (Barbieri) | Biology as Code (this work) |
| --- | --- | --- |
| Nature of claim | Descriptive | Prescriptive |
| Core idea | Biology contains codes | Nutrition models should be written as code |
| Metaphor | Semiotics, organic codes | Infrastructure as code; executable specification |
| Primary concern | Meaning, interpretation, coding conventions | Versioning, testing, provenance, fail-closed evaluation, diffable models |
| Falsified by | Evidence that a claimed code is chemically determined rather than conventional | A model that cannot be versioned, tested, or traced to a source |

The last row is the one that matters in practice. The two programs are not rivals
because they are not answerable to the same evidence. Barbieri's is a claim about
what living systems *are*; this is a claim about how models of them *ought to be
built*, and it is defeated by engineering failure rather than by biology.

## Register-specific versions

Four other places carry this note. They are deliberately different lengths, and one
of them makes a deliberately weaker claim.

**README / PyPI long description** — short, factual, no thesis:

> **On the name.** *Code Biology* (Barbieri and others) is an existing field that
> studies organic codes in living systems. This project is unrelated: it is a
> methodological stance that nutrition and pathway models should be written like
> software — versioned, tested, provenance-tracked, fail-closed. Descriptive
> literature, prescriptive tool.

**Package docstring** — one sentence, because a docstring is not the place for an
argument:

> Unrelated to *Code Biology* (Barbieri), which studies organic codes in living
> systems; the claim here is methodological, not semiotic.

**Zenodo description** — one sentence, aimed at search disambiguation rather than
at a reader.

**JOSS paper** — formal, with the citation, and scoped to the *software* rather
than to the book's thesis. This distinction is load-bearing and easy to get wrong.

## A narrower claim for the package than for the book

The book argues that nutrition science *should* be written as code. The package is
a 0.1.0 alpha that does it for one small domain. Those are not the same claim, and
putting the book's thesis in the README of an alpha reads as overclaiming.

So the package-facing versions say what the software *is* — a methodological stance
made runnable — and leave the disciplinary argument to the book. A reviewer who
finds the package via PyPI should not have to accept a thesis about the field in
order to evaluate a toolkit.

## A second, milder collision

*Source Code for Biology and Medicine* is a journal that published software papers
for biology and medicine. It is a weaker collision than Barbieri's — nobody will
mistake a journal for a paradigm — but the phrase does compete in search, so
"biology as code" alone is a poor search term. Prefer the full package name
`biology-as-code` and the DOI in anything meant to be findable.

## Why "executable specification" may travel further than "infrastructure as code"

"Infrastructure as code" is precise and lands instantly with engineers. It lands
with almost no one in nutrition science, where the reference class is unfamiliar.
For mixed or academic audiences, *executable specification* carries the same
content — a spec you can run and test rather than prose you interpret — without
requiring the reader to know what Terraform is.

Both phrasings appear above. Use the audience's vocabulary rather than a single
canonical metaphor.
