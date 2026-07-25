# Contributing data — strengthen the register

Most nutrition data is crowd-sourced into a swamp because nothing gates it. This
project is different: **every contribution walks a fail-closed gate before it can
strengthen anything.** An unsourced number can never become a confident one, so the
crowd can only ever *strengthen* the register — never weaken its epistemics.

A contribution is a small JSON file. You add one, open a PR, and CI validates it
with `biology_as_code.contrib.validate_contribution`
(see [`tests/test_contribution.py`](../tests/test_contribution.py)). The verdict is
one of three:

| Verdict | Meaning |
| --- | --- |
| `ACCEPTED` | Schema-valid, the target resolves, and a **primary source** backs it. It can raise the target's strength in the [validation ledger](VALIDATION_LEDGER.md). |
| `NEEDS_SOURCE` | Well-formed and on-target, but unsourced. Recorded `OPEN` (strength `0`) — kept, but promotes nothing. |
| `REFUSE` | Malformed, the target doesn't exist, or a **magnitude is asserted with no primary evidence.** |

The one rule behind all three: **empty beats fake.**

## What you can contribute

Start with **evidence** — it's the highest-leverage type, because it raises the
tier of rules the whole engine already uses.

| `type` | Strengthens | Must carry |
| --- | --- | --- |
| `evidence` | a law's evidence tier (FLOW → EVIDENCE → UNITS) | a resolvable `source` |
| `packet_fill` | fills a food packet field, fewer `UNEVALUABLE` | structural fills need no magnitude; magnitudes need a source |
| `claim` | the reference claim corpus (claim × food × expected verdict) | the law path that produces the verdict |
| `gate_bound` | a new gate or bound rule | a source **and** it must satisfy the CI invariant (`GateRule` ↔ `gate.present`) |

## The shape

```json
{
  "id": "contrib.evidence-unlu-2005-law020",
  "type": "evidence",
  "target": { "kind": "law", "ref": "LAW-020" },
  "payload": { "law": "LAW-020", "finding": "intrinsic food lipid opens the fat-vehicle gate" },
  "source": { "kind": "pubmed", "pmid": "15735074", "citation": "Unlu NZ et al. J Nutr. 2005;135(3):431-436." },
  "submitted": "2026-07-25"
}
```

- **`target.kind`** is `law`, `packet`, `nutrient`, or `claim`. `law` and `packet`
  refs must exist in the live register, or the contribution is `REFUSE`d.
- **`source`** is `pubmed` (a PMID), `doi`, `guideline`, or `textbook` (a citation
  string). No fabricated metadata — a PMID that isn't a PMID is `NEEDS_SOURCE`.
- **`asserts_magnitude: true`** means you're claiming a specific number. That path
  is `REFUSE`d without a primary source. Directions (expands/narrows) don't need
  one; magnitudes always do.
- **`strength`** is assigned by review on the ledger's 0–5 scale — leave it out.

Three worked examples live in [`examples/contributions/`](../examples/contributions):
one `ACCEPTED`, one `NEEDS_SOURCE`, one `REFUSE`.

## How to submit

1. **Fork** the repo.
2. Add one file: `examples/contributions/contrib.<short-slug>.json`.
3. Open a **pull request**. CI runs the gate; the verdict shows in the checks.
4. A maintainer merges `ACCEPTED` contributions, and the target's ledger row rises.

Prefer not to touch JSON? Open an
[**evidence issue**](https://github.com/murffious/biology_as_code/issues/new?template=evidence.yml)
— the form maps one-to-one onto the fields above, and a maintainer turns it into
the file.

## What survives scale

- **Never** a magnitude without a primary source.
- **Never** a green verdict over a missing field.
- Every accepted contribution carries its source into the ledger. That trail — not
  anyone's authority — is what makes the register trustworthy.
