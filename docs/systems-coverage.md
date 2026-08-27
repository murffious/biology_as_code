# System coverage layer

Fail-closed map from a meal observation to the 11 medical body systems.

This module does **not** invent system effects. It prints which walks can
start from the fields a meal or trial actually declared.

## Rules

Taken from `docs/constitution.md`:

- empty beats fake
- gate ≠ bound
- L1→L5 without L3 is malformed
- mechanism walks never emit `Confirmed`

## What ships

| Artifact | Call |
|---|---|
| Coverage table | `cover_meal({...})` |
| Claim linter | `lint_claim("UPF causes depression.")` |
| Trial coverage | `trial_coverage("hall_2019")` |
| Edge ledger / next studies | `next_studies()` |

Shipped adapters: digestive, endocrine, cardiovascular, immune, nervous.

Parked (always `UNEVALUABLE`): integumentary, skeletal, muscular, respiratory, urinary, reproductive.

## Research coded here (not new RCTs)

### Hall 2019 (`PMID:31105044`)

| System | State | Why |
|---|---|---|
| Digestive | HOLDS | Eating rate measured |
| Endocrine | OPEN | Fasting hormones ≠ meal-stimulated GLP-1/PYY |
| Cardiovascular | OPEN | +0.9 kg / +508 kcal is surplus, not a CVD endpoint |
| Immune | UNEVALUABLE | No mucus/emulsifier assay |
| Nervous | OPEN | Rate compatible with reward; not isolated |
| Six parked | UNEVALUABLE | By design |

### Dicken 2025 UPDATE

Coded from public summaries used in the companion review. DOI/PMID must be
confirmed before journal deposit. Weight-class difference is treated as
cardiovascular/endocrine OPEN, not HOLDS, because eating rate was not
measured the way Hall measured it.

### Construct mismatch already in the ledger

`upf.endocrine.gi.t2d` is `REFUTED` as a *pathway assignment*, not as
"UPF is safe." The 2024 analysis of 1,995 GI-table items found mean GI of
UPF was not higher than minimally processed food (PMC11600077). GI is the
wrong L3 for the UPF trial effect.

`upf.nervous.mnp.dementia` is `REFUSE`. Tissue MNP reports are not dietary
exposure.

## What this is not

- Not a Kibo score
- Not 11 green checkmarks
- Not medical advice
- Not a replacement for `biology_as_code.audit.audit_claim` (that module
  walks nutrient gates on typed food packets; this module files the walk
  under anatomy and lints prose)
