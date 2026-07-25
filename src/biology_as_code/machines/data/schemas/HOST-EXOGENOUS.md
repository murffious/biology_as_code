# Host exogenous agents (meds · supplements · hormones)

**One simple model, three domains.** Avoid building three parallel drug encyclopedias.

## Core idea

```text
HostExogenousItem {
  domain:    medication | supplement | hormone
  class_id:  glp1_ra | vitamin_d | testosterone | …
  delivery:  oral | subcutaneous | intravenous | patch_transdermal | pellet_implant | …
  onboard:   true/false
  label?:    what the user calls it
  dose_text?: free text only — never a dosing engine
}
```

| Piece | File |
|-------|------|
| Delivery routes | `delivery-modality.catalog.json` |
| Unified item list | `HostExogenousProfile.schema.json` |
| Med classes (GLP-1 ready) | `medications.catalog.json` |
| Supplement classes | `supplements.catalog.json` |
| Hormone classes | `hormones.catalog.json` |
| Med-only profile (compat) | `MedicationProfile.schema.json` (route expanded = delivery) |

## Delivery modalities (keep coarse)

| id | Examples |
|----|----------|
| `oral` | pills, powders, liquids |
| `sublingual` | under tongue |
| `subcutaneous` | GLP-1 pens, many peptide/insulin SQ |
| `intramuscular` | IM B12, some T |
| `intravenous` | clinic IV drips |
| `patch_transdermal` | estradiol patch |
| `topical` | gels/creams |
| `pellet_implant` | hormone pellets |
| `nasal` / `inhaled` / `rectal` | occasional |
| `unknown` / `other` | escape hatches |

**Process hint only:** GI channel (oral) can interact with meals; parenteral/skin **bypasses oral absorption stories** for that agent — food quality coaching still independent.

## Domains

| domain | Catalog | Ready now |
|--------|---------|-----------|
| **medication** | medications.catalog | **glp1_ra** full; others stub |
| **supplement** | supplements.catalog | thin classes + IV drip class |
| **hormone** | hormones.catalog | stubs + delivery defaults |

## What we deliberately skip

- Infusion rates, implant mg/day curves  
- Bioequivalence oral vs inject  
- “IV Myers cocktail cures X” claims  
- Auto drug–drug interactions  

## Persona fields

- `medications` / `medications_structured` — existing  
- `supplements` (string[]) + optional `supplements_structured`  
- optional `hormones_structured` or unified `exogenous` profile  

Legacy strings still coerce via aliases.

## Scripts

```bash
python3 scripts/exogenous.py --user alex
python3 scripts/exogenous.py --list-deliveries
```
