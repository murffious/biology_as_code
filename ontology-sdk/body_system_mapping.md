# BodySystem → biology-as-code models

`BodySystem` is an **interface**, not one fat object.
Each implementer is a real organ-system model. Need and System Load Index are functions over those models.

```
MealLog + FoodBatch
        │
        ▼
predictAbsorption()
        │  calls, in order, every BodySystem the human has
        ▼
DigestiveAssimilation.absorb()     # breakdown + uptake
        │
        ▼
EndocrineSetpoint.modulate()       # insulin / thyroid / incretin setpoints
        │
        ▼
RenalHandling.retain()             # keep vs excrete
        │
        ▼
bioavailability[] on DigestionEvent
        │
        ▼
nutrientGap() = target − absorbed
systemLoadIndex() = Σ system.load(event)
```

Missing systems drop confidence. They do not crash the chain.

---

## 1. Interface

```python
class BodySystem(Protocol):
    system_id: str
    human_id: str
    system_kind: Literal["gi", "renal", "endocrine", "hepatic", "immune"]
    as_of: datetime
    source: str
    confidence: float  # 0–1, falls when state is inferred

    def absorb(self, incoming: NutrientVector, ctx: MealContext) -> NutrientVector:
        """Transform incoming nutrients. Default: identity."""
        ...

    def target_adjust(self, base_target: NutrientVector, human: PersonContext) -> NutrientVector:
        """Shift DRI-like targets. Default: identity."""
        ...

    def load(self, event: DigestionEvent, incoming: NutrientVector) -> SystemLoad:
        """Work this meal imposed on the system. Feeds System Load Index."""
        ...
```

Shared types:

```python
NutrientVector = list[tuple[str, float, str]]   # nutrient_id, amount, unit
SystemLoad = dict  # {system_kind, score_0_100, drivers[], confidence}
```

Ontology object type `BodySystem` keeps the identity row (`system_id`, `human_id`, `system_kind`).
Subtype-specific state lives on the implementer objects below. Do not put insulin, GFR, and lipase on one row.

---

## 2. Implementers (the models you are writing)

### A. DigestiveAssimilation  `system_kind = gi`

LANGE-shaped stages, not a single `absorption_rate` float.

| Stage | What the model does | State properties | Reads from food | Writes onto DigestionEvent |
|---|---|---|---|---|
| 1 Ingestion / matrix | Can enzymes reach the nutrient? | dentition_ok, gastric_ph, gastric_emptying_t | processing_level, fiber, fat | matrix_access_0_1 |
| 2 Luminal breakdown | Hydrolysis capacity | enzyme_output{amylase, lipase, protease, lactase}, bile_availability | macros, chain length | fraction_hydrolyzed[] |
| 3 Mucosal uptake | Transporters + surface | villus_integrity, transporter_capacity{sglt1, pept1, dmt1, npc1l1}, transit_time_h | mineral form (heme vs nonheme), phytate, oxalate | fraction_absorbed[] |
| 4 First-pass handoff | What leaves the gut | microbiome_diversity, scfa_potential, intestinal_inflammation | polyphenols, fermentable fiber | portal_delivery[] |

`absorb()`:

```
delivered = food.nutrient_vector
           × matrix_access
           × fraction_hydrolyzed
           × fraction_absorbed
           × (1 − gut_loss)
```

`load()` drivers (System Load Index, GI component):

- osmotic / fiber bulk vs transit_time_h
- enzyme demand vs enzyme_output (UPF / high refined starch raises demand)
- bile demand vs fat load
- fermentative load (FODMAP-like) vs microbiome_diversity
- epithelial stress if processing_level is ultra-processed and matrix is collapsed

`target_adjust()`: usually identity. Exception: documented malabsorption → raise target for the poorly absorbed nutrient (e.g. B12 if IF/ileum flagged). That raise is a **need change**, not a food score.

Link: `DigestionEvent.occurred_in → DigestiveAssimilation` is the default link. Every logged meal should hit this system if the object exists.

AssayLike inputs that calibrate it: fecal calprotectin, elastase, breath H2, serum B12/MMA, ferritin+TIBC as proxy for DMT1 iron path, CGM as glycemic_response.

---

### B. EndocrineSetpoint  `system_kind = endocrine`

Does not digest. It changes **how the same absorbed vector is handled** and **what the target is**.

| Axis | State properties | Nutrient effect | Need effect |
|---|---|---|---|
| Incretin / insulin | insulin_sensitivity, fasting_glucose, cgm_variability, glp1_tone | same carbs → different glycemic_response and storage vs oxidation | carb quality ranking changes more than carb grams |
| Thyroid | tsh, ft4, inferred_metabolic_rate | energy expenditure | energy + iodine + selenium targets |
| Adrenal / circadian | cortisol_pattern, meal_timing_fit | protein/glucose partitioning | timing constraints on NutritionPlan |
| Calcium–phosphate | pth, vit_d_status | Ca/P handling after gut | Ca, D, P, Mg targets |
| Sex steroids | (optional, later) | iron loss context in cycling humans | iron target_adjust |

`absorb()`: mostly identity. May scale **retained carbohydrate / fat** after GI delivery using insulin_sensitivity (not a second absorption step — a disposal step). Keep this explicit so you do not double-count GI absorption.

`target_adjust()` is the main job:

```
target_energy     *= f(inferred_metabolic_rate, activity_level)
target_iron       *= f(sex, losses)            # Human + this axis
target_vitamin_d  *= f(vit_d_status, season)   # FarmContext sunlight can feed this
target_iodine     *= f(thyroid axis present)
```

`load()` drivers:

- glycemic excursion vs insulin_sensitivity (CGM on DigestionEvent)
- protein load vs incretin tone
- late-night meal vs cortisol_pattern
- iodine/selenium gap while thyroid axis is strained

AssayLike inputs: A1c, CGM, TSH/FT4, 25-OH D, fasting insulin.

Genetics touch this system hard (T2D risk SNPs, DIO2, VDR). `modulates` stays a function: GeneticProfile → EndocrineSetpoint.state, not a stored link on every event.

---

### C. RenalHandling  `system_kind = renal`

Last gate: keep, convert, or dump.

| Function | State properties | Nutrient effect | Need effect |
|---|---|---|---|
| Filtration | egfr, hydration | water-soluble clearance | raise water-soluble targets only if wasting is documented |
| Electrolyte handling | na_setpoint, k_handling, phosphate_threshold | Na/K/P retained | Na/K/P targets |
| Vitamin D activation | 1a_hydroxylase_proxy (from 1,25 vs 25-OH if you have both) | converts 25-OH D → active | D target vs “active D available” |
| Nitrogen waste | bun_proxy, protein_load_tolerance | protein ceiling | protein target cap, not a floor |
| Acid–base | net_endogenous_acid_load tolerance | fruit/veg vs sulfur amino acids | ranking of NutrientSources, not grams of “alkaline” |

`absorb()` here means **retain after filtration**, not gut absorb:

```
retained = portal_or_systemic_vector
         × retain_fraction(egfr, nutrient_id)
         − obligatory_loss
```

`target_adjust()`:

- low egfr → cap protein, cap K/P, do not blindly raise
- high obligatory Ca/Mg loss → raise those targets
- poor 1α-hydroxylation → raising dietary D does less; flag conversion, don’t just inflate the DRI

`load()` drivers:

- nitrogen load from protein
- sodium load
- phosphate load (especially additive phosphate in UPF — processing_level again)
- acid load
- hydration vs solute load

AssayLike inputs: creatinine/eGFR, electrolytes, urine Na/K if available, 25-OH D ± 1,25, BUN.

---

### D. Later implementers (do not create objects yet)

| system_kind | Model name | Only add when |
|---|---|---|
| hepatic | HepaticTransform | you model first-pass conversion (folate, vit D 25-hydroxylation, first-pass AA) |
| immune | InflammatoryTone | you have CRP/calprotectin feeding load() |
| microbiome | (keep inside GI for now) | you have stool sequencing; until then it is a GI property |

Microbiome stays a **property of DigestiveAssimilation** until it has its own rows. That follows the Foundry rule: no object type without instances.

---

## 3. How the ontology functions call the models

### predictAbsorption(food, human, geneticProfile?, systems[])

```
vec = food.nutrient_vector * portion
ctx = MealContext(food.processing_level, food.phytochemical_load, event.transit_time_h)

gi    = systems.get("gi")
endo  = systems.get("endocrine")
renal = systems.get("renal")

if gi:    vec = gi.absorb(vec, ctx)
if endo:  vec = endo.absorb(vec, ctx)     # disposal, not a second gut
if renal: vec = renal.retain(vec, ctx)

# genetics scale specific nutrients after systems
vec = apply_alleles(vec, geneticProfile)

return vec with confidence = min(confidences used)
```

Order is physiological: lumen → setpoint / disposal → kidney.
Do not run renal before GI.

### nutrientGap(human, window)

```
base = dri(human.age, human.sex, human.activity_level)
for sys in human.systems:
    base = sys.target_adjust(base, human)

absorbed = sum(predictAbsorption(...) for meals in window)
gap = base - absorbed
```

Targets move because **systems** moved, not because a NutritionNeed row was edited.

### systemLoadIndex(human, event) → 0–100

This is the biology-as-code metric. It is a function, same rule as Need.

```
loads = [sys.load(event, incoming) for sys in human.systems if sys]
sli = weighted_mean(loads, weights={gi: 0.45, endocrine: 0.30, renal: 0.25})
```

Weights are a policy knob, not physiology. Publish them. Do not hide them inside absorb().

SLI answers a different question than gap:

| Function | Question |
|---|---|
| nutrientGap | Did the person get enough of nutrient X? |
| systemLoadIndex | How hard did this food make the body work to get it / clear it? |

A whey shake can close a protein gap and still raise renal + endocrine load.
An intact-matrix bean pot can be slower GI work and lower endocrine load per gram absorbed.

That is the point of keeping load() off the nutrient_vector.

---

## 4. Object / link / action changes

Replace the single `BodySystem` property bag with:

| Object type | Implements | Extra properties |
|---|---|---|
| DigestiveAssimilation | BodySystem | enzyme_output{}, transit_time_h baseline, microbiome_diversity, transporter_capacity{}, gastric_ph |
| EndocrineSetpoint | BodySystem | insulin_sensitivity, inferred_metabolic_rate, tsh, vit_d_status, cortisol_pattern |
| RenalHandling | BodySystem | egfr, na_setpoint, protein_load_tolerance, activation_d_proxy |

Links:

| Link | From | To | Cardinality |
|---|---|---|---|
| has_system | Human | BodySystem (interface) | 1:N |
| occurred_in | DigestionEvent | DigestiveAssimilation | N:1 recommended |
| calibrated_by | BodySystem | AssayLike | 1:N |
| modulated_by | BodySystem | GeneticProfile | N:1 derived |

Actions that write system state (not meal state):

| Action | Writes |
|---|---|
| IngestLabResult | already exists; side effect: if analyte maps to a system property, update that implementer + bump as_of |
| RecordGIResponse | updates DigestionEvent AND DigestiveAssimilation.transit / symptoms running baseline |
| RecalibrateSystem | explicit coach/model write of enzyme_output, egfr, insulin_sensitivity |

Do not add `UpdateNeed`. Need recomputes.

---

## 5. Property ownership (stop leaking)

| Property you had on generic BodySystem | Owner now |
|---|---|
| absorption_rate | delete — replaced by DigestiveAssimilation.absorb() |
| enzyme_output | DigestiveAssimilation |
| microbiome_diversity | DigestiveAssimilation |
| glycemic_response | DigestionEvent (observation), EndocrineSetpoint (trait) |
| inferred_metabolic_rate | EndocrineSetpoint (and/or GeneticProfile) |
| egfr | RenalHandling |
| processing_level | FoodBatch — systems read it, they do not store it |

`absorption_rate` as a single float fights the model. Kill it.

---

## 6. Minimum to code

1. `BodySystem` protocol with absorb / target_adjust / load
2. `DigestiveAssimilation` with three coefficients: matrix_access, hydrolyze, uptake
3. `EndocrineSetpoint.target_adjust` for energy + D + iron only
4. `RenalHandling.retain` as identity until eGFR exists
5. `systemLoadIndex` averaging whatever implementers are present

GI first. Endocrine second. Renal as a pass-through until labs exist.
Same rule as the ontology: no object without rows, no term without a function.
