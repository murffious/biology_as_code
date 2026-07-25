# Contrast report — Alex Rivera × two plates

**SSOT:** `/Users/morf/Downloads/morf-engineering/mealcoachai/dev/NUTRI-COLLECTIVE_0/nutri-collective/machines/schemas/fixtures/meals`  
**User:** Alex Rivera (`alex`) · goal=weight_loss · app_score=72

**Meal A:** Grilled Chicken, Quinoa & Broccoli Bowl (`raw_01_chicken_quinoa_broccoli_bowl`)  
**Meal B:** Instant Ramen Lunch (`upf_01_instant_ramen`)

> A (raw_01_chicken_quinoa_broccoli_bowl) vs B (upf_01_instant_ramen): plate_quality → A, iron_walk → A, scfa → A

_All magnitudes OPEN/FLOW teaching. Not clinical advice. See meals/ACCURACY.md._

## Side-by-side metrics

| Metric | Meal A | Meal B | Δ (A−B) | Note |
|--------|--------|--------|---------|------|
| `plate_quality` | 0.82 | 0.2 | 0.62 | higher better |
| `density` | 0.436 | 0.258 | 0.178 | higher better |
| `fiber_g` | 6.68 | 1.95 | 4.73 | context |
| `protein_g` | 52.27 | 9.89 | 42.38 | context |
| `nova_max` | 4 | 4 | 0.0 | lower often less UPF |
| `kibo_score` | 75.0 | 70.0 | 5.0 | meal engine OPEN |
| `atp_units` | 812.6 | 702.8 | 109.8 | OPEN energy FLOW |
| `iron_walk_yield` | 1.2 | 0.33 | 0.87 | higher friendlier iron story |
| `iron_bioavailability_factor` | 0.48 | 0.132 | 0.348 | OPEN |
| `scfa_mmol` | 4.01 | 1.17 | 2.84 | fiber → colon teaching |
| `micelle_gate_open` | True | True | 0.0 | ADEK path |
| `energy_charge` | 0.955 | 0.93 | 0.025 | OPEN |

## Claim Q&A — where verdicts differ

### `q_fiber_scfa`

**Q:** Does this meal produce a colon SCFA story in the sim?

- **A (raw_01_chicken_quinoa_broccoli_bowl):** `support` — Yes. fiber≈6.7 g → scfa_mmol≈4.01 (FLOW prototype: fiber × soft factor, LAW-025/026 magnitudes not locked). Useful to compare high-fiber vs low-fiber plates; no…
- **B (upf_01_instant_ramen):** `partial` — Yes. fiber≈1.9 g → scfa_mmol≈1.17 (FLOW prototype: fiber × soft factor, LAW-025/026 magnitudes not locked). Useful to compare high-fiber vs low-fiber plates; no…

### `q_iron_vitamin_c`

**Q:** Does this plate support the ‘C helps iron’ teaching claim?

- **A (raw_01_chicken_quinoa_broccoli_bowl):** `support` — Partially yes. ascorbate_same_meal=True; iron_walk_yield=1.2; iron_bioavailability_factor=0.48. The engine applies LAW-004-style ascorbate expansion and can als…
- **B (upf_01_instant_ramen):** `partial` — Weak / no strong C signal. ascorbate_same_meal=False; iron_walk_yield=0.33; iron_bioavailability_factor=0.132. The engine applies LAW-004-style ascorbate expans…

### `q_nova_upf`

**Q:** Does NOVA / processing paint this plate as ultra-processed?

- **A (raw_01_chicken_quinoa_broccoli_bowl):** `partial` — Packet nova_max=4, nova_modal=1, plate_quality=0.82 (quality uses solid-food NOVA so a UPF drink does not fully paint the solids). Yes — at least one NOVA-4 com…
- **B (upf_01_instant_ramen):** `support` — Packet nova_max=4, nova_modal=4, plate_quality=0.20 (quality uses solid-food NOVA so a UPF drink does not fully paint the solids). Yes — at least one NOVA-4 com…

### `q_protein_adequacy`

**Q:** Is protein content a strength of this meal in the sim framing?

- **A (raw_01_chicken_quinoa_broccoli_bowl):** `support` — Plate protein ≈ 52.3 g (absorbed teaching ≈ 48.1 g). Yes — high relative to a typical meal band. No muscle-protein-synthesis lab is run; leucine threshold is no…
- **B (upf_01_instant_ramen):** `partial` — Plate protein ≈ 9.9 g (absorbed teaching ≈ 9.1 g). Moderate/lower protein for a main plate. No muscle-protein-synthesis lab is run; leucine threshold is not ful…

## Full Q&A summary counts

| | A | B |
|--|--:|--:|
| support | 5 | 3 |
| partial | 2 | 4 |
| refuse | 2 | 2 |
| context | 3 | 3 |

## What this demo is for

1. Same host, two packets — differences come from the **meal**, not a new user.
2. Soft yields (iron, SCFA, quality) move in teaching-friendly directions for whole-food vs UPF.
3. Claim battery **supports** mechanism questions and **refuses** disease/glycemic overclaims on both.
4. Not computed here: full TS ScoreAxes / 128-factor vector (next layer).

