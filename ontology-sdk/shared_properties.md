# Shared properties

Foundry definition: a property used on multiple object types so name, description, base type, formatting, type classes, and render hints are edited in one place. Values stay per object. Globe icon in Ontology Manager. Not the same thing as a *shared ontology* (multi-org space).

Employee.start_date and Contractor.start_date share metadata. Their dates are different rows.

---

## Why this matters here

Nutrition breaks when the same idea is typed differently on each object:

- FoodBatch stores `mg`
- LabResult stores `milligrams`
- Plan target stores `Milligram`
- DigestionEvent stores a float with no unit

A shared property forces one base type, one format, one description. Interfaces (`NutrientSource`, `AssayLike`, `BodySystem`) should be built from these fields, not from lookalike columns.

---

## Catalog (register once)

### Provenance (on almost every type)

| Shared property | Base type | Format / type class | Search | Used on |
|---|---|---|---|---|
| `as_of` | timestamp | ISO-8601, timezone-aware | sort yes, search no | Human, all events, all systems, Plan, FoodBatch |
| `source` | string | enum: user, lab, farm_assay, usda, model, coach | yes | same |
| `confidence` | double | 0–1, 2 decimal | no | same |

`as_of` is the “start date” of this ontology. Change its description once: *When this value was true in the world, not when it was written.*

### Identity

| Shared property | Base type | Notes | Used on |
|---|---|---|---|
| `human_id` | string | title-key never; always a foreign key | GeneticProfile, MealLog, DigestionEvent, LabResult, BodySystem implementers, NutritionPlan |
| `display_name` | string | searchable | Human, FoodBatch, FarmContext, Plan |

### Measurement (the load-bearing set)

Do not make `protein_mg` a property. Make these four shared, then put them in an array/struct.

| Shared property | Base type | Format | Used inside |
|---|---|---|---|
| `nutrient_id` | string | controlled vocab (same catalog as USDA + extras) | nutrient_vector[], targets[], bioavailability[], LabResult.analyte (alias) |
| `amount` | double | raw number, never a string | same |
| `unit` | string | UCUM (`mg`, `ug`, `g`, `kcal`, `IU`) | same |
| `analyte` | string | same vocab as nutrient_id where they overlap | LabResult, FoodAssay, CGM-as-AssayLike |

`LabResult.analyte` should *use* the `nutrient_id` shared property, or a shared `analyte` that is explicitly mapped to it. Two vocabularies is how iron labs stop joining to iron in food.

### Food / process

| Shared property | Base type | Used on |
|---|---|---|
| `processing_level` | string enum: intact, processed, ultra | FoodBatch, Recipe*, MealLog (derived rollup only) |
| `harvest_date` | date | FoodBatch, FarmContext |
| `geo` | geopoint or string | FarmContext, Environment |

### Body / plan

| Shared property | Base type | Used on |
|---|---|---|
| `system_kind` | string enum: gi, endocrine, renal | BodySystem implementers |
| `status` | string enum: draft, offered, accepted, superseded | NutritionPlan (do not reuse for labs) |

`status` is a good example of what **not** to overshare. Plan status ≠ lab status ≠ meal status. Shared properties are for the same meaning, not the same English word.

---

## Metadata to centralize

For each row above, lock:

| Metadata | Example on `amount` |
|---|---|
| Name | Amount |
| Description | Magnitude of a nutrient or analyte. Unit lives on `unit`. Never store “12 mg” in this field. |
| Base type | double |
| Value formatting | 2–4 decimals, no unit suffix |
| Render hints | not searchable; sortable only inside a single analyte |
| Visibility | normal (prominent would spam every view) |

For `confidence`: hidden on catalog-facing FoodBatch views for public_reader if you do not want model scores in policy exports; prominent on Human 360.

Render hints matter: making `confidence` searchable on every type will tax indexes for no product reason.

---

## Shared property vs nearby concepts

| Concept | What is shared | What is not |
|---|---|---|
| Shared property | field metadata | the values |
| Interface | shape + methods (`absorb`, `load`) | implementation |
| Shared ontology | whole ontology across orgs | n/a for a single-org deployment until farms/labs are separate orgs |
| Link type | relationship schema | the edges |

`NutrientSource` says “this type has a nutrient_vector.”
`amount` + `unit` + `nutrient_id` say “those three columns always mean the same thing.”
You want both. Interface without shared properties still lets Recipe invent `qty` and FoodBatch keep `amount`.

---

## What to share / what to keep local

**Share** if you would be angry to see two formatters for it.
**Keep local** if the meaning diverges.

| Share | Do not share |
|---|---|
| as_of, source, confidence | Human.goals (shape is local) |
| nutrient_id, amount, unit | enzyme_output (GI only) |
| human_id | egfr (renal only) |
| processing_level | NutritionPlan.constraints |
| display_name | MealLog.photo_uri |

---

## Failure modes this prevents

1. Unit drift (`mg` vs `milligram` vs `mcg` labeled `mg`)
2. Time drift (`created_at` vs `logged_at` vs `drawn_at` all meaning “when it was true”)
3. Analyte ≠ nutrient_id so labs never hit `nutrientGap`
4. Confidence as 0–100 on systems and 0–1 on meals
5. `status` reused until “accepted” appears on a lab

---

## Implementation note (without Foundry)

A shared property in code is:

```text
registry/properties.yaml   # metadata
object_type.MealLog.as_of  # uses registry id "as_of"
object_type.LabResult.as_of
```

The object keeps its own API field name if you must (`drawn_at` can *use* shared `as_of`). Foundry does exactly that: object property ID stays stable; shared metadata attaches. Use that for LabResult — UX says “drawn at,” ontology says this is `as_of`.
