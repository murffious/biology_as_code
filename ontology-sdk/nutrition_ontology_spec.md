# Nutrition Ontology Spec (v0.1)
Digital twin of a person's nutrition world.
Need is computed, not stored.

## 1. Object types

| Object type | Kind | Primary key | Title | Required properties | Optional properties |
|---|---|---|---|---|---|
| Human | entity | human_id | display_name | age, sex, activity_level | bmi, goals[], timezone |
| GeneticProfile | entity | profile_id | panel_name | human_id | snps{}, alleles{}, inferred_metabolic_rate |
| FoodBatch | entity | batch_id | food_name | nutrient_vector[] | harvest_date, phytochemical_load, processing_level |
| FarmContext | entity | farm_id | plot_name | — | npk{}, ph, temp_c, sunlight_hours, microbiome_density |
| BodySystem | entity | system_id | system_name | human_id, system_kind | absorption_rate, enzyme_output, microbiome_diversity |
| MealLog | event | meal_id | logged_at | human_id, logged_at | portion, photo_uri, estimated_macros{} |
| DigestionEvent | event | digestion_id | occurred_at | human_id, occurred_at | transit_time_h, glycemic_response, bioavailability{} |
| LabResult | event | lab_id | analyte + drawn_at | human_id, analyte, value, unit, drawn_at | method, lab_name |
| NutritionPlan | entity | plan_id | title | human_id, status, targets[] | constraints[], valid_from, valid_to |

`system_kind` ∈ {gi, renal, endocrine, hepatic, immune}

`status` on NutritionPlan ∈ {draft, offered, accepted, superseded}

### Nutrient measurement shape (shared)
Use this array everywhere instead of one column per nutrient:

```
nutrient_vector[] / targets[] / bioavailability[] / estimated_macros{}:
  { nutrient_id, amount, unit, confidence? }
```

Shared metadata on every object: `as_of`, `source`, `confidence`

---

## 2. Link types

| Link type | From | To | Cardinality | Required? | Stored on |
|---|---|---|---|---|---|
| has_profile | Human | GeneticProfile | 1:1 | no | GeneticProfile.human_id |
| experiences | Human | DigestionEvent | 1:N | yes | DigestionEvent.human_id |
| logged | Human | MealLog | 1:N | yes | MealLog.human_id |
| consumed_in | FoodBatch | DigestionEvent | N:N | no | join table |
| plated_in | FoodBatch | MealLog | N:N | yes if known food | join table |
| occurred_in | DigestionEvent | BodySystem | N:1 | no | DigestionEvent.system_id |
| grown_in | FoodBatch | FarmContext | N:1 | no | FoodBatch.farm_id |
| modulates | GeneticProfile | DigestionEvent | 1:N | derived | function, not stored |
| evidenced_by | NutritionPlan | LabResult \| MealLog | 1:N | no | join table |
| applies_to | NutritionPlan | Human | N:1 | yes | NutritionPlan.human_id |
| has_system | Human | BodySystem | 1:N | no | BodySystem.human_id |

Do not persist `modulates`. Genetics change predicted absorption at read time.

---

## 3. Interfaces

| Interface | Implementers | Shared fields | Why |
|---|---|---|---|
| NutrientSource | FoodBatch, Recipe*, Supplement* | nutrient_vector[], serving, density | rank any edible the same way |
| AssayLike | LabResult, FoodAssay*, CgmReading* | analyte, value, unit, observed_at | one ingest path for measurements |
| PersonContext | Human | age, sex, activity_level | function inputs stay stable |

\* Recipe, Supplement, FoodAssay, CgmReading are later types. Do not create them until you have rows.

---

## 4. Action types

Writes only. Nightly USDA / CGM sync stays a pipeline.

### LogMeal
- Params: human, items[] (`NutrientSource` + portion), logged_at, photo?
- Preconditions: human exists; each item implements NutrientSource; portion > 0
- Effects:
  - create MealLog
  - create DigestionEvent
  - create `plated_in` and `consumed_in` links
  - side effect: run `predictAbsorption`, write bioavailability{} onto the event
- Invalid if: free-text food with no NutrientSource and no pending-match flag

### AttachGeneticReport
- Params: human, snps{}, source
- Preconditions: human exists; snp keys are known rsIDs or flagged unknown
- Effects: upsert GeneticProfile; link has_profile
- Side effect: mark open NutritionPlan as stale (do not auto-rewrite)

### RecordGIResponse
- Params: digestion_id, transit_time_h?, symptoms[], glycemic_response?
- Preconditions: event exists and belongs to caller / coach-of
- Effects: update DigestionEvent
- Side effect: if transit or symptoms exceed thresholds, tag BodySystem.gi

### IngestLabResult
- Params: human, analyte, value, unit, drawn_at
- Preconditions: unit compatible with analyte; drawn_at not in the future
- Effects: create LabResult
- Side effect: if value outside personal or clinical band, expose gap in next `nutrientGap()`

### GenerateNutritionPlan
- Params: human, horizon_days, constraints[]
- Preconditions: human exists
- Effects: create NutritionPlan (status=draft) from `planWeek()`; link applies_to
- Does not accept the plan. That is a separate write.

### AcceptRecommendation
- Params: plan_id
- Preconditions: plan.status ∈ {draft, offered}; plan belongs to human
- Effects: status=accepted; any previous accepted plan → superseded
- Side effect: freeze targets[] for valid_from/valid_to

---

## 5. Functions (need lives here)

### predictAbsorption(food, human, geneticProfile?, bodySystem?) → nutrient_vector[]
What fraction of each nutrient becomes available.

Inputs used if present, ignored if missing:
- food.nutrient_vector and processing_level
- bodySystem.absorption_rate, microbiome_diversity
- geneticProfile alleles that touch that nutrient (e.g. MTHFR/folate, HFE/iron, GC/vitamin D)
- meal context from the sibling DigestionEvent if already created

Missing inputs → lower confidence, not a failed call.

### nutrientGap(human, window) → { nutrient_id, target, intake, absorbed, gap, confidence }[]
The need function.

```
target    = DRI adjusted by age, sex, activity, plus allele modifiers
intake    = sum of NutrientSource.nutrient_vector on MealLogs in window
absorbed  = sum of DigestionEvent.bioavailability in window
            (fall back to intake × default coefficient if no event)
gap       = target − absorbed
```

Never write this array onto Human. Call it when the Object View opens and when GenerateNutritionPlan runs.

### rankNutrientSources(human, nutrient_id, constraints) → NutrientSource[]
Order implementers of NutrientSource by:
1. absorbed amount per serving for that nutrient
2. constraint fit (allergen, pattern, budget, UPF/processing_level)
3. confidence of the underlying assay

Used by GenerateNutritionPlan; also usable as a standalone coach query.

### planWeek(human, goals) → NutritionPlan draft
Orchestrator, not a fourth primitive.
Calls nutrientGap + rankNutrientSources, writes targets[] and a suggested source list. Persisted only through GenerateNutritionPlan.

---

## 6. Object views

**Human 360** — profile, SNPs, 7-day gap chart, recent meals, open labs, current accepted plan  
**FoodBatch lineage** — farm context, assays, who ate it, reported GI outcomes  
**DigestionEvent replay** — plate → transit → glycemic → next lab  

Coach UI reads views. It does not query five tables.

---

## 7. What not to model yet

- NutritionalNeed as an object (stale the next time someone eats)
- One property per micronutrient
- FarmContext as required (most rows will not have plot-level NPK)
- Recipe / Supplement types before you have instances
- Foundry roles/platform until there is a second actor (coach, lab, farm) writing into the same twin

---

## 8. Minimum viable graph

Ship with only:
1. Human
2. MealLog
3. FoodBatch (or any NutrientSource)
4. LabResult
5. NutritionPlan
6. Functions: nutrientGap, rankNutrientSources
7. Actions: LogMeal, IngestLabResult, GenerateNutritionPlan, AcceptRecommendation

Add GeneticProfile, DigestionEvent, BodySystem, FarmContext when those rows exist.

Need = target − absorbed.
Absorbed is a function of food × gut × genes.
Everything else is memory for that calculation.
