# Food subsets taxonomy

**Home:** `machines/schemas/food-subsets/`  
**Honesty:** OPEN / FLOW teaching labels — not clinical grades, not chain endorsements.

## Design rule (important)

**Acquisition context ≠ food quality.**

Someone can buy a **nice salad at a drive-thru** or a **UPF dessert at home**.  
So we **never** encode “fast food” as automatically NOVA-4 or low quality.

| Axis | Answers | Does *not* answer |
|------|---------|-------------------|
| **Acquisition / venue** | Where / how obtained (QSR, grocery, home-cooked…) | How healthy the plate is |
| **Packet quality** | NOVA, matrix, density, HP, oils, sugars | Whether it came from a chain |

```text
meal_context.acquisition  →  "quick_service_restaurant"
packet quality (separate) →  nova_max, plate_quality, avoid_flags, HP-1…
```

### Examples

| Plate | Acquisition | Quality signals |
|-------|-------------|-----------------|
| McDonald’s side salad + grilled chicken, olive oil dressing | `quick_service` | may be **NOVA 1–3**, high quality |
| Homemade Pop-Tarts breakfast | `home_prepared` | still **NOVA 4** / UPF |
| Gas-station chips + soda | `convenience_retail` | NOVA 4, high HP risk |
| Chipotle-style bowl (beans, rice, salsa, veg) | `fast_casual` | mixed NOVA; judge by packet |

---

## Three subset taxonomies

| File | Purpose |
|------|---------|
| `meal-acquisition.catalog.json` | Venue / channel (includes fast food **as context**) |
| `oil-lipid.catalog.json` | Oil / fat identity + lipid profile fields |
| `sugar-profile.catalog.json` | Sugar kinds, added vs intrinsic, sweetener flags |
| `FoodSubsetTags.schema.json` | Shape of tags attached to a meal or ingredient |
| `classify_food_subsets.py` | Rule classifier over SSOT meal fixtures |

---

## Fast food — recommended model

Use **acquisition**, not a quality category:

```json
"meal_context": {
  "acquisition": "quick_service",
  "acquisition_detail": "drive_thru",
  "chain_hint": "generic_qsr",
  "confidence": "declared"
}
```

Optional convenience **bundle tags** (not scores):

- `qsr_salad_path` — user chose salad / grilled / veg-forward at QSR  
- `qsr_combo_path` — classic combo (burger/nuggets/fries/soda)  
- `qsr_unknown` — venue known, plate not classified  

**Scoring still uses the packet** (macros, NOVA, oils, sugars).  
Acquisition only answers: *“Was this a time-poor / out-of-home channel?”* (useful for coach demos, Casey persona, logging friction).

---

## Oils & sugars

Independent of venue:

- **Oils:** `oil_class` + measured `lipid_profile` (sat/MUFA/PUFA/ω/trans) when present  
- **Sugars:** `sugar_kind` + totals + industrial sweetener flags  

See catalogs for enums and HP-1 / glycemic hooks.

---

## Honesty

- No chain API, no “this restaurant is healthy.”  
- Declared acquisition can be wrong (user mis-taps “drive-thru”).  
- Classifier guesses are `confidence: rule` — prefer user declare later.
