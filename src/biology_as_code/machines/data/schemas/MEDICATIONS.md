# Medications (host L4) — starter system

**SSOT catalog:** `medications.catalog.json`  
**Instance shape:** `MedicationProfile.schema.json`  
**Honesty:** OPEN — self-report / import. **Not** a pharmacy, not CDSS, not prescribing.

## Scope discipline

Drugs can explode into “a ton of stuff.” We **do not** build a full formulary.

| Do | Don’t |
|----|--------|
| Class-level hooks (`glp1_ra`, `metformin`, …) | Every NDC / dose titration |
| Nutrition & process **biases** (protein priority) | Interaction severity engines |
| Claim **refuse** lists | “Food replaces your Rx” |
| Start with **GLP-1 RA** fully specified | Endogenous L-cell GLP-1 = same object |

## Architecture

```text
UserPersona.medications[]          (legacy free strings)
UserPersona.medications_structured → MedicationProfile
        │
        ▼
resolveMedicationFlags()  →  { glp1_ra, metformin, statin, c8_active, goal_bias, claim_refuses }
        │
        ├─► UserGoals soft bias (C-8 when glp1_ra)
        ├─► claim Q&A battery
        └─► later: HostState teaching flags (acid for PPI, etc.)
```

Endogenous **hormone** GLP-1 (L-cells, digestion maps) stays on the **packet/process** narrative.  
Exogenous **GLP-1 RA** is a **host medication class**.

## C-8 (ontology) ↔ product

From `kiboMasterOntology` **C-8 GLP-1 Override**:

> If User.GLP1 = True → Calorie Goal −20%; Fiber Goal −20%; Protein Priority = #1

Implementation: soft `c8_goal_bias` when `glp1_ra.onboard` — **FLOW teaching scales**, not medical targets.

## Science snapshot (GLP-1 RA) — OPEN summary

As of catalog `as_of` (not a systematic review):

1. **Class effects** include reduced appetite / increased satiety and **delayed gastric emptying** (degree varies by agent and duration of therapy).  
2. Trials show **lower energy intake** and clinically meaningful weight loss for labeled weight-management agents — magnitudes not locked into Kibo.  
3. Practical nutrition themes: **protein density** when total food volume falls; GI symptom tolerance; resistance training + protein for lean mass during loss; UPF quality still matters.  
4. **Complementary** to clinician-prescribed therapy — app never stops or starts the drug.

## First class ready: `glp1_ra`

See catalog entry for examples (semaglutide, tirzepatide, …), effects, and refuse claims.

Other classes (`metformin`, `statin`, `ppi`) are **stubs** so the schema doesn’t paint us into a corner.

## Persona seed

- Free-text `medications` kept for compatibility.  
- `medications_structured` preferred when present.  
- Demo: weight-loss persona may carry `glp1_ra` onboard for C-8 / claim demos (mock only).

## Delivery (injections, IV, patches, pellets…)

Shared with supplements & hormones — see **`delivery-modality.catalog.json`** and **`HOST-EXOGENOUS.md`**.

| Field | Meaning |
|-------|---------|
| `delivery` | Preferred: `subcutaneous`, `oral`, `intravenous`, `patch_transdermal`, `pellet_implant`, … |
| `route` | Compat alias of `delivery` |

GLP-1 pens default **`subcutaneous`**. IV nutrient drips use supplement class `iv_nutrient_drip` + `intravenous`. Hormone pellets use `pellet_implant`. No PK simulation.

```bash
python3 scripts/exogenous.py --list-deliveries
python3 scripts/exogenous.py --user taylor   # B12 IM + metformin oral
```

## Scripts

```bash
cd nutri-collective
python3 scripts/medications.py --user alex
python3 scripts/exogenous.py --user alex
python3 scripts/test_run_user_meal.py --user alex --quiet-sim
```
