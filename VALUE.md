# What this repository is worth

Not a body simulator. **A standard for not lying about food.**

That distinction is the whole asset. Everything below follows from it.

---

## What is actually valuable

**1. A constitution that is rare in nutrition software.**
`label ≠ dose`, `gate ≠ bound`, four evaluation seats, the L1→L5 causal stack,
`empty beats fake`. Most nutrition tooling does the opposite and hides it: a
missing field silently becomes a zero, and a zero silently becomes a score. See
[`docs/constitution.md`](docs/constitution.md).

**2. FDP-1 as a real spec, with a validator.**
Provenance attached to a number is a public-good layer that food-composition
databases, front-of-pack scores, and consumer apps all lack. A spec with a
running validator is worth more than a position paper.

**3. Executable teaching.**
Spinach ± oil. Iron ± tea / ascorbate. Whole vs skim milk. These are runnable
fixtures, not diagrams — they demonstrate a gate closing rather than asserting
that one exists.

**4. A package that actually ships.**
PyPI, CI, law cards, packets, claim auditor. Alpha, but real. Policy papers
without running code are sermons.

---

## What it is not worth

- **Predicting ATP, ROS, GSH, or metabolic outcomes from a meal field.** Not "not
  yet" — not the product.
- **A clinical or consumer score.** Explicitly out of scope. Keeping it out *is*
  part of the value.
- **Completeness.** Forty pathway graphs and ten machines are a syllabus, not a
  genome-scale model. This does not replace COBRApy, and it does not replace
  trials.

---

## One claim this repository cannot support

There is an appealing pitch that goes roughly:

> Connect an AI agent to this repo and it can calculate the SCFA yield, route it
> through hepatic clearance, and output the exact molar yield of
> β-hydroxybutyrate — a biological calculator that grounds LLM answers in
> thermodynamic reality.

**It cannot do this, and that is deliberate.** The code refuses to:

| Module | What it returns | What it refuses |
|---|---|---|
| `dig/colon_fermentation.py` | acetate / propionate / butyrate **as named products** | every `amounts` value is `None`; no g→g conversion |
| `dig/hepatic_routes.py` | the distinct sinks each SCFA can reach | first-pass clearance fractions stay OPEN |
| `dig/mitochondrial_routes.py` | TCA → NADH/FADH₂ → ETC path, P/O as identity | ATP moles and superoxide grams stay OPEN |
| `dig/respiratory_control.py` | State 3 vs State 4 **direction** | no leak percentage of anything |

A fixed yield table would make the repository *more confident and less true*. The
refusal is the feature being sold. An agent grounded on this engine gets
"UNEVALUABLE, and here is the field that is missing" — which is a better answer
than a fabricated molar yield, and is the only answer that survives review.

The numbers behind those refusals are documented, with sources and with an
explicit rule about which may be encoded, in
[`docs/metabolic-constants.md`](docs/metabolic-constants.md).

---

## The honest product wedge

**Judgment and audit:** *"this claim cannot be evaluated from this packet."*

That sentence is useful to regulators, journals, and anyone tired of green badges
sitting on top of missing data. A 24-hour digital twin is not useful, because
nobody can check it.

---

## Who the first user is

Neither "developers building health apps" nor "researchers modelling trials",
exactly. The first user is the **reviewer** role that both of those contain —
someone who has to reject a nutrition claim *in writing* and needs a defensible
reason. Concretely: journal reviewers and editors, standards and regulatory
staff, and evidence-synthesis teams.

Three reasons to aim there first:

1. **They get value at N = 1.** One audited claim is already useful. An app needs
   coverage across a whole food database before it ships at all, and this repo is
   nowhere near that breadth — an app developer hits the completeness wall on day
   one.
2. **Their pain is exactly this repo's best output.** They do not want a score.
   They want a defensible refusal with the missing field named.
3. **They are the only population that can supply `LAW-SPEC` PRs.** Writing a law
   card is a natural byproduct of a researcher's existing work. An app developer
   has no incentive to contribute one, so a developer-first strategy consumes the
   law library without growing it.

App developers are the second audience, not the first, and they become viable
only after the card library has breadth. The right first artifact for the wedge
user is therefore not a prediction API — it is the claim auditor as a citable,
reproducible verdict.

---

## How this stays worth the time

Merge the identity and route work, and the roadmap filter. **Do not merge the
ledgers.** Mutable mmol pools, `min(potential, adp)` engines, and invented yield
tables would convert a defensible standard into an indefensible toy, and the
conversion is one-way: once a fake number ships, every downstream user treats it
as real.

The repository's value is bounded by adoption, and adoption depends on it
remaining the thing you can point at when you need to say *no* with a citation.
