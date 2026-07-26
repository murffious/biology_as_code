# FDP-1: Food Data Provenance Declaration

**Status:** Draft — Request for Comments
**Version:** 0.1.0
**Author:** Paul Murff
**Date:** 2026-07-26
**License:** Apache-2.0. Patent non-assertion covenant applies (see PATENTS.md).
**Normative form:** This Markdown document is normative. Any rendered PDF is provided for convenience only; if the two differ, the Markdown governs.

---

## Abstract

Food-quality scores are computed from data that regulation permits to be inaccurate, and no current scoring system declares which data it used. This document specifies a minimal format for declaring the provenance of a nutrient value and the validation status of a score computed from such values. It does not specify how to score food. It is intended to wrap any existing system — Nutri-Score, Health Star Rating, Nutri-Grade, Food Compass, or proprietary scores — without modification to that system.

---

## 1. Motivation

Under 21 CFR 101.9(g), a declared nutrient value in the United States is compliant if Class I nutrients meet at least 100% of the declared amount, Class II at least 80%, and calories, sugars, sodium, fat, and cholesterol do not exceed 120%. In the European Union, Regulation (EU) No 1169/2011 Article 31(4) permits declared values to derive from manufacturer analysis, calculation from ingredients, *or* calculation from generally accepted data, with Commission tolerance ranges applied on top.

A label value is therefore a legally bounded estimate, not a measurement. Databases that ingest label values — including USDA FoodData Central's Branded Foods — inherit those bounds. Every score computed downstream inherits them silently, with no error bar and no indication of source.

The gap this addresses is not "which food is healthy." It is that no scoring system currently states what it knew, how well it knew it, or how much of its answer rests on a legally permitted approximation.

---

## 2. Value declaration

Every nutrient value SHALL declare seven fields.

| Field | Type | Notes |
|---|---|---|
| `nutrient_ref` | string | Coded nutrient identity in a declared system: `hmdb:HMDB0000122`, `chebi:29033`, `usda.nutrient:303`. Names *which* nutrient this value is for. |
| `value` | number \| `OPEN` | See §4 |
| `unit` | UCUM string | e.g. `mg`, `g`, `kcal` |
| `source` | enum | `analytical` \| `label` \| `calculated` \| `imputed` \| `literature` \| `OPEN` |
| `source_ref` | string | Identifier of the *source record* the value was taken from: `usda.fdc:169097`, `foodb:FDB012345`, `hmdb:HMDB0000122` |
| `method` | string \| `OPEN` | Analytical method where applicable: `aoac:2011.25`, `aoac:991.43` |
| `retrieved` | ISO 8601 date | When the value was obtained from `source_ref` |

**`nutrient_ref` names the nutrient; `source_ref` names the source.** They answer different questions — *which* nutrient this is versus *where* the number came from — and a value declaration is unreadable in isolation without the first. A `nutrient_ref` resolves through a declared crosswalk such as `MASTER_CROSSWALK.tsv`; this is what makes a detached declaration self-describing and lets two declarations of the same nutrient be compared mechanically.

**`method` is not optional decoration.** Dietary fibre determined by AOAC 985.29, 991.43, and 2011.25 yields systematically different results for the same food, because the later methods capture resistant starch and low-molecular-weight soluble fibre the earlier ones miss. A fibre value without a method is not comparable to another fibre value.

### Provenance grades

| Grade | `source` | Meaning |
|---|---|---|
| **A** | `analytical` | Laboratory-determined, method declared |
| **B** | `calculated` | Derived from analytical values of declared components |
| **C** | `label` | Manufacturer-declared; subject to regulatory tolerance |
| **D** | `imputed` \| `literature` | Borrowed from a similar food or the published record |
| **—** | `OPEN` | Not known. See §4 |

---

## 3. Score declaration

A score computed from declared values SHALL declare five fields.

| Field | Type | Notes |
|---|---|---|
| `score_id` | string | System and version: `nutri-score:2023`, `kibo:2.1` |
| `inputs` | array | Array of `{ nutrient_ref, source_ref }` pairs, each identifying one value declaration (§2) consumed |
| `provenance_grade` | enum | **Computed, not asserted.** See §3.1 |
| `weights_published` | URI \| `false` | Where the weights and their derivation can be read |
| `validation` | object | See §3.2 |

### 3.1 The weakest-link rule

> **A score's provenance grade is the grade of its lowest-graded input.**

A score is not more trustworthy than the worst thing it was computed from. A composite drawing 40 analytical values and one label-derived value is Grade C. This is the only normative computation in this specification, and it is deliberately unforgiving: averaging provenance would let a system bury its weak inputs under its strong ones, which is precisely the behaviour this document exists to prevent.

### 3.2 Validation status

| Level | Meaning |
|---|---|
| `none` | No published validation |
| `face` | Expert judgment that outputs appear sensible |
| `convergent` | Agrees with an already-validated instrument |
| `criterion-intermediate` | Associated with health outcomes in published cohorts |
| `criterion-substantial` | Consistently associated with hard outcomes across multiple independent cohorts |

`validation` SHALL carry `{ level, citation }`. A level above `none` without a citation is non-conforming.

The tiers follow the rubric used in the 2023 *AJCN* systematic review of nutrient profiling systems, which found substantial criterion validation for Nutri-Score and intermediate for most others. A WHO review has found that the large majority of nutrient profiling models carry no validation mechanism at all. Declaring `none` honestly is conforming; implying more than you have is not.

---

## 4. The OPEN convention

> **A value that is not known SHALL be declared `OPEN`. It SHALL NOT be imputed silently, defaulted to zero, or omitted.**

`OPEN` is a first-class value. Omitting a field and declaring it `OPEN` are different statements: the first is silence, the second is a claim about the limits of what is known. Consumers of a declaration MUST be able to distinguish them.

Coverage SHOULD be reported as the fraction of fields carrying non-`OPEN` values, per dataset. Honest partial coverage is conforming; invented completeness is not.

---

## 5. Forward compatibility

> **Once FDP, always FDP.**

Any document conforming to FDP-1 SHALL remain valid under all future revisions. Future versions may add optional fields; they may not remove fields, redefine grades, or alter the weakest-link rule. Archives written today must still parse in twenty years.

This is a promise, not a version policy. It is why the specification is small: everything in it is permanent, so very little belongs in it.

---

## 6. Conformance

An implementation conforms if:

1. Every nutrient value carries all seven fields of §2.
2. Every score carries all five fields of §3, and every `inputs` entry resolves to a declared value by its `{ nutrient_ref, source_ref }` pair.
3. `provenance_grade` is computed by the weakest-link rule, not asserted.
4. Unknown values are `OPEN`, never invented.
5. `validation.level` above `none` carries a citation.

Conformance says nothing about whether a score is *correct*. It says only that a reader can determine what the score was computed from and what evidence supports it. That is the entire scope of this document.

---

## 7. Non-goals

This specification does not define healthy food, prescribe nutrients to include in a score, define weights, rank foods, or endorse any scoring system. Systems competing on scoring methodology can and should conform simultaneously.

---

## 8. Normative references

FoodOn · USDA FoodData Central · FooDB · HMDB · ChEBI · KEGG · InChIKey · UCUM · AOAC Official Methods of Analysis · 21 CFR 101.9(g) · Regulation (EU) No 1169/2011

---

## 9. Reference implementation

`github.com/murffious/biology_as_code` — validator, `MASTER_CROSSWALK.tsv`, and a worked example declaring full provenance across a single meal evaluated under two host states.

---

## Comments

Open an issue on the repository. This is a draft and expected to change until three independent implementations exist.
