# Meal-fixture support data

Reference libraries and derived reports that travel *with* the 67 teaching meals
but are **not meals themselves** (so the meal loader's `list_meal_files()` glob
skips this `_support/` subdirectory). Preserved verbatim from the original app's
`machines/schemas/fixtures/meals/` so nothing is lost as that repo is archived.
The original app note for this folder is kept as `README.original-app.md`.

## Reference libraries (input data — hand-curated)

| File | What it is |
|------|------------|
| `beverage_library.json` | Beverage packets (teaching cargo/partners for drinks). |
| `off_products_snapshot.json` | Small Open Food Facts snapshot (branded product rows). |
| `packets-for-sim.json` | Packet-shaped inputs prepared for the simulator. |
| `payloads-for-sim.json` | FoodPayload-shaped inputs prepared for the simulator. |

## Derived reports (regenerable — kept as provenance)

| File | What it is |
|------|------------|
| `_index.json` | The app's original meal index (superseded by `../index.json`). |
| `FOOD_SUBSET_CLASSIFICATION.json` | Acquisition / oil / sugar tags over the meals. |
| `truth_enrichment_report.json` | Enrichment/accuracy report over the meal set. |
| `ACCURACY.md` | Notes on how the meal numbers were sourced. |
| `CONTRAST_*` | Worked side-by-side of a whole-food vs a UPF meal. |
| `TEST_RUN_*` | A captured end-to-end run (persona + meal → bridge). |

These are snapshots: the reports can be regenerated from the meals + engine, and
are kept only as provenance, not as a source of truth.
