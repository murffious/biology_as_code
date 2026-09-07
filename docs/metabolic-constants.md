# Metabolic constants: sources, and what may be encoded

This page ties each quantitative constant used around the digestion and redox
route modules to its source, and — separately — to a **rule about whether the
engine is allowed to compute with it**.

Those are two different questions, and conflating them is the failure mode this
repository exists to prevent. A number can be well sourced and still be illegal
to multiply by a meal field.

---

## The three tiers

| Tier | Meaning | Engine rule |
|---|---|---|
| **Identity** | Fixed by chemistry or structure. Does not vary between people. | **May be encoded** as a constant. |
| **Teaching constant** | An accepted physiological value with real spread around it. | May be **named** as identity. Never multiplied by a meal field. |
| **Population statistic** | A cohort average that masks large individual variation. | **Must stay OPEN** per packet. Evidence, not law. |

The tier, not the quality of the citation, decides what the code may do. Hinkle's
P/O ratios are excellent science and still may not be applied to a gram of fibre.

---

## Tier 1 — Identity (encoded)

Structural stoichiometry. These are already constants in the package.

| Constant | Value | Where encoded | Source |
|---|---|---|---|
| SOD dismutation | 2 O₂•⁻ + 2 H⁺ → H₂O₂ + O₂ | `SOD_O2_PER_H2O2 = 2` | McCord & Fridovich 1969 |
| GPx reduction | H₂O₂ + 2 GSH → 2 H₂O + GSSG | `GPX_GSH_PER_H2O2 = 2` | Lubos et al. 2011 |
| Oxidative PPP | G6P + 2 NADP⁺ → Ru5P + 2 NADPH + CO₂ | `PPP_NADPH_PER_G6P = 2` | Stanton 2012 |
| Glutathione reductase | GSSG + NADPH + H⁺ → 2 GSH + NADP⁺ | `GR_GSH_PER_GSSG = 2`, `GR_NADPH_PER_GSSG = 1` | Deponte 2013 |

Documented, not yet encoded — no module needs them:

| Constant | Value | Source |
|---|---|---|
| SMCT1 symport | 1 SCFA⁻ : 2 Na⁺ | Miyauchi et al. / den Besten et al. 2013 |
| H⁺ translocated per 2e⁻ | Complex I: 4, Complex III: 4, Complex IV: 2 | Chemiosmotic consensus |
| H⁺ per NADH / FADH₂ oxidised | 10 / 6 | as above |
| ATP synthase c-ring | c₈ → 8 H⁺ per 3 ATP = 2.67 H⁺/ATP | Mammalian structural biology |
| Transport surcharge | +1 H⁺/ATP (ANT + Pᵢ) → 3.67 H⁺/ATP total | as above |

---

## Tier 2 — Teaching constants (named, never applied)

| Constant | Value | Status in code | Source |
|---|---|---|---|
| P/O ratio, NADH-linked | ~2.5 (mechanistic ceiling ~2.72) | `PO_NADH = 2.5`, emitted as `po_identity` only | Hinkle 1991, 2005 |
| P/O ratio, FADH₂-linked | ~1.5 (mechanistic ceiling ~1.63) | `PO_FADH2 = 1.5`, same | Hinkle 1991, 2005 |

`dig/mitochondrial_routes.py` returns these in a `po_identity` field while every
entry in `amounts` stays `None`. The ratio is reported as a fact about the
respiratory chain; it is never used to turn a nutrient mass into ATP moles.

The ceilings (2.72, 1.63) follow from the tier-1 identities above:
10 H⁺ ÷ 3.67 H⁺/ATP ≈ 2.72, and 6 H⁺ ÷ 3.67 ≈ 1.63. The accepted 2.5 / 1.5 sit
below the ceilings because basal proton leak dissipates part of the gradient —
which is precisely why they are a *range in disguise* and belong in tier 2.

---

## Tier 3 — Population statistics (must stay OPEN)

**None of these are encoded, and none may be.** They are recorded here so that a
future contributor can see they were considered and rejected as law, rather than
overlooked.

| Constant | Reported value | Why it cannot be law | Source |
|---|---|---|---|
| SCFA molar ratio | ~60:20:20 acetate : propionate : butyrate | Population average over individual microbiomes | Miller & Wolin 1996 |
| Total colonic SCFA yield | 400–600 mmol/day | Depends on substrate, transit, and community | den Besten et al. 2013 |
| Electron leak, State 4 | ~1.0–2.0% of O₂ consumption | Isolated-mitochondria assay condition | Boveris & Chance 1973; St-Pierre 2002 |
| Electron leak, State 3 | ~0.1–0.2% of O₂ consumption | as above | St-Pierre et al. 2002 |
| Maximal H₂O₂ flux | ~20 nmol·min⁻¹·mg protein⁻¹ | Isolated pigeon heart, hyperoxic buffer | Boveris & Chance 1973 |
| Total cellular glutathione | 1–10 mM | Tissue-specific; a host seat, not a meal output | Lu 2013 |
| GSH:GSSG at rest | > 100:1 | Host redox state, not a function of a food packet | Lu 2013 |
| Glutathione redox poise | −240 to −280 mV | Derived from the above; same objection | Lu 2013 |

### The sources say so themselves

The strongest argument against encoding tier 3 comes from the reviews that
report it:

> The 60:20:20 SCFA ratio remains a population average that mathematically masks
> vast individual stoichiometric variations based on local colonic
> micro-environments, transit times, and the efficiency of resident methanogens.
> Universal constants for exact RS-to-butyrate molar yields in a given human are
> technically impossible without mapping the specific metagenomic structure of
> that individual's colonic ecosystem.

and, on respiratory state:

> In real, intact human myocytes experiencing highly variable, often hypoxic
> metabolic demands, mitochondria do not exist in pure State 3 or State 4, but
> rather fluctuate dynamically between them. Mapping the precise temporal
> percentage of electron leak over a 24-hour physiological cycle in vivo remains
> beyond current methodological capabilities.

A per-meal engine that emits a butyrate mass or a leak percentage is asserting
exactly the measurement its own sources say does not exist. That is why
`dig/respiratory_control.py` returns a **direction** (`state_3` / `state_4`,
`leak_direction` low/high) and no percentage, and why
`dig/colon_fermentation.py` returns SCFA **identity** with `amounts` all `None`.

---

## What a tier-3 number would need to become tier 2

Not a better citation — a **declared seat**. Tier 3 constants are properties of a
host and its microbiota, not of a food. They can enter a computation only when
the packet or host state actually declares the relevant field (measured GSH pool,
sequenced community, measured transit time), and then they are *evidence attached
to that declaration*, not a default. Silence stays UNEVALUABLE.

---

## Verification status

**The PMIDs below are recorded as supplied and have _not_ been resolved against
PubMed.** Network egress to PubMed was unavailable when this page was written, so
every identifier here is unverified.

This matters because this repository has already been bitten by it.
`tools/check_curies.py` exists because a resolve-and-diff pass found **23 of 79
place ids (29%)** in the digestive atlas naming a different body part — every one
of which passed a regex. An identifier that has not been resolved is decoration.

| Source | PMID as supplied | Status |
|---|---|---|
| Miller & Wolin 1996 | 8962261 | unresolved |
| den Besten et al. 2013 | **conflict — see below** | unresolved |
| Hinkle 1991 | 1939103 | unresolved |
| Hinkle 2005 | 15639704 | unresolved |
| Boveris & Chance 1973 | 4749271 | unresolved |
| St-Pierre et al. 2002 | 12417066 | unresolved |
| Lu 2013 | 22995213 | unresolved |
| Brand 2010 | 20463404 | unresolved, currently shipped in `dig/mitochondrial_routes.py` |

### Open conflict: den Besten et al. 2013

Three different PMIDs have been offered for the same review across three sources:

| Value | Origin |
|---|---|
| `24023713` | an earlier draft; already rejected in-tree |
| `24347302` | currently shipped in `dig/hepatic_routes.py` |
| `23985657` | the constants review this page was built from |

At most one is right. Until someone resolves it, the citation attached to SCFA
route identity is **`candidate`, not `verified`** — and this conflict is a
worked example of why the tier table above refuses to let an unresolved number
drive a computation.

Resolving these is a good first contribution: fetch each record, diff the title
against the claim it is attached to, and open a PR that either confirms the id or
replaces it.

---

## See also

- [Constitution](constitution.md) — `gate ≠ bound`, the four seats, L1→L5
- [VALUE.md](https://github.com/murffious/biology_as_code/blob/main/VALUE.md) —
  what the repository is and is not worth
