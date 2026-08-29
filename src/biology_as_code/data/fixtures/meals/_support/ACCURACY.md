# meals-50 — accuracy & honesty for SIM use

**Status:** solid enough to drive the reference simulator and PacketLoad demos  
**Not:** clinical nutrition software, lab assays, or locked UNITS magnitudes  
**Date:** 2026-07-23  

This seed is **close to real** (real barcodes, USDA rows, computed portions) and **explicitly imperfect**. Read this before trusting a score.

---

## What we did

### 1. Base meals (already real-sourced)
- Every ingredient points at `curated-foods-dev` via `source.pk` (`FOOD#…` or `BARCODE#…`).
- Portion nutrition = `per_100g × grams / 100` (QA: scale math FAIL=0).
- Meal totals = sum of ingredients.
- Branded lines carry FDC/OFF-style label text + avoid_flags where present.
- Hydration added on **62/67** meals (real drinks: Gatorade, Diet Coke, Essentia, smartwater, Tropicana, Topo Chico, water, coffee, milk…).

### 2. Truth enrichment (`enrich_truth.py`)
Run over **129 unique ingredients** (321 total lines):

| Step | Action |
|------|--------|
| Online OFF | Cached product fetch by GTIN when available (**26** products OK this run) |
| Online FDC | Attempted by `fdcId` — **DEMO_KEY rate-limited** (24 fails this run); use real key + re-run to improve |
| NOVA | Assigned on **all 321** ingredients |
| Micro honesty | Branded/OFF zero micros treated as **undeclared**, not true zero |
| Peer estimates | P10–P90 bands within food class from analytical USDA rows in-corpus |
| Meal `derived` | `nova_max`, `nova_modal`, `full_panel_coverage_pct` |

### 3. Sim projection (`meals_to_sim.py`)
Maps each meal →:
- **`FoodPayload`** for `bridge_engine.simulate_payload` (macros, fiber, quality, soft vitamins, anti-nutrient proxy)
- **`PacketLoad`** for DigestRun / playground (`items`, `nova_class`, `macros_g`, hydration channel)

---

## Accuracy by field

| Field | How “true” | Typical confidence | Notes |
|-------|------------|--------------------|--------|
| Ingredient identity + grams | High | High | Real pk/GTIN; grams are recipe design not weighed plate |
| Macros (P/C/F/kcal/fiber/Na) | High for seed | High | Computed from FDC/branded/OFF panels; Atwater may diverge on sauces/powders |
| Branded micros | **Low–medium** | Low when label-sparse | **149/321** lines `label_sparse` — zeros → undeclared in `nutrition_truth` |
| Analytical micros (USDA whole foods) | High | High | Best for raw chicken, produce, grains |
| Peer micro **estimates** | Medium | OPEN only | P10–P90 from peers; **not** lab values for that SKU |
| NOVA class | Medium | Mixed | See breakdown below |
| Macro online cross-check | Medium | Partial | **47** ok vs FDC/OFF, **2** review/mismatch (limited online coverage) |
| Cooking method / form | Low | FLOW | Often `unknown` / inferred |
| Quality / density scores for sim | Soft teaching | FLOW | Derived from NOVA + protein/fiber/coverage — **not** a published index |

### NOVA assignment mix (321 ingredients)

| Source | Count | Confidence meaning |
|--------|------:|--------------------|
| `curated_map` | 191 | Whole foods / oils / simple fluids we know well |
| `rule` | 77 | Industrial markers on ingredient list or avoid_flags |
| `openfoodfacts` | 53 | OFF `nova_group` when product resolved |

Confidence tags: **high 201 · medium 60 · low 60**.

### Meal-level `nova_max` (67 meals)

Rough spread after enrichment: many meals are **3–4** once branded items or sports drinks are on the plate (e.g. chicken bowl + Gatorade → `nova_max: 4` even though the solids are whole food). That is **honest for the full packet including beverage**, not a claim that the chicken is UPF.

---

## Imperfections (do not paper over)

1. **FDC live API mostly failed this pass** (rate limit). Re-run:
   ```bash
   python3 enrich_truth.py --fdc-api-key "$FDC_API_KEY" --max-online 200 --copy-fixtures
   ```
   Cache lives in `meals-50/cache/`.

2. **OFF coverage partial** (26 cached products). More GTINs → better NOVA + macro checks.

3. **Gold Dynamo / `fdc_branded_nova_enriched`** not joined in this workspace — when available, prefer it over rules.

4. **Vitamin units in FoodPayload** are soft: mcg/mg mixed into bridge “intake bump” logic — fine for OPEN sim, not DRI math.

5. **Peer bands are corpus-small** (n often 3–15). Ranges are directional.

6. **5 snacks still have no drink** on purpose (incomplete-log demos).

7. **Sim quality_score** is a teaching curve from NOVA, not Nutri-Score / Health Star.

---

## How close to “real” for the SIM?

| Use case | Ready? |
|----------|--------|
| Run `simulate_payload` on named meals | **Yes** |
| Compare whole-food vs UPF trajectories | **Yes** (use raw_* vs upf_*) |
| Persona + plate DigestRun demos | **Yes** (PacketLoad export) |
| Clinical advice / personal DRI | **No** |
| Publishable nutrient claims | **No** without re-validation against FDC bulk + labels |

**Working definition of success:** real-world identifiers + consistent math + honest gaps + sim can consume the plate.  
**Not success:** pretending every micro and NOVA is laboratory-certain.

---

## Commands

```bash
# Offline QA (structure + math)
python3 qa_meals50.py

# Re-enrich NOVA/truth (online when possible)
python3 enrich_truth.py --max-online 80 --copy-fixtures

# List meals for sim
python3 meals_to_sim.py --list

# Show FoodPayload + PacketLoad
python3 meals_to_sim.py --meal raw_01_chicken_quinoa_broccoli_bowl --show

# Run bridge sim on a meal
python3 meals_to_sim.py --meal upf_01_instant_ramen --simulate

# Export all packets / payloads for app fixtures
python3 meals_to_sim.py \
  --export-packets ../nutri-collective/machines/schemas/fixtures/meals/packets-for-sim.json \
  --export-payloads ../nutri-collective/machines/schemas/fixtures/meals/payloads-for-sim.json
```

---

## File map

| Path | Role |
|------|------|
| `NN_*.json` | Full meal seed + `nova_*` + `nutrition_truth` + `derived` |
| `truth_enrichment_report.json` | Counts from last enrich run |
| `cache/off/`, `cache/fdc/` | Online response cache |
| `meals_to_sim.py` | Sim / PacketLoad adapter |
| `ACCURACY.md` | This document |
| `fixtures/meals/` (under nutri-collective) | Copy next to user personas |

Companion user seeds: `fixtures/user-personas.json` + inventory. Join later as `DigestRun { host, packet, clinical, goals }`.
