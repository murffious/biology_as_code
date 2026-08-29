# Machines · run schemas (L1–L3 carrier)

**Home:** `nutri-collective/machines/schemas/`  
**Not** process/stage graphs — those stay in `process/`, `stage/`, `lens/`.

| File | Layer | Role |
|------|--------|------|
| `HostState.schema.json` | L1 | Who is running (boot + physiology flags) |
| `PacketLoad.schema.json` | L2 | Plate: ingredients, NOVA, cooking, residue flags, derived matrix |
| `IngestionEvent.schema.json` | L3-ingest | Chew time, sequence/order, pace |
| `DigestRun.schema.json` | Carrier | host + packet + optional ingestion → process |
| `ScoreAxes.schema.json` | **Process measurements** | Four FLOW axes (not constitutional LAW) |
| `score-axes.catalog.json` | Catalog | Terms, process_hooks, DigestRun field map, legacy keys |
| `HostClinicalProfile.schema.json` | L1 clinical | Genetics, biomarkers, hormonal, dynamic_state (**setup/mock**) |
| `fixtures/host-clinical-mock.json` | Fixture | MTHFR + IR HIGH + inflammation HIGH |
| `UserGoals.schema.json` | L1 goals | Weight loss / manage / gain, BMI, energy bias |
| `fixtures/user-goals-mock.json` | Fixture | weight_loss + BMI mock |
| `UserPersona.schema.json` | L1 persona | Named mock user: host + clinical + goals + prefs + app + data_inventory |
| `DataSource.schema.json` | Provenance | One connected/declared/missing stream (Part 0.6 maturity) |
| `fixtures/user-personas.json` | Seed | 8 hand-crafted personas (alex…avery) — SSOT for playground + Python |
| `fixtures/user-persona-data-inventory.json` | Provenance seed | Per-slug sources, 7 lifestyle loads, microbiome, readiness |
| `fixtures/data-sources.catalog.json` | Catalog | Real-world source classes (wearable, labs, Viome-class, CGM…) |
| `fixtures/` | **SSOT seed** | Users + meals — **product/sim tests must load here** |
| `fixtures/meals/` | Meal seed | 67 enriched meals + ACCURACY.md |
| `food-subsets/` | Taxonomies | Acquisition (fast food = venue), oils, sugars — **quality separate** |
| `nutri-collective/scripts/test_run_user_meal.py` | Test | Persona + meal → bridge (fixtures only) |
| `nutri-collective/scripts/classify_food_subsets.py` | Classifier | Tag meals with acquisition / oil / sugar |

**Do not run product tests against repo-root `meals-50/`** (workshop only). See `fixtures/README.md`.

### Fast food design rule

`quick_service` = **where you bought it**, not bad food. A QSR salad can score well on NOVA/quality; home Pop-Tarts can score poorly. See `food-subsets/FOOD-SUBSETS.md`.

### Medications (L4 host) — GLP-1 first

| File | Role |
|------|------|
| `MedicationProfile.schema.json` | Structured med items (`class_id`, onboard) |
| `medications.catalog.json` | Classes; **`glp1_ra` ready**, others stub |
| `MEDICATIONS.md` | Scope + science snapshot + C-8 |

```bash
python3 scripts/medications.py --user alex
python3 scripts/test_run_user_meal.py --user alex --quiet-sim   # includes GLP-1 claim Qs when onboard
```

**Not** a formulary or CDSS. Endogenous L-cell GLP-1 ≠ GLP-1 RA pen.

### Delivery modalities (inject / IV / patch / pellet)

Same shape for **meds, supplements, hormones** — route only, no PK:

| File | Role |
|------|------|
| `delivery-modality.catalog.json` | oral, SQ, IM, IV, patch, pellet, … |
| `HostExogenousProfile.schema.json` | unified item list (`domain` + `class_id` + `delivery`) |
| `supplements.catalog.json` | small supplement classes |
| `hormones.catalog.json` | small hormone classes (stubs) |
| `HOST-EXOGENOUS.md` | design rules |

```bash
python3 scripts/exogenous.py --list-deliveries
python3 scripts/exogenous.py --list-all-users
```
| `BioactiveCompound.schema.json` | Compound | kind + **provenance** + attachment |
| `bioactive-peptides.catalog.json` | Peptides | collagen split, carnosine, VPP/IPP, edges |
| `BIOACTIVE-PROVENANCE.md` | Doc | 3 origin tiers + grades |

## Map → MachineContext (`meal.*` / `host.*` / `intake.*`)

App stages read **flat dotted fields**. Adapter: `src/lib/machines/digestRun.ts` → `toMachineContext(run)`.

| Schema path | MachineContext field |
|-------------|----------------------|
| `host.ready` | `host.ready` |
| `host.acid_capacity` | `host.acidCapacity` |
| `host.bile_capacity` | `host.bileCapacity` |
| `host.insulin_resistance` | `host.insulinResistance` |
| `host.post_surgical` | `host.postSurgical` |
| `host.alcohol_with_meal` | `host.alcohol` |
| `host.leucine_adequacy` | `host.leucineAdequacy` |
| `packet.intake.*` | `intake.food` / `hydration` / `supplement` |
| `packet.macros_g.protein` | `meal.proteinG` |
| `packet.macros_g.fat` | `meal.fatG` |
| `packet.macros_g.carb` | `meal.glucoseG` (available CHO teaching) |
| `packet.macros_g.fiber` | `meal.fiberG` |
| `packet.macros_g.fructose` | `meal.fructoseG` |
| `packet.derived.matrix_integrity` (+ chew boost) | `meal.matrixIntegrity` |
| `packet.derived.food_quality` | `meal.foodQuality` |
| `ingestion.mastication_quality` / derived | `meal.masticationQuality` |
| `ingestion.food_order_score` / derived | `meal.foodOrderScore` |
| `ingestion.chew_time_s_*` | `meal.chewTimeS` (mean or total) |

## Processing combined (items)

`derivePacketDerived(items)` (TS):

1. **nova_max** = max item `nova_class` (default 1 if all unknown → honesty OPEN).  
2. **industrial** = mean `industrial_processing` or map from nova.  
3. **cook_stress** = max severity of `cooking_methods` (fry/smoke > steam/raw).  
4. **processing_combined** = clamp mix of industrial + cook (FLOW).  
5. **matrix_integrity** ≈ `1 - processing_combined` (form liquid/UPF floors it).  
6. **food_quality** ≈ matrix with residual residue soft penalty (OPEN if only proxies).  
7. **residue_burden** = max flag intensity (default OPEN honesty).

## Chew + order

| Prefer | Fallback |
|--------|----------|
| `sequence[].chew_time_s` | `chew_time_s_mean_per_bite` → `mastication_quality` |
| ordered `sequence[].rank` | `food_order_score` alone |

High chew → small **positive** `matrix_integrity_boost` (FLOW).

### Multi-item oral loop (implemented)

```ts
import { buildOralItemContexts, shouldMultiItemOral, getStage, trace } from "../src/lib/machines";

if (shouldMultiItemOral(run)) {
  for (const loop of buildOralItemContexts(run)) {
    trace(getStage("oral")!, loop.ctx); // one oral path per rank
  }
}
```

- UI: `MachineStageTrace` with `digestRun` + sequence → rank chips.  
- Claim: `digestRunToClaimPacket(run)` + optional `<MachineStageTrace digestRun={…} />` in Claim cards.  
- Process hop still **meal aggregate** `toMachineContext`; only **oral** micro-runs per item.

## Python crosswalk (simulator_latest)

| Schema | Python today |
|--------|----------------|
| HostState | `physiological_state.HostState` + profile flags |
| PacketLoad | `meal_engine.FoodPayload` (+ extend items) |
| IngestionEvent | `physiological_state.IngestionContext` |
| DigestRun | not unified yet — build from payload + profile |

## Examples

See `src/lib/machines/digestRun.ts` fixtures and `src/__tests__/digestRun.test.ts`.

UI: Digestion lab → `MachineStageTrace` (knobs → `mealKnobsToDigestRun`); Claim cards → **Load fixture · salad + oil**.

## Process measurements (ScoreAxes)

These are **measurements of the process / packet quality**, not Court LAWs.

| id | term | legacy |
|----|------|--------|
| `density` | Nutrient density | `law_1_density` |
| `glycemic_velocity` | Glycemic velocity | `law_2_glycemic` |
| `oxidative_burden` | Oxidative burden | `law_3_inflammation` |
| `matrix_vitality` | Matrix vitality | `law_4_vitality` |

```ts
import { measureScoreAxes, FIXTURE_SALAD_OIL } from "../src/lib/machines";
const m = measureScoreAxes(FIXTURE_SALAD_OIL);
// m.axes.density.term === "Nutrient density"
// m.composite.score  // FLOW 0–100
```

Each axis lists `process_hooks` (which `stage.*` it reads) in `score-axes.catalog.json`.

## Host clinical (genetics / labs / dynamic) — setup only

```ts
import {
  MOCK_HOST_CLINICAL,
  deriveSoftConstraints,
  withClinicalProfile,
  FIXTURE_SALAD_OIL,
  toMachineContext,
} from "../src/lib/machines";

const run = withClinicalProfile(FIXTURE_SALAD_OIL, MOCK_HOST_CLINICAL);
// run.clinical.constraints → teaching mocks, not enforced yet
const ctx = toMachineContext({ ...FIXTURE_SALAD_OIL, clinical: MOCK_HOST_CLINICAL });
// ctx.host.mthfrMutation, insulinResistance, inflammationStatus
```

| Block | Example | Soft constraint (later) |
|-------|---------|-------------------------|
| `genetics.mthfr_mutation` | `true` | avoid synthetic folic acid |
| `hormonal_profile.insulin_resistance` | `HIGH` | limit glycemic_velocity |
| `dynamic_state.inflammation_status` | `HIGH` | prefer lower oxidative_burden |

**Not clinical software.** Default honesty **OPEN**.

## User goals (weight / BMI)

```ts
import {
  MOCK_USER_GOALS_WEIGHT_LOSS,
  enrichUserGoals,
  goalProcessHints,
  FIXTURE_SALAD_OIL,
  toMachineContext,
} from "../src/lib/machines";

const goals = enrichUserGoals(MOCK_USER_GOALS_WEIGHT_LOSS);
// goals.body.bmi, bmi_band, energy_bias: deficit

const ctx = toMachineContext({ ...FIXTURE_SALAD_OIL, goals });
// ctx.host.goalPrimary === "weight_loss"
// ctx.host.bmiBand === "OBESITY_I"
```

| `primary` | Energy bias (if unspecified) |
|-----------|------------------------------|
| `weight_loss` | deficit |
| `weight_management` | maintenance |
| `weight_gain` | surplus |
| `recomp` / `performance` / … | unspecified unless set |

Hints only — **not** enforced on process/ScoreAxes yet. Honesty **OPEN**.

## User personas (named seed profiles)

Hand-crafted personas — **not** Faker noise. Same JSON is the SSOT for:

- Playground / app: `src/lib/machines/userPersonas.ts`
- Python simulator: `book/simulator_latest/fixtures/user_personas.py`

```ts
import {
  getPersona,
  resolveMockPersona,
  withPersonaHost,
  FIXTURE_SALAD_OIL,
  toMachineContext,
  personaSummaries,
} from "../src/lib/machines";

const taylor = getPersona("taylor"); // IR / at_risk
const run = withPersonaHost(FIXTURE_SALAD_OIL, "alex");
const ctx = toMachineContext(run);
// Switch: ?mockUser=riley  or  VITE_MOCK_USER=jordan
const demo = resolveMockPersona(new URLSearchParams(location.search).get("mockUser"));
```

| slug | Name | Primary goal | App state | Why |
|------|------|--------------|-----------|-----|
| `alex` | Alex Rivera | weight_loss | active | Happy path |
| `jordan` | Jordan Lee | recomp | power_user | High protein / training |
| `sam` | Sam Patel | general_health | plateau | Older / inflammation |
| `taylor` | Taylor Kim | metabolic_health | at_risk | IR + low adherence |
| `morgan` | Morgan Ellis | weight_management | onboarding | `host.ready=0` |
| `casey` | Casey Brooks | weight_management | active | Time-poor / UPF |
| `riley` | Riley Chen | general_health | power_user | Vegan high score |
| `avery` | Avery Torres | performance | power_user | Athlete energy needs |

Each persona embeds **HostState** + **HostClinicalProfile** + **UserGoals** (process-ready) plus product `preferences` / `app` / `recent_meals` for coach demos.

Python:

```bash
cd book/simulator_latest && python3 fixtures/user_personas.py
# or: from fixtures.user_personas import get_persona, apply_persona_to_physiological_state
```

### Provenance (book Part 0) — how a real user would have the data

Mocks must answer *where the number came from*, not invent perfect panels.

| Stream | Book home | Example providers (perishable) | Maturity |
|--------|-----------|--------------------------------|----------|
| Sleep / HRV / steps | 0.3, 0.6 L1 | Oura, Whoop, Apple Watch, Garmin | MATURE / EMERGING |
| CGM (output sensor) | 0.3, 0.6 | Libre, Dexcom, OTC CGM | MATURE |
| Blood panel | 0.3 deep diagnostic | Quest, Labcorp, Function Health | MATURE |
| Genetics ROM | 0.8 | 23andMe, SelfDecode | MATURE (partial dump) |
| Stool microbiome | 0.3 deep diagnostic | Viome, Thorne, Tiny Health | EMERGING |
| Food log | 0.3 food-shaped hole | tracking app, Cronometer, photo AI | EMERGING / MANUAL |
| Meds / supplements | 0.6 L4 | Pharmacy / HealthKit / self-report | MANUAL |
| Social / substances | 0.6, A.7 pillars | Onboarding questionnaire | MANUAL |

**Seven lifestyle loads** (ACLM six + book `kinetic_load`): sleep, activity, stress, social, substance_avoidance, nutrition_quality, kinetic_load — each has `load_0_1` + `source_ids` on the persona inventory.

**Readiness (Part 0.1):**
- `configure_ready` — age/sex/body present enough (`host.ready`)
- `calibrate_ready` — ≥1 wearable stream **or** labs/genetics/microbiome imported

```ts
import { getPersona, personaToAppFlags, personaConnectedSources } from "../src/lib/machines";
const flags = personaToAppFlags(getPersona("taylor")!);
// flags.hasCgm, hasLabs, hasGenetics, lifestyleLoads, configureReady, calibrateReady
```

## Product scoring

The product meal score is **proprietary and is not part of this open package**. The
open tree exposes only the four process measurements — see `ScoreAxes.schema.json`
and `score-axes.catalog.json`. Anything about the private scorer's internals is
deliberately omitted here.
