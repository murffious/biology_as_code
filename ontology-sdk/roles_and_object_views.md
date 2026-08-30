# Roles matrix and Object Views
Closes the two remaining core Foundry concepts: Roles and Object Views.

Need and SLI stay functions. Views *call* them. Roles decide who can run the actions that change the twin.

---

## 1. Roles

Grant at two levels:
- Ontology resource (type-level): who even knows `LabResult` exists
- Object instance: which Human / which Plan

| Role | Who | Scope |
|---|---|---|
| `client` | The person whose twin this is | objects linked to their `human_id` |
| `coach` | A coaching application or a human clinician | assigned Human set only |
| `lab_writer` | Lab, CGM vendor, assay pipeline | create `AssayLike` for a consented human |
| `catalog_editor` | USDA sync, farm, public food schema | `FoodBatch`, `FarmContext` only |
| `pipeline` | Nightly jobs | no PHI writes except via action types |
| `public_reader` | Policy / research | published catalog + aggregated de-identified metrics |

No role sees another client’s GeneticProfile, LabResult, or MealLog.

### 1.1 Object types

R = read, W = edit properties, C = create, — = none  
Instance scope in parentheses.

| Object type | client | coach | lab_writer | catalog_editor | pipeline | public_reader |
|---|---|---|---|---|---|---|
| Human | R (self) | R/W assigned | — | — | R ids only | — |
| GeneticProfile | R self | R assigned | — | — | — | — |
| MealLog | R/C self | R assigned | — | — | — | — |
| DigestionEvent | R self | R assigned | — | — | R | — |
| LabResult | R self | R assigned | C consented | — | C via action | — |
| DigestiveAssimilation / EndocrineSetpoint / RenalHandling | R self | R assigned | — | — | R | — |
| NutritionPlan | R self | R/W assigned | — | — | R | — |
| FoodBatch | R | R | — | R/W/C | C | R published |
| FarmContext | R | R | — | R/W/C | C | R published |

PHI objects are never world-readable. Catalog objects are.

### 1.2 Actions

| Action | client | coach | lab_writer | catalog_editor | pipeline |
|---|---|---|---|---|---|
| LogMeal | yes (self) | yes (assigned, with audit) | — | — | — |
| RecordGIResponse | yes (self) | yes (assigned) | — | — | — |
| AttachGeneticReport | yes (self) | yes (assigned) | — | — | — |
| IngestLabResult | — | yes (assigned) | yes (consented human) | — | yes (if mapped to this action) |
| RecalibrateSystem | — | yes | — | — | yes from new assays |
| GenerateNutritionPlan | yes (self, draft only) | yes (assigned) | — | — | — |
| AcceptRecommendation | yes (self only) | — | — | — | — |
| PublishFoodBatch | — | — | — | yes | yes |

`AcceptRecommendation` is client-only on purpose. A coach can offer a plan. Only the person accepts it.

### 1.3 Functions

Functions inherit the object-set they are passed. No extra privilege.

| Function | client | coach | public_reader |
|---|---|---|---|
| predictAbsorption | own meals | assigned | — |
| nutrientGap | own window | assigned | — |
| rankNutrientSources | yes (catalog is public) | yes | catalog-only, no personal gap |
| systemLoadIndex | own events | assigned | de-identified aggregate later |
| planWeek | own draft | assigned | — |

### 1.4 Default deny

- Coach cannot accept a plan.
- Catalog editor cannot read MealLog.
- Lab writer cannot read GeneticProfile.
- Public reader cannot call nutrientGap on a human_id.
- Pipeline cannot patch Human.goals; it can only submit declared actions.

---

## 2. Object Views

A view is the hub for one object: header properties, linked objects, derived metrics, actions the current role may run.

Widgets call functions at render time. They do not read a stored Need column.

### 2.1 Human 360  — object: Human

**Header**
- display_name, age, sex, activity_level, as_of
- Role chip: you are client | coach
- Confidence strip: % of systems present, last lab date, last meal date

**Row A — derived metrics (functions)**
- 7-day `nutrientGap` bars (target vs absorbed, not intake)
- `systemLoadIndex` sparkline for last 14 meals
- Current NutritionPlan status + valid_to

**Row B — linked objects**
- GeneticProfile summary (allele chips that actually change targets)
- BodySystem cards: GI / Endocrine / Renal, each with confidence and last calibrated_by assay
- Last 10 MealLogs (time, title, SLI, gap contribution)

**Row C — labs and plan**
- Open LabResults (out-of-band analytes highlighted)
- Accepted plan targets vs this week’s absorbed
- Suggested NutrientSources from `rankNutrientSources` for the largest gap

**Actions in the rail (role-filtered)**
- client: LogMeal, RecordGIResponse, AttachGeneticReport, GenerateNutritionPlan (draft), AcceptRecommendation
- coach: same except AcceptRecommendation; plus RecalibrateSystem, IngestLabResult, GenerateNutritionPlan

**Do not put on this view**
- Farm NPK tables
- Raw SNP file
- Per-nutrient column dump

---

### 2.2 FoodBatch lineage  — object: FoodBatch

**Header**
- food_name, batch_id, harvest_date, processing_level
- nutrient_vector (top 8 + “more”)
- confidence / source (USDA vs farm assay vs user)

**Row A — origin**
- Linked FarmContext if present (NPK, sunlight, pH) — hide section if no link
- processing_level callout (feeds GI.load)

**Row B — biological effect (functions, not marketing)**
- Predicted absorb() through a *reference* GI (baseline coefficients) vs through *this client’s* GI if the viewer is in a Human context
- Estimated SLI contribution: GI / endocrine / renal slices

**Row C — who used it (role-gated)**
- client/coach: this human’s MealLogs that plated_in this batch + reported GI responses
- catalog_editor / public_reader: de-identified use counts only, or nothing

**Actions**
- catalog_editor: edit nutrient_vector, link grown_in
- client/coach: “add to LogMeal” (opens action with this batch prefilled)

---

### 2.3 DigestionEvent replay  — object: DigestionEvent

**Header**
- occurred_at, human title, transit_time_h, glycemic_response
- confidence of bioavailability[]

**Timeline (left → right)**
1. MealLog plate (FoodBatches + portions)
2. DigestiveAssimilation.absorb — matrix / hydrolyze / uptake coefficients used
3. EndocrineSetpoint.absorb — disposal, if present
4. RenalHandling.absorb — retain, if present
5. bioavailability[] written on this event
6. Following LabResults in the next 24–72h (evidenced_by)

**Side panel**
- system.load() for this event (three scores + drivers)
- alleles that changed this event (function, not a stored link)

**Actions**
- RecordGIResponse (client/coach)
- RecalibrateSystem if the coach is correcting a coefficient that this replay exposed

---

### 2.4 NutritionPlan desk  — object: NutritionPlan

**Header**
- title, status, valid_from / valid_to, who generated

**Body**
- targets[] vs live `nutrientGap` for the same window
- ranked sources that the plan named
- constraints[] (allergen, pattern, UPF cap)

**Actions**
- client: AcceptRecommendation if status ∈ {draft, offered}
- coach: GenerateNutritionPlan (creates a new draft; does not overwrite accepted)
- Accepting supersedes the previous accepted plan — shown as a link, not a delete

---

### 2.5 BodySystem card  — object: DigestiveAssimilation | EndocrineSetpoint | RenalHandling

Opened from Human 360, not a top-level nav item at MVP.

**Header**
- system_kind, as_of, source, confidence

**State**
- implementer properties only (enzyme_output vs egfr vs insulin_sensitivity)
- calibrated_by AssayLike list

**Behavior**
- last 7 events: this system’s load() series
- which nutrient_ids this system currently scales in absorb() or target_adjust()

**Actions**
- coach: RecalibrateSystem
- client: read-only unless the property is a self-report (symptoms → GI)

---

## 3. View × role matrix

| View | client | coach | lab_writer | catalog_editor | public_reader |
|---|---|---|---|---|---|
| Human 360 | own | assigned | — | — | — |
| FoodBatch lineage | yes | yes | — | yes | published batches |
| DigestionEvent replay | own | assigned | — | — | — |
| NutritionPlan desk | own | assigned | — | — | — |
| BodySystem card | own | assigned | — | — | — |

---

## 4. Widget rules

1. Gap and SLI widgets call functions on open and on action success. No cache older than the latest MealLog / LabResult `as_of`.
2. Empty systems render as “not calibrated · confidence low”, not as zeros.
3. Catalog pages never embed a named Human.
4. Every action button is hidden if the role matrix says no — do not show a disabled Accept to the coach.
5. Derived numbers always show confidence next to the value.

---

## 5. MVP views

Ship two:
1. Human 360 (client + coach)
2. FoodBatch lineage (everyone who can read food)

Add DigestionEvent replay when DigestionEvent objects exist.
Add BodySystem card when RecalibrateSystem exists.
Add NutritionPlan desk when GenerateNutritionPlan writes drafts.
