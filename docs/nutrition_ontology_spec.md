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

---

## 9. BodySystem mapped onto biology-as-code models

One object type. Kind is a discriminator, not a subclass.
Each instance is the current state of one physiological subsystem for one Human.
System Load Index is a function over those instances plus recent events. Do not store SLI as a property that goes stale.

`system_kind` ∈ {gi, renal, endocrine, hepatic}

### 9.1 Shared BodySystem shape

```
BodySystem
  system_id
  human_id
  system_kind
  as_of
  source                  # lab | inferred | model | user
  confidence
  state{}                 # kind-specific observables
  capacity{}              # kind-specific ceilings / reserve
  modifiers{}             # kind-specific coefficients used by functions
```

Link: Human `has_system` BodySystem (1:N).  
Link: DigestionEvent `occurred_in` BodySystem (N:1), usually `gi`.

### 9.2 GI — digestive assimilation flow

This is the primary input to `predictAbsorption`.

| State | What it is | Typical source |
|---|---|---|
| transit_time_h | mouth-to-exit or gastric + intestinal | RecordGIResponse, stool timing |
| enzyme_output | relative protease / lipase / amylase / lactase | inferred from symptoms + genetics, later assays |
| microbiome_diversity | alpha-diversity or coarse proxy | stool test, else default |
| mucosal_integrity | 0–1 barrier / inflammation proxy | calprotectin, symptoms |
| gastric_acidity | low / normal / high | meds (PPI), symptoms |

| Capacity | Meaning |
|---|---|
| max_meal_load | how much structure the tract can break this sitting |
| fiber_tolerance | fermentable load before symptoms |

| Modifiers written for functions | |
|---|---|
| absorption_rate | 0–1 scalar per nutrient class (iron, Ca, fat-sol vitamins, AA) |
| processing_penalty | extra loss if FoodBatch.processing_level is high (UPF / SLI hook) |

GI load contributors from a MealLog / DigestionEvent:
- refined starch + isolated sugar → glycemic_response
- emulsifiers / isolated fiber / industrial fats → mucosal + microbiome stress
- intact matrix + phytochemicals → lower load, often higher micronutrient yield

GI output into need:
```
absorbed[n] = intake[n] × absorption_rate[class(n)]
              × matrix_factor(food)
              × enzyme_factor(n)
              × transit_factor
```

### 9.3 Renal — clearance and electrolyte / nitrogen load

Does not absorb food. It changes **targets** and flags when intake is a burden.

| State | Source |
|---|---|
| egfr | LabResult creatinine / cystatin |
| hydration | intake logs, weight, labs |
| sodium_status | labs, BP proxy |
| potassium_status | labs |
| urea_load | inferred from protein intake + LabResult BUN |

| Capacity | |
|---|---|
| nitrogen_ceiling | protein load the kidney can clear without raising SLI |
| electrolyte_band | Na/K/PO4 acceptable window |

Renal output into need:
- if egfr low → lower protein target, lower K/PO4 target, raise fluid target
- urea_load high → raise SLI even if macros “hit goal”

Labs that implement AssayLike and attach here: creatinine, eGFR, BUN, Na, K, PO4.

### 9.4 Endocrine — setpoint layer

Changes **targets** and the glycemic half of DigestionEvent.

| State | Source |
|---|---|
| insulin_sensitivity | HOMA-IR, CGM variability, waist/TG proxy |
| thyroid_status | TSH, fT4 |
| cortisol_load | time-of-day, sleep, inferred |
| sex_hormone_context | age, sex, optional labs |
| vitamin_d_status | 25-OH D LabResult |

| Capacity | |
|---|---|
| glycemic_tolerance | how much rapid CHO before excursion |
| energy_setpoint | inferred TDEE band |

Endocrine output into need:
- low insulin_sensitivity → lower rapid-CHO rank in `rankNutrientSources`, higher fiber/protein rank
- low vitamin_d_status → raise vitamin D target; absorption still goes through GI + fat meal context
- thyroid low → lower energy target until treated; do not hide it inside “eat less”

AssayLike: glucose, HbA1c, insulin, TSH, 25-OH D, lipids.

### 9.5 Hepatic — first-pass and storage (include when you have the model)

| State | Source |
|---|---|
| alt_ast | labs |
| steatosis_proxy | labs + waist + TG |
| glycogen_status | inferred from intake timing |
| first_pass_capacity | alcohol, fructose, xenobiotic load |

Hepatic output:
- high fructose / ethanol load → SLI up, not just “calories”
- fat-soluble storage (A, D, E, K, B12 via other paths) changes whether gap is urgent

### 9.6 System Load Index (function, not an object)

```
systemLoad(human, window) → {
  total,              # 0–100
  by_system: { gi, renal, endocrine, hepatic },
  drivers: [],        # meal_ids / lab_ids that moved the score
  confidence
}
```

Each system returns a 0–1 load. Total is a weighted combine, not a sum of nutrients.

```
gi_load        = f(processing_level, glycemic_response, transit deviation,
                   mucosal_integrity, enzyme shortfall)
renal_load     = f(nitrogen above ceiling, electrolyte excursion, low egfr)
endocrine_load = f(glycemic excursion, low insulin_sensitivity, sleep/cortisol)
hepatic_load   = f(fructose+ethanol, ALT/AST, steatosis_proxy)

SLI = 100 × (w_gi·gi + w_ren·renal + w_end·endo + w_hep·hepatic)
```

Default weights until you fit them: gi 0.40, endocrine 0.25, hepatic 0.20, renal 0.15.

SLI is the *cost* of hitting a nutrient target.  
`nutrientGap` answers “are we short.”  
`systemLoad` answers “what did it cost the organism to get here.”  
A plan that closes iron gap by flooding refined cereal can raise SLI. Rank sources by absorbed nutrient **per load**, not per calorie.

### 9.7 How the three need functions read BodySystem

**predictAbsorption**  
Reads `gi.modifiers` first. Applies `endocrine.insulin_sensitivity` only to carbohydrate bioavailability / glycemic_response. Ignores renal. Missing BodySystem → default coefficients, confidence down.

**nutrientGap**  
Targets start from DRI × Human(age, sex, activity).  
Then `endocrine` and `renal` *rewrite targets* (protein, K, D, energy, fluid).  
Intake still comes from MealLog. Absorbed still comes from GI.

**rankNutrientSources**  
Score = absorbed[n] / (1 + ΔSLI if this source is eaten).  
That is the biology-as-code replacement for “eat this because USDA says so” and a cleaner alternative to using NOVA as the only ranking key. processing_level still feeds gi_load.

### 9.8 DigestionEvent as the GI sample

A DigestionEvent is one run of the GI model.

```
DigestionEvent
  occurred_in → BodySystem(kind=gi)
  transit_time_h          → writes back to gi.state.transit_time_h (EMA, not overwrite)
  glycemic_response       → writes endocrine.state snapshot + gi_load
  bioavailability{}       → output of predictAbsorption for that plate
```

Do not create a RenalEvent or EndocrineEvent yet. Those systems update from AssayLike labs and from aggregates of DigestionEvents.

### 9.9 Minimal code surface (matches the models)

```
class BodySystem:
    kind: Literal["gi", "renal", "endocrine", "hepatic"]
    state: dict
    capacity: dict
    modifiers: dict

def gi_assimilate(food: NutrientSource, gi: BodySystem, genes, endocrine) -> Bioavailability
def renal_adjust_targets(targets, renal: BodySystem) -> Targets
def endocrine_adjust_targets(targets, endocrine: BodySystem) -> Targets
def system_load(human, window) -> SLI
```

`BodySystem.gi` *is* the digestive assimilation model, persisted as state.  
The Python you are writing against LANGE is the function body.  
The ontology only stores the observables those functions need on the next call.

