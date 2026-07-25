# Seed fixtures — **single source of truth (SSOT)**

All product / sim tests should load data from **this directory**, not from repo-root `meals-50/`.

```text
nutri-collective/machines/schemas/fixtures/
├── user-personas.json                 # 8 personas
├── user-persona-data-inventory.json   # provenance / lifestyle / readiness
├── data-sources.catalog.json
├── user-goals-mock.json
├── host-clinical-mock.json
└── meals/                             # 67 enriched meals + ACCURACY.md
    ├── 01_raw_01_….json
    ├── …
    ├── ACCURACY.md
    ├── packets-for-sim.json           # optional export
    └── payloads-for-sim.json
```

## Run the test (fixtures only)

```bash
cd nutri-collective
python3 scripts/test_run_user_meal.py
python3 scripts/test_run_user_meal.py --user taylor --meal upf_01_instant_ramen
python3 scripts/meals_to_sim.py --list
python3 scripts/meals_to_sim.py --meal raw_01_chicken_quinoa_broccoli_bowl --simulate
```

Scripts print `[ssot] meals_dir=.../fixtures/meals` so you can confirm the path.

### Claim Q&A battery (after the run)

`test_run_user_meal.py` reverse-engineers the sim into **seeded claim questions** the system can answer with science/law hooks:

| Example question | Uses |
|------------------|------|
| Will ADEK / micelle path open? | `micelle_gate_open`, fat_g, L-FAT-1 |
| Does C help iron here? | `iron_walk_yield`, ascorbate, LAW-004 |
| SCFA / fiber story? | fiber, `scfa_mmol`, LAW-025/026 |
| Low glycemic claim? | **Refuse** (no ScoreAxes glycemic in this path) |
| Disease prevention claim? | **Refuse** + refuse list |

Outputs:

- `meals/TEST_RUN_{user}_{meal}.json` → includes `claim_qa_battery[]`
- `meals/TEST_RUN_{user}_{meal}_claims.md` → human-readable Q&A

```bash
python3 scripts/test_run_user_meal.py --quiet-sim   # still prints Q&A summary
python3 scripts/test_run_user_meal.py --no-qa        # sim only
```

### Medications (GLP-1 first)

Structured host meds live in persona `medications_structured` + catalog:

- `../MedicationProfile.schema.json`
- `../medications.catalog.json` — **`glp1_ra` ready**; metformin/statin/ppi stubs
- `../MEDICATIONS.md`

Alex seed includes mock **GLP-1 RA** → C-8 goal bias + extra claim Q&As (`q_glp1_*`).

```bash
python3 scripts/medications.py --user alex
```

### Dual-plate contrast (same user, two meals)

```bash
python3 scripts/contrast_run.py
# default: alex × chicken bowl vs instant ramen
python3 scripts/contrast_run.py --user taylor
```

Writes `meals/CONTRAST_{user}_{mealA}_vs_{mealB}.json` + `.md` with side-by-side yields and claim-verdict flips.

## vs `meals-50/` at repo root

| Path | Role |
|------|------|
| **`fixtures/` (here)** | **Final seed for app + sim tests** |
| `NUTRI-COLLECTIVE_0/meals-50/` | Workshop / enrich pipeline (QA, hydration, truth). **Do not point product tests here.** |

If you re-run enrich scripts in `meals-50/`, copy results back into `fixtures/meals/` before testing.

## Accuracy

See `meals/ACCURACY.md` — real barcodes/USDA where possible; NOVA + micros imperfect; all OPEN/FLOW teaching.
